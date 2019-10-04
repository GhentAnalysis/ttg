#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--sample',   action='store',      default='TT_Dil')
argParser.add_argument('--year',     action='store',      default='None', choices=['2016', '2017', '2018'])
argParser.add_argument('--submit',   action='store_true', default=False,  help='submit the script, needed as for some large samples runtime exceeds 5 hours')
argParser.add_argument('--isChild',  action='store_true', default=False,  help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--runLocal', action='store_true', default=False,  help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='do not launch subjobs, only show them')
argParser.add_argument('--debug',    action='store_true', default=False,  help='only run over first three files for debugging')
argParser.add_argument('--selectID', action='store',      default='phoCB', choices=['phoCB', 'phoCBfull', 'leptonMVA-phoCB'])

args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

if not args.isChild and args.submit:
  from ttg.tools.jobSubmitter import submitJobs
  submitJobs(__file__, ('sample', 'year'), [(args.sample, args.year,)], argParser, queue='highbw', wallTime='168', jobLabel = "BT")
  exit(0)

if not args.sample or not args.year:
  log.info("Specify the sample and the year")
  exit(0)

from ttg.reduceTuple.btagEfficiency import getPtBins, getEtaBins
from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, goodJets
from ttg.samples.Sample import createSampleList, getSampleFromList

def getBTagMCTruthEfficiencies(c, btagWP):  # pylint: disable=R0912
  for i in sample.eventLoop():
    c.GetEntry(i)
    if not selectLeptons(c, c, 2):       continue
    if not selectPhotons(c, c, 2, True): continue
    goodJets(c, c)

    for j in c.jets:
      pt     = c._jetSmearedPt[j]
      eta    = abs(c._jetEta[j])
      flavor = abs(c._jetHadronFlavor[j])
      for myPtBin in getPtBins():
        if pt >= myPtBin[0] and (pt < myPtBin[1] or myPtBin[1] < 0):
          for myEtaBin in getEtaBins():
            if abs(eta) >= myEtaBin[0] and abs(eta) < myEtaBin[1]:
              if abs(flavor) == 5:   flav = 'b' 
              elif abs(flavor) == 4: flav = 'c'
              else:                  flav = 'other'
              myBin = str(myPtBin) + str(myEtaBin) + flav
              if c._jetDeepCsv_b[j] + c._jetDeepCsv_bb[j] > btagWP: passing[myBin] += c._weight
              total[myBin] += c._weight

workingPoints = {'2016':0.6321, '2017':0.4941, '2018':0.4184}

passing = {}
total   = {}
for ptBin in getPtBins():
  for etaBin in getEtaBins():
    for f in ['b', 'c', 'other']:
      name = str(ptBin) + str(etaBin) + f
      passing[name] = 0.
      total[name]   = 0.

sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuplesTrigger_'+ args.year +'.conf'))
samples    = [getSampleFromList(sampleList, sample) for sample in args.sample.split("+")]

for sample in samples:
  chain = sample.initTree(shortDebug=args.debug)
  setIDSelection(chain, args.selectID)
  getBTagMCTruthEfficiencies(chain, btagWP = workingPoints[args.year])

mceff = {}
for ptBin in getPtBins():
  mceff[tuple(ptBin)] = {}
  for etaBin in getEtaBins():
    mceff[tuple(ptBin)][tuple(etaBin)] = {}
    for f in ['b', 'c', 'other']:
      name = str(ptBin) + str(etaBin) + f
      mceff[tuple(ptBin)][tuple(etaBin)][f] = passing[name]/total[name] if total[name] > 0 else 0

pklFile = 'deepCSV_' + args.selectID + '_' + args.sample + '_' + args.year + ('DEBUG' if args.debug else '') + '.pkl'
pickle.dump(mceff, file(os.path.expandvars('$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/' + pklFile), 'w'))
log.info('Efficiencies deepCSV for ' + str(args.year) +':')
log.info('Finished')
