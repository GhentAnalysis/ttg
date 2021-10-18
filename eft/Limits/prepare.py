#!/usr/bin/env python

import ROOT
import os, sys, math
import numpy as np
#import htcondor
import pickle
import multiprocessing

sys.path.append("../GenEFTAnalysis/EDAnalyzers/macro/")
from reweight import eft

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def proc1d(fnom, op, coup, input, outdir, m, wev, ic):
    
    fnames = []
    
    if options.year not in ['Run2']:
        fname = fnom+'_'+op+str(coup)+'.root'
        os.system('cp '+input+'/'+fnom+'.root '+outdir+'/'+op+'_1d/'+m+'/'+fname)
        fnames.append(fname)
    else:
        for f in fnom:
            fname = f+'_'+op+str(coup)+'.root'
            os.system('cp '+input+'/'+f+'.root '+outdir+'/'+op+'_1d/'+m+'/'+fname)
            fnames.append(fname)
    os.system('cp '+input+'/srFit.txt '+outdir+'/'+op+'_1d/'+m+'/srFit_'+op+str(coup)+'.txt')
                    
    with open(input+'/srFit.txt', 'r') as fcard:
        with open(outdir+'/'+op+'_1d/'+m+'/srFit_'+op+str(coup)+'.txt', 'wt') as fcardmod:
            for line in fcard:
                if options.year not in ['Run2']:
                    fcardmod.write(line.replace('srFit_'+options.year+'_shapes.root', 'srFit_'+options.year+'_shapes_'+op+str(coup)+'.root'))
                else:
                    for y in ['2016', '2017', '2018']:
                        line = line.replace('srFit_'+y+'_shapes.root', 'srFit_'+y+'_shapes_'+op+str(coup)+'.root')
                    fcardmod.write(line)

    for fname in fnames:
                    
        f = ROOT.TFile(outdir+'/'+op+'_1d/'+m+'/'+fname, 'UPDATE')
                
        keys = f.GetListOfKeys()
        for k in keys:
                              
            h = f.Get(k.GetName()+'/TTGamma')
            h.SetName('TTGamma')
            nb = h.GetXaxis().GetNbins()
            vover = h.GetBinContent(nb+1)
            h.SetBinContent(nb, h.GetBinContent(nb)+vover)
            h.SetBinContent(nb+1, 0.)
            h.SetBinError(nb+1, 0.)

            proc = ['ZG', 'singleTop', 'nonprompt', 'other']

            b = {}
            bv = np.zeros(nb).tolist()
            for p in proc:
                b[p] = f.Get(k.GetName()+'/'+p)
                vover = b[p].GetBinContent(nb+1)
                b[p].SetBinContent(nb, b[p].GetBinContent(nb)+vover)
                b[p].SetBinContent(nb+1, 0.)
                b[p].SetBinError(nb+1, 0.)
                b[p].SetName(p)
                for ib in range(nb):
                    bv[ib] += b[p].GetBinContent(ib+1)
            for ib in range(nb):
                bv[ib] += h.GetBinContent(ib+1)                            

            hobs = f.Get(k.GetName()+'/data_obs')
            if hobs:
                vover = hobs.GetBinContent(nb+1)
                hobs.SetBinContent(nb, hobs.GetBinContent(nb)+vover)
                hobs.SetBinContent(nb+1, 0.)
                hobs.SetBinError(nb+1, 0.)
                hobs.SetName('data_obs')

            if m == 'expected':
                
                if hobs:
                    hobs.Reset()
                    for p in proc:
                        hobs.Add(b[p])
                    hobs.Add(h)

            nbins = 1 if mtype == 'inclusive' else h.GetXaxis().GetNbins()
            for ib in range(nbins):
                        
                w = wev[mtype][ib][ic]
                if wsm[ib] > 0: 
                    sf = w/wsm[ib]
                else:
                    sf = 1.
                    print 'Found negative weight'

                if mtype == 'inclusive':
                    h.Scale(sf)
                else:
                    h.SetBinContent(ib+1, h.GetBinContent(ib+1)*sf)
                    h.SetBinError(ib+1, h.GetBinError(ib+1)*sf)
                            
        f.Write('', ROOT.TObject.kOverwrite)
        f.Close()

