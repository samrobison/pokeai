def damge(pokeData, moveData, ownership, currentHP):
    stab = 1
    if pokeData.pokeType[0] == moveData.pokeType or pokeData.pokeType[1] == moveData.pokeType:
        stab = 1.5
    if ownership == False:
        print 'hi'
    else:
        print 'hi'

#def accuracy(stuff):

#def typeEffectiveness((type, type), (type, type)):

def calcMaxStats(data):
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

def calcMinStats(data):
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

Pokedex = {
    'Normal': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 1,
        'Poison': 1,
        'Ground': 1,
        'Rock': .5,
        'Bug': 1,
        'Ghost': 0,
        'Steel': .5,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 1
    },
    'Fighting': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Flying': {
        'Normal': 1,
        'Fighting': 2,
        'Flying': 1,
        'Poison': 1,
        'Ground': 1,
        'Rock': .5,
        'Bug': 2,
        'Ghost': 1,
        'Steel': .5,
        'Fire': 1,
        'Water': 1,
        'Grass': 2,
        'Electric': .5,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 1
    }
    'Poison': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 1,
        'Poison': .5,
        'Ground': .5,
        'Rock': .5,
        'Bug': 1,
        'Ghost': .5,
        'Steel': 0,
        'Fire': 1,
        'Water': 1,
        'Grass': 2,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 2
    }
    'Ground': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 0,
        'Poison': 2,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 1,
        'Steel': 2,
        'Fire': 2,
        'Water': 1,
        'Grass': .5,
        'Electric': 2,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 1
    }
    'Rock': {
        'Normal': 1,
        'Fighting': .5,
        'Flying': 2,
        'Poison': 1,
        'Ground': .5,
        'Rock': 1,
        'Bug': 2,
        'Ghost': 1,
        'Steel': .5,
        'Fire': 2,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 1
    }
    'Bug': {
        'Normal': 1,
        'Fighting': .5,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 1,
        'Bug': 1,
        'Ghost': .5,
        'Steel': .5,
        'Fire': .5,
        'Water': 1,
        'Grass': 2,
        'Electric': 1,
        'Psychic': 2,
        'Ice': 1,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Ghost': {
        'Normal': 0,
        'Fighting': 1,
        'Flying': 1,
        'Poison': 1,
        'Ground': 1,
        'Rock': 1,
        'Bug': 1,
        'Ghost': 2,
        'Steel': 1,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': 2,
        'Ice': 1,
        'Dragon': 1,
        'Dark': .5,
        'Fairy': 1
    }
    'Steel': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 1,
        'Poison': 1,
        'Ground': 1,
        'Rock': 2,
        'Bug': 1,
        'Ghost': 1,
        'Steel': .5,
        'Fire': .5,
        'Water': .5,
        'Grass': 1,
        'Electric': .5,
        'Psychic': 1,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 1,
        'Fairy': 2
    }
    'Fire': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 1,
        'Poison': 1,
        'Ground': 1,
        'Rock': .5,
        'Bug': 2,
        'Ghost': 1,
        'Steel': 2,
        'Fire': .5,
        'Water': .5,
        'Grass': 2,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 2,
        'Dragon': .5,
        'Dark': 1,
        'Fairy': 1
    }
    'Water': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': 1,
        'Poison': 1,
        'Ground': 2,
        'Rock': 2,
        'Bug': 1,
        'Ghost': 1,
        'Steel': 1,
        'Fire': 2,
        'Water': .5,
        'Grass': .5,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': .5,
        'Dark': 1,
        'Fairy': 1
    }
    'Grass': {
        'Normal': 1,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 2,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 1,
        'Steel': .5,
        'Fire': .5,
        'Water': 2,
        'Grass': .5,
        'Electric': 1,
        'Psychic': 1,
        'Ice': 1,
        'Dragon': .5,
        'Dark': 2,
        'Fairy': .5
    }
    'Electric': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Psychic': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Ice': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Dragon': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Dark': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
    'Fairy': {
        'Normal': 2,
        'Fighting': 1,
        'Flying': .5,
        'Poison': .5,
        'Ground': 1,
        'Rock': 2,
        'Bug': .5,
        'Ghost': 0,
        'Steel': 2,
        'Fire': 1,
        'Water': 1,
        'Grass': 1,
        'Electric': 1,
        'Psychic': .5,
        'Ice': 2,
        'Dragon': 1,
        'Dark': 2,
        'Fairy': .5
    }
}
