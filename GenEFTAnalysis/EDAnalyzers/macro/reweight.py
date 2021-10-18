#!/usr/bin/env python

import ROOT
import sys
import pickle
import numpy as np
import array
import utils

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

class eft:

    def __init__(self):

        if not options.comb:
            if options.fast: reg = np.arange(-2.5, 3.0, 0.5).tolist()
            else:            
                reg1 = np.arange(-1.0, 1.05, 0.05).tolist()
                reg2 = np.arange(-2.0, -1.0, 0.1).tolist()
                reg3 = np.arange(-2.5, -2.0, 0.25).tolist()
                reg4 = np.arange(1.1, 2.1, 0.1).tolist()
                reg5 = np.arange(2.25, 2.75, 0.25).tolist()
                reg = reg3+reg2+reg1+reg4+reg5
        else:
#1L            reg = [-0.6, -0.55, -0.483, -0.45, -0.417, -0.383, -0.35, -0.317, -0.283, -0.25, -0.217, -0.183, -0.15, -0.117, -0.083, -0.05, -0.017, 0, 0.017, 0.05, 0.083, 0.117, 0.15, 0.183, 0.217, 0.25, 0.283, 0.317, 0.35, 0.383, 0.417, 0.45, 0.483, 0.55, 0.6]
            reg = [-1, -0.95 -0.9, -0.85, -0.8, -0.75, -0.7, -0.65, -0.6, -0.55, -0.483, -0.45, -0.417, -0.383, -0.35, -0.317, -0.283, -0.25, -0.217, -0.183, -0.15, -0.117, -0.083, -0.05, -0.017, 0, 0.017, 0.05, 0.083, 0.117, 0.15, 0.183, 0.217, 0.25, 0.283, 0.317, 0.35, 0.383, 0.417, 0.45, 0.483, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]
            
#        for ir, r in enumerate(reg): reg[ir] = np.round(r, 2)
        for ir, r in enumerate(reg): reg[ir] = np.round(r, 3)
        print('Total number of scan points:', len(reg))
        
        self.ctZ = reg
        self.ctZI = reg
        self.ctW = reg
        self.ctWI = reg

        self.param = {}

        # Define photon pt bins
        ptbins = []
        fpt = ROOT.TFile.Open(options.input, 'OPEN')
        hpt = fpt.Get('sr_ee/TTGamma')
        for i in range(hpt.GetXaxis().GetNbins()):
            ptbins.append(hpt.GetXaxis().GetBinLowEdge(i+1))
        ptbins.append(hpt.GetXaxis().GetBinUpEdge(hpt.GetXaxis().GetNbins()))
        
        self.param['photon_pt'] = {'var': 'pt', 'bins': ptbins}
        
        self.param['inclusive'] = {'var': 'pt', 'bins': [ptbins[0], ptbins[-1]]}

        self.nev = {}
        
        self.sm_weight = {}

        self.ctZ_1d_weight = {}
        self.ctZI_1d_weight = {}
        self.ctW_1d_weight = {}
        self.ctWI_1d_weight = {}
        
        self.ctZ_ctZI_2d_weight = {}
        
        for k, v in self.param.iteritems():

            self.nev[k] = []
            
            self.sm_weight[k] = []
            
            self.ctZ_1d_weight[k] = []
            self.ctZI_1d_weight[k] = []
            self.ctW_1d_weight[k] = []
            self.ctWI_1d_weight[k] = []
            
            self.ctZ_ctZI_2d_weight[k] = []
            
            nbins = len(v['bins'])-1

            for i in range(nbins):
                
                self.nev[k].append(0)
                
                self.sm_weight[k].append(0.)
                
                self.ctZ_1d_weight[k].append(np.zeros(len(self.ctZ)).tolist())
                self.ctZI_1d_weight[k].append(np.zeros(len(self.ctZI)).tolist())
                self.ctW_1d_weight[k].append(np.zeros(len(self.ctW)).tolist())
                self.ctWI_1d_weight[k].append(np.zeros(len(self.ctWI)).tolist())
                
                self.ctZ_ctZI_2d_weight[k].append(np.zeros(len(self.ctZ)*len(self.ctZI)).tolist())

    def eval(self, func, par, ib):

        evpass = False
        
        # Reference point
        ref = func.Eval(4., 4., 4., 4.)
