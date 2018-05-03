from libs import *
from movedex import MoveDex
from database import *
from pokedex import Pokedex
import re

class Move:
    def null_init(self):
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
        self.stalling_move = False

    ### Methods ###
    def __init__(self, move_hash):
        self.null_init()
        if move_hash != None:
            self.power = move_hash['basePower']
            self.type = move_hash['type']
            self.accuracy = move_hash['accuracy']
            self.name = move_hash['name']
            self.category = move_hash['category']
            self.stalling_move = 'stalling_move' in move_hash
            if 'zMovePower' in move_hash:
                self.zPower = move_hash['zMovePower']
            self.pp = move_hash['pp']
            self.priority = move_hash['priority']
            if 'boosts' in move_hash:
                self.boosts = move_hash['boosts']

class Pokemon:

    def null_init(self):
        ### Data ###
        self.moves = []
        # data is basestats
        self.data = {}
        # stats is calculated stats with ev's iv's and nature
        self.stats = {}
        self.type = ()
        self.item = ""
        self.move_locked = False
        self.friendly = True
        self.ability = ""
        self.name = ""
        self.other_forms = []
        self.item = ""
        self.level = 0


    ### Methods ###
    def __init__(self, my_init_string=None, name=None, abil=None, moves=None, stat=None, item_held=None):
        self.null_init()
        if my_init_string is not None:
            self.my_from_string(my_init_string)
            return 
        pokemon = Pokedex[name]
        self.name = name
        self.level = 100
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
            self.stats = self.calc_stats(stat)
            self.item = item_held
            self.movedLockingItem = False
        else:
            self.stats = self.max_stats()
            possibleMoves = findMovesForPokemon(self.name)
            if len(possibleMoves) == 0:
                self.moves.append(Move(None))
            else:
                for move in possibleMoves:
                    if move[1] in MoveDex:
                        self.moves.append( Move(MoveDex[str(move[1])]) )
    
    def my_from_string(self, string):
        parsed = re.search("((?:[\\w-]+\\s?){1,2})(?:\\([\\w\\s-]+\\))?\\sL(\\d+)\\nHP:\\s100\\.0%\\s\\((\\d+)\\/+\\d+\\)\\nAbility:\\s([\\w\\s-]+)\\/\\sItem:\\s([\\w\\s]+)\\n(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\n..(['\\w\\s-]+)\\n..(['\\w\\s-]+)\\n..(['\\w\\s-]+)\\n..(['\\w\\s]+)", string)
        groups = parsed.groups()
        self.name = groups[0]
        self.level = groups[1]
        self.hp = groups[2]
        self.ability = groups[3]
        self.item = groups[4]
        self.stats = {
            'hp': self.hp,
            'atk':groups[5], 
            'defe': groups[6],
            'spa': groups[7],
            'spd': groups[8], 
            'spe': groups[9],
        }
        self.add_move(groups[10])
        self.add_move(groups[11])
        self.add_move(groups[12])
        self.add_move(groups[13])
        self.data = Pokedex[self.name.lower()]['baseStats']


    def theirs_from_string(self, string):
        parsed = re.search("((?:[\\w]+\\s?){1,2})(?:\\([\\w\\s-]+\\))?\\sL(\\d+)\\nHP:\\s100%\\n(?:Ability|Possible abilities):\\s(?:[,\\w\\s-]+)\\n(\\d+)\\sto\\s(\\d+)", string)
        groups = parsed.groups()
        self.name = groups[0]
        self.level = groups[1]
        self.data = Pokedex[self.name.lower()]['baseStats']
        self.stats = self.max_stats()

    def add_move(self, move_name):
        if move_name in MoveDex:
            self.moves.append( Move(MoveDex[move_name]) )

    def setStats(self, stats):
        self.data = stats

    def get_stat(self, stat):
        return self.stats[stat]

    def get_stats(self):
        return self.stats

    def calc_stats(self, stats):
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
            self.move_locked = True
        if "Choice Band" in self.item:
            newData['atk'] *= 1.5
            self.move_locked = True
        if "Choice Specs" in self.item:
            newData['spa'] *= 1.5
            self.move_locked = True
        #set modified stats
        return newData

    def max_stats(self):
        return calc_max_stats(self.data)

    def min_stats(self):
        return calc_min_stats(self.data)
