#!/usr/bin/env python

import ROOT
import os, sys, math
import numpy as np
import pickle

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def runToy(output, yname, toy):

    np.random.seed(toy)
    
    fname = ['srFit_'+yname+'_shapes'] if yname not in ['RunII'] else ['srFit_2016_shapes', 'srFit_2017_shapes', 'srFit_2018_shapes']
    for fn in fname:
        f = ROOT.TFile(output+'/'+yname+'/'+fn+'.root', 'UPDATE')
        keys = f.GetListOfKeys()
        keysn = [k.GetName() for k in keys]
        knom = ['sr_ee', 'sr_mumu', 'sr_emu']
        for k in knom:
            keysn.remove(k)
            keysn.insert(-1, k)
        ksys = {}
        for kn in keysn:
            if not (kn == 'sr_ee' or kn == 'sr_mumu' or kn == 'sr_emu'): # systematics
                hsm = None
                for p in ['TTGamma', 'ZG', 'singleTop', 'nonprompt', 'other']:
                    h = f.Get(kn+'/'+p)
                    h.SetDirectory(0)
                    if not hsm:
                        hsm = h.Clone('h_sys_'+kn)
                        hsm.SetDirectory(0)
                    else: hsm.Add(h)
                isee = bool('sr_ee' in kn)
                ismm = bool('sr_mumu' in kn)
                isem = bool('sr_emu' in kn)
                ksysc = None
                if isee:
                    if 'ee' not in ksys: ksys['ee'] = {}
                    ksysc = ksys['ee']
                elif ismm:
                    if 'mumu' not in ksys: ksys['mumu'] = {}
                    ksysc = ksys['mumu']
                elif isem:
                    if 'emu' not in ksys: ksys['emu'] = {}
                    ksysc = ksys['emu']
                if 'Up' in kn:
                    if 'up' not in ksysc: ksysc['up'] = [hsm]
                    else: ksysc['up'].append(hsm)
                elif 'Down' in kn:
                    if 'down' not in ksysc: ksysc['down'] = [hsm]
                    else: ksysc['down'].append(hsm)
            else: # nominal
                hsm = None
                for p in ['TTGamma', 'ZG', 'singleTop', 'nonprompt', 'other']:
                    h = f.Get(kn+'/'+p)
                    h.SetDirectory(0)
                    if not hsm: 
                        hsm = h.Clone('h_sm')
                        hsm.SetDirectory(0)
                    else: hsm.Add(h)
                h_data = f.Get(kn+'/data_obs')
                h_data.SetName('data_obs')
                nb = h_data.GetXaxis().GetNbins()
                for ib in range(nb):
                    dup, ddown = 0., 0.
                    for ks in ksys[kn.split('_')[1]]['up']:
                        dup += math.pow(hsm.GetBinContent(ib+1)-ks.GetBinContent(ib+1), 2)
                    dup = math.sqrt(dup)
                    for ks in ksys[kn.split('_')[1]]['down']:
                        ddown += math.pow(hsm.GetBinContent(ib+1)-ks.GetBinContent(ib+1), 2)
                    ddown = math.sqrt(ddown)
                    d = int(hsm.GetBinContent(ib+1))
                    if d > 0: 
                        dp = np.random.poisson(d, 1)
                        sys = abs(dup+ddown)/2./float(d)*float(dp[0])
                        dg = np.random.normal(dp, sys, 1)
#                        print 'nom=',d,'pois=',dp[0],'gaus=',dg[0],'stat=',math.sqrt(d),'sys=',sys
                    else:
                        dg = 0
                    if dg < 0: dg = 0.
                    dg = int(dg)
                    h_data.SetBinContent(ib+1, dg)
                    h_data.SetBinError(ib+1, math.sqrt(dg))                
                    
        f.Write('', ROOT.TObject.kOverwrite)
        f.Close()    
    
def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Prepare SM toys"
    
    parser = OptionParser(usage)
    parser.add_option("--input", type=str, default='../../EFTinputJune16', help="Input directory [default: %default]")
    parser.add_option("--toys", type=int, default=20, help="Number of toys [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()
    
    input = options.input
    
    os.system('rm -rf '+input+'Toy*')
    
    for t in range(options.toys):
    
        print 'toy >>', t
        output = input+'Toy'+str(t)
    
        os.system('cp -r '+input+' '+output)
    
        for iy, y in enumerate(['2016', '2017', '2018', 'RunII']):
            print(y)
            runToy(output, y, 4*t+iy)
