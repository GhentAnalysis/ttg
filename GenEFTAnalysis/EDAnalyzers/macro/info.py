#! /usr/bin/env python

import os, sys, math
import subprocess
import common as c
import xml.etree.ElementTree as ET
import json
import ROOT

from optparse import OptionParser

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n Script to create the list of output trees"

    parser = OptionParser(usage)
    parser.add_option("-d","--dir",default="jobs/",help="input directory with processed ntuples [default: %default]")
    parser.add_option("-s","--samples",default="samples.xml",help="list of samples [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()

    home = os.getcwd()

    fout = open('info.xml',"w+")
    fout.write('<data>\n')

    samples = next(os.walk(options.dir))[1]
    
    submitList = eval('c.submitList')

    os.system('rm -f '+options.dir+'/*/merged*')
    
    print 'Getting info'
    for s in samples:
        found = False
        for s0, tag in submitList:
            sname = s0+'_'+tag
            if sname == s:
                    
                found = True
                
                print sname
                
                files = []

                for r, d, f in os.walk(options.dir+s):
                    filesROOT = [x for x in f if 'root' in x]
                    for ff in range(len(filesROOT)):
                        if '.root' in filesROOT[ff]:
                            fname = options.dir+s+'/'+filesROOT[ff]
                            files.append(fname)
                            
                filelist = []
                for f in files:
                    filelist.append('        <file>'+f+'</file>\n')

                if len(filelist) > 0:
                    fout.write('    <sample id="'+s+'">\n')
                    for f in filelist:
                        fout.write(f)
                    fout.write('    </sample>\n')

        if not found:
            print 'Not found sample '+s
            exit

    fout.write('</data>\n')
    fout.close()
