#! /usr/bin/env python
from ttg.tools.logger import getLogger
log = getLogger()

import glob, ROOT, sys

def testT2(directory):
  for i in glob.glob(directory + '/*.root'):
    log.info('Trying ' + str(i))
    chain = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
    chain.Add('dcap://maite.iihe.ac.be/' + i)
    log.info('Success: ' + str(chain.GetEntries()))

testT2(sys.argv[1])
