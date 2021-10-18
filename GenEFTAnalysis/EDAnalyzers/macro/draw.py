#!/usr/bin/env python

import ROOT
import sys
import numpy as np
import utils
import style

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
from matplotlib import gridspec

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
plt.rcParams['figure.subplot.left'] = 0.2
plt.rcParams['figure.subplot.bottom'] = 0.2
plt.rcParams['figure.subplot.right'] = 0.96
plt.rcParams['figure.subplot.top'] = 0.95

f = ROOT.TFile.Open('jobs/ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt_crab_ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt__1/merged.root')
tr = f.Get('val')

#nmax = -1
nmax = 10000

labels = ['t', 'W', 'b', 'lepton', 'hadron', 'udcsg']
#weights = ['SM', 'ctZ_1_ctZI_0_ctW_0_ctWI_0', 'ctZ_0_ctZI_1_ctW_0_ctWI_0', 'ctZ_0_ctZI_0_ctW_1_ctWI_0', 'ctZ_0_ctZI_0_ctW_0_ctWI_1']
weights = ['SM', 'ctZ_2_ctZI_0_ctW_0_ctWI_0', 'ctZ_0_ctZI_2_ctW_0_ctWI_0']
colors = ['royalblue', 'darkorange', 'limegreen', 'gold', 'sienna', 'crimson']
colorsEFT = ['royalblue', 'darkorange', 'limegreen', 'gold', 'sienna']
explode = [0.3, 0, 0, 0, 0, 0]
fills = [True, False, False, False, False, False]
fillsEFT = [False, False, False, False, False]

