from pokedex import Pokedex

class Pokemon:

    ### Data ###
    moves = []
    data = {}
    item = ''
    friendly = True

    ### Methods ###
    def __init__(self, name, mine):
        pokemon = Pokedex[name]
        self.data = pokemon[baseStats]
        currentHp = calcMaxStats(self.data)['hp']
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
    types = []
    accuracy = 0

    ### Methods ###
    def __init__(self, damageType, powe, ts, acc):
        self.physical = damageType
        self.power = powe
        self.types = ts
        self.accuracy = acc
