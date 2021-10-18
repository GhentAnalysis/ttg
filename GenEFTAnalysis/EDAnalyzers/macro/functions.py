import utils
import math

def overlap(eta,phi,ecol,drMax):
    
    passed = True
    idxMin = -1
    drMin = 777
    
    for eidx, e in enumerate(ecol):
        dr = utils.deltaR(eta,phi,e.eta,e.phi)
        if (dr < drMin):
            idxMin = eidx
            drMin = dr
    
    if (drMin < drMax):
        passed = False
        
    return passed, drMin, idxMin