#        ref = 1
        
        sm_weight = func.Eval(0., 0., 0., 0.)/ref

        ctZ_1d_weight = []
        ctZI_1d_weight = []
        ctW_1d_weight = []
        ctWI_1d_weight = []

        for ic, c in enumerate(self.ctZ): ctZ_1d_weight.append(func.Eval(c, 0., 0., 0.)/ref) 
        for ic, c in enumerate(self.ctZI): ctZI_1d_weight.append(func.Eval(0., c, 0., 0.)/ref)
        for ic, c in enumerate(self.ctW): ctW_1d_weight.append(func.Eval(0., 0., c, 0.)/ref)
        for ic, c in enumerate(self.ctWI): ctWI_1d_weight.append(func.Eval(0., 0., 0., c)/ref)
        
        if all(v < options.cut for v in ctZ_1d_weight) and \
        all(v < options.cut for v in ctZI_1d_weight) and \
        all(v < options.cut for v in ctW_1d_weight) and \
        all(v < options.cut for v in ctWI_1d_weight):
        
            evpass = True
        
            self.nev[par][ib] += 1
            
            self.sm_weight[par][ib] += sm_weight
            
            for ic, c in enumerate(self.ctZ): self.ctZ_1d_weight[par][ib][ic] += ctZ_1d_weight[ic]
            for ic, c in enumerate(self.ctZI): self.ctZI_1d_weight[par][ib][ic] += ctZI_1d_weight[ic]
            for ic, c in enumerate(self.ctW): self.ctW_1d_weight[par][ib][ic] += ctW_1d_weight[ic]
            for ic, c in enumerate(self.ctWI): self.ctWI_1d_weight[par][ib][ic] += ctWI_1d_weight[ic]
            
            for ic, c in enumerate(self.ctZ):
                for ic2, c2 in enumerate(self.ctZI):
                    self.ctZ_ctZI_2d_weight[par][ib][ic+ic2*len(self.ctZ)] += func.Eval(c, c2, 0., 0.)/ref
                    
        return evpass, sm_weight, ctZ_1d_weight, ctZI_1d_weight

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n Produce EFT weights (inclusive or differential)"

    parser = OptionParser(usage)
    parser.add_option("--nmax", type=int, default=-1, help="Maximum number of events [default: %default]")
    parser.add_option("--cut", type=float, default=100000., help="Maximum EFT weight [default: %default]")
    parser.add_option("--verbose", action='store_true', help="Print out weights [default: %default]")
    parser.add_option("--overflow", action='store_true', help="Include over/underflow events in the last/first bin [default: %default]")
    parser.add_option("--fast", action='store_true', help="Use coarse parametrization [default: %default]")
    parser.add_option("--level", type=str, default="lhe", help="Reweighting level (lhe or ps) [default: %default]")
    parser.add_option("--input", type=str, default="../../../Limits/EFTinputApr25/2016/srFit_2016_shapes.root", help="Input ROOT file with histograms for combine [default: %default]")
    parser.add_option("--comb", action='store_true', help="Use WC values that are consistent with the single-lepton scans [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':
    
    options = main()
    
    f = ROOT.TFile.Open('jobs/ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt_crab_ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt__1/merged.root')
    tr = f.Get('val')
    
    lhe = True if options.level == 'lhe' else False
    
    weights = eft()
    
    fdata = ROOT.TFile('weights.root', 'RECREATE')

    nw = len(weights.ctZ)
    
    weight_eft = array.array( 'f', [ 0 for i in range(nw) ] )
    weight_sm = array.array( 'f', [ 0 for i in range(nw) ] )
    weight_sf = array.array( 'f', [ 0 for i in range(nw) ] )
    
    wdata = []
    for i in range(len(weights.param['photon_pt']['bins'])-1):
        wdata.append(ROOT.TTree('weights_pt'+str(i), 'weights_pt'+str(i)))
        wdata[-1].Branch('weight_eft', weight_eft, 'weight_eft['+str(nw)+']/F')
        wdata[-1].Branch('weight_sm', weight_sm, 'weight_sm['+str(nw)+']/F')
        wdata[-1].Branch('weight_sf', weight_sf, 'weight_sf['+str(nw)+']/F')
            
    print('Process data ('+str(tr.GetEntries())+')')
    
    fstr = \
    "[0]+"+\
    "[1]*(x[0]-4.000000)+"+\
    "[2]*(x[1]-4.000000)+"+\
    "[3]*(x[2]-4.000000)+"+\
    "[4]*(x[3]-4.000000)+"+\
    "[5]*pow((x[0]-4.000000),2)+"+\
    "[6]*(x[0]-4.000000)*(x[1]-4.000000)+"+\
    "[7]*(x[0]-4.000000)*(x[2]-4.000000)+"+\
    "[8]*(x[0]-4.000000)*(x[3]-4.000000)+"+\
    "[9]*pow((x[1]-4.000000),2)+"+\
    "[10]*(x[1]-4.000000)*(x[2]-4.000000)+"+\
    "[11]*(x[1]-4.000000)*(x[3]-4.000000)+"+\
    "[12]*pow((x[2]-4.000000),2)+"+\
    "[13]*(x[2]-4.000000)*(x[3]-4.000000)+"+\
    "[14]*pow((x[3]-4.000000),2)"
    
    func = ROOT.TFormula("ParamFunc", fstr)

    for iev, ev in enumerate(tr):

        if iev > options.nmax and options.nmax >= 0: break
    
        coeff = ev.coeff
        
        for ip in range(func.GetNpar()):
            func.SetParameter(ip, coeff[ip])

        for k, v in weights.param.iteritems():

            ib = -1

            rpref = ''
            if lhe: rpref = 'lhe'
            vbr = eval('ev.'+rpref+v['var'])
            foundPhoton = False
            for iv in range(len(vbr)):
                if lhe: pid = ev.lhepid[iv]
                else: pid = ev.pid[iv]
                if pid == 22: 
                    var = eval('ev.'+rpref+v['var'])[iv]
                    foundPhoton = True
                    break
            if not foundPhoton:
                print('photon not found')
                sys.exit()
            vmin, vmax = -1, -1
            nbins = len(v['bins'])
            for b in range(nbins-1):
                if var > v['bins'][b] and var <= v['bins'][b+1]: 
                    vmin = v['bins'][b]
                    vmax = v['bins'][b+1]
                    
            if vmin < 0 or vmax < 0:
#                    continue
#                    if vmin < 0: ib = 0
                if vmin < 0: continue
                elif options.overflow: ib = nbins-2
                else: continue
            else:                    
                ib = v['bins'].index(vmin)
                    
            if ib < 0:
                print('Can not find a suitable bin')
                sys.exit()
            
            evpass, sm_weight, ctZ_1d_weight, ctZI_1d_weight = weights.eval(func, k, ib)
            
            if k in ['photon_pt'] and evpass:
                for iw in range(len(ctZ_1d_weight)):
                    weight_sm[iw] = sm_weight
                    weight_eft[iw] = ctZ_1d_weight[iw]
                    weight_sf[iw] = weight_eft[iw]/weight_sm[iw] if weight_sm[iw] > 0 else 0.
                wdata[ib].Fill()
                
    fdata.Write()
    fdata.Close()

    with open("weights.pkl", "wb") as fp:
        pickle.dump(weights, fp)
        
    if options.verbose:
        
        # Print out weights
        with open("weights.pkl", "r") as fp:
            weights = pickle.load(fp)
            
            for pk, pv in weights.param.iteritems():
                
                for ic, c in enumerate(weights.ctZ):
                    
                    print(pk, 'ctZ =', c)
                    nbins = len(pv['bins'])-1
                    
                    for ib in range(nbins):                                                
                        
                        weft = weights.ctZ_1d_weight[pk][ib][ic]
                        wsm = weights.sm_weight[pk][ib]
                        nev = weights.nev[pk][ib]
                        wsf = weft/wsm if wsm > 0. else 1.

                        print(ib, 'eft=', weft, 'sm=', wsm, 'sf=', wsf, '['+str(pv['bins'][ib])+', '+str(pv['bins'][ib+1])+']', 'stat=', nev)
                        
