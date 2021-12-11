#!/usr/bin/env python

import ROOT
import os, sys, glob, json

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Collect results from EFT fits"
    
    parser = OptionParser(usage)
    
    parser.add_option("--input", type=str, default='eft', help="Input directory name [default: %default]")
    parser.add_option("--op", type=str, default='ctZ,ctZI', help="List of WCs [default: %default]")
    parser.add_option("--dim", type=str, default='1d', help="Dimension of the fits [default: %default]")
    parser.add_option("--mode", type=str, default='expected', help="expected, observed, all [default: %default]")
    parser.add_option("--year", type=str, default='2016', help="Year of the data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--type", type=str, default='inclusive', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    parser.add_option("--sm", type=str, default='0.0', help="SM value of WC (precision is important) [default: %default]")
    parser.add_option("--toy", type=int, default=-1, help="Collect results from toys [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':
                                                            
    options = main()
    
    wdir = options.input+'_fit_'+options.type+'_'+options.year+('_Toy'+str(options.toy) if options.toy >= 0 else '')
    
    mode = ['expected']
    if options.mode in ['observed']: mode = ['observed']
    if options.mode in ['all']: mode = ['expected', 'observed']
    
    if options.mode in ['observed', 'all']:
        
        nom = wdir+'/nominal/fitResult.root'
        fnom = ROOT.TFile.Open(nom)
        tr = fnom.Get('limit')
        tr.GetEntry(0)
        rsf = tr.r
        
    if options.dim in ['1d']:

        for wc in options.op.split(','):
        
            fname = wdir+'/'+wc+'_'+options.dim+'/'
                
            for r in mode:
                
                nllSM = 0
            
                rout, routToys = {}, {}
                
                rdir = fname+r
                if not os.path.isdir(rdir): continue
                
                vwc = [i.split('/')[-2] for i in glob.glob(rdir+'/*/')]
                vwc_sm = [f for f in vwc if f.endswith(options.sm)][0]
                vwc.remove(vwc_sm)
                print 'Use SM point ('+r+'):', vwc_sm

                obsNLL, obsNLLToys = [], []
                for v in [vwc_sm]+vwc:

                    c = float(v.replace('srFit_'+wc, ''))

                    f = ROOT.TFile.Open(rdir+'/'+v+'/fitResult.root')
                    tr = f.Get('limit')
                    tr.GetEntry(0)
                    if options.toy < 0:
                        if v in [vwc_sm] and r in ['expected']: nllSM = tr.nll+tr.nll0
                    if tr.GetEntries() > 0:
                        deltaNLL = 2*(tr.nll+tr.nll0-nllSM)
                        rout[c] = deltaNLL
                        obsNLL.append(tr.nll+tr.nll0)
                        
#                    if options.toys > 0:
#                        obsNLLToys.append([])
#                        routToys[c] = []
#                        f0 = ROOT.TFile.Open(rdir+'/'+v+'/fitResult.root')
#                        f = ROOT.TFile.Open(rdir+'/'+v+'/fitResultToys.root')
#                        tr = f.Get('limit')
#                        tr0 = f0.Get('limit')
#                        for t in range(options.toys):
#                            tr.GetEntry(t)
#                            tr0.GetEntry(t)
##                            if v in [vwc_sm] and r in ['expected']: nllSM = (tr.nll-tr.nll0)+tr0.nll+tr0.nll0
##                            if tr.GetEntries() > 0:
##                                deltaNLL = 2*((tr.nll-tr.nll0)+tr0.nll+tr0.nll0-nllSM)
##                                routToys[c].append(deltaNLL)
##                                obsNLLToys[-1].append((tr.nll-tr.nll0)+tr0.nll+tr0.nll0)
#                            if v in [vwc_sm] and r in ['expected']: nllSM = (tr.nll)+tr0.nll+tr0.nll0
#                            if tr.GetEntries() > 0:
#                                deltaNLL = 2*((tr.nll)+tr0.nll+tr0.nll0-nllSM)
#                                routToys[c].append(deltaNLL)
#                                obsNLLToys[-1].append((tr.nll)+tr0.nll+tr0.nll0)
#                        f.Close()
#                        f0.Close()
                
                if r in ['observed'] or options.toy >= 0:
                    bestFit = min(obsNLL)
                    for k, v in rout.iteritems():
                        rout[k] -= 2*(bestFit)
                        
                foutput = rdir+'/result.json'
                with open(foutput, 'w') as write_file:
                    json.dump(rout, write_file, indent=2)
                      
#                if r in ['observed']:
#                    if options.toys > 0:
#                        for t in range(options.toys):
#                            bestFit = min([item[t] for item in obsNLLToys])
#                            for k, v in routToys.iteritems():
#                                routToys[k][t] -= 2*(bestFit)
                
#                if options.toys > 0:
#                    foutput = rdir+'/resultToys.json'
#                    with open(foutput, 'w') as write_file:
#                        json.dump(routToys, write_file, indent=2)
                    
    elif options.dim in ['2d']:

        op1 = options.op.split(',')[0]
        op2 = options.op.split(',')[1]
        wc = op1+'_'+op2
        
        fname = wdir+'/'+wc+'_'+options.dim+'/'
        print fname
        
        for r in mode:

            nllSM = 0
            
            rout = {}
                
            rdir = fname+r
            if not os.path.isdir(rdir): continue
            
            vwc = [i.split('/')[-2] for i in glob.glob(rdir+'/*/')]
            vwc_sm = [f for f in vwc if op1+options.sm+'_'+op2+options.sm in f][0]
            vwc.remove(vwc_sm)
            print 'Use SM point ('+r+'):', vwc_sm

            obsNLL = []
            for v in [vwc_sm]+vwc:
                
                c1 = float(v.replace('srFit_', '').split('_')[0].replace(options.op.split(',')[0], ''))
                c2 = float(v.replace('srFit_', '').split('_')[1].replace(options.op.split(',')[1], ''))

                f = ROOT.TFile.Open(rdir+'/'+v+'/fitResult.root')
                tr = f.Get('limit')
                if tr:
                    tr.GetEntry(0)
                    if v in [vwc_sm] and r in ['expected']: nllSM = tr.nll+tr.nll0
                    if tr.GetEntries() > 0:
                        deltaNLL = 2*(tr.nll+tr.nll0-nllSM)
                        rout[str(c1)+'_'+str(c2)] = deltaNLL
                        obsNLL.append(tr.nll+tr.nll0)

            if r in ['observed']:
                bestFit = min(obsNLL)
                for k, v in rout.iteritems():
                    rout[k] -= 2*(bestFit)
                    
            foutput = rdir+'/result.json'
            with open(foutput, 'w') as write_file:
                json.dump(rout, write_file, indent=2)                    
