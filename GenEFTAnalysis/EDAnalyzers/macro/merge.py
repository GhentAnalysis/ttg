#! /usr/bin/env python

import os, sys
import subprocess
import common as c
import xml.etree.ElementTree as ET
import json
import ROOT

from optparse import OptionParser

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n Script to merge output trees"

    parser = OptionParser(usage)
    parser.add_option("-f","--files",default="info.xml",help="input xml file list [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()

    home = os.getcwd()

    xmlTree = ET.parse(options.files)
    
    print 'Merge dataset:'
    for s in xmlTree.findall('sample'):
        
        sname = s.get('id')
        ssig = s.get('sig')
 
        print sname
#        sys.stdout.write(sname)
        
        tr = []
        for ch in s:
            tr.append(ch.text)
        
        outdir = tr[0].replace(sname,' ').split()[0]
        filestomerge = ' '.join(tr)
        outfile = outdir+sname+'/merged.root'
        os.system('rm -rf '+outfile)

#        sys.stdout.flush()
        
        os.system('hadd -f '+outfile+' '+filestomerge+' > /dev/null')
        
    print '\033[92mDone\033[0;0m'
