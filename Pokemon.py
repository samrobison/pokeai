from pokedex import Pokedex
from libs import *

class Move:

    ### Data ###
    physical = False
    power = 0
    pokeType = ''
    accuracy = 0
    name = ""
    zPower = None
    pp = 0
    boosts = []
    recharge = False

    ### Methods ###
    def __init__(self, moveHash):
        self.physical = moveHash['category']  == 'Physical'
        self.power = moveHash['basePower']
        self.pokeType = moveHash['type']
        self.accuracy = moveHash['accuracy']
        self.name = moveHash['name']
        if 'zMovePower' in moveHash:
            self.zPower = moveHash['zMovePower']
        self.pp = moveHash['pp']
        self.priority = moveHash['priority']
        if 'boosts' in moveHash:
            self.boosts = moveHash['boosts']

class Pokemon:

    ### Data ###
    moves = []
    data = {}
    pokeType = ()
    item = ""
    moveLockingItem = False
    friendly = True
    ability = ""
    name = ""
    otherForms = []

    ### Methods ###
    def __init__(self, name, abil=None, moves=None, stat=None, itemHeld=None):
        pokemon = Pokedex[name]
        self.name = name
        self.data = pokemon['baseStats']
        self.pokeType = pokemon['types']
        self.otherFormes = []
        if 'otherFormes' in pokemon:
            self.otherFormes = pokemon['otherFormes']
        if len(pokemon['types']) == 1:
            self.pokeType = (pokemon['types'][0], pokemon['types'][0])
        else:
            self.pokeType = (pokemon['types'][0], pokemon['types'][1])

        if abil != None:
            self.moves = []
            for move in moves:
                self.moves.append( Move( move ) )
            self. ability = abil
            self.friendly = False
            self.calcStats(stat)
            self.item = itemHeld
            self.moveLockingItem = False
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
        #add ev's
        for k in stats:
            newData[k] = newData[k] + (stats[k]/4)
        #add Choice boosts
        if "Choice Scarf" in self.item:
            newData['spe'] *= 1.5
            self.moveLockingItem = True
        if "Choice Band" in self.item:
            newData['atk'] *= 1.5
            self.moveLockingItem = True
        if "Choice Specs" in self.item:
            newData['spa'] *= 1.5
            self.moveLockingItem = True
        #set modified stats
        self.data = newData

    def maxStats(self):
        return calcMaxStats(self.data)

    def minStats(self):
        return calcMinStats(self.data)
