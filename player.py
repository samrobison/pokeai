import asyncio

from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import Player

from database import initDb
from game_logger import LOG_PATH, build_state, log_state
from minimax import choose_best_move, choose_best_switch


class MinimaxPlayer(Player):

    def __init__(self, *args, minimax_depth=2, **kwargs):
        super().__init__(*args, **kwargs)
        self._announced = set()
        self.minimax_depth = minimax_depth

    def choose_move(self, battle):
        if battle.battle_tag not in self._announced:
            self._announced.add(battle.battle_tag)
            print(f"Battle started: https://play.pokemonshowdown.com/{battle.battle_tag}")

        if battle.force_switch:
            env_pokemon = choose_best_switch(battle)
            if env_pokemon is not None:
                order = self.create_order(env_pokemon)
                print(f"  Turn {battle.turn}: switch in {env_pokemon.species} (scored)")
            else:
                order = self.choose_random_move(battle)
                print(f"  Turn {battle.turn}: switch fell back to random")
        else:
            env_action = choose_best_move(battle, depth=self.minimax_depth)
            if env_action is not None:
                order = self.create_order(env_action)
                label = getattr(env_action, 'id', None) or getattr(env_action, 'species', '?')
                print(f"  Turn {battle.turn}: minimax chose {label}")
            else:
                order = self.choose_random_move(battle)
                print(f"  Turn {battle.turn}: minimax fell back to random")

        # Resolve action for logging
        from poke_env.battle.move import Move as EnvMove
        from poke_env.battle.pokemon import Pokemon as EnvPokemon
        action = action_type = None
        if hasattr(order, "order"):
            if isinstance(order.order, EnvMove):
                action, action_type = order.order.id, "move"
            elif isinstance(order.order, EnvPokemon):
                action, action_type = order.order.species, "switch"

        log_state(build_state(battle, action=action, action_type=action_type))

        return order


async def main():
    import argparse

    from userinfo import username, password

    parser = argparse.ArgumentParser(description="Run the minimax agent on Pokemon Showdown")
    parser.add_argument("n", nargs="?", type=int, default=1,
                        help="Number of battles to play (default: 1)")
    parser.add_argument("--challenge", metavar="USER",
                        help="Challenge a specific player by username instead of laddering")
    parser.add_argument("--accept", metavar="USER", nargs="?", const="",
                        help="Accept incoming challenges. Optionally restrict to a username; "
                             "omit the username to accept from anyone.")
    parser.add_argument("--depth", type=int, default=4, help="Minimax search depth (default: 4)")
    timer = parser.add_mutually_exclusive_group()
    timer.add_argument("--timer", dest="timer", action="store_true",
                       help="Force the battle timer on (default: on for ladder, off for challenges)")
    timer.add_argument("--no-timer", dest="timer", action="store_false",
                       help="Force the battle timer off")
    parser.set_defaults(timer=None)
    args = parser.parse_args()

    initDb()

    # Default: timer on for ladder/accept, off for friendly challenges.
    if args.timer is None:
        start_timer = not args.challenge
    else:
        start_timer = args.timer

    player = MinimaxPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format="gen9randombattle",
        minimax_depth=args.depth,
        start_timer_on_battle_start=start_timer,
    )

    if args.challenge:
        print(f"Challenging {args.challenge} to {args.n} game(s) as {username}...")
        await player.send_challenges(args.challenge, n_challenges=args.n)
    elif args.accept is not None:
        opponent = args.accept or None  # "" -> None means accept from anyone
        who = opponent if opponent else "anyone"
        print(f"Waiting to accept {args.n} challenge(s) from {who} as {username}...")
        await player.accept_challenges(opponent, n_challenges=args.n)
    else:
        print(f"Queuing for {args.n} game(s) as {username} on gen9randombattle ladder...")
        await player.ladder(args.n)

    print(f"Done. Results: {player.n_won_battles}W / {player.n_lost_battles}L")
    print(f"Game states logged to: {LOG_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
