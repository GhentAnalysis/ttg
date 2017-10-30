#! /usr/bin/env python
from ttg.tools.logger import getLogger
log = getLogger()

import glob, os, ROOT, sys

def testT2(dir):
  for i in glob.glob(dir + '/*.root'):
    log.info('Trying ' + str(i))
    chain = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
    chain.Add('dcap://maite.iihe.ac.be/' + i)
    log.info('Success: ' + str(chain.GetEntries()))

testT2(sys.argv[1])
