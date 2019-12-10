#! /usr/bin/env python

import ROOT, os, uuid, numpy, math
import cPickle as pickle
from math import sqrt

fname = '/afs/cern.ch/user/k/kskovpen/public/ttG/2016/phoCBfull_compos_ALL/ee/llg-mll40-offZ-llgNoZ-signalRegion-photonPt20/signalRegions.pkl'

fPkl = pickle.load( open( fname, "rb" ) )

sel = 'signalRegions'
procName = 'TTGamma_Pr_Dilt#bar{t}#gamma (genuine)'
#sys = 'JEC'
sys = 'pu'

for s, h in fPkl.iteritems():
    if s == sel: hNom = h[procName]
    elif s == sel+sys+'Up': hUp = h[procName]
    elif s == sel+sys+'Down': hDown = h[procName]
    
print 'Nominal -----'
if hNom: print hNom.Print("all")
print 'Up -----'
if hUp: print hUp.Print("all")
print 'Down -----'
if hDown: print hDown.Print("all")

                
