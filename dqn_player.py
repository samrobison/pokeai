"""
DQNPlayer — poke-env Player that uses a trained DQN model for move selection.

Behaviour:
  • Force switches → minimax switch-scorer (same as minimax player)
  • Normal turns   → DQN (epsilon-greedy)
  • No model file / model can't decide → minimax fallback

Running:
    python dqn_player.py            # 1 game, loads model.pt
    python dqn_player.py 5          # 5 games
    python dqn_player.py --model path/to/model.pt --epsilon 0.1

Training workflow:
    1.  python player.py 20         # collect 20 games of minimax data
    2.  python train_offline.py     # warm-start + Q-learning → model.pt
    3.  python dqn_player.py 20     # play with DQN, collect more data
    4.  python train_offline.py     # retrain on combined data
    5.  repeat
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional

import numpy as np

from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import Player

from database import initDb
from dqn_model import DuelingDQN
from game_logger import LOG_PATH, build_state, log_state
from minimax import choose_best_move, choose_best_switch
from state_encoder import ACTION_DIM, STATE_DIM, encode_action_mask, encode_state

# Auto-detect best available device
import torch
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"


class DQNPlayer(Player):
    """
    Pokemon Showdown player that selects moves using a Dueling DQN.

    Parameters
    ----------
    model_path : str
        Path to a saved model checkpoint (created by train_offline.py).
        If the file doesn't exist the player falls back to minimax.
    epsilon : float
        Epsilon for ε-greedy exploration (0 = greedy, 1 = random).
    fallback_depth : int
        Minimax depth used when DQN falls back.
    """

    def __init__(
        self,
        *args,
        model_path:     str   = "model.pt",
        epsilon:        float = 0.05,
        fallback_depth: int   = 2,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._announced: set[str] = set()
        self.epsilon        = epsilon
        self.fallback_depth = fallback_depth

        self.model: Optional[DuelingDQN] = None
        if os.path.exists(model_path):
            try:
                self.model = DuelingDQN.load(model_path, device=DEVICE)
                print(f"DQN model loaded from {model_path}  (device={DEVICE}, ε={epsilon})")
            except Exception as exc:
                print(f"Warning: could not load model from {model_path}: {exc}")
                print("Will fall back to minimax.")
        else:
            print(f"No model at {model_path} — using minimax only.")

    # ── DQN action selection ──────────────────────────────────────────────────

    def _dqn_choose(self, battle):
        """
        Use the DQN to pick an action for a normal (non-force-switch) turn.

        Returns (env_action, label_str, method_str) or (None, None, reason_str)
        if selection fails.
        """
        assert self.model is not None

        state = build_state(battle)
        s_vec = encode_state(state)
        mask  = encode_action_mask(state)

        if not mask.any():
            return None, None, "no_valid_actions"

        # ε-greedy
        if np.random.random() < self.epsilon:
            idx    = int(np.random.choice(np.where(mask)[0]))
            method = "explore"
        else:
            q   = self.model.q_values(s_vec, mask, DEVICE)
            idx = int(np.argmax(q))
            method = "dqn"

        # Map index → poke-env object
        if idx < 4:
            moves = battle.available_moves
            if idx < len(moves):
                return moves[idx], moves[idx].id, method
        else:
            switches = battle.available_switches
            sw_idx = idx - 4
            if sw_idx < len(switches):
                return switches[sw_idx], switches[sw_idx].species, method

        return None, None, "idx_out_of_bounds"

    # ── Main decision hook ────────────────────────────────────────────────────

    def choose_move(self, battle):
        if battle.battle_tag not in self._announced:
            self._announced.add(battle.battle_tag)
            print(f"Battle started: https://play.pokemonshowdown.com/{battle.battle_tag}")

        action: Optional[str] = None
        action_type: Optional[str] = None

        # ── Force switch: use minimax switch scorer ───────────────────────────
        if battle.force_switch:
            env_poke = choose_best_switch(battle)
            if env_poke is not None:
                order = self.create_order(env_poke)
                action, action_type = env_poke.species, "switch"
                print(f"  Turn {battle.turn}: force-switch → {env_poke.species}")
            else:
                order = self.choose_random_move(battle)
                print(f"  Turn {battle.turn}: force-switch → random")

        # ── Normal turn: DQN ─────────────────────────────────────────────────
        elif self.model is not None:
            env_action, label, method = self._dqn_choose(battle)

            if env_action is not None:
                order = self.create_order(env_action)
                # Determine action type for logging
                from poke_env.battle.move import Move as EnvMove
                action_type = "move" if isinstance(env_action, EnvMove) else "switch"
                action = label
                print(f"  Turn {battle.turn}: {method} → {label}")

            else:
                # DQN couldn't decide; fall back to minimax
                env_action = choose_best_move(battle, depth=self.fallback_depth)
                if env_action is not None:
                    order = self.create_order(env_action)
                    label = getattr(env_action, "id", None) or getattr(env_action, "species", "?")
                    print(f"  Turn {battle.turn}: minimax fallback → {label}")
                else:
                    order = self.choose_random_move(battle)
                    print(f"  Turn {battle.turn}: random fallback")

        # ── No model: pure minimax ────────────────────────────────────────────
        else:
            env_action = choose_best_move(battle, depth=self.fallback_depth)
            if env_action is not None:
                order = self.create_order(env_action)
                label = getattr(env_action, "id", None) or getattr(env_action, "species", "?")
                action = label
                action_type = "move"
                print(f"  Turn {battle.turn}: minimax → {label}")
            else:
                order = self.choose_random_move(battle)
                print(f"  Turn {battle.turn}: random fallback")

        # ── Resolve action for logging if not already set ─────────────────────
        if action is None and hasattr(order, "order"):
            from poke_env.battle.move import Move as EnvMove
            from poke_env.battle.pokemon import Pokemon as EnvPokemon
            if isinstance(order.order, EnvMove):
                action, action_type = order.order.id, "move"
            elif isinstance(order.order, EnvPokemon):
                action, action_type = order.order.species, "switch"

        log_state(build_state(battle, action=action, action_type=action_type))
        return order


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    import argparse
    from userinfo import username, password

    parser = argparse.ArgumentParser(description="Play Pokemon Showdown with DQN")
    parser.add_argument("n",         nargs="?", type=int, default=1,
                        help="Number of battles to play")
    parser.add_argument("--model",   default="model.pt",
                        help="Path to trained model checkpoint")
    parser.add_argument("--epsilon", type=float, default=0.05,
                        help="Exploration rate (0=greedy, 1=random)")
    args = parser.parse_args()

    initDb()

    player = DQNPlayer(
        account_configuration = AccountConfiguration(username, password),
        server_configuration  = ShowdownServerConfiguration,
        battle_format         = "gen9randombattle",
        model_path            = args.model,
        epsilon               = args.epsilon,
        start_timer_on_battle_start = True,
    )

    print(f"Queuing for {args.n} game(s) as {username}…")
    await player.ladder(args.n)
    print(f"\nDone.  {player.n_won_battles}W / {player.n_lost_battles}L")
    print(f"Game states logged to: {LOG_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
