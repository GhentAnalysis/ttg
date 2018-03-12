#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.plots.plot         import getHistFromPkl
from ttg.tools.logger       import getLogger
log = getLogger(args.logLevel)

for sample in ['TTGamma', 'TTJets']: 
  print sample + ':\t\t\t'            + str(getHistFromPkl(('eleSusyLoose-phoCBfull',               'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'yield', '', [sample]).Integral())
  print sample + '(pixelSeedVeto):\t' + str(getHistFromPkl(('eleSusyLoose-phoCBfull-pixelSeedVeto', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'yield', '', [sample]).Integral())