vw, vorig, vpt, veta, \
vdr_pho_top_min, vdr_pho_top_max, \
vdr_pho_b_min, vdr_pho_b_max, \
vdr_pho_W_min, vdr_pho_W_max, \
vdr_pho_l_min, vdr_pho_l_max \
= {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

for l in labels:
    vw[l] = {}
    for w in weights:
        vw[l][w] = []
    vorig[l] = 0
    vpt[l] = []
    veta[l] = []
    vdr_pho_top_min[l] = []
    vdr_pho_top_max[l] = []
    vdr_pho_b_min[l] = []
    vdr_pho_b_max[l] = []
    vdr_pho_W_min[l] = []
    vdr_pho_W_max[l] = []
    vdr_pho_l_min[l] = []
    vdr_pho_l_max[l] = []
        
print 'Process data ('+str(tr.GetEntries())+')'
    
for iev, ev in enumerate(tr):

    if iev > nmax and nmax >= 0: break

    for i in range(tr.pid.size()):

        pt = tr.pt[i]
        eta = tr.eta[i]
        phi = tr.phi[i]
        pid = tr.pid[i]

        if pid != 22: continue
        if pt < 10: continue # cut at generator level
    
        dr_pho_top = []
        dr_pho_b = []
        dr_pho_W = []
        dr_pho_l = []
        
        for ii in range(tr.pid.size()):
            
            ppid = tr.pid[ii]
            peta = tr.eta[ii]
            pphi = tr.phi[ii]
            
            dr = utils.deltaR(eta,phi,peta,pphi)
            
            if abs(ppid) == 6:
                dr_pho_top.append(dr)
            elif abs(ppid) == 5:
                dr_pho_b.append(dr)
            elif abs(ppid) == 24:
                dr_pho_W.append(dr)
            elif abs(ppid) in [11,13,15]:
                dr_pho_l.append(dr)
                
        if len(dr_pho_top) < 2: continue
        if len(dr_pho_b) < 2: continue
        if len(dr_pho_W) < 2: continue
        if len(dr_pho_l) < 2: continue
        
        dr_pho_top.sort()
        dr_pho_b.sort()
        dr_pho_W.sort()
        dr_pho_l.sort()
        
        mid = tr.mid[i]

        cl = ''
        if abs(mid) in [11,13,15]: cl = 'lepton'
        elif abs(mid) == 24: cl = 'W'
        elif abs(mid) == 6: cl = 't'
        elif abs(mid) == 5: cl = 'b'
        elif abs(mid) > 100: cl = 'hadron'
        elif abs(mid) in [21,1,2,3,4]: cl = 'udcsg'
        else:
            print 'Unknown origin found', mid
            sys.exit()

        for w in weights:
            vw[cl][w].append(eval('tr.weight_'+w))
            
        vorig[cl] += 1
            
        vpt[cl].append(pt)
        veta[cl].append(eta)
        vdr_pho_top_min[cl].append(dr_pho_top[0])
        vdr_pho_top_max[cl].append(dr_pho_top[1])
        vdr_pho_b_min[cl].append(dr_pho_b[0])
        vdr_pho_b_max[cl].append(dr_pho_b[1])
        vdr_pho_W_min[cl].append(dr_pho_W[0])
        vdr_pho_W_max[cl].append(dr_pho_W[1])
        vdr_pho_l_min[cl].append(dr_pho_l[0])
        vdr_pho_l_max[cl].append(dr_pho_l[1])
        
wnorm = {}
wxsec = {}
for l in labels:
    wnorm[l] = {}
    wxsec[l] = {}
    for ww in weights:
        nev = sum(vw[l][ww])
        nw = len(vw[l][ww])
        wnorm[l][ww] = []
        wxsec[l][ww] = []
        for i in range(nw):
            wnorm[l][ww].append(vw[l][ww][i]/nev)
            wxsec[l][ww].append(vw[l][ww][i])
    
print 'Create plots'
        
res = []
for l in labels:
    res.append(vorig[l])
    
# origin
fig1, ax1 = plt.subplots()
ax1.pie(res, labels=labels, colors=colors, explode=explode, autopct='%1.1f%%', shadow=True, startangle=90)
ax1.axis('equal')
plt.savefig('pics/origin.pdf')
plt.close()

#var = ['pt', 'eta', 'dr_pho_top_min', 'dr_pho_top_max', 'dr_pho_b_min', 'dr_pho_b_max', \
#'dr_pho_W_min', 'dr_pho_W_max', 'dr_pho_l_min', 'dr_pho_l_max']
var = ['pt']

# shapes split by origin (not possible on GEN EFT)
#for p in var:
#    
#    fig = plt.figure()
#    gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
#    ax1 = plt.subplot(gs[0])
#    ax1.set_ylabel("$\mathrm{Normalized \ to \ unity}$")
#    if p == 'pt': bins = np.linspace(0., 500., 50)
#    elif p == 'eta': bins = np.linspace(-4.5, 4.5, 50)
#    elif p == 'dr_pho_top_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_top_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_b_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_b_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_W_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_W_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_l_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_l_max': bins = np.linspace(0., 5., 50)
#    h  = {}
#    for i, l in enumerate(labels):
#        if p == 'pt': data = vpt[l]
#        elif p == 'eta': data = veta[l]
#        elif p == 'dr_pho_top_min': data = vdr_pho_top_min[l]
#        elif p == 'dr_pho_top_max': data = vdr_pho_top_max[l]
#        elif p == 'dr_pho_b_min': data = vdr_pho_b_min[l]
#        elif p == 'dr_pho_b_max': data = vdr_pho_b_max[l]
#        elif p == 'dr_pho_W_min': data = vdr_pho_W_min[l]
#        elif p == 'dr_pho_W_max': data = vdr_pho_W_max[l]
#        elif p == 'dr_pho_l_min': data = vdr_pho_l_min[l]
#        elif p == 'dr_pho_l_max': data = vdr_pho_l_max[l]
#        h[l], hbins, patches = ax1.hist(data, bins, histtype='step', linewidth=1, color=colors[i], alpha=0.7, weights=wnorm[l]['SM'], label=l, fill=fills[i])
#    ax2 = plt.subplot(gs[1], sharex = ax1)
#    ax2.axhline(y=1.0, linestyle='--', linewidth=1)
#    ax2.set_ylabel("$\mathrm{X/t}$")
#    for il in range(1, len(labels)):
#        rat, binc = [], []
#        lab = labels[il]
#        for i, b in enumerate(h[lab]):
#            if abs(h['t'][i]) > 0: rat.append(h[lab][i]/h['t'][i])
#            else: rat.append(0.)
#            binc.append(bins[i])
#        ax2.hist(binc, bins, weights=rat, linewidth=1, histtype='step', color=colors[il], alpha=0.7, fill=fills[il])
#        ax2.set_ylim([0.5, 1.5])
#    plt.setp(ax1.get_xticklabels(), visible=False)
#    yticks = ax2.yaxis.get_major_ticks()
#    yticks[-1].label1.set_visible(False)
#    if p == 'pt': plt.xlabel("$\mathrm{E_{T} \ [GeV]}$")
#    elif p == 'eta': plt.xlabel("$\mathrm{\eta}$")
#    elif p == 'dr_pho_top_min': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{min}}$")
#    elif p == 'dr_pho_top_max': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{max}}$")
#    elif p == 'dr_pho_b_min': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{min}}$")
#    elif p == 'dr_pho_b_max': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{max}}$")
#    elif p == 'dr_pho_W_min': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{min}}$")
#    elif p == 'dr_pho_W_max': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{max}}$")
#    elif p == 'dr_pho_l_min': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{min}}$")
#    elif p == 'dr_pho_l_max': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{max}}$")
#    ax1.legend(loc='upper right')
#    plt.subplots_adjust(hspace=.0)
#    fig.align_ylabels()
#    plt.savefig('pics/'+p+'.pdf')
#    plt.close()

print 'Create matplotlib plots'

doNorm = False
# shapes split by couplings
for p in var:
    
    fig = plt.figure()
    gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
    ax1 = plt.subplot(gs[0])
    if doNorm: ax1.set_ylabel("$\mathrm{Normalized \ to \ unity}$")
    else: ax1.set_ylabel("$\mathrm{Number \ of \ events}$")
    if p == 'pt': bins = np.linspace(0., 500., 50)
    elif p == 'eta': bins = np.linspace(-4.5, 4.5, 50)
    elif p == 'dr_pho_top_min': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_top_max': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_b_min': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_b_max': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_W_min': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_W_max': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_l_min': bins = np.linspace(0., 5., 50)
    elif p == 'dr_pho_l_max': bins = np.linspace(0., 5., 50)
    h = {}
    for i, w in enumerate(weights):
        vdata = []
        vvw = []
        for l in labels:
            if p == 'pt': data = vpt[l]
            elif p == 'eta': data = veta[l]
            elif p == 'dr_pho_top_min': data = vdr_pho_top_min[l]
            elif p == 'dr_pho_top_max': data = vdr_pho_top_max[l]
            elif p == 'dr_pho_b_min': data = vdr_pho_b_min[l]
            elif p == 'dr_pho_b_max': data = vdr_pho_b_max[l]
            elif p == 'dr_pho_W_min': data = vdr_pho_W_min[l]
            elif p == 'dr_pho_W_max': data = vdr_pho_W_max[l]
            elif p == 'dr_pho_l_min': data = vdr_pho_l_min[l]
            elif p == 'dr_pho_l_max': data = vdr_pho_l_max[l]
            vdata += data
            if doNorm: vvw += wnorm[l][w]
            else: vvw += wxsec[l][w]
        if doNorm: vvw = [v / float(len(labels)) for v in vvw]
        h[w], hbins, patches = ax1.hist(vdata, bins, histtype='step', linewidth=1, color=colorsEFT[i], alpha=0.7, weights=vvw, label=w.replace('_','\_'), fill=fillsEFT[i])
    ax2 = plt.subplot(gs[1], sharex = ax1)
    ax2.axhline(y=1.0, linestyle='--', linewidth=1)
    ax2.set_ylabel("$\mathrm{EFT/SM}$")
    for iw in range(1, len(weights)):
        rat, binc = [], []
        lab = weights[iw]
        for i, b in enumerate(h[lab]):
            if abs(h['SM'][i]) > 0: rat.append(h[lab][i]/h['SM'][i])
            else: rat.append(0.)
            binc.append(bins[i])
        ax2.hist(binc, bins, weights=rat, linewidth=1, histtype='step', color=colorsEFT[iw], alpha=0.7, fill=fillsEFT[iw])
        ax2.set_ylim([0.5, 5.5])
    plt.setp(ax1.get_xticklabels(), visible=False)
    yticks = ax2.yaxis.get_major_ticks()
    yticks[-1].label1.set_visible(False)
    if p == 'pt': plt.xlabel("$\mathrm{E_{T} \ [GeV]}$")
    elif p == 'eta': plt.xlabel("$\mathrm{\eta}$")
    elif p == 'dr_pho_top_min': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{min}}$")
    elif p == 'dr_pho_top_max': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{max}}$")
    elif p == 'dr_pho_b_min': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{min}}$")
    elif p == 'dr_pho_b_max': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{max}}$")
    elif p == 'dr_pho_W_min': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{min}}$")
    elif p == 'dr_pho_W_max': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{max}}$")
    elif p == 'dr_pho_l_min': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{min}}$")
    elif p == 'dr_pho_l_max': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{max}}$")
    if p == 'pt': ax1.set_yscale('log')
    else: ax1.set_yscale('linear')
    ax1.legend(loc='upper right')
    plt.subplots_adjust(hspace=.0)
    fig.align_ylabels()
    plt.savefig('pics/'+p+'_EFT.pdf')
    plt.close()

