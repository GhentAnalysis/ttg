import os
import sys
import math
import operator
from array import array
import xml.etree.ElementTree as ET
import ROOT

import common as c
import objects as obj
import tree as tr
import functions as fun
import utils

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n Script to produce trees"

    parser = OptionParser(usage)
    parser.add_option("-s","--sample",default="sample",help="input sample [default: %default]")
    parser.add_option("-t","--tag",default="tag",help="production tag [default: %default]")
    parser.add_option("-x","--xml",default="samples.xml",help="input xml configuration [default: %default]")
    parser.add_option("-o","--output",default="output.root",help="output file name [default: %default]")
    parser.add_option("-n","--nmax",default=-1,help="max number of events [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()

    ROOT.gROOT.SetBatch()

    outFile = ROOT.TFile.Open(options.output,"RECREATE")

    files=[]
    xmlTree = ET.parse(options.xml)
    for s in xmlTree.findall('sample'):
        if s.get('id') == options.sample and s.get('tag') == options.tag:
            for child in s:
                files.append(child.text)
                
    val = tr.tree('val')

    gtr = ROOT.TChain(c.treeName)

    for f in files:
        print f
        gtr.Add(f)

    nEntries = gtr.GetEntries()
    print 'Number of events:', nEntries

    ie = 0

    Event = obj.event()
    
    print 'Process data ..'
    for ev in gtr:

        ie = ie + 1
        if (ie > int(options.nmax) and (int(options.nmax) >= 0)):
            break
        
        Event.fill(ev)

        Truth = obj.truth(ev, verbose=False)

        val.clear()
        
        val.weight_SM[0] = Event.weight_SM
        val.weight_ctZ_2_ctZI_0_ctW_0_ctWI_0[0] = Event.weight_ctZ_2_ctZI_0_ctW_0_ctWI_0
        val.weight_ctZ_0_ctZI_2_ctW_0_ctWI_0[0] = Event.weight_ctZ_0_ctZI_2_ctW_0_ctWI_0
        val.weight_ctZ_0_ctZI_0_ctW_2_ctWI_0[0] = Event.weight_ctZ_0_ctZI_0_ctW_2_ctWI_0
        val.weight_ctZ_0_ctZI_0_ctW_0_ctWI_2[0] = Event.weight_ctZ_0_ctZI_0_ctW_0_ctWI_2
        
        for c in Event.coeff:
            val.coeff.push_back(c)

        for i in range(len(Truth.ps)):
            
            pid = Truth.ps[i].pid

            val.pid.push_back(pid)
            val.pt.push_back(Truth.ps[i].pt)
            val.eta.push_back(Truth.ps[i].eta)
            val.phi.push_back(Truth.ps[i].phi)
            val.E.push_back(Truth.ps[i].E)
            val.mid.push_back(Truth.ps[i].mid)

        for i in range(len(Truth.lhe)):
            
            pid = Truth.lhe[i].pid

            val.lhepid.push_back(pid)
            val.lhept.push_back(Truth.lhe[i].pt)
            val.lheeta.push_back(Truth.lhe[i].eta)
            val.lhephi.push_back(Truth.lhe[i].phi)
            val.lheE.push_back(Truth.lhe[i].E)

        val.fill()
        
    outFile.Write()
    outFile.Close()
    
    print '\033[92mDone\033[0;0m'
