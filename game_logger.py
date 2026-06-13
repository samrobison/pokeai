"""
Structured per-turn game state logging.

Each turn is written as one JSON line to battles.jsonl:

  {
    "battle_id": "gen9randombattle-12345",
    "turn": 4,
    "my_pokemon": {
      "species": "charizard",
      "hp_fraction": 0.82,
      "status": null,
      "boosts": {"atk": 0, "def": 0, ...},
      "type": ["Fire", "Flying"],
      "base_stats": {"hp": 78, "atk": 84, ...},
      "moves": ["flamethrower", "icebeam", "airslash", "roost"]
    },
    "opponent_pokemon": {
      "species": "blastoise",
      "hp_fraction": 0.55,
      "status": "BRN",
      "type": ["Water"],
      "base_stats": {"hp": 79, "atk": 83, ...},
      "moves": ["surf", "icebeam"]          # only moves we've seen
    },
    "available_moves": [
      {"id": "flamethrower", "name": "Flamethrower", "base_power": 90,
       "type": "Fire", "category": "special", "accuracy": 1.0,
       "pp": 15, "max_pp": 24, "effectiveness": 0.5},
      ...
    ],
    "available_switches": ["venusaur", "snorlax"],
    "action": "flamethrower",
    "action_type": "move",
    "weather": null,
    "fields": [],
    "my_team_size": 3,
    "opponent_team_size": 2
  }
"""

import json
import os
from typing import Optional

from poke_env.battle import MoveCategory, Pokemon, PokemonType, Status

LOG_PATH = os.path.join(os.path.dirname(__file__), "battles.jsonl")


def _type_names(pokemon: Pokemon):
    types = [pokemon.type_1.name.capitalize()] if pokemon.type_1 else []
    if pokemon.type_2 and pokemon.type_2 != pokemon.type_1:
        types.append(pokemon.type_2.name.capitalize())
    return types


def _effectiveness(move, opponent: Optional[Pokemon]) -> Optional[float]:
    if opponent is None or move.type is None:
        return None
    try:
        return move.type.damage_multiplier(opponent.type_1, opponent.type_2)
    except Exception:
        return None


def _encode_my_pokemon(pokemon: Pokemon) -> dict:
    return {
        "species": pokemon.species,
        "hp_fraction": round(pokemon.current_hp_fraction, 4),
        "status": pokemon.status.name if pokemon.status else None,
        "boosts": dict(pokemon.boosts),
        "type": _type_names(pokemon),
        "base_stats": dict(pokemon.base_stats),
        "moves": [m.id for m in pokemon.moves.values()],
    }


def _encode_opponent(pokemon: Pokemon) -> dict:
    return {
        "species": pokemon.species,
        "hp_fraction": round(pokemon.current_hp_fraction, 4),
        "status": pokemon.status.name if pokemon.status else None,
        "type": _type_names(pokemon),
        "base_stats": dict(pokemon.base_stats),
        "moves": [m.id for m in pokemon.moves.values()],
    }


def _encode_available_moves(battle) -> list:
    opp = battle.opponent_active_pokemon
    result = []
    for move in battle.available_moves:
        result.append({
            "id": move.id,
            "name": move.entry.get("name", move.id),
            "base_power": move.base_power,
            "type": move.type.name.capitalize() if move.type else None,
            "category": move.category.name.lower() if move.category else None,
            "accuracy": move.accuracy,
            "pp": move.current_pp,
            "max_pp": move.max_pp,
            "effectiveness": _effectiveness(move, opp),
        })
    return result


def build_state(battle, action: Optional[str] = None, action_type: Optional[str] = None) -> dict:
    my = battle.active_pokemon
    opp = battle.opponent_active_pokemon
    my_alive = sum(1 for p in battle.team.values() if not p.fainted)
    opp_alive = sum(1 for p in battle.opponent_team.values() if not p.fainted)

    return {
        "battle_id": battle.battle_tag,
        "turn": battle.turn,
        "my_pokemon": _encode_my_pokemon(my) if my else None,
        "opponent_pokemon": _encode_opponent(opp) if opp else None,
        "available_moves": _encode_available_moves(battle),
        "available_switches": [p.species for p in battle.available_switches],
        "action": action,
        "action_type": action_type,
        "weather": next(iter(battle.weather)).name if battle.weather else None,
        "fields": [f.name for f in battle.fields],
        "my_team_size": my_alive,
        "opponent_team_size": opp_alive,
    }


def log_state(state: dict) -> None:
    # TODO: swap LOG_PATH for a DB write, remote store, replay buffer, etc.
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(state) + "\n")
