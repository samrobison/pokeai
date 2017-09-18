from pokedex import Pokedex
from libs import *
from movedex import MoveDex
from database import *

class Move:
    def nullInit(self):
        ### Data ###
        self.category = False
        self.power = 0
        self.type = ''
        self.accuracy = 100
        self.name = ""
        self.zPower = None
        self.pp = 0
        self.boosts = []
        self.recharge = False
        self.stallingMove = False

    ### Methods ###
    def __init__(self, moveHash):
        self.nullInit()
        if moveHash != None:
            self.power = moveHash['basePower']
            self.type = moveHash['type']
            self.accuracy = moveHash['accuracy']
            self.name = moveHash['name']
            self.category = moveHash['category']
            self.stallingMove = 'stallingMove' in moveHash
            if 'zMovePower' in moveHash:
                self.zPower = moveHash['zMovePower']
            self.pp = moveHash['pp']
            self.priority = moveHash['priority']
            if 'boosts' in moveHash:
                self.boosts = moveHash['boosts']

class Pokemon:

    def nullInit(self):
        ### Data ###
        self.moves = []
        # data is basestats
        self.data = {}
        # stats is calculated stats with ev's iv's and nature
        self.stats = {}
        self.type = ()
        self.item = ""
        self.moveLocked = False
        self.friendly = True
        self.ability = ""
        self.name = ""
        self.otherForms = []
        self.item = ""


    ### Methods ###
    def __init__(self, name, abil=None, moves=None, stat=None, itemHeld=None):
        self.nullInit()
        pokemon = Pokedex[name]
        self.name = name
        self.data = pokemon['baseStats']
        self.type = pokemon['types']
        self.otherFormes = []
        if 'otherFormes' in pokemon:
            self.otherFormes = pokemon['otherFormes']
        if len(pokemon['types']) == 1:
            self.type = (pokemon['types'][0], pokemon['types'][0])
        else:
            self.type = (pokemon['types'][0], pokemon['types'][1])

        if moves != None:
            for move in moves:
                self.moves.append( Move( move ) )
            self. ability = abil
            self.friendly = False
            self.stats = self.calcStats(stat)
            self.item = itemHeld
            self.movedLockingItem = False
        else:
            self.stats = self.maxStats()
            possibleMoves = findMovesForPokemon(self.name)
            if len(possibleMoves) == 0:
                self.moves.append(Move(None))
            else:
                for move in possibleMoves:
                    if move[1] in MoveDex:
                        self.moves.append( Move(MoveDex[str(move[1])]) )

    def addMove(self, moveName):
        if moveName in MoveDex:
            self.moves.append( Move(MoveDex[moveName]) )

    def setStats(self, stats):
        self.data = stats

    def getStat(self, stat):
        return self.stats[stat]

    def stats(self):
        return self.stats

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
            self.movedLocked = True
        if "Choice Band" in self.item:
            newData['atk'] *= 1.5
            self.movedLocked = True
        if "Choice Specs" in self.item:
            newData['spa'] *= 1.5
            self.movedLocked = True
        #set modified stats
        return newData

    def maxStats(self):
        return calcMaxStats(self.data)

    def minStats(self):
        return calcMinStats(self.data)
