from libs import *

class Node:

    ### Data ###
    parent = None
    children = []
    myPokemon = None
    theirPokemon = None
    myHp = 0
    theirHp = 0
    endNode = False
    probablilty = 1
    myMove = None
    theirMove = None
    myItem = ""
    theirItem = ""
    myStatus = ""
    theirStatus = ""
    seeded = False
    ### Methods ###

    # for after moves that pokemon do
    def __init__(self, par=None, damageToMe=None, damageToThem=None, poke1=None, poke2=None, myMo=None, theirMo=None):
        if par != None:
            self.parent = par
            self.endNode = False
            self.children = []
            if poke1 == None:
                self.myPokemon = self.parent.myPokemon
                self.theirPokemon = self.parent.theirPokemon
                self.myHp = self.parent.myHp - damageToMe
                self.theirHp = self.parent.theirHp - damageToThem
                self.myMove = myMo
                self.theirMove = theirMo
                self.myItem = self.parent.myItem
                if (self.myHp <= 0 or self.theirHp <= 0):
                    self.endNode = True
                    # print "endnode "+ self.myPokemon.name + " " + self.theirPokemon.name
            else:
                self.myPokemon = poke1
                self.theirPokemon = poke2
                self.myHp = self.myPokemon.data['hp']
                self.theirHp = calcMaxStats(self.theirPokemon.data)['hp']
                self.myItem = poke1.item

    def addChild(self, node):
        self.children.append(node)

    def isBattleRoot(self):
        if not self.isTreeRoot() and self.myPokemon != None and self.theirPokemon != None and self.myMove == None: #and self.theirMove == None:
            return True
        return False

    def isTreeRoot(self):
        if self.parent == None:
            return True
        return False

class Tree:

    ### Data ###
    rootNode = None
    currentNode = None

    ### Methods ###
    def __init__(self, myPokeSet, theirPokeSet ):
        self.rootNode = Node()
        self.buildTree(myPokeSet, theirPokeSet)

    def buildTree(self, myPokeSet, theirPokeSet):
        for myMon in myPokeSet:
            for theirMon in theirPokeSet:
                newNode = Node(poke1=myMon, poke2=theirMon, par=self.rootNode)
                self.rootNode.addChild(newNode)
                self.fillPath(newNode, 0)


    def fillPath(self, node, depth):
        if node.endNode == False and depth < 5:
            moves = node.myPokemon.moves
            #lock to single move if both pokemon have been selected a move has been used and the item is locking
            notRoot = not node.isTreeRoot
            lockinItem = node.myPokemon.moveLockingItem
            
            if (not node.isTreeRoot
            and node.myPokemon.moveLockingItem
            and node.item != None
            and not node.isBattleRoot() ):
            # and not node.parent.isBattleRoot()) :
                moves = [node.parent.myMove]
                print "alsdjflaks;jfals;"
            for move in moves:
                damage = damge(node.myPokemon, node.theirPokemon, move, False, node.theirHp)
                dam = damage[0]
                if dam > 0:
                    newNode = Node(damageToMe=0, damageToThem=dam, par=node, myMo=move)
                    # print node.myPokemon.name +" "+ node.theirPokemon.name+" "+str(dam)+" "+move.name
                    node.addChild(newNode)
                    self.fillPath(newNode, depth + 1)

    def getMoveUsed(self, startNode, endNode):
        tmpNode = endNode
        print "getmoveused: "+tmpNode.myMove.name
        while startNode != tmpNode.parent:
            tmpNode = tmpNode.parent
            if tmpNode.myMove != None:
                print "getmoveused: "+tmpNode.myMove.name
            else:
                print "getmoveused: "
        if tmpNode.myMove != None:
            return tmpNode.myMove.name
        else:
            return ""

    def findRootOfPicked(self, mine, theirs):
        for state in self.rootNode.children:
            print mine + " " + theirs
            if state.myPokemon.name == mine and state.theirPokemon.name == theirs:
                self.currentNode = state
                return state

    def findNextState(self):
        self.currentNode = self.currentNode.children[0]
        return (self.currentNode.myPokemon.name, self.currentNode.myMove.name)

    def shortestPath(self, startNode):
        stack = []
        index = -1
        activeNode = startNode
        while activeNode.endNode == False:
            stack = stack + activeNode.children
            index += 1
            activeNode = stack[index]
            # print str(index) + " " + str(len(stack)) + " " + activeNode.myMove.name +  " " +str(activeNode.theirHp)


            if index >= len(stack):
                break
        return (activeNode.myPokemon.name, self.getMoveUsed(startNode, activeNode))
