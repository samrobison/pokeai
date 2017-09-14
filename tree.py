from libs import *

class Node:

    def nullInit(self):
        ### Data ###
        self.parent = None
        self.children = []
        self.myPokemon = None
        self.theirPokemon = None
        self.myHp = 0
        self.theirHp = 0
        self.endNode = False
        self.probablilty = 1
        self.myMove = None
        self.theirMove = None
        self.myItem = ""
        self.theirItem = ""
        self.myStatus = ""
        self.theirStatus = ""
        self.imSeeded = False
        self.theyreSeeded = False

        self.edge = None

    # for after moves that pokemon do
    def __init__(self, par=None,  poke1=None, poke2=None, myMo=None, theirMo=None):
        self.nullInit()
        #go on if not the root node
        if par != None:
            self.parent = par
            #for battling
            if myMo != None or theirMo != None:
                self.myPokemon = self.parent.myPokemon
                self.theirPokemon = self.parent.theirPokemon
                self.myMove = myMo
                self.theirMove = theirMo
                self.myItem = self.parent.myItem

            #for choosing the pokemon sent out
            else:
                self.myPokemon = poke1
                self.theirPokemon = poke2
                self.myHp =poke1.stats['hp']
                self.theirHp = poke2.stats['hp']
                self.myItem = poke1.item

    def damage(self, damageToMe, damageToThem):
        statusDamage = self.statusDamage()
        damageToMe += statusDamage[0]
        damageToThem += statusDamage[1]

        self.myHp = self.parent.myHp - damageToMe
        self.theirHp = self.parent.theirHp - damageToThem
        self.edge = Edge( prob=(self.myMove.accuracy + self.theirMove.accuracy), reward=calcReward(self.myHp, self.theirHp) )
        if (self.myHp <= 0 or self.theirHp <= 0):
            self.endNode = True
            self.children = None

    def addChild(self, node):
        self.children.append(node)

    def isBattleRoot(self):
        if self.edge == None and self.myMove == None:
            return True
        return False

    def setStatus(self, mine, theirs):
        if mine != None:
            if mine.name == 'Leech Seed':
                self.theirSeed = True
            elif mine.name == 'Toxic':
                self.theirStatus = 'Toxic'
        if theirs != None:
            if theirs.name == 'Leech Seed':
                self.theirSeed = True
            elif theirs.name == 'Toxic':
                self.theirStatus = 'Toxic'

    def statusDamage(self):
        damage = (0,0)
        if self.theirSeed:
            damage[0] -= self.myPokemon.getStat('hp') * 0.12
            damage[1] += self.theirPokemon.getStat('hp') * 0.12
        return damage

    def calcReward(self, myHealth, theirHealth):
        #my health will be < 0 while thiers >= 0
        if myHealth > 0 and theirHealth <= 0:
            return 999999

        #my health will be >= 0 while thiers < 0
        elif myHealth <= 0 and theirHealth > 0:
            return -999999

        #both of our health <= 0
        #TODO: understand priority and speed ties
        elif myHealth <= 0 and theirHealth <= 0:
            if self.myPokemon.getStat('spe') >=  self.theirPokemon.getStat('spe'):
                return 999999
            else:
                return -999999

        #non death senarios
        else:
            return (float(myHealth)/ self.myPokemon.getStat('hp')) - (float(theirHealth)/ self.theirPokemon.getStat('hp'))

    def isTreeRoot(self):
        if self.parent == None:
            return True
        return False

class Edge:
    def __init__(self, prob=None, action=None, reward=None):
        self.prob = 1
        self.action = action
        self.reward = reward

class Tree:

    ### Methods ###
    def __init__(self, myPokeSet, theirPokeSet ):
        self.rootNode = Node()
        self.currentState = self.rootNode
        self.buildTree(myPokeSet, theirPokeSet)

    def buildTree(self, myPokeSet, theirPokeSet):
        for myPoke in myPokeSet:
            for theirPoke in theirPokeSet:
                print(myPoke.name + " "+ theirPoke.name)

                battleRoot = Node(par=self.rootNode, poke1=myPoke, poke2=theirPoke)
                self.rootNode.addChild(battleRoot)
                self.fillPath(battleRoot, 0)

    def fillPath(self, node, depth):
        if depth < 10:
            newNode = None
            #if we are not choosing a pokemon and its is a locking move/item
            if not node.isBattleRoot() and node.myPokemon.moveLocked:
                for theirMove in node.theirPokemon.moves:
                    newNode = self.createNewNode(node, node.myMove, theirMove)

            elif not node.isBattleRoot() and node.theirPokemon.moveLocked:
                for myMove in node.myPokemon.moves:
                    newNode = self.createNewNode()

            elif not node.isBattleRoot() and node.myPokemon.moveLocked and node.theirPokemon.moveLocked:
                newNode = self.createNewNode(node, node.myMove, node.theirMove)

            else:
                for myMove in node.myPokemon.moves:
                    for theirMove in node.theirPokemon.moves:
                        newNode = self.createNewNode(node, node.myMove, theirMove)

            self.fillPath(newNode, depth + 1)


    def createNewNode(self, node, myMove, theirMove):
        newNode = Node(myMo=myMove, theirMo=theirMove, par=node)
        node.addChild(newNode)

        damage = (0,0)
        #damage from my move to them
        if myMove.category == 'Status':
            #stall move like proctect
            if myMove.stallingMove:
                if myMove.name == 'Protect':
                    newNode.damage(0,0)
                    return newNode
            # status move like toxic
            else:
                node.setStatus(myMove, None)
        #damaging move
        else:
            damage[0] = calcDamge(node.myPokemon.stats, node.theirPokemon.stats, node.myMove, node.myHp)[0]

        #damage from their move to me
        if theirMove.category == 'Status':
            #stall move like proctect
            if theirMove.stallingMove:
                if theirMove.name == 'Protect':
                    newNode.damage(0,0)
                    return newNode
            # status move like toxic
            else:
                node.setStatus(None, theirMove)
        #null move
        elif not theirMove.category:
            damage[1] = 0
        #damaging move
        else:
            damage[1] = calcDamge(node.myPokemon.stats, node.theirPokemon.stats, node.myMove, node.myHp)[0]

        newNode.damage(0,0)
        return newNode

    def getMoveUsed(self, startNode, endNode):
        raiseNotDefined()

    def findRootOfPicked(self, mine, theirs):
        self.currentState = self.rootNode.children[2]
        self.currentState

    def findNextState(self):
        state = None
        maxReward = 0
        for child in self.currentState.children:
            if maxReward > child.edge.reward:
                state = child
                maxReward = child.edge.reward
        return state

    def shortestPath(self, startNode):
        raiseNotDefined()
