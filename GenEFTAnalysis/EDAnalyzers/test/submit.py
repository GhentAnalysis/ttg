#!/usr/bin/env python

import os, sys
import htcondor

from optparse import OptionParser

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
        
    usage = "usage: %prog [options]\n Submit jobs to copy files from one T2 to another"

    parser = OptionParser(usage)
    parser.add_option("--pref", default="root://eos.grid.vbc.ac.at/", help="prefix [default: %default]")
    parser.add_option("--jobs", default="jobs", help="jobs output directory [default: %default]")
    parser.add_option("--input", default="/eos/vbc/experiments/cms/store/user/llechner/", help="input directory [default: %default]")
    parser.add_option("--output", default="/pnfs/iihe/cms/store/user/kskovpen/Herwig/", help="output directory [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])
    
    return options

def job(proxy, dname, postfix, fout):
    
    j = "#!/bin/bash\n\n"
    
    j += "export X509_USER_PROXY="+proxy+"\n"
    
    j += "echo \"Start: $(/bin/date)\"\n"
    j += "echo \"User: $(/usr/bin/id)\"\n"
    j += "echo \"Node: $(/bin/hostname)\"\n"
    j += "echo \"CPUs: $(/bin/nproc)\"\n"
    j += "echo \"Directory: $(/bin/pwd)\"\n"
    
    j += "xrdcp "+options.pref+options.input+postfix+" root://maite.iihe.ac.be/"+options.output+dname+"/.\n"
    
    fwrite = fout+'.sh'
    with open(fwrite, 'w') as f:
        f.write(j)
        
    os.system('chmod u+x '+fwrite)
                                
if __name__ == '__main__':
    
    options = main()

    proxy = '/user/kskovpen/proxy/x509up_u20657'
    arch = 'slc6_amd64_gcc700'
    wt = '06:00:00'
    
    url = 'eos.grid.vbc.ac.at'
    com = 'xrdfs '+url+' ls '
    
    cwd = os.getcwd()
    
    samples = ['ttGamma_Dilept_Herwig7_v2', 'ttGamma_Dilept_Herwigpp_v2', 'ttGamma_SingleLept_Herwig7_v2', \
    'ttGamma_SingleLept_Herwigpp_v2', 'ttGamma_Dilept_Pythia8_v2', 'ttGamma_SingleLept_Pythia8_v2']
    
    os.system('rm -rf '+options.jobs)
    os.system('mkdir '+options.jobs)
    
    for s in samples:
        
        print s
    
        if not os.path.isdir(options.output+s): os.system('mkdir '+options.output+s)
        else:
            os.system('rm -rf '+options.output+s)
            os.system('mkdir '+options.output+s)
            
        os.system('mkdir '+options.jobs+'/'+s)
        
        dlist = os.popen(com+options.input+s+'/').read().splitlines()
        for ss in dlist:
            ddlist = os.popen(com+ss+'/').read().splitlines()
            for sss in ddlist:
                dddlist = os.popen(com+sss+'/').read().splitlines()
                for ssss in dddlist:
                    ddddlist = os.popen(com+ssss+'/').read().splitlines()
                    for d in ddddlist:
                        if '.root' in d:
                            fname = d.split('/')[-1]
                            postfix = d.replace(options.input, '')
                            
                            fout = cwd+'/'+options.jobs+'/'+s+'/'+fname
                            job(proxy, s, postfix, fout)
                            
                            js = htcondor.Submit({\
                            "executable": fout+'.sh', \
                            "output": fout+'.out', \
                            "error": fout+'.err', \
                            "log": fout+'.log' \
                            })
                            
                            schedd = htcondor.Schedd()
                            with schedd.transaction() as shd:
                                cluster_id = js.queue(shd)
