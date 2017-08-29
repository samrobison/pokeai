from pokedex import Pokedex
from libs import *

class Move:

    ### Data ###
    physical = False
    power = 0
    pokeType = ''
    accuracy = 0
    name = ""

    ### Methods ###
    def __init__(self, damageType, powe, ts, acc, na):
        self.physical = damageType
        self.power = powe
        self.pokeType = ts
        self.accuracy = acc
        self.name = na

class Pokemon:

    ### Data ###
    moves = []
    data = {}
    pokeType = ()
    item = ''
    friendly = True
    ability = ""
    name = ""

    ### Methods ###
    def __init__(self, name, abil=None, moves=None, stat=None):
        pokemon = Pokedex[name]
        self.name = name
        self.data = pokemon['baseStats']
        self.pokeType = pokemon['types']
        if len(pokemon['types']) == 1:
            self.pokeType = (pokemon['types'][0], pokemon['types'][0])
        else:
            self.pokeType = (pokemon['types'][0], pokemon['types'][1])

        if abil != None:
            self.moves = []
            for move in moves:
                self.moves.append(Move(move['category'] != "special", move['basePower'], move['type'], move['accuracy'], move['name']))
            self. ability = abil
            self.friendly = False
            self.calcStats(stat)

    def setStats(self, stats):
        self.data = stats

    def stats(self):
        return self.data

    def calcStats(self, stats):
        newData = {}
        iv = 31

        newData['hp'] = 110 + self.data['hp']*2 + iv
        newData['atk']  = (5 + self.data['atk']  * 2 + iv)
        newData['defe'] = (5 + self.data['defe'] * 2 + iv)
        newData['spa']  = (5 + self.data['spa']  * 2 + iv)
        newData['spd']  = (5 + self.data['spd']  * 2 + iv)
        newData['spe']  = (5 + self.data['spe']  * 2 + iv)
        for k in stats:
            newData[k] = newData[k] + (stats[k]/4)

        self.data = newData

    def maxStats(self):
        return calcMaxStats(self.data)

    def minStats(self):
        return calcMinStats(self.data)
