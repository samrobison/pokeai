#def damge(stuff):

#def accuracy(stuff):

#def typeEffectiveness((type, type), (type, type)):

def calcMaxStats(data):
    #{'hp': 45, 'atk': 49, 'defe': 49, 'spa': 65, 'spd': 65, 'spe': 45},
    iv = 31
    ev = 63
    data['hp'] = 110 + data['hp']*2 + ev + iv
    data['atk']  = (5 + data['atk']  * 2 + ev + iv) * 1.1
    data['defe'] = (5 + data['defe'] * 2 + ev + iv) * 1.1
    data['spa']  = (5 + data['spa']  * 2 + ev + iv) * 1.1
    data['spd']  = (5 + data['spd']  * 2 + ev + iv) * 1.1
    data['spe']  = (5 + data['spe']  * 2 + ev + iv) * 1.1

    return data
