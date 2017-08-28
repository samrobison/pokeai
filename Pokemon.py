class Pokemon:

    moves = []
    data = {}
    item = ''

    def __init__(self, name):
        print "hi"



class Move:

    physical = False
    power = 0
    types = []
    accuracy = 0

    def __init__(self, damageType, powe, ts, acc):
        self.physical = damageType
        self.power = powe
        self.types = ts
        self.accuracy = acc
