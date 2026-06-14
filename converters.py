"""Convert poke-env battle objects to our internal Pokemon/Move types."""

from poke_env.battle import MoveCategory
from poke_env.battle.move import Target

from libs import nameFormat
from Pokemon import Move as AIMove, Pokemon as AIPokemon

CATEGORY_MAP = {
    MoveCategory.PHYSICAL: 'Physical',
    MoveCategory.SPECIAL: 'special',
    MoveCategory.STATUS: 'status',
}


def _self_boosts(env_move) -> dict:
    """
    Stat-stage changes that land on the *user* of the move.

    Combines:
      - env_move.self_boost : self-effect of damaging moves
                              (Draco Meteor -2 SpA, Close Combat -1 Def/-1 SpD, ...)
      - env_move.boosts     : only when the move targets SELF
                              (Swords Dance +2 Atk, Nasty Plot +2 SpA, ...)

    Opponent-targeting stat moves (Growl, Charm) are intentionally excluded —
    they affect the opponent, which the search does not yet model on their side.
    """
    boosts: dict = {}

    if env_move.self_boost:
        for stat, amount in env_move.self_boost.items():
            boosts[stat] = boosts.get(stat, 0) + amount

    if env_move.boosts and env_move.target == Target.SELF:
        for stat, amount in env_move.boosts.items():
            boosts[stat] = boosts.get(stat, 0) + amount

    return boosts


def move_from_env(env_move):
    accuracy = int(env_move.accuracy * 100)
    move_hash = {
        'basePower': env_move.base_power,
        'type': env_move.type.name.capitalize(),
        'accuracy': accuracy,
        'name': env_move.entry.get('name', env_move.id),
        'category': CATEGORY_MAP.get(env_move.category, 'status'),
        'pp': env_move.max_pp,
        'priority': env_move.priority,
        'boosts': _self_boosts(env_move),  # stat changes applied to the user
        'fixed_damage': env_move.damage or 0,  # 'level' or int for Seismic Toss etc.
        'heal': env_move.heal or 0.0,          # Recover/Soft-Boiled/Roost = 0.5
        'drain': env_move.drain or 0.0,        # Giga Drain = 0.5 of damage dealt
    }
    return AIMove(move_hash)


def pokemon_from_env(env_pokemon, use_max_stats=False):
    base = env_pokemon.base_stats
    base_stats = {
        'hp':   base['hp'],
        'atk':  base['atk'],
        'defe': base['def'],
        'spa':  base['spa'],
        'spd':  base['spd'],
        'spe':  base['spe'],
    }

    t1 = env_pokemon.type_1.name.capitalize() if env_pokemon.type_1 else 'Normal'
    t2 = env_pokemon.type_2.name.capitalize() if env_pokemon.type_2 else t1

    p = AIPokemon.__new__(AIPokemon)
    p.null_init()
    p.name = nameFormat(env_pokemon.species)
    p.level = env_pokemon.level or 100
    p.data = base_stats
    p.type = (t1, t2)
    # Best-known ability: the revealed one, or the only possibility if unambiguous.
    ability = env_pokemon.ability
    if not ability:
        possible = env_pokemon.possible_abilities or []
        if len(possible) == 1:
            ability = possible[0]
    p.ability = (ability or '').replace(' ', '').lower()
    p.item = env_pokemon.item or ''
    p.friendly = True
    p.otherFormes = []

    actual = env_pokemon.stats
    has_actual = actual and any(v is not None for v in actual.values())

    if use_max_stats or not has_actual:
        p.stats = p.max_stats()
    else:
        p.stats = {
            'hp':   actual.get('hp') or 0,
            'atk':  actual.get('atk') or 0,
            'defe': actual.get('def') or 0,
            'spa':  actual.get('spa') or 0,
            'spd':  actual.get('spd') or 0,
            'spe':  actual.get('spe') or 0,
        }

    for env_move in env_pokemon.moves.values():
        p.moves.append(move_from_env(env_move))

    if not p.moves:
        p.moves.append(AIMove(None))

    return p
