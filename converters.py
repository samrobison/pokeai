"""Convert poke-env battle objects to our internal Pokemon/Move types."""

from poke_env.battle import MoveCategory

from libs import nameFormat
from Pokemon import Move as AIMove, Pokemon as AIPokemon

CATEGORY_MAP = {
    MoveCategory.PHYSICAL: 'Physical',
    MoveCategory.SPECIAL: 'special',
    MoveCategory.STATUS: 'status',
}


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
    p.ability = env_pokemon.ability or ''
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
