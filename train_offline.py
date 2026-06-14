"""
Offline DQN training from battles.jsonl.

Outcome-driven Q-learning (Double DQN):
  Build (s, a, r, s′, done) transitions from logged episodes.
  Reward: HP-delta per turn + ±1.0 terminal win/loss bonus, so the network
  learns the actions that lead to WINNING games rather than imitating the
  policy that generated the data (minimax). Losing games still contribute as
  negative signal through their −1.0 terminal reward.
  Loss: smooth-L1 Bellman error with action masking.

Usage:
    python train_offline.py                        # defaults
    python train_offline.py --log battles.jsonl --out model.pt
    python train_offline.py --ql_epochs 40         # train longer
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

import numpy as np
import torch
import torch.nn.functional as F

from dqn_model import DuelingDQN
from replay_buffer import ReplayBuffer
from state_encoder import (
    ACTION_DIM, STATE_DIM,
    encode_action_mask, encode_state, state_action_idx,
)

# ── Hyperparameters ───────────────────────────────────────────────────────────

GAMMA         = 0.99    # discount factor
LR            = 3e-4    # Adam learning rate
BATCH_SIZE    = 256
TARGET_UPDATE = 300     # steps between target-network hard updates
GRAD_CLIP     = 1.0

# Auto-detect best available device (Apple Silicon MPS, CUDA, or CPU)
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"


# ── Data loading ──────────────────────────────────────────────────────────────

def load_episodes(path: str) -> list[list[dict]]:
    """Read battles.jsonl and group into per-battle episode lists."""
    records: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    episodes: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        episodes[rec["battle_id"]].append(rec)

    # Sort each episode by turn number
    return [
        sorted(turns, key=lambda x: x["turn"])
        for turns in episodes.values()
    ]


def infer_outcome(episode: list[dict]) -> str:
    """
    Win/loss for an episode. Prefer the explicit outcome record (logged at
    battle end); fall back to guessing from the final turn's team sizes for
    older data that predates outcome logging.
    """
    for rec in episode:
        if rec.get("type") == "outcome":
            if rec.get("won") is True:
                return "won"
            if rec.get("won") is False:
                return "lost"
            return "unknown"  # tie / None

    turns = [r for r in episode if r.get("type") != "outcome"]
    if not turns:
        return "unknown"
    last = turns[-1]
    if last.get("opponent_team_size", 1) == 0:
        return "won"
    if last.get("my_team_size", 1) == 0:
        return "lost"
    return "unknown"


def turn_reward(prev: dict, curr: dict) -> float:
    """
    Dense reward for one turn.
    Positive when we deal more HP% to the opponent than we take.
    """
    my_prev  = (prev.get("my_pokemon")       or {}).get("hp_fraction", 0.0)
    my_curr  = (curr.get("my_pokemon")       or {}).get("hp_fraction", 0.0)
    opp_prev = (prev.get("opponent_pokemon") or {}).get("hp_fraction", 0.0)
    opp_curr = (curr.get("opponent_pokemon") or {}).get("hp_fraction", 0.0)
    return (opp_prev - opp_curr) - (my_prev - my_curr)


def build_transitions(episodes: list[list[dict]]) -> list[tuple]:
    """
    Convert all episodes into (s, a, r, s′, done, mask, next_mask) tuples.
    Skips turns where the logged action can't be mapped to an action index
    (e.g. random fallbacks with no action recorded).
    """
    transitions: list[tuple] = []
    skipped = 0

    for episode in episodes:
        outcome    = infer_outcome(episode)
        terminal_r = 1.0 if outcome == "won" else (-1.0 if outcome == "lost" else 0.0)

        # Only learn from real turn records (drop the terminal outcome record).
        turns = [r for r in episode if r.get("type") != "outcome"]

        for i, rec in enumerate(turns):
            a_idx = state_action_idx(rec)
            if a_idx is None:
                skipped += 1
                continue

            s    = encode_state(rec)
            mask = encode_action_mask(rec)

            if i + 1 < len(turns):
                r      = turn_reward(rec, turns[i + 1])
                s_next = encode_state(turns[i + 1])
                nm     = encode_action_mask(turns[i + 1])
                done   = False
            else:
                r      = terminal_r
                s_next = np.zeros(STATE_DIM, np.float32)
                nm     = np.zeros(ACTION_DIM, bool)
                done   = True

            transitions.append((s, a_idx, r, s_next, done, mask, nm))

    if skipped:
        print(f"  ({skipped} turns skipped — no mapped action)")
    return transitions


# ── Offline Double DQN ────────────────────────────────────────────────────────

def ql_step(
    model:     DuelingDQN,
    target:    DuelingDQN,
    optimizer: torch.optim.Optimizer,
    buf:       ReplayBuffer,
    step:      int,
) -> float | None:
    """One mini-batch Double-DQN update. Returns loss or None if buffer too small."""
    if len(buf) < BATCH_SIZE:
        return None

    states, actions, rewards, next_states, dones, masks, next_masks = buf.sample(BATCH_SIZE)

    states      = torch.FloatTensor(states).to(DEVICE)
    actions     = torch.LongTensor(actions).to(DEVICE)
    rewards     = torch.FloatTensor(rewards).to(DEVICE)
    next_states = torch.FloatTensor(next_states).to(DEVICE)
    dones       = torch.FloatTensor(dones).to(DEVICE)
    next_masks  = torch.BoolTensor(next_masks).to(DEVICE)
    masks       = torch.BoolTensor(masks).to(DEVICE)

    with torch.no_grad():
        # Double DQN: online net selects action, target net evaluates it
        next_q_online  = model(next_states).masked_fill(~next_masks, -1e9)
        next_actions   = next_q_online.argmax(dim=1)
        next_q_target  = target(next_states)
        next_v         = next_q_target.gather(1, next_actions.unsqueeze(1)).squeeze(1)
        target_q       = rewards + GAMMA * next_v * (1.0 - dones)

    model.train()
    current = model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
    loss    = F.smooth_l1_loss(current, target_q)

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
    optimizer.step()

    # Hard update target network periodically
    if step % TARGET_UPDATE == 0:
        target.load_state_dict(model.state_dict())

    return loss.item()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Offline DQN training for Pokemon battles")
    parser.add_argument("--log",        default="battles.jsonl", help="JSONL game log")
    parser.add_argument("--out",        default="model.pt",      help="Output model path")
    parser.add_argument("--ql_epochs",  type=int, default=20,    help="Q-learning epochs over dataset")
    args = parser.parse_args()

    if not os.path.exists(args.log):
        print(f"Log file not found: {args.log}")
        print("Play some battles first (player.py or dqn_player.py) to generate training data.")
        return

    print(f"Device: {DEVICE}")
    print(f"\nLoading episodes from {args.log} …")
    episodes = load_episodes(args.log)
    print(f"  {len(episodes)} battles found")
    wins = sum(1 for e in episodes if infer_outcome(e) == "won")
    print(f"  {wins}W / {len(episodes)-wins}L (unknown outcomes count as losses)")

    print("\nBuilding transitions …")
    transitions = build_transitions(episodes)
    print(f"  {len(transitions)} usable transitions")

    if not transitions:
        print("No usable transitions — make sure actions are logged correctly.")
        return

    # Initialise models
    model  = DuelingDQN().to(DEVICE)
    target = DuelingDQN().to(DEVICE)
    target.load_state_dict(model.state_dict())
    target.eval()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    # ── Offline Q-learning (outcome-driven; no minimax imitation) ─────────────
    if args.ql_epochs > 0:
        print(f"\n── Offline Q-learning ({args.ql_epochs} passes over dataset) ─────────")
        buf = ReplayBuffer(capacity=max(len(transitions) * 2, 10_000))
        for t in transitions:
            buf.push(*t)

        step       = 0
        batch_loss = 0.0
        n_updates  = 0

        for epoch in range(1, args.ql_epochs + 1):
            for _ in range(0, len(transitions), BATCH_SIZE):
                loss = ql_step(model, target, optimizer, buf, step)
                if loss is not None:
                    batch_loss += loss
                    n_updates  += 1
                step += 1
            avg = batch_loss / max(n_updates, 1)
            if epoch == 1 or epoch % 5 == 0:
                print(f"  Epoch {epoch:3d}/{args.ql_epochs}  TD-loss = {avg:.4f}")
            batch_loss = n_updates = 0

    model.save(args.out)
    print("\nDone.")


if __name__ == "__main__":
    main()
