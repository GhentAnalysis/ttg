#! /usr/bin/env python

#
# Script to create flat lepton trees
# i.e. one entry per lepton (not per event)
#

#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--type',      action='store',      default='rocCurve2016',       help='Specify type of reducedTuple')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Retrieve sample list, reducedTuples need to be created for the samples listed in tuples.conf
#
from ttg.samples.Sample import createSampleList, getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + args.type + '.conf'))

#
# Submit subjobs:
#   - each sample is splitted by the splitJobs parameter defined in sampleList, if a sample runs too slow raise the splitJobs parameter
#
if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]

  jobs = []
  for sample in sampleList:
    jobs += [(sample.name, str(i)) for i in xrange(sample.splitJobs)]
  submitJobs(__file__, ('sample', 'subJob'), jobs, argParser, subLog=args.type)
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#
import ROOT
ROOT.gROOT.SetBatch(True)

sample = getSampleFromList(sampleList, args.sample)
c      = sample.initTree(shortDebug=args.debug)

#
# Create flat lepton tree
#
from ttg.tools.helpers import reducedTupleDir, isValidRootFile
outputId   = str(args.subJob)
outputName = os.path.join(reducedTupleDir, sample.productionLabel, args.type, sample.name, sample.name + '_' + outputId + '.root')

try:    os.makedirs(os.path.dirname(outputName))
except: pass

if not args.overwrite and isValidRootFile(outputName):
  log.info('Finished: valid outputfile already exists')
  exit(0)

outputFile = ROOT.TFile(outputName ,"RECREATE")
outputFile.cd()

outputTree = ROOT.TTree("flatLeptonTree", "flatLeptonTree")

newBranches = ['pt/F', 'eta/F', 'flavor/I', 'mvaTTH/F', 'mvaTZQ/F', 'isPrompt/O']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)


#
# Loop over the tree, skim, make new vars and add the weights
# --> for more details about the skims and new variables check the called functions in ttg.reduceTuple.objectSelection
#
log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None):
  if c.GetEntry(i) < 0:
    log.warning("problem reading entry, skipping")
    continue

  for i in range(c._nLight):
    newVars.isPrompt  = c._lIsPrompt[i]
    newVars.pt        = c._lPt[i]
    newVars.eta       = c._lEta[i]
    newVars.flavor    = c._lFlavor[i]
    newVars.mvaTZQ    = c._leptonMvatZq[i]
    newVars.mvaTTH    = c._leptonMvaTTH[i]
    outputTree.Fill()

outputTree.AutoSave()
outputFile.Close()
log.info('Finished')

