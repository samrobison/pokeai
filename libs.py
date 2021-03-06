import sys
import inspect

def calcDamge(poke1, poke2, move, currentHP):
    MIN_MULT = 0.85
    MAX_MULT = 1.0
    minDamage = 0
    maxDamage = 0
    probability = 0.0

    #find out whether STAB or not
    stab = 1.0
    if (poke1.type[0] == move.type) or (poke1.type[1] == move.type):
        if poke1.ability == 'Adaptability':
            stab = 1.5 * 1.5
        else:
            stab = 1.5

    #find type effectiveness modifier
    effective = moveEffectiveness(move, poke2)

    #find damage before min max multiplier
    damage = 0
    if move.category == 'Physical':
        damage = int( ( int( (42 * move.power * int(poke1.stats['atk'] / poke2.stats['defe'])) / 50) + 2) * stab * effective)
    elif move.category == 'special':
        damage = int( ( int( (42 * move.power * int(poke1.stats['spa'] / poke2.stats['spd'])) / 50) + 2) * stab * effective)
    minDamage = int(damage * MIN_MULT)
    maxDamage = int(damage * MAX_MULT)

    #find probanility of the move killing
    if currentHP > maxDamage:
        probability = 0.0
    elif currentHP <= minDamage:
        probability = 1.0
    else:
        probability = float(currentHP - minDamage)/(maxDamage - minDamage)
    return (minDamage, maxDamage, probability)

#def accuracy(stuff):

def moveEffectiveness(move, pokemon ):
    return TypeChart[move.type][pokemon.type[0]] * TypeChart[move.type][pokemon.type[1]]

def damageStatus(myStatus, theirStatus, mySeed, theirSeed):
    raiseNotDefined()

def statusEffective(move, pokemon):
    if move.type in pokemon.type or moveEffectiveness(move, pokemon) == 0:
        return False
    return True

def raiseNotDefined():
    fileName = inspect.stack()[1][1]
    line = inspect.stack()[1][2]
    method = inspect.stack()[1][3]

    print("*** Method not implemented: %s at line %s of %s" % (method, line, fileName))
    sys.exit(1)


def nameFormat(text):
    return text.replace(" ", "").replace("-", "").replace("'", "").replace("*", "").lower()

def calc_max_stats(data):
    iv = 31
    ev = 63
    newData = {}

    newData['hp'] = 110 + data['hp']*2 + ev + iv
    newData['atk']  = (5 + data['atk']  * 2 + ev + iv) * 1.1
    newData['defe'] = (5 + data['defe'] * 2 + ev + iv) * 1.1
    newData['spa']  = (5 + data['spa']  * 2 + ev + iv) * 1.1
    newData['spd']  = (5 + data['spd']  * 2 + ev + iv) * 1.1
    newData['spe']  = (5 + data['spe']  * 2 + ev + iv) * 1.1
    return newData

def calc_min_stats(data):
    iv = 31
    ev = 0
    newData = {}

    newData['hp'] = 110 + data['hp']*2 + ev + iv
    newData['atk']  = (5 + data['atk']  * 2 + ev + iv) * 0.9
    newData['defe'] = (5 + data['defe'] * 2 + ev + iv) * 0.9
    newData['spa']  = (5 + data['spa']  * 2 + ev + iv) * 0.9
    newData['spd']  = (5 + data['spd']  * 2 + ev + iv) * 0.9
    newData['spe']  = (5 + data['spe']  * 2 + ev + iv) * 0.9
    return newData

