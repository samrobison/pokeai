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
    myMove = ""
    theirMove = ""
    ### Methods ###

    # #for initial creation
    # def __init__():
    #     print "created"
    #
    # #for when 2 pokemon are chosen for the first time
    # def __init__(self, poke1, poke2, par):
    #     self.myPokemon = poke1
    #     self.theirPokemon = poke2
    #     self.myHp = self.myPokemon.stats()['hp']
    #     self.theirHp = self.theirPokemon.calcMaxStats( theirPokemon.stats() )
    #     self.parent = par

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
                self.myMove = myMo.name
                self.theirMove = theirMo
                if (self.myHp <= 0 or self.theirHp <= 0):
                    self.endNode = True
                    # print "endnode "+ self.myPokemon.name + " " + self.theirPokemon.name
            else:
                self.myPokemon = poke1
                self.theirPokemon = poke2
                self.myHp = self.myPokemon.data['hp']
                self.theirHp = calcMaxStats(self.theirPokemon.data)['hp']

    def addChild(self, node):
        self.children.append(node)

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
            for move in node.myPokemon.moves:
                damage = damge(node.myPokemon, node.theirPokemon, move, False, node.theirHp)
                dam = damage[0]
                if dam > 0:
                    newNode = Node(damageToMe=0, damageToThem=dam, par=node, myMo=move)
                    #  node.myPokemon.name +" "+ node.theirPokemon.name+" "+str(node.theirHp)+" "+move.name
                    node.addChild(newNode)
                    self.fillPath(newNode, depth + 1)

    def getMoveUsed(self, startNode, endNode):
        tmpNode = endNode
        while startNode != tmpNode.parent:
            tmpNode = tmpNode.parent
        return tmpNode.myMove

    def findRootOfPicked(self, mine, theirs):
        for state in self.rootNode.children:
            print mine + " " + theirs
            if state.myPokemon.name == mine and state.theirPokemon.name == theirs:
                self.currentNode = state
                return state

    def shortestPath(self, startNode):
        stack = []
        index = -1
        currentNode = startNode
        while currentNode.endNode == False:
            stack = stack + currentNode.children
            currentNode = stack[index]
            index += 1
            if index >= len(stack):
                break
        return(currentNode.myPokemon.name, self.getMoveUsed(startNode, currentNode))
