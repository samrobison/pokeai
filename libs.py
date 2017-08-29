#def damge(stuff):

#def accuracy(stuff):

#def typeEffectiveness((type, type), (type, type)):

def calcMaxStats(data):
    iv = 31
    ev = 63
    newData = {}

    newData['hp'] = 110 + data['hp']*2 + ev + iv
    newData['atk']  = (5 + data['atk']  * 2 + ev + iv) * 1.1
    newData['defe'] = (5 + data['defe'] * 2 + ev + iv) * 1.1
    newData['spa']  = (5 + data['spa']  * 2 + ev + iv) * 1.1
    newData['spd']  = (5 + data['spd']  * 2 + ev + iv) * 1.1
    newData['spe']  = (5 + data['spe']  * 2 + ev + iv) * 1.1
    return newData

def calcMinStats(data):
    iv = 31
    ev = 0
    newData = {}

    newData['hp'] = 110 + data['hp']*2 + ev + iv
    newData['atk']  = (5 + data['atk']  * 2 + ev + iv) * 0.9
    newData['defe'] = (5 + data['defe'] * 2 + ev + iv) * 0.9
    newData['spa']  = (5 + data['spa']  * 2 + ev + iv) * 0.9
    newData['spd']  = (5 + data['spd']  * 2 + ev + iv) * 0.9
    newData['spe']  = (5 + data['spe']  * 2 + ev + iv) * 0.9
    return newData
