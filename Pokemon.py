from pokedex import Pokedex

class Pokemon:

    ### Data ###
    moves = []
    data = {}
    pokeType = ()
    item = ''
    friendly = True

    ### Methods ###
    def __init__(self, name, mine):
        pokemon = Pokedex[name]
        self.data = pokemon['baseStats']
        self.pokeType = pokemon['types']
        self.friendly = mine

    def setStats(stats):
        self.data = stats

    def stats():
        return data

    def maxStats():
        return calcMaxStats(self.data)

    def minStats():
        return calcMinStats(self.data)



class Move:

    ### Data ###
    physical = False
    power = 0
    pokeType = ''
    accuracy = 0

    ### Methods ###
    def __init__(self, damageType, powe, ts, acc):
        self.physical = damageType
        self.power = powe
        self.pokeType = ts
        self.accuracy = acc
