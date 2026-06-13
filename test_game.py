"""
Runs a single self-play test game between two RandomBattlePlayer bots.
No account registration needed — unregistered PS names are used.
Results are logged to battles.jsonl.
"""
import asyncio

from poke_env import AccountConfiguration, ShowdownServerConfiguration

from game_logger import LOG_PATH
from player import RandomBattlePlayer

import random, string

def _rand_name():
    return "pai" + "".join(random.choices(string.ascii_lowercase + string.digits, k=9))

BOT1 = _rand_name()
BOT2 = _rand_name()


async def main():
    bot1 = RandomBattlePlayer(
        account_configuration=AccountConfiguration(BOT1, None),
        server_configuration=ShowdownServerConfiguration,
        battle_format="gen9randombattle",
    )
    bot2 = RandomBattlePlayer(
        account_configuration=AccountConfiguration(BOT2, None),
        server_configuration=ShowdownServerConfiguration,
        battle_format="gen9randombattle",
    )

    print(f"Starting test game: {BOT1} vs {BOT2}")
    print(f"Game state will be logged to: {LOG_PATH}\n")

    await asyncio.gather(
        bot1.send_challenges(BOT2, n_challenges=1),
        bot2.accept_challenges(BOT1, n_challenges=1),
    )

    winner = BOT1 if bot1.n_won_battles > 0 else BOT2
    print(f"\nGame over. Winner: {winner}")
    print(f"  {BOT1}: {bot1.n_won_battles}W / {bot1.n_lost_battles}L")
    print(f"  {BOT2}: {bot2.n_won_battles}W / {bot2.n_lost_battles}L")
    print(f"Log written to: {LOG_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
