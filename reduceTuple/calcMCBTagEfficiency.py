#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)

import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--CSV',            action='store_true', default=False)
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.reduceTuple.btagEfficiency import ptBins, etaBins
from ttg.reduceTuple.objectSelection import select2l, selectPhoton, goodJets
from ttg.samples.Sample import createSampleList,getSampleFromList
sampleList           = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples.conf'))
sample               = getSampleFromList(sampleList, 'TTJets_Dilep')
chain                = sample.initTree()
chain.QCD            = False
chain.photonCutBased = True
chain.photonMva      = False
chain.eleMva         = False
chain.eleMvaTight    = False

def getBTagMCTruthEfficiencies(c, overwrite=False, isCSV=False, btagWP=0.6324):
  passing = {}
  total   = {}
  for ptBin in ptBins:
    for etaBin in etaBins:
      for f in ['b','c','other']:
        name = str(ptBin) + str(etaBin) + f
        passing[name] = 0.
        total[name]   = 0.

  for i in sample.eventLoop():
    c.GetEntry(i)
    if not select2l(c, c):           continue
    if not selectPhoton(c, c, True): continue
    goodJets(c, c)
 
    for j in c.jets:
      pt     = c._jetPt[j]
      eta    = abs(c._jetEta[j])
      flavor = abs(c._jetHadronFlavour[j])
      for ptBin in ptBins:
        if pt>=ptBin[0] and (pt<ptBin[1] or ptBin[1]<0):
          for etaBin in etaBins:
            if abs(eta)>=etaBin[0] and abs(eta)<etaBin[1]:
              if abs(flavor)==5:   f = 'b' 
              elif abs(flavor)==4: f = 'c'
              else:                f = 'other'
              name = str(ptBin) + str(etaBin) + f
              if (not isCSV) and c._jetDeepCsv_b[j] + c._jetDeepCsv_bb[j] > btagWP: passing[name] += c._weight
              if isCSV     and c._jetCsvV2[j] > btagWP:                             passing[name] += c._weight
              total[name] += c._weight

  mceff = {}
  for ptBin in ptBins:
    mceff[tuple(ptBin)] = {}
    for etaBin in etaBins:
      mceff[tuple(ptBin)][tuple(etaBin)] = {}
      for f in ['b','c','other']:
        name = str(ptBin) + str(etaBin) + f
        mceff[tuple(ptBin)][tuple(etaBin)][f] = passing[name]/total[name] if total[name] > 0 else 0
 
  return mceff

if args.CSV: res = getBTagMCTruthEfficiencies(chain, isCSV=True,  btagWP=0.8484)
else:        res = getBTagMCTruthEfficiencies(chain, isCSV=False, btagWP=0.6324)

pickle.dump(res, file(os.path.expandvars('$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/' + ('CSVv2' if args.CSV else 'deepCSV') + '.pkl'), 'w'))
log.info('Efficiencies ' +  ('CSVv2' if args.CSV else 'deepCSV') + ':')
log.info(res)
