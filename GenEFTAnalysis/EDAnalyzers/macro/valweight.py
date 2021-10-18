#!/usr/bin/env python

import pickle
from reweight import eft
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print 'load weights'
with open("weights.pkl", "r") as fp:
    weights = pickle.load(fp)
            
print 'perform validation'

lastPtBin = 8

for pk, pv in weights.param.iteritems():

    wc = []
    xs = []
    
    for ic, c in enumerate(weights.ctZ):

        print pk, 'ctZ =', c
        nbins = len(pv['bins'])-1 if pk not in ['inclusive'] else 1

        wsmSum = 0
        weftSum = 0
        nevSum = 0
        
        for ib in range(nbins):
            
            weft = weights.ctZ_1d_weight[pk][ib][ic]
            wsm = weights.sm_weight[pk][ib]
            nev = weights.nev[pk][ib]
            wsf = weft/wsm if wsm > 0. else 1.
            
            wsmSum += wsm
            weftSum += weft
            nevSum += nev
            
            if pk in ['inclusive']:                
                wc.append(c)
                xs.append(weft)
            elif (ib == lastPtBin):
                wc.append(c)
                xs.append(weft)
            
            if pk not in ['inclusive']: print ib, 'eft=', weft, 'sm=', wsm, 'sf=', wsf, '['+str(pv['bins'][ib])+', '+str(pv['bins'][ib+1])+']', 'N=', nev
            else: print 'eft=', weft, 'sm=', wsm, 'sf=', wsf, 'N=', nev
        
        if pk not in ['inclusive']: print 'EFT =', weftSum, 'SM =', wsmSum, 'N =', nevSum

    plt.figure(figsize=(9, 3))
    plt.subplot()
    plt.plot(wc, xs)
    plt.savefig('pics/ctZ'+'_'+pk+'.pdf')
    
