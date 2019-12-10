#! /usr/bin/env python

import ROOT, os, uuid, numpy, math
from math import sqrt

fname = 'combine/srFit_shapes.root'

f = ROOT.TFile(fname,'OPEN')

procName = 'TTGamma'
#sys = 'JEC'
sys = 'pu'
hNomName = 'sr_ee'
hDownName = 'sr_ee'+sys+'Down'
hUpName = 'sr_ee'+sys+'Up'

hNom = f.Get(hNomName+'/'+procName)
hDown = f.Get(hDownName+'/'+procName)
hUp = f.Get(hUpName+'/'+procName)
    
print 'Nominal -----'
if hNom: print hNom.Print("all")
print 'Up -----'
if hUp: print hUp.Print("all")
print 'Down -----'
if hDown: print hDown.Print("all")

                
