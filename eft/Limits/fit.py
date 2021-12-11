#!/usr/bin/env python

import ROOT
import os, sys, glob, json, time
import multiprocessing, htcondor

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Run EFT fits"
    
    parser = OptionParser(usage)
    
    parser.add_option("--ws", action='store_true', help="Produce workspaces [default: %default]")
    parser.add_option("--fit", action='store_true', help="Do fits [default: %default]")
    parser.add_option("--obs", action='store_true', help="Get observed limit [default: %default]")
    parser.add_option("--output", type=str, default='eft', help="Output directory name [default: %default]")
    parser.add_option("--dim", type=str, default='1d', help="Dimension of the fits [default: %default]")
    parser.add_option("--op", type=str, default='ctZ,ctZI', help="Coefficient names [default: %default]")
    parser.add_option("--multicore", action='store_true', help="Run parallel jobs on local cpus [default: %default]")
    parser.add_option("--cluster", action='store_true', help="Run parallel jobs on cluster [default: %default]")
    parser.add_option("--toy", type=int, default=-1, help="Number of toys [default: %default]")
    parser.add_option("--ncores", type=int, default=8, help="Number of parallel jobs in cluster mode [default: %default]")
    parser.add_option("--year", type=str, default='2016', help="Year of the data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--type", type=str, default='inclusive', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    parser.add_option("--npoi", type=int, default=1, help="Number of scanned points per job [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])
    
    return options

def waitcluster(schedd, jobs):
    
    print 'Wait for jobs to finish ..'

    while True:
        for j in jobs:
            res = schedd.query(
            constraint='ClusterId=={}'.format(j),
            projection=["JobStatus"],
            )
            if len(res) == 0:
                jobs.remove(j)
        if len(jobs) == 0: break
        time.sleep(1)
        
    print 'Done'
                
def ws(f, wdir, cdir, idir, is1d):

    os.chdir(cdir)
    dname = f.replace('.txt', '').replace(idir, '')
    
    os.system('mkdir '+wdir+dname)
    os.chdir(wdir+dname)
    os.system('cp '+cdir+idir+dname+'.txt .')
    if bool(is1d): os.system('cp '+cdir+idir+'srFit_*_shapes_'+dname.split('_')[1]+'.root .')
    else: os.system('cp '+cdir+idir+'srFit_*_shapes_'+dname.split('_')[1]+'_'+dname.split('_')[2]+'.root .')
    os.system('text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:defaultModel -o srFit_model.root '+dname+'.txt')
    
def jobws(proxy, dname, wdir, cdir, idir, is1d, fsh):
    
    j = "#!/bin/bash\n\n"
    
    j += "export X509_USER_PROXY="+proxy+"\n"
    
    j += "echo \"Start: $(/bin/date)\"\n"
    j += "echo \"User: $(/usr/bin/id)\"\n"
    j += "echo \"Node: $(/bin/hostname)\"\n"
    j += "echo \"CPUs: $(/bin/nproc)\"\n"
    j += "echo \"Directory: $(/bin/pwd)\"\n"
    
    j += "source /cvmfs/cms.cern.ch/cmsset_default.sh\n"
    
    j += "cd "+cdir+"\n"
    
    j += "export SCRAM_ARCH=slc6_amd64_gcc700\n"
    j += "eval `scramv1 runtime -sh`\n"
    
    for d in dname:
        
        j += "cd "+wdir+d+"\n"
        j += "cp "+cdir+idir+d+".txt .\n"

        if bool(is1d):
            j += "cp "+cdir+idir+"srFit_*_shapes_"+d.split('_')[1]+".root .\n"
        else:
            j += "cp "+cdir+idir+"srFit_*_shapes_"+d.split('_')[1]+'_'+d.split('_')[2]+".root .\n"

        j += "text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:defaultModel -o srFit_model.root "+d+".txt\n"
        j += "cd -\n"
    
    with open(fsh, 'w') as f:
        f.write(j)
        
    os.system('chmod u+x '+fsh)
    
def mlfit(f, wdir, cdir, idir, opname, nllnom, is1d = True):

    c = []
    if not is1d:
        ops = options.op.split(',')
        c.append(float(f.replace('.txt', '').replace(idir+'srFit_', '').split('_')[0].replace(ops[0], '')))
        c.append(float(f.replace('.txt', '').replace(idir+'srFit_', '').split('_')[1].replace(ops[1], '')))
    else: c.append(float(f.replace('.txt', '').replace(idir+'srFit_', '').replace(opname, '')))
    
    os.chdir(cdir)        
    dname = f.replace('.txt', '').replace(idir, '')
    os.chdir(wdir+dname)

    res = 'failed'
    tol = 0.001
    ntry = 0
    while 'failed' in res:
        print 'tolerance =', tol, f
        res = os.popen('combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --cminDefaultMinimizerStrategy=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminDefaultMinimizerTolerance='+str(tol)).read()
        tol += 0.01
        ntry += 1
        if ntry > 20:
            print 'not converged, exiting ..'
            break

    os.system('mv higgsCombineTest.MultiDimFit.mH120.root fitResult.root')
                
    f = ROOT.TFile.Open('fitResult.root')
    tr = f.Get('limit')
    tr.GetEntry(0)
    deltaNLL = -2*(tr.nll-nllnom)
    
    return c, deltaNLL

def jobmlfit(proxy, dname, wdir, cdir, idir, opname, nllnom, fsh, is1d = True):
    
    j = "#!/bin/bash\n\n"
    
    j += "export X509_USER_PROXY="+proxy+"\n"
    
    j += "echo \"Start: $(/bin/date)\"\n"
    j += "echo \"User: $(/usr/bin/id)\"\n"
    j += "echo \"Node: $(/bin/hostname)\"\n"
    j += "echo \"CPUs: $(/bin/nproc)\"\n"
    j += "echo \"Directory: $(/bin/pwd)\"\n"
    
    j += "source /cvmfs/cms.cern.ch/cmsset_default.sh\n"
    
    j += "cd "+cdir+"\n"
    
    j += "export SCRAM_ARCH=slc6_amd64_gcc700\n"
    j += "eval `scramv1 runtime -sh`\n"

    for d in dname:
        
        j += "cd "+wdir+d+"\n"

        j += "tol=0.001\n"
        j += "ntry=0\n"
        j += "while [ true ]\n"
        j += "do\n"
        j += "  echo \"tolerance = ${tol}\"\n"
        j += "  res=$(combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --cminDefaultMinimizerStrategy=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminDefaultMinimizerTolerance=${tol})\n"
#        if options.toys > 0:
#            j += "  rest=$(combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --cminDefaultMinimizerStrategy=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminDefaultMinimizerTolerance=${tol} --toysFrequentist --bypassFrequentistFit -t "+str(options.toys)+")\n"
#            j += "  rest=$(combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --cminDefaultMinimizerStrategy=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --cminDefaultMinimizerTolerance=${tol} --saveWorkspace)\n"
#            j += "  rest=$(combine higgsCombineTest.MultiDimFit.mH120.root --snapshotName MultiDimFit -M MultiDimFit --toysFrequentist --bypassFrequentistFit -P r --algo singles --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 -t 10)"
#            j += "  rest=$(combine higgsCombineTest.MultiDimFit.mH120.root --snapshotName MultiDimFit -M MultiDimFit --toysFrequentist --bypassFrequentistFit -P r --algo singles --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 -t 10 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1)"            
        j += "  isFailed=$(echo ${res} | grep failed)\n"
        j += "  if [[ ${isFailed} == \"\" ]]; then\n"
        j += "    echo \"done\"\n"
        j += "    break;\n"
        j += "  else\n"
        j += "    echo \"try with tol=${tol}\"\n"
        j += "    tol=$(echo \"${tol}+0.01\" | bc -l)\n"
        j += "    ntry=$[$ntry+1]\n"
        j += "    if [[ ${ntry} -ge 20 ]]; then\n"
        j += "      echo \"not converged, exiting ..\"\n"
        j += "      break\n"
        j += "    fi\n"
        j += "  fi\n"
        j += "done\n"
        
        j += "mv higgsCombineTest.MultiDimFit.mH120.root fitResult.root\n"
#        if options.toys > 0:
#            j += "mv higgsCombineTest.MultiDimFit.mH120.123456.root fitResultToys.root\n"
        
        j += "cd -\n"
    
    with open(fsh, 'w') as f:
        f.write(j)
        
    os.system('chmod u+x '+fsh)

if __name__ == '__main__':
                                                            
    options = main()
    
    proxy = '/user/kskovpen/proxy/x509up_u20657'

    outdir = options.output+'_fit_'+options.type+'_'+options.year+('_Toy'+str(options.toy) if options.toy >= 0 else '')
    if options.ws and not os.path.isdir(outdir): os.system('mkdir '+outdir)
    
    ndir = outdir+'/nominal/'
#    indir = ndir.replace('fit', 'input').replace('_toys', '')
    indir = ndir.replace('fit', 'input')
    if (options.ws and options.obs) and not os.path.isdir(ndir): os.system('mkdir '+ndir)

    cdir = os.getcwd()+'/'

    # 1d
    
    if options.dim == '1d':
    
        print 'Start 1d fits ..'
    
        for opname in options.op.split(','):
        
            op = opname+'_1d'
    
            os.chdir(cdir)
        
            wdir = outdir+'/'+op+'/expected/'
            if options.obs: wdir = outdir+'/'+op+'/observed/'
#            idir = wdir.replace('fit', 'input').replace('_toys', '')
            idir = wdir.replace('fit', 'input')
            
            coup = list(set(glob.glob(idir+'*.txt'))-set(glob.glob(idir+'*_1l.txt'))-set(glob.glob(idir+'*_2l.txt')))

            if options.ws:

                # ws creation
                
                print 'Create workspaces for', opname, '..'
                
                if not os.path.isdir(outdir+'/'+op): os.system('mkdir '+outdir+'/'+op)
            
                os.system('rm -rf '+wdir)
                os.system('mkdir '+wdir)

                if options.obs:
                        
                    os.chdir(cdir)
                    os.chdir(ndir)
                    if not os.path.isfile('srFit_model.root'):                
                        f = 'srFit.txt'
                        dname = f.replace('.txt', '')
                        os.system('cp '+cdir+indir+dname+'.txt .')
                        os.system('cp '+cdir+indir+'*shape*.root .')
                        os.system('text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:defaultModel -o srFit_model.root '+dname+'.txt > combine.log')
                
                if options.multicore:
                
                    pool = multiprocessing.Pool(options.ncores)
                    jobs = []
                    for f in coup: jobs.append( pool.apply_async(ws, (f, wdir, cdir, idir, 1)) )
                    pool.close()
                    for job in jobs: result = job.get()
                
                elif options.cluster:
                    
                    jobs = []
                    schedd = htcondor.Schedd()
                    dname, fout = [], []
                    for icoup, f in enumerate(coup):
                    
                        dname.append(f.replace('.txt', '').replace(idir, ''))
                        os.system('mkdir '+cdir+'/'+wdir+dname[-1])
                        fout.append(cdir+'/'+wdir+dname[-1]+'/'+dname[-1])
                
                        if ((icoup+1) % options.npoi == 0) or (icoup == len(coup)-1):
                            
                            jobws(proxy, dname, wdir, cdir, idir, 1, fout[-1]+'.sh')
                        
                            js = htcondor.Submit({\
                            "executable": fout[-1]+'.sh', \
                            "output": fout[-1]+'.out', \
                            "error": fout[-1]+'.err', \
                            "requirements": "machine != \"node26-9.wn.iihe.ac.be\" && machine != \"node24-2.wn.iihe.ac.be\" && machine != \"node22-10.wn.iihe.ac.be\" ", \
                            "log": fout[-1]+'.log' \
                            })
                        
                            with schedd.transaction() as shd:
                                cluster_id = js.queue(shd)
                                jobs.append(cluster_id)
                                
                            dname, fout = [], []

#                    waitcluster(schedd, jobs)
                    
                else:
                
                    for f in coup: 
                        ws(f, wdir, cdir, idir, 1)

            if options.fit:
                
                print 'Run fits for', opname, '..'
            
                rout = {}
        
                rsf = 1.
                nllnom = 0.
        
                if options.obs:
                
                    os.chdir(ndir)
                    os.system('combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 > combine.log')
                    os.system('mv higgsCombineTest.MultiDimFit.mH120.root fitResult.root')
                    f = ROOT.TFile.Open('fitResult.root')
                    tr = f.Get('limit')
                    tr.GetEntry(0)
                    rsf = tr.r
                    nllnom = tr.nll
        
                # run fit
                if options.multicore:
                
                    pool = multiprocessing.Pool(options.ncores)
                    jobs = []
                    for f in coup: jobs.append( pool.apply_async(mlfit, (f, wdir, cdir, idir, opname, nllnom)) )
                    pool.close()
                    for job in jobs:
                        result = job.get()
                        c = result[0][0]
                        rout[c] = result[1]
                        
                elif options.cluster:

                    schedd = htcondor.Schedd()

                    dname, fout = [], []
                    for icoup, f in enumerate(coup):
                    
                        dname.append(f.replace('.txt', '').replace(idir, ''))
                        fout.append(cdir+'/'+wdir+dname[-1]+'/'+dname[-1]+'_fit')
                        
                        if ((icoup+1) % options.npoi == 0) or (icoup == len(coup)-1):
                        
                            jobmlfit(proxy, dname, wdir, cdir, idir, opname, nllnom, fout[-1]+'.sh')
                
                            js = htcondor.Submit({\
                            "executable": fout[-1]+'.sh', \
                            "output": fout[-1]+'.out', \
                            "error": fout[-1]+'.err', \
                            "requirements": "machine != \"node26-9.wn.iihe.ac.be\" && machine != \"node24-2.wn.iihe.ac.be\" && machine != \"node22-10.wn.iihe.ac.be\" ", \
                            "log": fout[-1]+'.log' \
                            })
                
                            with schedd.transaction() as shd:
                                cluster_id = js.queue(shd)
                                
                            dname, fout = [], []
                    
                else:
                
                    for f in coup: 
                        result = mlfit(f, wdir, cdir, idir, opname, nllnom)
                        c = result[0][0]
                        rout[c] = result[1]
                        
                if not (options.multicore or options.cluster):

                    os.chdir(cdir)
                    foutput = wdir+'result.json'
                    with open(foutput, 'w') as write_file:
                        json.dump(rout, write_file, indent=2)

    # 2d
    
    elif options.dim == '2d':
    
        print 'Perform 2d fits ..'
    
        ops = options.op.split(',')
        
        op = ops[0]+'_'+ops[1]+'_2d'
    
        os.chdir(cdir)
        
        wdir = outdir+'/'+op+'/expected/'
        if options.obs: wdir = outdir+'/'+op+'/observed/'
#        idir = wdir.replace('fit', 'input').replace('_toys', '')
        idir = wdir.replace('fit', 'input')

        coup = list(set(glob.glob(idir+'*.txt'))-set(glob.glob(idir+'*_1l.txt'))-set(glob.glob(idir+'*_2l.txt')))

        if options.ws:

            # ws creation
            
            print 'Create workspaces for 2d fits with', ops[0], 'and', ops[1], '..'
            
            if not os.path.isdir(outdir+'/'+op): os.system('mkdir '+outdir+'/'+op)
            
            os.system('rm -rf '+wdir)
            os.system('mkdir '+wdir)

            if options.obs:
            
                os.chdir(cdir)
                os.chdir(ndir)
                if not os.path.isfile('srFit_model.root'):                
                    f = 'srFit.txt'
                    dname = f.replace('.txt', '')
                    os.system('cp '+cdir+indir+dname+'.txt .')
                    os.system('cp '+cdir+indir+'*shape*.root .')
                    os.system('text2workspace.py -P HiggsAnalysis.CombinedLimit.PhysicsModel:defaultModel -o srFit_model.root '+dname+'.txt')

            # ws creation
            if options.multicore:
                
                pool = multiprocessing.Pool(options.ncores)
                jobs = []
                for f in coup: jobs.append( pool.apply_async(ws, (f, wdir, cdir, idir, 0)) )
                pool.close()
                for job in jobs: result = job.get()
                
            elif options.cluster:
                
                jobs = []                
                schedd = htcondor.Schedd()
                
                dname, fout = [], []
                for icoup, f in enumerate(coup):
                    
                    dname.append(f.replace('.txt', '').replace(idir, ''))
                    os.system('mkdir '+cdir+'/'+wdir+dname[-1])
                    fout.append(cdir+'/'+wdir+dname[-1]+'/'+dname[-1])
                    
                    if ((icoup+1) % options.npoi == 0) or (icoup == len(coup)-1):
                        
                        jobws(proxy, dname, wdir, cdir, idir, 0, fout[-1]+'.sh')
                    
                        js = htcondor.Submit({\
                        "executable": fout[-1]+'.sh', \
                        "output": fout[-1]+'.out', \
                        "error": fout[-1]+'.err', \
                        "requirements": "machine != \"node26-9.wn.iihe.ac.be\" && machine != \"node24-2.wn.iihe.ac.be\" && machine != \"node22-10.wn.iihe.ac.be\" ", \
                        "log": fout[-1]+'.log' \
                        })
                        
                        with schedd.transaction() as shd:
                            cluster_id = js.queue(shd)
                            jobs.append(cluster_id)
                            
                        dname, fout = [], []
                        
#                waitcluster(schedd, jobs)
                
            else:
                
                for f in coup: 
                    ws(f, wdir, cdir, idir, 0)
            
        if options.fit:
            
            print 'Run fits for', op, '..'
            
            rout = {}
            
            rsf = 1.
            nllnom = 0.
        
            if options.obs:
                
                os.chdir(ndir)
                os.system('combine -M MultiDimFit srFit_model.root --saveNLL --expectSignal=1 --freezeParameters r --setParameters r=1 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 > combine.log')
                os.system('mv higgsCombineTest.MultiDimFit.mH120.root fitResult.root')
                f = ROOT.TFile.Open('fitResult.root')
                tr = f.Get('limit')
                tr.GetEntry(0)
                rsf = tr.r
                nllnom = tr.nll
        
            # run fit
            if options.multicore:
                
                pool = multiprocessing.Pool(options.ncores)
                jobs = []
                for f in coup: jobs.append( pool.apply_async(mlfit, (f, wdir, cdir, idir, op, nllnom, False)) )
                pool.close()
                for job in jobs:
                    result = job.get()
                    c1 = result[0][0]
                    c2 = result[0][1]
                    rout[str(c1)+'_'+str(c2)] = result[1]
                    
            elif options.cluster:
                
                schedd = htcondor.Schedd()

                dname, fout = [], []
                for icoup, f in enumerate(coup):
                    
                    dname.append(f.replace('.txt', '').replace(idir, ''))
                    fout.append(cdir+'/'+wdir+dname[-1]+'/'+dname[-1]+'_fit')
                    
                    if ((icoup+1) % options.npoi == 0) or (icoup == len(coup)-1):
                    
                        jobmlfit(proxy, dname, wdir, cdir, idir, op, nllnom, fout[-1]+'.sh', is1d = False)
                    
                        js = htcondor.Submit({\
                        "executable": fout[-1]+'.sh', \
                        "output": fout[-1]+'.out', \
                        "error": fout[-1]+'.err', \
                        "requirements": "machine != \"node26-9.wn.iihe.ac.be\" && machine != \"node24-2.wn.iihe.ac.be\" && machine != \"node22-10.wn.iihe.ac.be\" ", \
                        "log": fout[-1]+'.log' \
                        })
                        
                        with schedd.transaction() as shd:
                            cluster_id = js.queue(shd)
                            
                        dname, fout = [], []

            else:
                
                for f in coup: 
                    result = mlfit(f, wdir, cdir, idir, op, nllnom, is1d = False)
                    c1 = result[0][0]
                    c2 = result[0][1]
                    rout[str(c1)+'_'+str(c2)] = result[1]
                    
            if not (options.multicore or options.cluster):

                os.chdir(cdir)
                foutput = wdir+'result.json'
                with open(foutput, 'w') as write_file:
                    json.dump(rout, write_file, indent=2)                