def proc2d(fnom, op1, op2, coup, coup2, input, outdir, m, wev, ic, ic2):
    
    fnames = []

    if options.year not in ['Run2']:
        fname = fnom+'_'+op1+str(coup)+'_'+op2+str(coup2)+'.root'
        os.system('cp '+input+'/'+fnom+'.root '+outdir+'/'+op1+'_'+op2+'_2d/'+m+'/'+fname)
        fnames.append(fname)
    else:
        for f in fnom:
            fname = f+'_'+op1+str(coup)+'_'+op2+str(coup2)+'.root'
            os.system('cp '+input+'/'+f+'.root '+outdir+'/'+op1+'_'+op2+'_2d/'+m+'/'+fname)
            fnames.append(fname)
    os.system('cp '+input+'/srFit.txt '+outdir+'/'+op1+'_'+op2+'_2d/'+m+'/srFit_'+op1+str(coup)+'_'+op2+str(coup2)+'.txt')
                    
    with open(input+'/srFit.txt', 'r') as fcard:
        with open(outdir+'/'+op1+'_'+op2+'_2d/'+m+'/srFit_'+op1+str(coup)+'_'+op2+str(coup2)+'.txt', 'wt') as fcardmod:
            for line in fcard:
                if options.year not in ['Run2']:
                    fcardmod.write(line.replace('srFit_'+options.year+'_shapes.root', 'srFit_'+options.year+'_shapes_'+op1+str(coup)+'_'+op2+str(coup2)+'.root'))
                else:
                    for y in ['2016', '2017', '2018']:
                        line = line.replace('srFit_'+y+'_shapes.root', 'srFit_'+y+'_shapes_'+op1+str(coup)+'_'+op2+str(coup2)+'.root')
                    fcardmod.write(line)

    for fname in fnames:
                    
        f = ROOT.TFile(outdir+'/'+op1+'_'+op2+'_2d/'+m+'/'+fname, 'UPDATE')
                
        keys = f.GetListOfKeys()
        for k in keys:

            h = f.Get(k.GetName()+'/TTGamma')
            h.SetName('TTGamma')
            nb = h.GetXaxis().GetNbins()
            vover = h.GetBinContent(nb+1)
            h.SetBinContent(nb, h.GetBinContent(nb)+vover)
            h.SetBinContent(nb+1, 0.)
            h.SetBinError(nb+1, 0.)
            
            proc = ['ZG', 'singleTop', 'nonprompt', 'other']

            b = {}
            bv = np.zeros(nb).tolist()
            for p in proc:
                b[p] = f.Get(k.GetName()+'/'+p)
                vover = b[p].GetBinContent(nb+1)
                b[p].SetBinContent(nb, b[p].GetBinContent(nb)+vover)
                b[p].SetBinContent(nb+1, 0.)
                b[p].SetBinError(nb+1, 0.)
                b[p].SetName(p)
                for ib in range(nb):
                    bv[ib] += b[p].GetBinContent(ib+1)
            for ib in range(nb):
                bv[ib] += h.GetBinContent(ib+1)                            

            hobs = f.Get(k.GetName()+'/data_obs')
            if hobs:
                vover = hobs.GetBinContent(nb+1)
                hobs.SetBinContent(nb, hobs.GetBinContent(nb)+vover)
                hobs.SetBinContent(nb+1, 0.)
                hobs.SetBinError(nb+1, 0.)
                hobs.SetName('data_obs')
                
            if m == 'expected':
                if hobs:
                    hobs.Reset()
                    for p in proc:
                        hobs.Add(b[p])
                    hobs.Add(h)
                    
            nbins = 1 if mtype == 'inclusive' else h.GetXaxis().GetNbins()

            for ib in range(nbins):

                w = wev[mtype][ib][ic+ic2*len(wval)]
                if wsm[ib] > 0: sf = w/wsm[ib]
                else:
                    sf = 1.
                    print 'Found negative weight'

                if mtype == 'inclusive':
                    h.Scale(sf)
                else:
                    h.SetBinContent(ib+1, h.GetBinContent(ib+1)*sf)
                    h.SetBinError(ib+1, h.GetBinError(ib+1)*sf)

        f.Write('', ROOT.TObject.kOverwrite)
        f.Close()
    
