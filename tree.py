from libs import *

class Tree:

    class Node:

        ### Data ###
        parent = None
        children = []
        myPokemon = None
        theirPokemon = None
        myHp = 0
        theirHp = 0

        ### Methods ###

        #for initial creation
        def __init__():
            print "created"

        #for when 2 pokemon are chosen for the first time
        def __init__(self, poke1, poke2, par):
            self.myPokemon = poke1
            self.theirPokemon = poke2
            self.myHp = self.myPokemon.stats()['hp']
            self.theirHp = self.theirPokemon.calcMaxStats( theirPokemon.stats() )
            self.parent = par

        # for after moves that pokemon do
        def __init__(self, par, damageToMe, damageToThem):
            self.parent = par
            self.myPokemon = self.parent.myPokemon
            self.theirPokemon = self.parent.theirPokemon
            self.myHp = self.parent.myHp - damageToMe
            self.theirHp = self.parent.theirHp - damageToThem

        def addChild(node):
            children.append(node)


    ### Data ###
    rootNode = None

    ### Methods ###
    def __init__(self, myPokeSet, theirPokeSet ):
        self.rootNode = Node()
        buildTree()

    def buildTree(myPokeSet, theirPokeSet):
        for myMon in myPokeSet:
            for theirMon in theirPokeSet:
                newNode = Node(myMon, theirMon, self.rootNode)
                self.rootNode.addChild(newNode)
                self.fillPath(newNode)


    def fillPath(node):
        for move in node.myPokemon.moves:
            calcDamage()
