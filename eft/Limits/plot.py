#!/usr/bin/env python

import ROOT
import os, sys, glob, json
import numpy as np
import array
import pickle as pkl

import style

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def getOpLabel(name):
    
    if name == 'ctZ': lab = 'C_{tZ}/#Lambda^{2}'
    elif name == 'ctZI': lab = 'C_{tZ}^{I}/#Lambda^{2}'
    else:
        print 'Unknown operator'
        sys.exit()
    
    return lab

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Plot NLL scan results"
    
    parser = OptionParser(usage)
    parser.add_option("--input", type=str, default='eft_fit', help="Input directory name [default: %default]")
    parser.add_option("--output", type=str, default='pics', help="Output directory name [default: %default]")
    parser.add_option("--op", type=str, default='ctZ,ctZI', help="Coefficient names [default: %default]")
    parser.add_option("--obs", action='store_true', help="Show observed limits [default: %default]")
    parser.add_option("--customcl", action='store_true', help="Use custom-defined CL intervals [default: %default]")
    parser.add_option("--year", type=str, default='2016', help="Year of data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--xmin", type=float, default=-3.0, help="X axis minimum range [default: %default]")
    parser.add_option("--xmax", type=float, default=3.0, help="X axis maximum range [default: %default]")
    parser.add_option("--ymin", type=float, default=0.0, help="Y axis minimum range [default: %default]")
    parser.add_option("--ymax", type=float, default=20.0, help="Y axis maximum range [default: %default]")
    parser.add_option("--ymaxprof", type=float, default=10.0, help="Y axis maximum range [default: %default]")
    parser.add_option("--s1v", type=float, default=1.0, help="Probability at one sigma [default: %default]")
    parser.add_option("--s2v", type=float, default=3.84, help="Probability at two sigmas [default: %default]")
    parser.add_option("--s1v2d", type=float, default=2.30, help="Probability at one sigma for 2D fit [default: %default]")
    parser.add_option("--s2v2d", type=float, default=5.99, help="Probability at two sigmas for 2D fit [default: %default]")
    parser.add_option("--dim", type=str, default='1d', help="Dimension of the fits [default: %default]")
    parser.add_option("--type", type=str, default='inclusive', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    parser.add_option("--label", type=str, default='', help="Append string to the year label [default: %default]")
    parser.add_option("--toy", type=int, default=-1, help="Plot results from toys [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

def getGraphs1d(wdir, res):

    gr, bestfit = [], []
    
    gr.append({})
    bestfit.append({})
        
    for w in res:
            
        fres = wdir+w+'/result.json'
        with open(fres, "r") as read_file:
            r = json.load(read_file)

        coup, nll = [], []
        for k, v in r.iteritems():
            coup.append(float(k))
            nll.append(v)
            
        z = zip(coup, nll)
        nll = zip(*sorted(z))[1]    
        coup.sort()
            
        coup = np.array(coup, dtype='d')
        nll = np.array(nll, dtype='d')
        if 'Run2' in options.year and options.toy < 0:
            for iv, v in enumerate(nll):
                if v < 1E-1 and w in ['observed'] and 'Comb' in options.label: nll[iv] = 0.03
                elif v < 1E-2 and w in ['observed']: nll[iv] = 0.01
                elif v < 0 and w in ['expected']: nll[iv] = 0
            
        gr[-1][w] = ROOT.TGraph(len(nll), coup, nll)
        bestfit[-1][w] = coup[np.argmin(nll)]
            
    return gr, bestfit

def getGraphs1dProfiled(wdir, wres, meas = 'c1', prof = 'c2'):

    gr, bestfit = {}, {}
    
    for w in wres:

        fres = wdir+w+'/result.json'
        with open(fres, "r") as read_file:
            res = json.load(read_file)

        data = []
        for k, v in res.iteritems():
            coup1 = float(k.split('_')[0])
            coup2 = float(k.split('_')[1])
            nll = v
            if 'Run2' in options.year and options.toy < 0:
#                if nll < 1E-1 and w in ['observed'] and 'Comb' in options.label: nll = 0.03
#                elif nll < 1E-2 and w in ['observed']: nll = 0.01
                if v < 0 and w in ['expected']: nll = 0.005
            if meas == 'c1': data.append({meas:coup1, prof:coup2, 'nll':nll})
            else: data.append({meas:coup2, prof:coup1, 'nll':nll})
        
        data_prof = sorted(data, key = lambda i: i[prof])
        data_measprof = sorted(data_prof, key = lambda i: i[meas])
    
        nllprof, cprof, cmeascprof = [], [], []
    
        cmeascur = data_measprof[0][meas]
        nlla = []
    
        for d in data_measprof:

            cmeas = d[meas]
            cprof = d[prof]
            nll = d['nll']
            nlla.append(nll)
        
            if cmeascur != cmeas:
                
                nlla = np.array(nlla, dtype='d')    
                imin = np.argmin(nlla)
                
                cmeascprof.append(cmeascur)
                nllprof.append(nlla[imin])

                nlla = []
                
                cmeascur = cmeas
                
        coup_cprof = np.array(cmeascprof, dtype='d')
        nll_cprof = np.array(nllprof, dtype='d')
        
        bestfit[w] = coup_cprof[np.argmin(nll_cprof)]
    
        gr[w] = ROOT.TGraph(len(nll_cprof), coup_cprof, nll_cprof)
        
    print bestfit
    
    return gr, bestfit

def getContours2d(wdir, wres, cname):

    fres = wdir+wres+'/result.json'
    with open(fres, "r") as read_file:
        res = json.load(read_file)

    coup1, coup2, nll = [], [], []
    for k, v in res.iteritems():
        coup1.append(float(k.split('_')[0]))
        coup2.append(float(k.split('_')[1]))
        nll.append(v)
        
    coup1 = np.array(coup1, dtype='d')
    coup2 = np.array(coup2, dtype='d')
    nll = np.array(nll, dtype='d')
    
    imin = np.argmin(nll)
    nllmin = min(nll)
    c1min = coup1[imin]
    c2min = coup2[imin]
    
    nbins = 90

    c0 = ROOT.TCanvas('c0_nll_'+wres, 'c0_nll_'+wres, 500, 500)
    c0.cd()
    hAxis = ROOT.TH2F('hAxis_nll_'+wres, 'hAxis_nll_'+wres, nbins, options.xmin, options.xmax, nbins, options.xmin, options.xmax)    
    hAxis.Draw()

    hAxis.GetXaxis().SetTitle(getOpLabel(options.op.split(',')[0])+' [TeV^{2}]')
    hAxis.GetYaxis().SetTitle(getOpLabel(options.op.split(',')[1])+' [TeV^{2}]')
        
    grNll = ROOT.TGraph2D('gr_'+wres, 'gr_'+wres, len(nll), coup1, coup2, nll)
    grNll.SetNpx(100)
    grNll.SetNpy(100)
    
    hNll = grNll.GetHistogram().Clone()

    hNll.Smooth(1, 'k5b')

    contVal = readNLL(cname, dim = '2d')
    hNll.SetContour(len(contVal), array.array('d', contVal))
    hNll.Draw('CONT LIST SAME')
    c0.Update()
    
    gr = ROOT.gROOT.GetListOfSpecials().FindObject('contours').Clone()

    return [hAxis, grNll, gr, c1min, c2min]

def buildBands(gr, x2n, x2p, bestfit):
    
    x2n2 = x2n[0]
    x2n1 = x2n[1] if len(x2n) > 1 else 777
    if len(x2p) > len(x2n):
        x2n2 = x2n[0]
        x2n1 = x2p[0]
        x2p2 = x2p[1]
        x2p1 = x2p[2]
    else:
        x2p2 = x2p[0]
        x2p1 = x2p[1] if len(x2p) > 1 else 777
    
    xb, yb = [], []
    xb1, yb1 = [], []
    xb2, yb2 = [], []
    
    if len(x2p) == len(x2n):
        
        if 'Run2' in options.year:
            for ig in range(100000):
                xg = -10.+ig*0.0001
                if xg >= x2n2 and xg != 777 and xg < bestfit:
                    xb.append(xg)
                    if gr.Eval(xg) >= 0.: yb.append(gr.Eval(xg))
                    else: yb.append(0.)
        else:
            for ig in range(gr.GetN()):
                xg = gr.GetX()[ig]
                if xg > x2n2 and xg != 777 and xg < bestfit:
                    xb.append(xg)
                    yb.append(gr.Eval(xg))

        for ig in range(gr.GetN()):
            xg = gr.GetX()[ig]
            if xg < x2p2 and xg != 777 and xg >= bestfit:
                xb.append(xg)
                if gr.Eval(xg) >= 0.: yb.append(gr.Eval(xg))
                else: yb.append(0.)

#            for ig in range(1000):
#                xg = -10.+ig*0.01
#                if xg < x2p2 and xg != 777 and xg > bestfit:
#                    xb.append(xg)
#                    yb.append(gr.Eval(xg))
                
    else:

        if 'Run2' in options.year:
            for ig in range(100000):
                xg = -10.+ig*0.0001
                if xg > x2n2 and xg != 777 and xg < bestfit:
                    xb1.append(xg)
                    if gr.Eval(xg) >= 0.: yb1.append(gr.Eval(xg))
                    else: yb1.append(0.)

            for ig in range(100000):
                xg = -10.+ig*0.0001
                if xg < x2n1 and xg != 777 and xg >= bestfit:
                    xb1.append(xg)
                    if gr.Eval(xg) >= 0.: yb1.append(gr.Eval(xg))
                    else: yb1.append(0.)
        else:
                
            for ig in range(gr.GetN()):
                xg = gr.GetX()[ig]
                if xg > x2n2 and xg != 777 and xg < bestfit:
                    xb1.append(xg)
                    yb1.append(gr.Eval(xg))

            for ig in range(gr.GetN()):
                xg = gr.GetX()[ig]
                if xg < x2n1 and xg != 777 and xg > bestfit:
                    xb1.append(xg)
                    yb1.append(gr.Eval(xg))
                
        xb1.append(x2n1); 
        yb1.append(gr.Eval(x2n1))
        xb1.append(x2n1); yb1.append(0.)

        xb1.insert(0, x2n2); 
        yb1.insert(0, gr.Eval(x2n2))
        xb1.insert(0, x2n2); yb1.insert(0, 0.)

#        for ig in range(1000):
#            xg = -10.+ig*0.01
#            if xg > x2p2 and xg < x2p1 and xg != 777 and xg > bestfit:
#                xb2.append(xg)
#                yb2.append(gr.Eval(xg))
        
        for ig in range(gr.GetN()):
            xg = gr.GetX()[ig]
            if xg > x2p2 and xg < x2p1 and xg != 777 and xg > bestfit:
                xb2.append(xg)
                yb2.append(gr.Eval(xg))

        xb2.append(x2p1);
        yb2.append(gr.Eval(x2p1))
        xb2.append(x2p1); yb2.append(0.)

        xb2.insert(0, x2p2); 
        yb2.insert(0, gr.Eval(x2p2))
        xb2.insert(0, x2p2); yb2.insert(0, 0.)
        for ix, x in enumerate(xb2):
            print x, yb2[ix]
                
#    for ig in range(1000):
#        neg = -10.+ig*0.01
#        if neg >= x2n2 and neg != 777 and neg < bestfit:
#            xb.append(neg)
#            yb.append(gr.Eval(neg))

#    for ig in range(1000):
#        pos = -10.+ig*0.01
#        if pos <= x2p2 and pos != 777 and pos > bestfit:
#            xb.append(pos)
#            yb.append(gr.Eval(pos))

    if len(x2p) == len(x2n):
        xb.append(x2p2);
        yb.append(gr.Eval(x2p2))
        xb.append(x2p2); yb.append(0.)
        
        xb.insert(0, x2n2); 
        yb.insert(0, gr.Eval(x2n2))
        xb.insert(0, x2n2); yb.insert(0, 0.)
            
        xb = np.array(xb, dtype='d')
        yb = np.array(yb, dtype='d')        
        
        band = [ROOT.TGraph(len(yb), xb, yb)]
    else:
        band = []
        xb1 = np.array(xb1, dtype='d')
        yb1 = np.array(yb1, dtype='d')
        xb2 = np.array(xb2, dtype='d')
        yb2 = np.array(yb2, dtype='d')
        band.append(ROOT.TGraph(len(yb1), xb1, yb1))
        band.append(ROOT.TGraph(len(yb2), xb2, yb2))
            
    return band

def readNLL(cname, dim = '1d'):
    
#    f = 'intervals/results/'+options.year+options.label+'/'+cname+'_cl.pkl'

    if dim == '1d': return [options.s1v, options.s2v]
    else: return [options.s1v2d, options.s2v2d]
    
#    if not os.path.isfile(f) or not options.customcl:
#        if options.dim == '1d': return [options.s1v, options.s2v]
#        else: return [options.s1v2d, options.s2v2d]
#    else:
#        f = open(f, 'rb')
#        return pkl.load(f)

def writeNLL(gr, out = ''):
    
    coup, nll = [], []
    
    for i in range(gr.GetN()):
        c = gr.GetX()[i]
        l = gr.GetY()[i]
        coup.append(c)
        nll.append(l)
        
    if out != '':
        pkl.dump({'coup': coup, 'nll': nll}, open(out, "wb"))

def writeNLL2d(hnll, out = ''):
    
    coup1, coup2, nll = [], [], []

    h = hnll.GetHistogram()
    mhnll = h.GetMaximum()
    for bx in range(1, h.GetXaxis().GetNbins()+1):
        for by in range(1, h.GetYaxis().GetNbins()+1):
            c1 = h.GetXaxis().GetBinCenter(bx)
            c2 = h.GetYaxis().GetBinCenter(by)
            vnll = h.GetBinContent(bx, by)
            coup1.append(c1)
            coup2.append(c2)
            nll.append(vnll)
        
    if out != '':
        pkl.dump({'coup1': coup1, 'coup2': coup2, 'nll': nll}, open(out, "wb"))
        
def drawLimit1d(gr, bestfit, outdir, opname, toy = -1, prof = False):

    c1 = ROOT.TCanvas()
    
    gr['expected'].Draw('ACP')
    if options.obs: gr['observed'].Draw('CP SAME')
    
    gr['expected'].GetYaxis().SetRangeUser(options.ymin, options.ymax)
    if options.obs: gr['observed'].GetYaxis().SetRangeUser(options.ymin, options.ymax)
    
    if prof:
        gr['expected'].GetYaxis().SetRangeUser(options.ymin, options.ymaxprof)
        if options.obs: gr['observed'].GetYaxis().SetRangeUser(options.ymin, options.ymaxprof)

    gr['expected'].GetXaxis().SetLimits(options.xmin, options.xmax)
    if options.obs: gr['observed'].GetXaxis().SetLimits(options.xmin, options.xmax)
        
    gr['expected'].SetMarkerSize(0.)
    gr['expected'].SetMinimum(0.)
    gr['expected'].SetLineWidth(2)
    gr['expected'].GetXaxis().SetTitle(getOpLabel(op)+' [TeV^{-2}]')
    gr['expected'].GetYaxis().SetTitle('-2 #Delta lnN')

    if options.obs:
            
        gr['observed'].SetMarkerSize(0.)
        gr['observed'].SetLineColor(ROOT.kRed)
        gr['observed'].SetLineWidth(2)
        gr['observed'].SetMarkerColor(ROOT.kRed)
        
    s1limexpP, s1limexpN, s2limexpP, s2limexpN = [], [], [], []
    s1limobsP, s1limobsN, s2limobsP, s2limobsN = [], [], [], []

    cntexp = gr['expected'].Eval(bestfit['expected'])
    if options.obs: cntobs = gr['observed'].Eval(bestfit['observed'])
    
    if not prof: contVal = readNLL(op if not options.obs else op+'_obs', dim = '1d')
    else: contVal = readNLL(opname if not options.obs else opname+'_obs', dim = '1d')

    s1v = contVal[0]
    s2v = contVal[1]
        
#    nst = 1000000
#    step = 0.000001

    nst = 10000
    step = 0.001
    
    for i in range(nst):

        posExp = i*step
        negExp = -i*step
        
        llrexpP = gr['expected'].Eval(posExp)
        llrexpN = gr['expected'].Eval(negExp)

        if options.obs:

            posObs = bestfit['observed'] +i*step
            negObs = bestfit['observed'] -i*step
            
            llrobsP = gr['observed'].Eval(posObs)
            llrobsN = gr['observed'].Eval(negObs)

        if cntexp > s1v:
                
            if llrexpP < s1v and len(s1limexpP) == 0: s1limexpP.append(posExp)
            if llrexpP > s1v and len(s1limexpP) == 1: s1limexpP.append(posExp)
            if llrexpP < s2v and len(s2limexpP) == 0: s2limexpP.append(posExp)
            if llrexpP > s2v and len(s2limexpP) == 1: s2limexpP.append(posExp)
            
            if llrexpN < s1v and len(s1limexpN) == 0: s1limexpN.append(negExp)
            if llrexpN > s1v and len(s1limexpN) == 1: s1limexpN.append(negExp)
            if llrexpN < s2v and len(s2limexpN) == 0: s2limexpN.append(negExp)
            if llrexpN > s2v and len(s2limexpN) == 1: s2limexpN.append(negExp)
                
        else:

            if llrexpP > s1v and len(s1limexpP) == 0: s1limexpP.append(posExp)
            if llrexpP > s2v and len(s2limexpP) == 0: s2limexpP.append(posExp)
                
            if llrexpN > s1v and len(s1limexpN) == 0: s1limexpN.append(negExp)
            if llrexpN > s2v and len(s2limexpN) == 0: s2limexpN.append(negExp)
            
        if options.obs:

            if cntobs > s1v:

                if llrobsP < s1v and len(s1limobsP) == 0: s1limobsP.append(posObs)
                if llrobsP > s1v and len(s1limobsP) == 1: s1limobsP.append(posObs)
                if llrobsP < s2v and len(s2limobsP) == 0: s2limobsP.append(posObs)
                if llrobsP > s2v and len(s2limobsP) == 1: s2limobsP.append(posObs)
                    
                if llrobsN < s1v and len(s1limobsN) == 0: s1limobsN.append(negObs)
                if llrobsN > s1v and len(s1limobsN) == 1: s1limobsN.append(negObs)
                if llrobsN < s2v and len(s2limobsN) == 0: s2limobsN.append(negObs)
                if llrobsN > s2v and len(s2limobsN) == 1: s2limobsN.append(negObs)
                    
            else:

                if llrobsP > s1v and (len(s1limobsP) == 0 or len(s1limobsP) == 2): s1limobsP.append(posObs)
                if llrobsP < s1v and (len(s1limobsP) == 1 or len(s1limobsP) == 3): s1limobsP.append(posObs)
                if llrobsP > s2v and (len(s2limobsP) == 0 or len(s2limobsP) == 2): s2limobsP.append(posObs)
                if llrobsP < s2v and (len(s2limobsP) == 1 or len(s2limobsP) == 3): s2limobsP.append(posObs)

                if llrobsN > s1v and (len(s1limobsN) == 0 or len(s1limobsN) == 2): s1limobsN.append(negObs)
                if llrobsN < s1v and (len(s1limobsN) == 1 or len(s1limobsN) == 3): s1limobsN.append(negObs)
                if llrobsN > s2v and (len(s2limobsN) == 0 or len(s2limobsN) == 2): s2limobsN.append(negObs)
                if llrobsN < s2v and (len(s2limobsN) == 1 or len(s2limobsN) == 3): s2limobsN.append(negObs)
        
    if options.obs:
        
        band95 = buildBands(gr['observed'], s2limobsN, s2limobsP, bestfit['observed'])
        for iband in band95:
            iband.SetFillColor(ROOT.kOrange)
            iband.SetLineColor(ROOT.kOrange)
            iband.Draw('F SAME')
        
        band68 = buildBands(gr['observed'], s1limobsN, s1limobsP, bestfit['observed'])
        for iband in band68:                
            iband.SetFillColor(ROOT.kGreen+1)
            iband.SetLineColor(ROOT.kGreen+1)
            iband.Draw('F SAME')
        
    else:

        band95 = buildBands(gr['expected'], s2limexpN, s2limexpP, bestfit['expected'])
        for iband in band95:
            iband.SetFillColor(ROOT.kOrange)
            iband.SetLineColor(ROOT.kOrange)
            iband.Draw('F SAME')
        
        band68 = buildBands(gr['expected'], s1limexpN, s1limexpP, bestfit['expected'])
        for iband in band68:
            iband.SetFillColor(ROOT.kGreen+1)
            iband.SetLineColor(ROOT.kGreen+1)
            iband.Draw('F SAME')

    if not options.obs:
        
        sexp = []
        for isr, sr in enumerate([s1limexpP, s1limexpN, s2limexpP, s2limexpN]):
            for s in sr:
                if s == 0.: continue
                sexp.append(ROOT.TLine(s, options.ymin, s, gr['expected'].Eval(s)))
                if isr < 2: sexp[-1].SetLineColor(ROOT.kGreen+1)
                else: sexp[-1].SetLineColor(ROOT.kOrange)
                sexp[-1].SetLineStyle(1)
                sexp[-1].SetLineWidth(2)
                sexp[-1].Draw()

    else:

        sobs = []
        for isr, sr in enumerate([s1limobsP, s1limobsN, s2limobsP, s2limobsN]):
            for s in sr:
                if s == 0.: continue
                sobs.append(ROOT.TLine(s, options.ymin, s, gr['observed'].Eval(s)))
                if isr < 2: sobs[-1].SetLineColor(ROOT.kGreen+1)
                else: sobs[-1].SetLineColor(ROOT.kOrange)
                sobs[-1].SetLineStyle(1)
                sobs[-1].SetLineWidth(2)
                sobs[-1].Draw()
        
    gr['expected'].Draw('CP SAME')
    if options.obs: gr['observed'].Draw('CP SAME')
    
    rout = {}
    for t in ['expected', 'observed']:
        if not options.obs and t in ['observed']: continue
        rout[t] = {}
        
    if len(s1limexpP) > 1 and 0. not in s1limexpP:
        lexp68 = 'Expected 68% CL ['+("%.2f" % round(s1limexpN[1],2))+', '+("%.2f" % round(s1limexpN[0],2))+'], ['+("%.2f" % round(s1limexpP[0],2))+', '+("%.2f" % round(s1limexpP[1],2))+']'
        rout['expected']['68'] = [s1limexpN[1], s1limexpN[0], s1limexpP[0], s1limexpP[1]]
    elif len(s1limexpP) > 1:
        lexp68 = 'Expected 68% CL ['+("%.2f" % round(s1limexpN[1],2))+', '+("%.2f" % round(s1limexpP[1],2))+']'
        rout['expected']['68'] = [s1limexpN[1], s1limexpP[1]]
    else:
        lexp68 = 'Expected 68% CL ['+("%.2f" % round(s1limexpN[0],2))+', '+("%.2f" % round(s1limexpP[0],2))+']'
        rout['expected']['68'] = [s1limexpN[0], s1limexpP[0]]

    if len(s2limexpP) > 1 and 0. not in s2limexpP:
        lexp95 = 'Expected 95% CL ['+("%.2f" % round(s2limexpN[1],2))+', '+("%.2f" % round(s2limexpN[0],2))+'], ['+("%.2f" % round(s2limexpP[0],2))+', '+("%.2f" % round(s2limexpP[1],2))+']'
        rout['expected']['95'] = [s2limexpN[1], s2limexpN[0], s2limexpP[0], s2limexpP[1]]
    elif len(s2limexpP) > 1:
        lexp95 = 'Expected 95% CL ['+("%.2f" % round(s2limexpN[1],2))+', '+("%.2f" % round(s2limexpP[1],2))+']'
        rout['expected']['95'] = [s2limexpN[1], s2limexpP[1]]
    else:
        lexp95 = 'Expected 95% CL ['+("%.2f" % round(s2limexpN[0],2))+', '+("%.2f" % round(s2limexpP[0],2))+']'
        rout['expected']['95'] = [s2limexpN[0], s2limexpP[0]]

    if options.obs:
            
        if len(s1limobsP) > 1 and len(s1limobsN) > 1 and 0. not in s1limobsP:
            lobs68 = 'Observed 68% CL ['+("%.2f" % round(s1limobsN[1],2))+', '+("%.2f" % round(s1limobsN[0],2))+'], ['+("%.2f" % round(s1limobsP[0],2))+', '+("%.2f" % round(s1limobsP[1],2))+']'
            rout['observed']['68'] = [s1limobsN[1], s1limobsN[0], s1limobsP[0], s1limobsP[1]]
        elif len(s1limobsP) > 1 and len(s1limobsN) == 1 and 0. not in s1limobsP:
            lobs68 = 'Observed 68% CL ['+("%.2f" % round(s1limobsN[0],2))+', '+("%.2f" % round(s1limobsP[0],2))+'], ['+("%.2f" % round(s1limobsP[1],2))+', '+("%.2f" % round(s1limobsP[2],2))+']'
            rout['observed']['68'] = [s1limobsN[0], s1limobsP[0], s1limobsP[1], s1limobsP[2]]
        elif len(s1limobsP) > 1:
            lobs68 = 'Observed 68% CL ['+("%.2f" % round(s1limobsN[1],2))+', '+("%.2f" % round(s1limobsP[1],2))+']'
            rout['observed']['68'] = [s1limobsN[1], s1limobsP[1]]
        else:
            lobs68 = 'Observed 68% CL ['+("%.2f" % round(s1limobsN[0],2))+', '+("%.2f" % round(s1limobsP[0],2))+']'
            rout['observed']['68'] = [s1limobsN[0], s1limobsP[0]]

        if len(s2limobsP) > 1 and 0. not in s2limobsP:
            lobs95 = 'Observed 95% CL ['+("%.2f" % round(s2limobsN[1],2))+', '+("%.2f" % round(s2limobsN[0],2))+'], ['+("%.2f" % round(s2limobsP[0],2))+', '+("%.2f" % round(s2limobsP[1],2))+']'
            rout['observed']['95'] = [s2limobsN[1], s2limobsN[0], s2limobsP[0], s2limobsP[1]]
        elif len(s2limobsP) > 1:
            lobs95 = 'Observed 95% CL ['+("%.2f" % round(s2limobsN[1],2))+', '+("%.2f" % round(s2limobsP[1],2))+']'
            rout['observed']['95'] = [s2limobsN[1], s2limobsP[1]]
        else:
            lobs95 = 'Observed 95% CL ['+("%.2f" % round(s2limobsN[0],2))+', '+("%.2f" % round(s2limobsP[0],2))+']'
            rout['observed']['95'] = [s2limobsN[0], s2limobsP[0]]

    leg = ROOT.TLegend(0.30,0.60,0.75,0.82)
    leg.SetFillColor(253)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    if options.obs: leg.AddEntry(gr['observed'], 'Profiled log-likelihood (observed)', 'l')
    leg.AddEntry(gr['expected'], 'Profiled log-likelihood (expected)', 'l')
    if options.obs:
        leg.AddEntry(band68[0], lobs68, 'f')
        leg.AddEntry(band95[0], lobs95, 'f')
    else:
        leg.AddEntry(band68[0], lexp68, 'f')
        leg.AddEntry(band95[0], lexp95, 'f')
    leg.Draw()
    
    s1 = ROOT.TLine(options.xmin, s1v, options.xmax, s1v)
    s1.SetLineColor(ROOT.kGray)
    s1.SetLineStyle(2)
    s1.SetLineWidth(2)
    s1.Draw()

    s2 = ROOT.TLine(options.xmin, s2v, options.xmax, s2v)
    s2.SetLineColor(ROOT.kGray)
    s2.SetLineStyle(2)
    s2.SetLineWidth(2)
    s2.Draw()
    
    t1, t2, t3 = style.cmslabel(2, options.year, False)
    t1.Draw()
    t3.Draw()
    
    ROOT.gPad.RedrawAxis()
    
    pname = outdir+'/'+op
    if prof: pname += '_prof'
    if options.obs: pname += '_obs'
    if options.toy >= 0: pname += '_'+str(toy)

    if options.obs: writeNLL(gr['observed'], pname+'.pkl')
    else: writeNLL(gr['expected'], pname+'.pkl')
    
    picname = pname + '.pdf'
    c1.Print(picname)
        
    c1.Clear()

    xmin = gr['expected'].GetX()[0]
    xmax = gr['expected'].GetX()[gr['expected'].GetN()-1]
    fbf, xbf = 1e+10, 0
    for ix in range(10000):
        x = xmin + ix*abs(xmax-xmin)/10000.
        f = gr['expected'].Eval(x)
        if f < fbf:
            fbf = f
            xbf = x
    rout['expected']['bestfit'] = xbf
    rout['expected']['bestfitv'] = fbf
    
    if options.obs:

        xmin = gr['observed'].GetX()[0]
        xmax = gr['observed'].GetX()[gr['observed'].GetN()-1]
        fbf, xbf = 1e+10, 0
        for ix in range(10000):
            x = xmin + ix*abs(xmax-xmin)/10000.
            f = gr['observed'].Eval(x)
            if f < fbf:
                fbf = f
                xbf = x
        rout['observed']['bestfit'] = xbf
        rout['observed']['bestfitv'] = fbf
        
    resname = pname + '.json'
    with open(resname, 'w') as write_file:
        json.dump(rout, write_file, indent=2)
        
def drawLimit2d(gr, outdir):

    c1 = ROOT.TCanvas()
    
    igr = 0 if len(gr) == 1 else 1

    axis = gr[igr][0]
    nll = gr[igr][1]
    
    nll.SetHistogram(axis)
    nll.SetMaximum(options.ymax)
    nll.GetZaxis().SetTitle('-2 #Delta ln L')
    
    hnll = nll.GetHistogram()
    mhnll = hnll.GetMaximum()
    xp, yp, zp = ROOT.Double(0), ROOT.Double(0), ROOT.Double(0)
    for bx in range(1, hnll.GetXaxis().GetNbins()+1):
        for by in range(1, hnll.GetYaxis().GetNbins()+1):
            if hnll.GetBinContent(bx, by) == 0:
                hnll.SetBinContent(bx, by, mhnll)
    
    nll.Draw('COLZ')
    
    gr68Exp = gr[0][2].At(0).Clone()
    for ig in range(gr68Exp.GetSize()):
        gr68Exp[ig].SetLineColor(ROOT.kBlack)
        gr68Exp[ig].SetLineStyle(2)
        gr68Exp[ig].SetLineWidth(2)
        gr68Exp[ig].Draw('C SAME')

    gr95Exp = gr[0][2].At(1).Clone()
    for ig in range(gr95Exp.GetSize()):
        gr95Exp[ig].SetLineColor(ROOT.kBlack)
        gr95Exp[ig].SetLineStyle(1)
        gr95Exp[ig].SetLineWidth(2)
        gr95Exp[ig].Draw('C SAME')

    if options.obs:
        
        gr68Obs = gr[1][2].At(0).Clone()
        for ig in range(gr68Obs.GetSize()):
            gr68Obs[ig].SetLineColor(ROOT.kRed)
            gr68Obs[ig].SetLineStyle(2)
            gr68Obs[ig].SetLineWidth(2)
            gr68Obs[ig].Draw('C SAME')

        gr95Obs = gr[1][2].At(1).Clone()
        for ig in range(gr95Obs.GetSize()):
            gr95Obs[ig].SetLineColor(ROOT.kRed)
            gr95Obs[ig].SetLineStyle(1)
            gr95Obs[ig].SetLineWidth(2)
            gr95Obs[ig].Draw('C SAME')
            
    sm = ROOT.TMarker(0., 0., 22)
    sm.SetMarkerColor(ROOT.kBlack)
    sm.SetMarkerSize(1.2)
    sm.Draw()

    bestfit = ROOT.TMarker(gr[igr][3], gr[igr][4], 29)
    bestfit.SetMarkerColor(ROOT.kRed)
    bestfit.SetMarkerSize(1.3)
    bestfit.Draw()
    
    leg1 = ROOT.TLegend(0.17,0.80,0.46,0.90)
    leg1.SetFillColor(0)
    leg1.SetFillStyle(0)
    leg1.SetBorderSize(0)
    leg1.AddEntry(sm,"Standard Model","p")
    leg1.AddEntry(bestfit,"Best fit","p")
    leg1.Draw()

    if options.obs:
        
        legObs = ROOT.TLegend(0.17,0.20,0.46,0.30)
        legObs.SetFillColor(0)
        legObs.SetFillStyle(0)
        legObs.SetBorderSize(0)
        legObs.AddEntry(gr68Obs[0],"Observed 68% CL","l")
        legObs.AddEntry(gr95Obs[0],"Observed 95% CL","l")
        legObs.Draw()
        
        legExp = ROOT.TLegend(0.56,0.20,0.79,0.30)
        legExp.SetFillColor(0)
        legExp.SetFillStyle(0)
        legExp.SetBorderSize(0)
        legExp.AddEntry(gr68Exp[0],"Expected 68% CL","l")
        legExp.AddEntry(gr95Exp[0],"Expected 95% CL","l")
        legExp.Draw()
        
    else:
        
        legExp = ROOT.TLegend(0.17,0.20,0.40,0.30)
        legExp.SetFillColor(0)
        legExp.SetFillStyle(0)
        legExp.SetBorderSize(0)
        legExp.AddEntry(gr68Exp[0],"Expected 68% CL","l")
        legExp.AddEntry(gr95Exp[0],"Expected 95% CL","l")
        legExp.Draw()
    
    t1, t2, t3 = style.cmslabel(2, options.year, True)
    t1.Draw()
    t3.Draw()
    
    pname = outdir+'/'+options.op.split(',')[0]+'_'+options.op.split(',')[1]        
    if options.obs: pname += '_obs'

    if options.obs: writeNLL2d(nll, pname+'.pkl')
    else: writeNLL2d(nll, pname+'.pkl')
    
    pname += '.pdf'
    c1.Print(pname)
    
    c1.Clear()
    
if __name__ == '__main__':
                                                            
    options = main()
    
    outdir = options.output+'/'+options.type+'/'+options.year+options.label+('_Toy'+str(options.toy) if options.toy >= 0 else '')
    
    if not os.path.isdir(options.output): os.system('mkdir '+options.output)
    if not os.path.isdir(options.output+'/'+options.type): os.system('mkdir '+options.output+'/'+options.type)
    if not os.path.isdir(outdir): os.system('mkdir '+outdir)
    
    ROOT.gROOT.SetBatch()
    
    pstyle = style.SetPlotStyle(2)
    
    # 1d
    
    if options.dim in ['1d']:
    
        for op in options.op.split(','):

            wdir = options.input+'_'+options.type+'_'+options.year+('_Toy'+str(options.toy) if options.toy >= 0 else '')+'/'+op+'_1d/'
            
            res = ['expected']
            if options.obs: res.append('observed')
            
            gr, bestfit = getGraphs1d(wdir, res)
            nt = len(gr)
            for t in range(nt):
                drawLimit1d(gr[t], bestfit[t], outdir, op, toy=t)

    pstyle = style.SetPlotStyle(1)
        
    # 2d
    
    if options.dim in ['2d']:

        if len(options.op.split(',')) < 2: sys.exit()

        op1 = options.op.split(',')[0]
        op2 = options.op.split(',')[1]
    
        wdir = options.input+'_'+options.type+'_'+options.year+'/'+op1+'_'+op2+'_2d/'

        cname = op1+'_'+op2+'_obs' if options.obs else op1+'_'+op2
        gr = []
        res = getContours2d(wdir, 'expected', cname)
        gr.append(res)
        if options.obs:
            res = getContours2d(wdir, 'observed', cname)
            gr.append(res)
            
        drawLimit2d(gr, outdir)
    
        pstyle = style.SetPlotStyle(2)
    
        # 1d profiled (based on 2d fits)

        res = ['expected']
        if options.obs: res.append('observed')

        op = 'ctZ'
        gr, bestfit = getGraphs1dProfiled(wdir, res, meas = 'c1', prof = 'c2')
        drawLimit1d(gr, bestfit, outdir, op, prof = True)
    
        op = 'ctZI'
        gr, bestfit = getGraphs1dProfiled(wdir, res, meas = 'c2', prof = 'c1')
        drawLimit1d(gr, bestfit, outdir, op, prof = True)
