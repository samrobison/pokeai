class Tree:

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
