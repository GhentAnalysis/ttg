#!/usr/bin/python

# Get list of files in some area on T2

import os, sys

#pref = 'root://eos.grid.vbc.ac.at/'
pref = 'root://maite.iihe.ac.be/'
#fpath = '/eos/vbc/experiments/cms/store/user/llechner/'
fpath = '/pnfs/iihe/cms/store/user/kskovpen/Herwig/'

samples = ['ttGamma_Dilept_Herwig7_v2', 'ttGamma_Dilept_Herwigpp_v2', 'ttGamma_SingleLept_Herwig7_v2', \
'ttGamma_SingleLept_Herwigpp_v2', 'ttGamma_Dilept_Pythia8_v2', 'ttGamma_SingleLept_Pythia8_v2']

#url = 'eos.grid.vbc.ac.at'
url = 'maite.iihe.ac.be'
com = 'xrdfs '+url+' ls '
    
for s in samples:
    
    with open(s+'.txt', 'w') as f:
        
        dlist = os.popen(com+fpath+'/'+s+'/').read().splitlines()
        for d in dlist:
            if '.root' in d:
                f.write(pref+d+'\n')
        f.close()
