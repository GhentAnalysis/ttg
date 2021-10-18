#! /usr/bin/env python

import os
import sys
import xml.etree.ElementTree as ET
import subprocess
import common as c

from optparse import OptionParser

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    home = os.getcwd()

    usage = "usage: %prog [options]\n Script to submit Analyzer jobs to batch"

    parser = OptionParser(usage)
    parser.add_option("-f","--files",default="1",help="number of files per job [default: %default]")
    parser.add_option("-x","--xml",default="samples.xml",help="input xml configuration [default: %default]")
    parser.add_option("-o","--out",default="jobs",help="output directory [default: %default]")
    parser.add_option("-n","--nmax",default="-1",help="number of processed events per job [default: %default]")
    parser.add_option("-b","--batch",default="pbs",help="batch system to use [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()

    os.system("cp /tmp/"+c.proxy+" "+c.proxydir+c.proxy)

    home = os.getcwd()

    outpath = home+"/"+options.out

    if os.path.isdir(outpath):
        os.system("rm -rf "+outpath)

    os.system("mkdir "+outpath)

    submitList = c.submitList
    
    nJobs = 0
    
    xmlTree = ET.parse(options.xml)
    for s in xmlTree.findall('sample'):
        for s0, t0 in submitList:
#            if sig not in ['prompt','nonprompt','all']: continue
            sname = s.get('id')
            stag = s.get('tag')
#            if 'TTJets' not in sname: continue
            if sname == s0 and stag == t0:
                files=[]
                for child in s:
                    files.append(child.text)

                jname = sname+'_'+stag
                
                nj = 0
                fjobname = []
                fjobtag = []
                fjobid = []
                fjobxml = []

                if os.path.isdir(outpath+"/"+jname):
                    os.system("rm -rf "+outpath+"/"+jname)
                os.system("mkdir "+outpath+"/"+jname)

                xml = outpath+"/"+jname+"/"+jname+"_"+str(nj)+".xml"
                fout = open(xml,"w+")
                fjobname.append(jname)
                fjobtag.append(stag)
                fjobid.append(str(nj))
                fjobxml.append(xml)
                fout.write('<data>\n')
                fout.write("<sample id=\""+jname+"\" tag=\""+stag+"\">\n")
                nc = 0
                files2read = int(len(files))
                for i in range(files2read):

                    nc = nc + 1

                    fout.write("    <file>"+files[i]+"</file>\n")

                    if (nc >= int(options.files)):
                        fout.write("</sample>\n")
                        fout.write("</data>")
                        fout.close()

                        if (i != (len(files)-1)):
                            nc = 0
                            nj = nj + 1

                            xml = outpath+"/"+jname+"/"+jname+"_"+str(nj)+".xml"
                            fout = open(xml,"w+")
                            fjobname.append(jname)
                            fjobtag.append(stag)
                            fjobid.append(str(nj))
                            fjobxml.append(xml)
                            fout.write('<data>\n')
                            fout.write("<sample id=\""+jname+"\" tag=\""+stag+"\">\n")

                if (nc < int(options.files)):
                    fout.write("</sample>\n")
                    fout.write("</data>")
                    fout.close()

                jid = 0

                for fidx, f in enumerate(fjobname):
                    print f, fjobid[jid]
                    outname = outpath+'/'+f+'/'+f+'_'+fjobid[jid]
                    outlog = outname+'.log'
                    output = outname+'.root'

                    if (options.batch=='pbs'):
                        
                        NoErrors = False
                        while NoErrors is False:
                            try:
                                res = subprocess.Popen(('qsub','-N','GenEFTTreeMaker','-q',c.batchqueue,'-o',outlog,'-j','oe','job.sh','-l','walltime='+c.walltime,'-v','nmax='+options.nmax+',sample='+f+',tag='+fjobtag[jid]+',xml='+fjobxml[jid]+',output='+output+',dout='+home+',proxy='+c.proxydir+c.proxy+',arch='+c.arch), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                out, err = res.communicate()
                                NoErrors = ('Invalid credential' not in err)
                                if not NoErrors: print '.. Resubmitted'
                            except KeyboardInterrupt:
                                sys.exit(0)
                            except:
                                pass                                

                    jid = jid + 1

                nJobs += jid
                
    print 'Total number of jobs submitted =', nJobs

