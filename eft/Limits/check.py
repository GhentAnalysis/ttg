#!/usr/bin/env python

import pickle as pkl
import numpy as np
import ROOT
from scipy.interpolate import interp1d
from scipy.integrate import simps
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import os, sys, json, math
from optparse import OptionParser
import style

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import MaxNLocator

plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Helvetica'
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Helvetica'
plt.rcParams['mathtext.bf'] = 'Helvetica:bold'
plt.rcParams['mathtext.sf'] = 'Helvetica'
plt.rcParams['mathtext.it'] = 'Helvetica:italic'
plt.rcParams['mathtext.tt'] = 'Helvetica'
plt.rcParams['mathtext.default'] = 'regular'
plt.rcParams['axes.labelsize'] = 17.0
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.labelpad'] = 10.0
plt.rcParams['xtick.labelsize'] = 16.0
plt.rcParams['ytick.labelsize'] = 16.0
plt.rcParams['xtick.minor.visible'] = True
plt.rcParams['ytick.minor.visible'] = True
plt.rcParams['legend.fontsize'] = 'small'
plt.rcParams['legend.handlelength'] = 1.5
plt.rcParams['legend.borderpad'] = 0.5
plt.rcParams['legend.frameon'] = True
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['grid.alpha'] = 0.8
plt.rcParams['grid.linestyle'] = ':'
plt.rcParams['axes.linewidth'] = 1
plt.rcParams['savefig.transparent'] = False
plt.rcParams['figure.subplot.left'] = 0.15
plt.rcParams['figure.subplot.right'] = 0.96
plt.rcParams['figure.subplot.top'] = 0.90
plt.rcParams['figure.subplot.bottom'] = 0.22

pref = 'pics/photon_pt'
run = 'Run2'
op = 'ctZI'

data = [pref+'/'+run+'/'+op+'.json', \
pref+'/'+run+'_Toy0/'+op+'_0.json', \
pref+'/'+run+'_Toy1/'+op+'_0.json', \
pref+'/'+run+'_Toy2/'+op+'_0.json', \
pref+'/'+run+'_Toy3/'+op+'_0.json', \
pref+'/'+run+'_Toy4/'+op+'_0.json', \
pref+'/'+run+'_Toy5/'+op+'_0.json', \
pref+'/'+run+'_Toy6/'+op+'_0.json', \
pref+'/'+run+'_Toy7/'+op+'_0.json', \
pref+'/'+run+'_Toy8/'+op+'_0.json', \
pref+'/'+run+'_Toy9/'+op+'_0.json', \
pref+'/'+run+'_Toy10/'+op+'_0.json', \
pref+'/'+run+'_Toy11/'+op+'_0.json', \
pref+'/'+run+'_Toy12/'+op+'_0.json', \
pref+'/'+run+'_Toy13/'+op+'_0.json', \
pref+'/'+run+'_Toy14/'+op+'_0.json', \
pref+'/'+run+'_Toy15/'+op+'_0.json', \
pref+'/'+run+'_Toy16/'+op+'_0.json', \
#pref+'/'+run+'_Toy17/'+op+'_0.json', \
pref+'/'+run+'_Toy18/'+op+'_0.json', \
pref+'/'+run+'_Toy19/'+op+'_0.json', \
]

pref = 'eft_input_photon_pt_'

y = '2016'
hist2016 = [pref+run+'/'+op+'_1d/expected/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy0/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy1/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy2/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy3/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy4/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy5/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy6/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy7/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy8/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy9/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy10/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy11/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy12/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy13/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy14/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy15/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy16/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
#pref+run+'_Toy17/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy18/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
pref+run+'_Toy19/'+op+'_1d/observed/srFit_'+y+'_shapes_'+op+'0.0.root', \
]

d68, d95, dbf = [], [], []

for fd in data:

    with open(fd, "r") as read_file:
        d = json.load(read_file)
        d68.append(d['expected']['68'])
        d95.append(d['expected']['95'])
        dbf.append(d['expected']['bestfit'])
        
x, x68, x95, y68, y68errDown, y68errUp, y95, y95errDown, y95errUp = [], [], [], [], [], [], [], [], []
for i, d in enumerate(d68):
    x.append(i)
    bf = dbf[i] if i > 0 else 0.
    x68.append(i-0.1)
    y68.append(bf)
    y68errDown.append(abs(d[0]-bf))
    y68errUp.append(abs(d[1]-bf))
    
for i, d in enumerate(d95):
    bf = dbf[i] if i > 0 else 0.
    x95.append(i+0.1)
    y95.append(bf)
    y95errDown.append(abs(d[0]-bf))
    y95errUp.append(abs(d[1]-bf))

fig = plt.figure(figsize=(8, 5))
plt.errorbar(x68, y68, xerr = None, yerr = [y68errDown, y68errUp], fmt='.', ls='none', label='68\%', capsize=5, elinewidth=2)
plt.errorbar(x95, y95, xerr = None, yerr = [y95errDown, y95errUp], fmt='.', ls='none', label='95\%', capsize=5, elinewidth=2)
new_list = range(min(x), max(x)+1)
plt.title(op.replace('ctZI', '$\mathrm{C_{tZ}^{I}}$').replace('ctZ', '$\mathrm{C_{tZ}}$'), fontsize='xx-large')
plt.xticks(new_list)
plt.minorticks_off()
plt.ylim([-1.0, 1.0])
plt.xlabel('Measurement')
plt.ylabel('CL interval')
labels = []
labels.append('Expected')
for i in range(1, len(x)):
    labels.append('PE '+str(x[i]))
plt.gca().set_xticklabels(labels, rotation='vertical')
plt.axhline(y=y68[0]+y68errUp[0], linewidth=0.5, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][0], linestyle='--')
plt.axhline(y=y68[0]-y68errDown[0], linewidth=0.5, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][0], linestyle='--')
plt.axhline(y=y95[0]+y95errUp[0], linewidth=0.5, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][1], linestyle='--')
plt.axhline(y=y95[0]-y95errDown[0], linewidth=0.5, color=plt.rcParams['axes.prop_cycle'].by_key()['color'][1], linestyle='--')
plt.legend(loc='upper right', prop={'size': 12})
fig.savefig('check.pdf')

#ROOT.gROOT.SetBatch()

#pstyle = style.SetPlotStyle(2)

#hexp, hpe = None, []
#for ih in range(0, len(hist2016)):
#    f = ROOT.TFile(hist2016[ih], 'READ')
#    hee = f.Get('sr_ee/data_obs')
#    hmm = f.Get('sr_mumu/data_obs')
#    hem = f.Get('sr_emu/data_obs')
#    h = hee.Clone('hpe')
#    h.Add(hmm)
#    h.Add(hem)
#    h.SetBinErrorOption( ROOT.TH1.kPoisson )
#    if ih == 0:
#        hexp = h
#        hexp.SetDirectory(0)
#    else:
#        hpe.append(h)
#        hpe[-1].SetDirectory(0)
#    f.Close()
    
#c0 = ROOT.TCanvas('c0', 'c0', 800, 500)
#c0.Divide(5, 2, 0, 0)
#for i in range(10):
#    c0.cd(i+1)
#    ROOT.gPad.SetLogy(1)
#    hexp.Draw('hist')
#    hexp.SetLineWidth(1)
#    hexp.SetLineColor(ROOT.kBlue)
#    hpe[i].Draw('hist ep1 SAME')
#    hpe[i].SetMarkerSize(0.5)
#    hexp.SetMaximum(1500)
#c0.Print('pe.pdf')