TypeChart = {
    'Normal': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 0.5,
        'Bug': 1.0,
        'Ghost': 0.0,
        'Steel': 0.5,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Fighting': {
        'Normal': 2.0,
        'Fighting': 1.0,
        'Flying': 0.5,
        'Poison': 0.5,
        'Ground': 1.0,
        'Rock': 2.0,
        'Bug': 0.5,
        'Ghost': 0.0,
        'Steel': 2.0,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 0.5,
        'Ice': 2.0,
        'Dragon': 1.0,
        'Dark': 2.0,
        'Fairy': .5
    },
    'Flying': {
        'Normal': 1.0,
        'Fighting': 2.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 0.5,
        'Bug': 2.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 2.0,
        'Electric': 0.5,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Poison': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 0.5,
        'Ground': 0.5,
        'Rock': 0.5,
        'Bug': 1.0,
        'Ghost': 0.5,
        'Steel': 0.0,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 2.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 2.0
    },
    'Ground': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 0.0,
        'Poison': 2.0,
        'Ground': 1.0,
        'Rock': 2.0,
        'Bug': 0.5,
        'Ghost': 1.0,
        'Steel': 2.0,
        'Fire': 2.0,
        'Water': 1.0,
        'Grass': 0.5,
        'Electric': 2.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Rock': {
        'Normal': 1.0,
        'Fighting': 0.5,
        'Flying': 2.0,
        'Poison': 1.0,
        'Ground': 0.5,
        'Rock': 1.0,
        'Bug': 2.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 2.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 2.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Bug': {
        'Normal': 1.0,
        'Fighting': 0.5,
        'Flying': 0.5,
        'Poison': 0.5,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 0.5,
        'Steel': 0.5,
        'Fire': 0.5,
        'Water': 1.0,
        'Grass': 2.0,
        'Electric': 1.0,
        'Psychic': 2.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 2.0,
        'Fairy': .5
    },
    'Ghost': {
        'Normal': 0.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 2.0,
        'Steel': 1.0,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 2.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 0.5,
        'Fairy': 1.0
    },
    'Steel': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 2.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 0.5,
        'Water': 0.5,
        'Grass': 1.0,
        'Electric': 0.5,
        'Psychic': 1.0,
        'Ice': 2.0,
        'Dragon': 1.0,
        'Dark': 1.0,
        'Fairy': 2.0
    },
    'Fire': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 0.5,
        'Bug': 2.0,
        'Ghost': 1.0,
        'Steel': 2.0,
        'Fire': 0.5,
        'Water': 0.5,
        'Grass': 2.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 2.0,
        'Dragon': 0.5,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Water': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 2.0,
        'Rock': 2.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 1.0,
        'Fire': 2.0,
        'Water': 0.5,
        'Grass': 0.5,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 0.5,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Grass': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 0.5,
        'Poison': 0.5,
        'Ground': 2.0,
        'Rock': 2.0,
        'Bug': 0.5,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 0.5,
        'Water': 2.0,
        'Grass': 0.5,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 0.5,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Electric': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 2.0,
        'Poison': 1.0,
        'Ground': 0.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 1.0,
        'Fire': 1.0,
        'Water': 2.0,
        'Grass': 0.5,
        'Electric': 0.5,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 0.5,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Psychic': {
        'Normal': 1.0,
        'Fighting': 2.0,
        'Flying': 1.0,
        'Poison': 2.0,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 0.5,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 0.0,
        'Fairy': 1.0
    },
    'Ice': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 2.0,
        'Poison': 1.0,
        'Ground': 2.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 0.5,
        'Water': 0.5,
        'Grass': 2.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 0.5,
        'Dragon': 2.0,
        'Dark': 1.0,
        'Fairy': 1.0
    },
    'Dragon': {
        'Normal': 1.0,
        'Fighting': 1.0,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 2.0,
        'Dark': 1.0,
        'Fairy': 0.0
    },
    'Dark': {
        'Normal': 1.0,
        'Fighting': 0.5,
        'Flying': 1.0,
        'Poison': 1.0,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 2.0,
        'Steel': 1.0,
        'Fire': 1.0,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 2.0,
        'Ice': 1.0,
        'Dragon': 1.0,
        'Dark': 0.5,
        'Fairy': .5
    },
    'Fairy': {
        'Normal': 1.0,
        'Fighting': 2.0,
        'Flying': 1.0,
        'Poison': 0.5,
        'Ground': 1.0,
        'Rock': 1.0,
        'Bug': 1.0,
        'Ghost': 1.0,
        'Steel': 0.5,
        'Fire': 0.5,
        'Water': 1.0,
        'Grass': 1.0,
        'Electric': 1.0,
        'Psychic': 1.0,
        'Ice': 1.0,
        'Dragon': 2.0,
        'Dark': 2.0,
        'Fairy': 1.0
    }
}
