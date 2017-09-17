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
        self.theirPoisonCount = 0
        self.myPoisonCount = 0

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
                self.theirItem = self.parent.theirItem
                self.myStatus = self.parent.myStatus
                self.theirStatus = self.parent.theirStatus
                self.imSeeded = self.parent.myStatus
                self.theyreSeeded = self.parent.theyreSeeded
                self.theirPoisonCount = self.parent.theirPoisonCount
                self.myPoisonCount = self.parent.myPoisonCount

            #for choosing the pokemon sent out
            else:
                self.myPokemon = poke1
                self.theirPokemon = poke2
                self.myHp =poke1.stats['hp']
                self.theirHp = poke2.stats['hp']
                self.myItem = poke1.item

    def damage(self, damageToThem, damageToMe):
        statusDamage = self.statusDamage()
        damageToMe += statusDamage[1]
        damageToThem += statusDamage[0]

        self.myHp = self.parent.myHp - damageToMe
        self.theirHp = self.parent.theirHp - damageToThem

        if self.myHp > self.myPokemon.getStat('hp'):
            self.myHp = self.myPokemon.getStat('hp')
        if self.theirHp > self.theirPokemon.getStat('hp'):
            self.theirHp = self.theirPokemon.getStat('hp')

        reward = self.calcReward(self.myHp, self.theirHp)
        self.edge = Edge( prob=(self.myMove.accuracy + self.theirMove.accuracy), reward=reward )
        if (self.myHp <= 0 or self.theirHp <= 0):
            self.endNode = True
            self.children = None

    def addChild(self, node):
        self.children.append(node)

    def isBattleRoot(self):
        if self.edge == None and self.myMove == None:
            return True
        return False

    def setStatus(self, myMove, theirMove):
        if myMove != None and myMove.category == 'status':
            if statusEffective(myMove, self.theirPokemon):
                if myMove.name == 'Leech Seed' and not self.theyreSeeded:
                    self.theyreSeeded = True
                elif myMove.name == 'Toxic' and self.theirStatus == '':
                    self.theirStatus = 'Poison'
                    self.theirPoisonCount = 1
            else:
                return False
        if theirMove != None and theirMove.category == 'status':
            if statusEffective(theirMove, self.myPokemon):
                if theirMove.name == 'Leech Seed' and not self.imSeeded:
                    self.imSeeded = True
                elif theirMove.name == 'Poison'and self.myStatus == '':
                    self.myStatus = 'Poison'
            else:
                return False
        return True

    def statusDamage(self):
        damage = [0,0]
        if self.theyreSeeded:
            damage[1] -= self.myPokemon.getStat('hp') * 0.12
            damage[0] += self.theirPokemon.getStat('hp') * 0.12
        if self.theirStatus == 'Poison':
            damage[0] += (self.theirPokemon.getStat('hp') * 0.12) * self.theirPoisonCount
            self.theirPoisonCount += 1
        return damage

    def calcReward(self, myHealth, theirHealth):
        #my health will be < 0 while thiers >= 0
        if myHealth > 0 and theirHealth <= 0:
            reward = 999999
        #my health will be >= 0 while thiers < 0
        elif myHealth <= 0 and theirHealth > 0:
            reward = -999999
        #both of our health <= 0
        #TODO: understand priority and speed ties
        elif myHealth <= 0 and theirHealth <= 0:
            if self.myPokemon.getStat('spe') >=  self.theirPokemon.getStat('spe'):
                reward = 999999
            else:
                reward = -999999
        #non death senarios
        else:
            reward = (float(myHealth)/ float(self.myPokemon.getStat('hp'))) - (float(theirHealth)/ float(self.theirPokemon.getStat('hp')))
            reward = int(reward * 10000)
        return reward

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
    def __init__(self, myPokeSet, theirPokeSet, db ):
        self.rootNode = Node()
        self.currentState = self.rootNode
        self.predictiveState = self.rootNode
        self.buildTree(myPokeSet, theirPokeSet)
        self.db = db

    def buildTree(self, myPokeSet, theirPokeSet):
        for myPoke in myPokeSet:
            for theirPoke in theirPokeSet:
                print(myPoke.name + " "+ theirPoke.name)

                battleRoot = Node(par=self.rootNode, poke1=myPoke, poke2=theirPoke)
                self.rootNode.addChild(battleRoot)
                self.fillPath(battleRoot, 0)

    def fillPath(self, node, depth):
        if depth < 10 and not node.endNode:
            # print "depth: " + str(depth)
            #if we are not choosing a pokemon and its is a locking move/item
            if not node.isBattleRoot() and node.myPokemon.moveLocked and node.theirPokemon.moveLocked:
                if self.effectiveMove(node.myMove, node.theirMove, node.myPokemon, node.theirPokemon, node):
                    newNode = self.createNewNode(node, node.myMove, node.theirMove)
                    self.fillPath(newNode, depth + 1)

            elif not node.isBattleRoot() and node.theirPokemon.moveLocked:
                for myMove in node.myPokemon.moves:
                    if self.effectiveMove(myMove, node.theirMove, node.myPokemon, node.theirPokemon, node):
                        newNode = self.createNewNode(node, myMove, node.theirMove)
                        self.fillPath(newNode, depth + 1)

            elif not node.isBattleRoot() and node.myPokemon.moveLocked:
                for theirMove in node.theirPokemon.moves:
                    if self.effectiveMove(node.myMove, theirMove, node.myPokemon, node.theirPokemon, node):
                        newNode = self.createNewNode(node, node.myMove, theirMove)
                        self.fillPath(newNode, depth + 1)

            else:
                for myMove in node.myPokemon.moves:
                    for theirMove in node.theirPokemon.moves:
                        if self.effectiveMove(myMove, theirMove, node.myPokemon, node.theirPokemon, node):
                            newNode = self.createNewNode(node, myMove, theirMove)
                            self.fillPath(newNode, depth + 1)

    def effectiveMove(self, myMove, theirMove, myPokemon, theirPokemon, node):
        effective = True
        if myMove.category == 'status':
            effective = effective and statusEffective(myMove, theirPokemon)
            if (node.theyreSeeded and myMove.name == 'Leech Seed') or node.theirStatus != '' and myMove.name == 'Toxic':
                return False
        else:
            effective = effective and moveEffectiveness(myMove, theirPokemon) != 0
        if theirMove.category == False:
            return effective
        elif theirMove.category == 'status':
            effective = effective and statusEffective(theirMove, myPokemon)
        else:
            effective = effective and moveEffectiveness(theirMove, myPokemon) != 0
        return effective


    def createNewNode(self, node, myMove, theirMove):
        newNode = Node(myMo=myMove, theirMo=theirMove, par=node)
        node.addChild(newNode)
        damage = [0, 0]

        #damage from my move to them
        if myMove.category == 'status':
            #stall move like proctect
            if myMove.stallingMove:
                if myMove.name == 'Protect':
                    newNode.damage(0,0)
                    return newNode
            # status move like toxic
            else:
                newNode.setStatus(myMove, None)
        #damaging move
        else:
            damage[0] = calcDamge(newNode.myPokemon, newNode.theirPokemon, newNode.myMove, newNode.myHp)[0]

        #damage from their move to me
        if theirMove.category == 'Status':
            #stall move like proctect
            if theirMove.stallingMove:
                if theirMove.name == 'Protect':
                    newNode.damage(0,0)
                    return newNode
            # status move like toxic
            else:
                newNode.setStatus(None, theirMove)
        #null move
        elif not theirMove.category:
            damage[1] = 0
        #damaging move
        else:
            damage[1] = calcDamge(newNode.theirPokemon, newNode.myPokemon, newNode.theirMove, newNode.myHp)[0]

        newNode.damage(damage[0], damage[1])
        return newNode

    def getMoveUsed(self, startNode, endNode):
        raiseNotDefined()

    def findRootForPicked(self, mine, theirs):
        for child in self.rootNode.children:
            if child.myPokemon.name == mine and child.theirPokemon.name == theirs:
                self.currentState = child
                print self.currentState.myPokemon.name + " " + self.currentState.theirPokemon.name
                return child
        raise Exception("Node not found for mypokemon: "+ mine +" theirpokemon: " + theirs)

    def findNextState(self):
        state = None
        maxReward = -9999999
        for child in self.currentState.children:
            print child.myMove.name + " " + str(child.edge.reward)
            if maxReward < child.edge.reward:
                state = child
                maxReward = child.edge.reward
        print "Greedy Move: " + state.myMove.name
        self.predictiveState = state

    def getNextMove(self):
        self.findNextState()
        return self.predictiveState.myMove.name

    def correctTree(self, enemyMove, damageToMe, damageToThem, myMoveSuccessful, theirMoveSuccessful):
        #update enemyMove in database
        #correct hp's
        #correct status and hp if move wasn't succesful
        #gestimate enemy stats based on move
        #update z-crystal status
        #update for mega evolutions

        self.currentState = self.predictiveState


    def choosePokemon(self):
        #choose celestella for now
        return 'celesteela'

    def shortestPath(self, startNode):
        raiseNotDefined()