def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Run EFT fits"
    
    parser = OptionParser(usage)
    parser.add_option("--op", type=str, default='ctZ,ctZI', help="Coefficient names [default: %default]")
    parser.add_option("--type", type=str, default='inclusive', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    parser.add_option("--input", type=str, default='16YaSRll', help="Input name tag [default: %default]")
    parser.add_option("--output", type=str, default='eft', help="Output name [default: %default]")
    parser.add_option("--year", type=str, default='2016', help="Year of the data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--coup", type=str, default='', help="Consider only selected coupling value [default: %default]")
    parser.add_option("--coup2", type=str, default='', help="Consider only selected coupling value [default: %default]")
    parser.add_option("--ncores", type=int, default=1, help="Number of parallel jobs [default: %default]")
    parser.add_option("--weights", type=str, default='fine', help="fine, fast, comb [default: %default]")
    parser.add_option("--toy", type=int, default=-1, help="Toy index [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()
    
    input = options.input
    if options.toy >= 0: 
        input = input.split('/')[0]+'Toy'+str(options.toy)+'/'+input.split('/')[1]
    
    opname = options.op.split(',')
    nop = len(opname)

    fnom = 'srFit_'+options.year+'_shapes'
    if options.year in ['Run2']: fnom = ['srFit_2016_shapes', 'srFit_2017_shapes', 'srFit_2018_shapes']

    if options.weights == 'fine': wfile = "../GenEFTAnalysis/EDAnalyzers/macro/weightsFine.pkl"
    elif options.weights == 'fast': wfile = "../GenEFTAnalysis/EDAnalyzers/macro/weightsFast.pkl"
    elif options.weights == '1l': wfile = "../GenEFTAnalysis/EDAnalyzers/macro/weights1L.pkl"
    elif options.weights == 'comb': wfile = "../GenEFTAnalysis/EDAnalyzers/macro/weightsComb.pkl"
    else:
        print 'Unknown weights'
        sys.exit()

    with open(wfile, "r") as fp:
        weights = pickle.load(fp)

    eft_input = options.output+'_input_'+options.type+'_'+options.year
    if options.toy >= 0: eft_input += '_Toy'+str(options.toy)
        
    if not os.path.isdir(eft_input):
        os.system('rm -rf '+eft_input)
        os.system('mkdir '+eft_input)

    os.system('rm -rf '+eft_input+'/nominal')
    os.system('mkdir '+eft_input+'/nominal')
    for op in opname:
        os.system('rm -rf '+eft_input+'/'+op+'_1d')
        os.system('mkdir '+eft_input+'/'+op+'_1d')
        os.system('mkdir '+eft_input+'/'+op+'_1d/observed')
        os.system('mkdir '+eft_input+'/'+op+'_1d/expected')
    if nop == 2:
        os.system('rm -rf '+eft_input+'/'+opname[0]+'_'+opname[1]+'_2d')
        os.system('mkdir '+eft_input+'/'+opname[0]+'_'+opname[1]+'_2d')
        os.system('mkdir '+eft_input+'/'+opname[0]+'_'+opname[1]+'_2d/observed')
        os.system('mkdir '+eft_input+'/'+opname[0]+'_'+opname[1]+'_2d/expected')

    mtype = options.type
    
    wsm = weights.sm_weight[mtype]

    os.system('cp '+input+'/srFit.txt '+eft_input+'/nominal/srFit.txt')
    if options.year not in ['Run2']: os.system('cp '+input+'/'+fnom+'.root '+eft_input+'/nominal/.')
    else:
        for f in fnom: os.system('cp '+input+'/'+f+'.root '+eft_input+'/nominal/.')
        
    # 1d
    
    print 'Preparing 1d inputs ..'
    
    for op in opname:
        
        wval = weights.ctZ
        wev = weights.ctZ_1d_weight
        if op == 'ctZI': 
            wval = weights.ctZI
            wev = weights.ctZI_1d_weight
    
        for m in ['observed', 'expected']:
            
            print op+':', m
                
            pool = multiprocessing.Pool(options.ncores)
            
            jobs = []
            
            for ic in range(len(wval)):
                
                coup = round(wval[ic], 3)
                
                if options.coup != '' and coup != float(options.coup): continue
                
                jobs.append( pool.apply_async(proc1d, (fnom, op, coup, input, eft_input, m, wev, ic)) )

            pool.close()
            for job in jobs: result = job.get()
            
    if options.toy >= 0:
        sys.exit()

    # 2d

    print 'Preparing 2d inputs ..'
    
    wval = weights.ctZ
    wval2 = weights.ctZI
    wev = weights.ctZ_ctZI_2d_weight
    
    for m in ['observed', 'expected']:
        
        print '2d:', m

        pool = multiprocessing.Pool(options.ncores)
        
        jobs = []

        for ic in range(len(wval)):
###            if ic not in [40,41,42,43,44,45,46,47,48,49]: continue
            for ic2 in range(len(wval2)):
                
                coup = round(wval[ic], 10)
                coup2 = round(wval2[ic2], 10)
                
###                if coup != 1.0 or coup2 != 0.0: continue

                if options.coup != '' and coup != float(options.coup): continue
                if options.coup2 != '' and coup2 != float(options.coup2): continue
                
                jobs.append( pool.apply_async(proc2d, (fnom, opname[0], opname[1], coup, coup2, input, eft_input, m, wev, ic, ic2)) )

        pool.close()
        for job in jobs: result = job.get()
