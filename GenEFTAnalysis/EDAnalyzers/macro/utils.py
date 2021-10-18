import math

def deltaR2( e1, p1, e2, p2):

    de = e1 - e2
    dp = deltaPhi(p1, p2)
    return de*de + dp*dp
            
def deltaR( *args ):

    return math.sqrt( deltaR2(*args) )
                
def deltaPhi( p1, p2):

    res = p1 - p2
    while res > math.pi:
        res -= 2*math.pi
    while res < -math.pi:
        res += 2*math.pi
    return res

def mll( p1, p2 ):

    res = math.pow(p1.E+p2.E,2)-math.pow(p1.px+p2.px,2)-math.pow(p1.py+p2.py,2)-math.pow(p1.pz+p2.pz,2)
    if res >= 0: res = math.sqrt(res)
    else: res = -1
    
    return res

def mlll( p1, p2, p3 ):

    res = math.pow(p1.E+p2.E+p3.E,2)-math.pow(p1.px+p2.px+p3.px,2)-math.pow(p1.py+p2.py+p3.py,2)-math.pow(p1.pz+p2.pz+p3.pz,2)
    if res >= 0: res = math.sqrt(res)
    else: res = -1
    
    return res

