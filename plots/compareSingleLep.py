#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.plots.plot   import Plot, getHistFromPkl
from ttg.tools.helpers import getResultsFile
from ttg.tools.logger import getLogger, logLevel
log = getLogger(args.logLevel)

import pickle, os, ROOT, shutil
ROOT.gROOT.SetBatch(True)

dilep     = getHistFromPkl(getResultsFile('sigmaIetaIeta-ttbar', 'noData', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p'), 'photon_chargedIso', ['TTJets'])
singlelep = getHistFromPkl(getResultsFile('sigmaIetaIeta-ttbar', 'noData', 'lg-looseLeptonVeto-njet4p-deepbtag1p'),                    'photon_chargedIso', ['TTJets'])

import ttg.tools.style as styles
dilep.style       = styles.fillStyle(ROOT.kRed)
singlelep.style   = styles.fillStyle(ROOT.kBlue)
dilep.texName     = "t#bar{t} (dilep)"
singlelep.texName = "t#bar{t} (singlelep)"

plot        = Plot('compareSingleLep', 'chargedIso(#gamma) (GeV)', None, None, overflowBin=None, stack=[[]], texY='Events')
plot.stack  = [[dilep],[singlelep]]
plot.histos = {i:i for i in sum(plot.stack, [])}

from ttg.tools.style import drawLumi
plot.draw(plot_directory = '.',
         ratio   = {'yRange':(0.1,1.9),'texY': 'ratio'},
         logX    = False, logY = False, sorting = False,
         yRange  = (0.0001, "auto"),
         drawObjects = drawLumi(None, 35.9),
)
log.info('Finished')