# shapes split by couplings and origin (not possible on GEN EFT)
#for p in var:

#    if p == 'pt': bins = np.linspace(0., 500., 50)
#    elif p == 'eta': bins = np.linspace(-4.5, 4.5, 50)
#    elif p == 'dr_pho_top_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_top_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_b_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_b_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_W_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_W_max': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_l_min': bins = np.linspace(0., 5., 50)
#    elif p == 'dr_pho_l_max': bins = np.linspace(0., 5., 50)
    
#    for l in labels:
        
#        if p == 'pt': data = vpt[l]
#        elif p == 'eta': data = veta[l]
#        elif p == 'dr_pho_top_min': data = vdr_pho_top_min[l]
#        elif p == 'dr_pho_top_max': data = vdr_pho_top_max[l]
#        elif p == 'dr_pho_b_min': data = vdr_pho_b_min[l]
#        elif p == 'dr_pho_b_max': data = vdr_pho_b_max[l]
#        elif p == 'dr_pho_W_min': data = vdr_pho_W_min[l]
#        elif p == 'dr_pho_W_max': data = vdr_pho_W_max[l]
#        elif p == 'dr_pho_l_min': data = vdr_pho_l_min[l]
#        elif p == 'dr_pho_l_max': data = vdr_pho_l_max[l]
#        
#        fig = plt.figure()
#        gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
#        ax1 = plt.subplot(gs[0])
#        ax1.set_ylabel("$\mathrm{Normalized \ to \ unity}$")
#        h = {}
#        for i, w in enumerate(weights):
#            h[w], hbins, patches = ax1.hist(data, bins, histtype='step', linewidth=1, color=colorsEFT[i], alpha=0.7, weights=wnorm[l][w], label=w.replace('_','\_'), fill=fillsEFT[i])
#        ax2 = plt.subplot(gs[1], sharex = ax1)
#        ax2.axhline(y=1.0, linestyle='--', linewidth=1)
#        ax2.set_ylabel("$\mathrm{EFT/SM}$")
#        for iw in range(1, len(weights)):
#            rat, binc = [], []
#            lab = weights[iw]
#            for i, b in enumerate(h[lab]):
#                if abs(h['SM'][i]) > 0: rat.append(h[lab][i]/h['SM'][i])
#                else: rat.append(0.)
#                binc.append(bins[i])
#            ax2.hist(binc, bins, weights=rat, linewidth=1, histtype='step', color=colorsEFT[iw], alpha=0.7, fill=fillsEFT[iw])
#            ax2.set_ylim([0.5, 1.5])
#        plt.setp(ax1.get_xticklabels(), visible=False)
#        yticks = ax2.yaxis.get_major_ticks()
#        yticks[-1].label1.set_visible(False)
#        if p == 'pt': plt.xlabel("$\mathrm{E_{T} \ [GeV]}$")
#        elif p == 'eta': plt.xlabel("$\mathrm{\eta}$")
#        elif p == 'dr_pho_top_min': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{min}}$")
#        elif p == 'dr_pho_top_max': plt.xlabel("$\mathrm{\Delta R(\gamma,t)_{max}}$")
#        elif p == 'dr_pho_b_min': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{min}}$")
#        elif p == 'dr_pho_b_max': plt.xlabel("$\mathrm{\Delta R(\gamma,b)_{max}}$")
#        elif p == 'dr_pho_W_min': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{min}}$")
#        elif p == 'dr_pho_W_max': plt.xlabel("$\mathrm{\Delta R(\gamma,W)_{max}}$")
#        elif p == 'dr_pho_l_min': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{min}}$")
#        elif p == 'dr_pho_l_max': plt.xlabel("$\mathrm{\Delta R(\gamma,l)_{max}}$")
#        if p == 'pt': ax1.set_yscale('log')
#        else: ax1.set_yscale('linear')
#        ax1.legend(loc='upper right')
#        plt.subplots_adjust(hspace=.0)
#        fig.align_ylabels()
#        plt.savefig('pics/'+p+'_'+l+'_EFT.pdf')
#        plt.close()

