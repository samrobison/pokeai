from pokedex import Pokedex

class Pokemon:

    moves = []
    data = {}
    item = ''

    def __init__(self, name):
        pokemon = Pokedex[name]
        self.data = pokemon[baseStats]

    def maxStats():
        return calcMaxStats(self.data)

    def minStats():
        return calcMinStats(self.data)



class Move:

    physical = False
    power = 0
    types = []
    accuracy = 0

    def __init__(self, damageType, powe, ts, acc):
        self.physical = damageType
        self.power = powe
        self.types = ts
        self.accuracy = acc
