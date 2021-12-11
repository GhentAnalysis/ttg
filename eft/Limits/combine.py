#!/usr/bin/env python

import ROOT
import os, sys, glob, json, csv
import shutil
import multiprocessing

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def ig_f(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Combine datacards"
    
    parser = OptionParser(usage)

    parser.add_option("--op", type=str, default='ctZ,ctZI', help="List of WCs [default: %default]")
    parser.add_option("--year", type=str, default='Run2', help="Year of the data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--inputsl", type=str, default='TOP-18-010-original/singleLeptonEFTCards', help="Single-lepton results [default: %default]")
    parser.add_option("--comb", action='store_true', help="Combine 1L and 2L inputs (by default 1L inputs are used) [default: %default]")
    parser.add_option("--ncores", type=int, default=8, help="Number of parallel jobs [default: %default]")
    parser.add_option("--toys", type=int, default=-1, help="Number of toys [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

def createToy():

    os.system('rm -rf TOP-18-010_Toy*')
    for it in range(options.toys):
        odir = 'TOP-18-010_Toy'+str(it)
        os.system('mkdir '+odir)
        for y in ['2016', '2017', '2018']:
            fname = 'TOP-18-010/singleLeptonEFTCards/'+y+'/cardFiles/expected/ctZ_0_ctZI_0_shape.root'
            f = ROOT.TFile

def applyCorrelations(fname, fnameROOT, dataCor):
    
    proc = ['signal', 'WG', 'ZG', 'fakes', 'other', 'QCD']
    
    dataCorList = []
    for d in dataCor.values():
        dataCorList += d
    dataCorSet = set(map(tuple, dataCorList))
    dataCorList = map(list, dataCorSet)

    # modify data card
    f = open(fname, "rt")
    data = f.read().splitlines()

    for idl, dl in enumerate(data):
        for d in dataCorList:
            if '-' in d or len(d) == 0: continue
            if dl != '' and dl.split()[0] == d[0] or (d[0] in proc and d[0] in dl):
                dl = dl.replace(d[0], d[1])
        data[idl] = dl
    data = '\n'.join(l for l in data)
        
    f.close()
    
    f = open(fname, "wt")
    f.write(data)
    f.close()
    
    # modify ROOT file
    for f in fnameROOT:
        fnameROOT_new = f.replace('TOP-18-010-original', 'TOP-18-010')
        fr = ROOT.TFile(f, 'READ')
        keys = fr.GetListOfKeys()
        objs = []
        for k in keys:
            objs.append(fr.Get(k.GetName()))
        fw = ROOT.TFile(fnameROOT_new, 'RECREATE')
        fw.cd()
        for obj in objs:
            name = obj.GetName()
            for d in dataCorList:
                if '-' in d or len(d) == 0: continue
                if name.endswith('_'+d[0]+'Down') or name.endswith('_'+d[0]+'Up') or d[0] in proc:
                    name = name.replace(d[0], d[1])
            obj.Write(name)
        fw.Write()
        fw.Close()
        fr.Close()

def proc1d(f, o, ys, m, cdir, ifile):
    
    fname = f.split('/')[-1]
    coup = fname.split(o)[-1].replace('0.0.txt', '0.txt').replace('.txt', '')
    coupR = '0.0' if coup == '0' else coup
    fslcard, fslroot = [], []
    for y in ys:
        if o in ['ctZ']: 
            fslcard.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_'+coup+'_ctZI_0_shapeCard.txt')
            fslroot.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_'+coup+'_ctZI_0_shape.root')
        else: 
            fslcard.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_0_ctZI_'+coup+'_shapeCard.txt')
            fslroot.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_0_ctZI_'+coup+'_shape.root')
    fdlcard = 'eft_input_photon_pt_'+options.year+'/'+o+'_1d/'+m+'/srFit_'+o+coupR+'.txt'
    outdir = 'eftComb_input_photon_pt_'+options.year+'/'+o+'_1d/'+m+'/'
    outfile = outdir+fname
    os.system('combineCards.py --prefix='+cdir+' '+' '.join(fslcard)+' > '+outfile.replace('.txt', '_1l.txt'))
    if not options.comb:
        os.system('cat '+outfile.replace('.txt', '_1l.txt')+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" > test_'+ifile+'.txt')
    else:
        os.system('cat '+outfile.replace('.txt', '_1l.txt')+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" | sed "s%-original%%g" > test_'+ifile+'.txt')
    os.system('mv test_'+ifile+'.txt '+outfile.replace('.txt', '_1l.txt'))
    os.system('cp '+fdlcard+' '+outfile.replace('.txt', '_2l.txt'))
    if options.comb:
        applyCorrelations(outfile.replace('.txt', '_1l.txt'), fslroot, dataCor)
        os.system('combineCards.py --prefix='+cdir+' '+outfile.replace('.txt', '_1l.txt')+' '+outfile.replace('.txt', '_2l.txt')+' > '+outfile)
        os.system('cat '+outfile+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" | sed "s%-original%%g" > test_'+ifile+'.txt')
        os.system('mv test_'+ifile+'.txt '+outfile)
        for f in fslroot: os.system('cp '+f.replace('-original', '')+' '+outdir)
    else:
        os.system('combineCards.py '+outfile.replace('.txt', '_1l.txt')+' > '+outfile)
        os.system('cat '+outfile+' | sed "s%'+outdir+'\/%\/%g" > test_'+ifile+'.txt')
        os.system('mv test_'+ifile+'.txt '+outfile)
        for f in fslroot: os.system('cp '+f+' '+outdir)
    for y in ys:
        fdlroot = 'eft_input_photon_pt_'+options.year+'/'+o+'_1d/'+m+'/srFit_'+y+'_shapes_'+o+coupR+'.root'
        os.system('cp '+fdlroot+' '+outdir)
            
def proc2d(f, ops, ops2d, ys, m, cdir, ifile):

    fname = f.split('/')[-1]
    coup1 = fname.split(ops[0])[1].split('_')[0]
    if coup1 == '0.0': coup1 = coup1.replace('0.0', '0')
    coup2 = fname.split(ops[1])[-1].replace('0.0.txt', '0.txt').replace('.txt', '')
    coup1R = '0.0' if coup1 == '0' else coup1
    coup2R = '0.0' if coup2 == '0' else coup2
    fslcard, fslroot = [], []
    for y in ys:
        fslcard.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_'+coup1+'_ctZI_'+coup2+'_shapeCard.txt')
        fslroot.append(options.inputsl+'/'+y+'/cardFiles/'+m+'/ctZ_'+coup1+'_ctZI_'+coup2+'_shape.root')
    fdlcard = 'eft_input_photon_pt_'+options.year+'/'+ops2d+'_2d/'+m+'/srFit_'+ops[0]+coup1R+'_'+ops[1]+coup2R+'.txt'
    outdir = 'eftComb_input_photon_pt_'+options.year+'/'+ops2d+'_2d/'+m+'/'
    outfile = outdir+fname
    os.system('combineCards.py --prefix='+cdir+' '+' '.join(fslcard)+' > '+outfile.replace('.txt', '_1l.txt'))
    if not options.comb:
        os.system('cat '+outfile.replace('.txt', '_1l.txt')+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" > test_'+ifile+'.txt')
    else:
        os.system('cat '+outfile.replace('.txt', '_1l.txt')+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" | sed "s%-original%%g" > test_'+ifile+'.txt')
    os.system('mv test_'+ifile+'.txt '+outfile.replace('.txt', '_1l.txt'))
    os.system('cp '+fdlcard+' '+outfile.replace('.txt', '_2l.txt'))
    if options.comb:
        applyCorrelations(outfile.replace('.txt', '_1l.txt'), fslroot, dataCor)
        os.system('combineCards.py --prefix='+cdir+' '+outfile.replace('.txt', '_1l.txt')+' '+outfile.replace('.txt', '_2l.txt')+' > '+outfile)
        os.system('cat '+outfile+' | sed "s%'+outdir+'\/%\/%g" | sed "s%'+cdir+'\/%\/%g" | sed "s%-original%%g" > test_'+ifile+'.txt')
        os.system('mv test_'+ifile+'.txt '+outfile)
        for f in fslroot: os.system('cp '+f.replace('-original', '')+' '+outdir)
    else:
        os.system('combineCards.py '+outfile.replace('.txt', '_1l.txt')+' > '+outfile)
        os.system('cat '+outfile+' | sed "s%'+outdir+'\/%\/%g" > test_'+ifile+'.txt')
        os.system('mv test_'+ifile+'.txt '+outfile)
        for f in fslroot: os.system('cp '+f+' '+outdir)
    for y in ys:
        fdlroot = 'eft_input_photon_pt_'+options.year+'/'+ops2d+'_2d/'+m+'/srFit_'+y+'_shapes_'+ops[0]+coup1R+'_'+ops[1]+coup2R+'.root'
        os.system('cp '+fdlroot+' '+outdir)
    
if __name__ == '__main__':
    
    options = main()
    
    cdir = os.getcwd()+'/'
    
    combdir = 'eftComb_input_photon_pt_'+options.year
    os.system('rm -rf '+combdir+'; mkdir '+combdir)
    mode = ['expected', 'observed']
    
    ops = options.op.split(',')

    ys = ['2016', '2017', '2018']
    if options.year not in ['Run2']: ys = [options.year]
    
    dataCor = {}
    if options.comb:
        os.system('rm -rf TOP-18-010/')
        shutil.copytree('TOP-18-010-original/', 'TOP-18-010/', ignore=ig_f)
        
        for y in ys:
            with open('conventions/'+y+'.csv') as f:
                reader = csv.reader(f)
                dataCor[y] = list(reader)
                f.close()
    
    ops = options.op.split(',')

    # 1d
    for o in ops:
        os.system('mkdir '+combdir+'/'+o+'_1d')
        for m in mode:
            
            os.system('mkdir '+combdir+'/'+o+'_1d/'+m)
            fcards = glob.glob('eft_input_photon_pt_'+options.year+'/'+o+'_1d/'+m+'/*.txt')

            jobs = []
            pool = multiprocessing.Pool(options.ncores)
            
            for ifile, f in enumerate(fcards):
                
                jobs.append( pool.apply_async(proc1d, (f, o, ys, m, cdir, str(ifile))) )
                    
            pool.close()
            for job in jobs: result = job.get()
                    
    os.system('mkdir '+combdir+'/nominal')
    os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_1d/'+m+'/srFit_ctZ0.0_1l.txt '+combdir+'/nominal/.')
    if not options.comb:
        for y in ys: os.system('cp '+options.inputsl+'/'+y+'/cardFiles/observed/ctZ_0_ctZI_0_shape.root '+combdir+'/nominal/.')
        os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_1d/'+m+'/srFit_ctZ0.0_1l.txt '+combdir+'/nominal/srFit.txt')
        for y in ys: os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_1d/'+m+'/srFit_'+y+'_shapes_ctZ0.0.root '+combdir+'/nominal/srFit_'+options.year+'_shapes.root')
    else:
        for y in ys: os.system('cp '+options.inputsl.replace('-original', '')+'/'+y+'/cardFiles/observed/ctZ_0_ctZI_0_shape.root '+combdir+'/nominal/.')
        os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_1d/'+m+'/srFit_ctZ0.0_2l.txt '+combdir+'/nominal/.')
        for y in ys: os.system('cp eft_input_photon_pt_'+options.year+'/ctZ_1d/'+m+'/srFit_'+y+'_shapes_ctZ0.0.root '+combdir+'/nominal/.')
        os.system('combineCards.py --prefix='+cdir+' '+combdir+'/nominal/srFit_ctZ0.0_2l.txt '+combdir+'/nominal/srFit_ctZ0.0_1l.txt'+' > '+combdir+'/nominal/srFit.txt')
        os.system('cat '+combdir+'/nominal/srFit.txt | sed "s%'+cdir+combdir+'/nominal/\/%\/%g" | sed "s%-original%%g" > test.txt')
        os.system('mv test.txt '+combdir+'/nominal/srFit.txt')

    # 2d
    ops2d = ops[0]+'_'+ops[1]
    os.system('mkdir '+combdir+'/'+ops2d+'_2d')
    for m in mode:
        os.system('mkdir '+combdir+'/'+ops2d+'_2d/'+m)
        fcards = glob.glob('eft_input_photon_pt_'+options.year+'/'+ops2d+'_2d/'+m+'/*.txt')
        
        jobs = []
        pool = multiprocessing.Pool(options.ncores)
        
        for ifile, f in enumerate(fcards):
            
            jobs.append( pool.apply_async(proc2d, (f, ops, ops2d, ys, m, cdir, str(ifile))) )

        pool.close()
        for job in jobs: result = job.get()
            
#    os.system('mkdir '+combdir+'/nominal')
#    os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_ctZI_2d/'+m+'/srFit_ctZ0.0_ctZI0.0_1l.txt '+combdir+'/nominal/.')
#    if not options.comb:
#        for y in ys: os.system('cp '+options.inputsl+'/'+y+'/cardFiles/observed/ctZ_0_ctZI_0_shape.root '+combdir+'/nominal/.')
#        os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_ctZI_2d/'+m+'/srFit_ctZ0.0_ctZI0.0_1l.txt '+combdir+'/nominal/srFit.txt')
#        for y in ys: os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_ctZI_2d/'+m+'/srFit_'+y+'_shapes_ctZ0.0_ctZI0.0.root '+combdir+'/nominal/srFit_'+options.year+'_shapes.root')
#    else:
#        for y in ys: os.system('cp '+options.inputsl.replace('-original', '')+'/'+y+'/cardFiles/observed/ctZ_0_ctZI_0_shape.root '+combdir+'/nominal/.')
#        os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_ctZI_2d/'+m+'/srFit_ctZ0.0_ctZI0.0_2l.txt '+combdir+'/nominal/.')
#        for y in ys: os.system('cp eftComb_input_photon_pt_'+options.year+'/ctZ_ctZI_2d/'+m+'/srFit_'+y+'_shapes_ctZ0.0_ctZI0.0.root '+combdir+'/nominal/.')
#        os.system('combineCards.py --prefix='+cdir+' '+combdir+'/nominal/srFit_ctZ0.0_ctZI0.0_2l.txt '+combdir+'/nominal/srFit_ctZ0.0_ctZI0.0_1l.txt'+' > '+combdir+'/nominal/srFit.txt')
#        os.system('cat '+combdir+'/nominal/srFit.txt | sed "s%'+cdir+combdir+'/nominal/\/%\/%g" | sed "s%-original%%g" > test.txt')
#        os.system('mv test.txt '+combdir+'/nominal/srFit.txt')
        