print 'Create ROOT plots'

ROOT.gROOT.SetBatch()

c1 = ROOT.TCanvas()

pstyle = style.SetPlotStyle(2)

ptbins = []
fpt = ROOT.TFile.Open('../../../Limits/16Yaphptll/srFit_2016_shapes.root', 'OPEN')
hpt = fpt.Get('sr_ee/TTGamma')
for i in range(hpt.GetXaxis().GetNbins()):
    ptbins.append(hpt.GetXaxis().GetBinLowEdge(i+1))
ptbins.append(hpt.GetXaxis().GetBinUpEdge(hpt.GetXaxis().GetNbins()))
    
hpt = {}
hpt['SM'] = ROOT.TH1D('hptSM', 'hptSM', len(ptbins)-1, np.array(ptbins))
hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'] = ROOT.TH1D('hptEFTR', 'hptEFTR', len(ptbins)-1, np.array(ptbins))
hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'] = ROOT.TH1D('hptEFTI', 'hptEFTI', len(ptbins)-1, np.array(ptbins))
    
for i, l in enumerate(labels):
    data = vpt[l]
    for j, d in enumerate(data):
        hpt['SM'].Fill(d, vw[l]['SM'][j])
        hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'].Fill(d, vw[l]['ctZ_2_ctZI_0_ctW_0_ctWI_0'][j])
        hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'].Fill(d, vw[l]['ctZ_0_ctZI_2_ctW_0_ctWI_0'][j])
        
hpt['SM'].SetLineColor(ROOT.kBlack)
hpt['SM'].SetLineWidth(2)

hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'].SetLineColor(ROOT.kRed)
hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'].SetLineWidth(2)

hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'].SetLineColor(ROOT.kBlue)
hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'].SetLineWidth(2)

hpt['SM'].Draw('hist e1')
hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'].Draw('hist e1 same')
hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'].Draw('hist e1 same')

leg = ROOT.TLegend(0.32,0.75,0.56,0.82)
leg.SetFillColor(253)
leg.SetBorderSize(0)
leg.AddEntry(hpt['SM'], "SM", "l")
leg.AddEntry(hpt['ctZ_2_ctZI_0_ctW_0_ctWI_0'], "C_{tZ} = 2", "l")
leg.AddEntry(hpt['ctZ_0_ctZI_2_ctW_0_ctWI_0'], "C^{[I]}_{tZ} = 2", "l")
leg.Draw()

t1, t2, t3 = style.cmslabel(2, '', False)
t1.Draw()
t2.Draw()
#t3.Draw()

c1.SetLogy(1)

c1.Print('pics/photonPtEFT.pdf')
c1.Clear()
