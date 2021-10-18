#!/usr/bin/env python

import pickle as pkl
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import simps
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import os, sys, math
from optparse import OptionParser

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
plt.rcParams['figure.subplot.left'] = 0.2
plt.rcParams['figure.subplot.right'] = 0.96
plt.rcParams['figure.subplot.top'] = 0.95

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Compute confidence intervals for log-likelihood"

    parser = OptionParser(usage)
    parser.add_option("--nll", type=str, default='ctZ_obs', help="Name of the file with NLL [default: %default]")
    parser.add_option("--year", type=str, default='Run2_Comb', help="Year of data taking [default: %default]")
    parser.add_option("--max", type=str, default='5.', help="Maximum NLL value [default: %default]")
    parser.add_option("--step", type=str, default='0.01', help="Step in NLL scan [default: %default]")
    parser.add_option("--type", type=str, default='inclusive', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    parser.add_option("--dim", type=str, default='1d', help="Number of dimensions [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    return options

def calcNLL(ax, c1, c2, nll, prob, nllcut):

    x, y = [], []
    
    nllstep = float(options.step)
    for inll in range(0, int(max(nll)*nllcut/nllstep)):
        nllv = nllstep*inll+0.01
        x.append(nllv)
        tr = ax.tricontour(c1, c2, nll, levels=[nllv])
        integ = 0.
        for i in range(len(c1)):
            point = Point(c1[i], c2[i])
            for collection in tr.collections:
                for path in collection.get_paths():
                    pols = path.to_polygons()
                    if len(pols) == 1:
                        polygon = Polygon(pols[0])
                        if polygon.contains(point):
                            integ += prob[i]
                    elif len(pols) == 2:
                        p1 = pols[0] if len(pols[0]) > len(pols[1]) else pols[1]
                        p2 = pols[1] if p1 == pols[0] else pols[0]
                        polygon1 = Polygon(p1)
                        polygon2 = Polygon(p2)
                        if polygon1.contains(point) and not polygon2.contains(point):
                            integ += prob[i]
#                    else:
#                        print('Empty regions, skip')
        for collection in tr.collections:
                collection.remove()
        y.append(integ)
    
    return x, y
    
if __name__ == '__main__':

    options = main()
    
    if not os.path.isdir('results'): os.system('mkdir results')
    if not os.path.isdir('results/'+options.year): os.system('mkdir results/'+options.year)

    f = open('../pics/photon_pt/'+options.year+'/'+options.nll+'.pkl', 'rb')
    data = pkl.load(f)

    if options.dim == '1d':
        
        cc = data['coup']
        nll = [d for d in data['nll'] if d < float(options.max)]
        coup = [c for ic, c in enumerate(cc) if data['nll'][ic] < float(options.max)]
        prob = [math.exp(-d/2.) for d in nll]
        
        fnll = interp1d(coup, nll, kind='cubic')
        fprob = interp1d(coup, prob, kind='cubic')
        
        # sample the function
        x = np.linspace(coup[0], coup[-1], num=1000, endpoint=True)
        y = [fprob(xv) for xv in x]
        ynll = [fnll(xv) for xv in x]
        for iv, yv in enumerate(y):
            if yv < 0.: y[iv] = 0.
        yint = simps(y)
        ypdf = [yv/yint for yv in y]
        imax = ypdf.index(max(ypdf))

        # find intersection points
        xspoints, nllpoints = [], []
        nllstep = float(options.step)
        for inll in range(1, int(max(ynll)/nllstep)):
            nllv = nllstep*inll
            sign = 1.
            xs = []
            for ip, xv in enumerate(x):
                if sign*(ynll[ip]-nllv) <= 0:
                    xs.append(ip)
                    sign *= -1.
            xspoints.append(xs)
            nllpoints.append(nllv)

        # integrate
        xpdfint, ypdfint = [], []
        for ip, nllv in enumerate(nllpoints):
            itv = xspoints[ip]
            if len(itv) < 2: continue
        
            xpdfint.append(nllv)
            yr = ypdf[itv[0]:itv[1]]
            yv = simps(yr)
            if len(itv) == 4:
                yr = ypdf[itv[2]:itv[3]]
                yv += simps(yr)
            ypdfint.append(yv)
        
        # find intervals
        cl68, cl95 = -1, -1
        for iv, yv in enumerate(ypdfint):
            if yv >= 0.68 and cl68 < 0:
                cl68 = xpdfint[iv]
            if yv >= 0.95 and cl95 < 0:
                cl95 = xpdfint[iv]
        
        cname = options.nll.split('_')[0]
        if cname == 'ctZ': cname = '$\mathrm{C_{tZ}}$'
        elif cname == 'ctZI': cname = '$\mathrm{C_{tZ}^{I}}$'

        gs_nll = plt.GridSpec(3, 1, hspace=0)
        gs_integ = plt.GridSpec(3, 1, top=0.28, bottom=-0.23)
        fig = plt.figure(figsize=(6, 7))
        ax1 = fig.add_subplot(gs_nll[0])
        ax1.set_ylabel('-2ln$\Delta\mathcal{L}$')
        ax2 = fig.add_subplot(gs_nll[1], sharex=ax1)
        ax2.set_xlabel(cname)
        ax2.set_ylabel('Probability density')
        ax1.plot(coup, nll, '.', x, fnll(x), '-')
        ax1.get_yaxis().set_label_coords(-0.15, 0.5)
        ax1.set_ylim(bottom=0, top=float(options.max))
        ax2.plot(x, ypdf, '-')
        ax2.get_yaxis().set_label_coords(-0.15, 0.5)
        ax2.set_ylim(bottom=0)
        nbins = len(ax2.get_xticklabels())
        ax1.yaxis.set_major_locator(MaxNLocator(nbins=nbins, prune='lower'))
        ax3 = fig.add_subplot(gs_integ[0])
        ax3.set_xlabel('-2ln$\Delta\mathcal{L}$')
        ax3.set_ylabel('Probability')
        ax3.plot(xpdfint, ypdfint, '-')
        ax3.axhline(y=0.68, color='g', linestyle=':', linewidth=1.)
        ax3.axhline(y=0.95, color='g', linestyle='--', linewidth=1.)
        ax3.axvline(x=cl68, color='r', linestyle=':', linewidth=1.)
        ax3.axvline(x=cl95, color='r', linestyle='--', linewidth=1.)
        ax3.plot(cl68, 0.68, 'r.')
        ax3.plot(cl95, 0.95, 'r.')
        ax3.text(9.0, 0.55, "68\%", color='g')
        ax3.text(9.0, 0.83, "95\%", color='g')
        ax3.text(cl68-0.25, 0.21, "{:.2f}".format(cl68), color='r', rotation='vertical')
        ax3.text(cl95-0.25, 0.21, "{:.2f}".format(cl95), color='r', rotation='vertical')
        ax3.get_yaxis().set_label_coords(-0.15, 0.5)
        ax3.set_ylim(bottom=0, top=1.)
        ax3.set_xlim(left=0., right=float(options.max))
        fig.savefig('results/'+options.year+'/'+options.nll+'_prob.pdf')
        
        cl = [cl68, cl95]
        f = open('results/'+options.year+'/'+options.nll+'_cl.pkl', 'wb')
        pkl.dump(cl, f)
    
    elif options.dim == '2d':
        
        coup1 = data['coup1']
        coup2 = data['coup2']
        nlll = [d for d in data['nll'] if d < float(options.max)]
        cc1 = [c for ic, c in enumerate(coup1) if data['nll'][ic] < float(options.max)]
        cc2 = [c for ic, c in enumerate(coup2) if data['nll'][ic] < float(options.max)]
        c1, c2, nll = [], [], []
        nllmax = max(nlll)
        for ic in range(len(cc1)):
            if abs(cc1[ic]) > 1.0 or abs(cc2[ic]) > 1.0: continue
            if options.year in ['2016']: 
                if abs(cc1[ic]) > 0.6 and abs(cc2[ic]) > 0.6 and nlll[ic] < 0.8*nllmax and 'obs' not in options.nll: continue
            if options.year in ['2017']:
                if abs(cc1[ic]) > 0.6 and abs(cc2[ic]) > 0.6 and nlll[ic] < 0.8*nllmax and 'obs' not in options.nll: continue
            if options.year in ['2018']:
                if (abs(cc1[ic]) > 0.75 or abs(cc2[ic]) > 0.7) and nlll[ic] < 0.9*nllmax and 'obs' not in options.nll: continue
            c1.append(cc1[ic])
            c2.append(cc2[ic])
            nll.append(nlll[ic])
        prob = [math.exp(-d/2.) for d in nll]
#        prob = [float(i)/sum(prob) for i in prob]
        yint = simps(prob)
        prob = [yv/yint for yv in prob]

        plt.rcParams['figure.subplot.left'] = 0.10
        plt.rcParams['figure.subplot.right'] = 0.95
        
        cname1 = options.nll.split('_')[0]
        if cname1 == 'ctZ': cname1 = '$\mathrm{C_{tZ}}$'
        elif cname1 == 'ctZI': cname1 = '$\mathrm{C_{tZ}^{I}}$'

        cname2 = options.nll.split('_')[1]
        if cname2 == 'ctZ': cname2 = '$\mathrm{C_{tZ}}$'
        elif cname2 == 'ctZI': cname2 = '$\mathrm{C_{tZ}^{I}}$'
        
        gs = plt.GridSpec(2, 2, bottom=0.15, height_ratios=[2,1])
        fig = plt.figure(figsize=(10, 6))
        ax1 = fig.add_subplot(gs[0])
        ax1.set_title('-2ln$\Delta\mathcal{L}$')
        ax1.set_xlabel(cname1)
        ax1.set_ylabel(cname2)        
        ax2 = fig.add_subplot(gs[1])
        ax2.set_title('Probability density')
        ax2.set_xlabel(cname1)
        ax2.set_ylabel(cname2)
        sc1 = ax1.scatter(c1, c2, c=nll, alpha=0.8, cmap='viridis')
        fig.colorbar(sc1, ax=ax1)
        nllcut = 1.0
        x, y = calcNLL(ax1, c1, c2, nll, prob, nllcut)
        
        # find intervals
        cl68, cl95 = -1, -1
        for iv, yv in enumerate(y):
            if yv >= 0.68 and cl68 < 0:
                cl68 = x[iv]
            if yv >= 0.95 and cl95 < 0:
                cl95 = x[iv]
        
        l1 = tr1 = ax1.tricontour(c1, c2, nll, levels=[cl68, cl95])
        ax1.clabel(l1, inline=1, fontsize=7)
        
        ax1.get_yaxis().set_label_coords(-0.15, 0.5)
        sc2 = ax2.scatter(c1, c2, c=prob, alpha=0.8, cmap='viridis')
        fig.colorbar(sc2, ax=ax2)
        ax2.get_yaxis().set_label_coords(-0.15, 0.5)
        ax3 = fig.add_subplot(gs[-1:, :])
        ax3.set_xlabel('-2ln$\Delta\mathcal{L}$')
        ax3.set_ylabel('Probability')
        fig.subplots_adjust(hspace=0.4)
        ax3.plot(x, y, '-')
        ax3.axhline(y=0.68, color='g', linestyle=':', linewidth=1.)
        ax3.axhline(y=0.95, color='g', linestyle='--', linewidth=1.)
        ax3.axvline(x=cl68, color='r', linestyle=':', linewidth=1.)
        ax3.axvline(x=cl95, color='r', linestyle='--', linewidth=1.)
        ax3.plot(cl68, 0.68, 'r.')
        ax3.plot(cl95, 0.95, 'r.')
        ax3.text(7.5, 0.55, "68\%", color='g')
        ax3.text(7.5, 0.83, "95\%", color='g')
        ax3.text(cl68-0.15, 0.21, "{:.2f}".format(cl68), color='r', rotation='vertical')
        ax3.text(cl95-0.15, 0.21, "{:.2f}".format(cl95), color='r', rotation='vertical')
#        ax3.get_yaxis().set_label_coords(-0.15, 0.5)
        ax3.set_ylim(bottom=0, top=1.)
        ax3.set_xlim(left=0., right=float(options.max)*min(nllcut, 0.7))
        fig.savefig('results/'+options.year+'/'+options.nll+'_prob.pdf')
        
        cl = [cl68, cl95]
        f = open('results/'+options.year+'/'+options.nll+'_cl.pkl', 'wb')
        pkl.dump(cl, f)
    
