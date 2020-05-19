#! /usr/bin/env python

#
# Script to create additional variables in the trees and reduce it to manageable size
#


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--type',      action='store',      default='UnfphoCB',              help='Specify type of reducedTuple')
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
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_2016.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_2017.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_2018.conf'))

#
# Submit subjobs:
#   - each sample is splitted by the splitJobs parameter defined in tuples.conf, if a sample runs too slow raise the splitJobs parameter
#   - data is additional splitted per run to avoid too heavy chains to be loaded
#
if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]
  if args.year:   sampleList = [s for s in sampleList if s.year == args.year]

  jobs = []
  for sample in sampleList:
    jobs += [(sample.name, sample.year, str(i)) for i in xrange(sample.splitJobs)]
  submitJobs(__file__, ('sample', 'year', 'subJob'), jobs, argParser, subLog=args.type, jobLabel = "RT")
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#
import ROOT
ROOT.gROOT.SetBatch(True)

sample = getSampleFromList(sampleList, args.sample, args.year)
c      = sample.initTree(shortDebug=args.debug)
c.year = sample.year #access to year wherever chain is passed to function, prevents having to pass year every time
forSys = (args.type.count('Scale') or args.type.count('Res')) and (sample.name.count('isr') or sample.name.count('fsr'))  # Tuple is created for specific sys


if not sample.isData:
  lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in sample.getTotalWeights()]


#
# Create new reduced tree (except if it already exists and overwrite option is not used)
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


#
# Switch off unused branches, avoid copying of branches we want to delete
#
# FIXME Update this so that we keep the skimmed size small

# unusedBranches = ["HLT", "Flag", "HN", "tau", "Ewk", "lMuon", "miniIso", "closest", "_pt", "decay"]
unusedBranches = ["HLT", "Flag", "HN", "tau", "lMuon", "decay", "tau", "Up", "Down", "_closest"]
# deleteBranches = ["Scale", "Res", "pass", "met", "POG", "lElectron"]
deleteBranches = ["Scale", "Res", "pass", "met", "lElectron", "_gen", "_pl", '_lhe', '_jet']
# unusedBranches += ["gen_nL", "gen_l", "gen_met"]
# deleteBranches += ["heWeight", "gen_ph"]
deleteBranches += ["heWeight"]
for i in unusedBranches + deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 0)
outputTree = sample.chain.CloneTree(0)
for i in deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 1)


#
# Define new branches
#
newBranches  = ['ph/I', 'ph_pt/F', 'phJetDeltaR/F', 'phBJetDeltaR/F', 'matchedGenPh/I', 'matchedGenEle/I', 'nphotons/I']
newBranches += ['PLph/I', 'PLph_pt/F', 'PLph_Eta/F', 'PLnphotons/I']
newBranches += ['njets/I', 'j1/I', 'j2/I', 'ndbjets/I', 'dbj1/I', 'dbj2/I']
newBranches += ['PLnjets/I', 'PLndbjets/I', 'PLj1/I', 'PLj2/I', 'PLj3/I', 'PLj4/I', 'PLj5/I', 'PLj6/I', 'PLdbj1/I', 'PLdbj2/I', 'PLdbj3/I', 'PLdbj4/I']
newBranches += ['l1/I', 'l2/I', 'looseLeptonVeto/O', 'l1_pt/F', 'l2_pt/F']
newBranches += ['PLl1/I', 'PLl2/I', 'PLl1_pt/F', 'PLl2_pt/F']
newBranches += ['mll/F', 'mllg/F', 'ml1g/F', 'ml2g/F', 'phL1DeltaR/F', 'phL2DeltaR/F', 'l1JetDeltaR/F', 'l2JetDeltaR/F', 'jjDeltaR/F']
newBranches += ['isEE/O', 'isMuMu/O', 'isEMu/O']
newBranches += ['PLisEE/O', 'PLisMuMu/O', 'PLisEMu/O']
newBranches += ['failReco/O']


newBranches += ['genWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)


from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR
from ttg.unfolding.PLobjectSelection import PLselectLeptons, PLselectPhotons, PLgoodJets, PLbJets

setIDSelection(c, args.type)

leptonID = 'MVA' if args.type.lower().count('leptonmva') else 'POG'



log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString=None):
  if c.GetEntry(i) < 0: 
    log.warning("problem reading entry, skipping")
    continue

  # NOTE if we're not doing continue here need way to deal with cases with <2 pl leptons
  if not PLselectLeptons(c, newVars): 
    # log.debug('event failed pl selection')
    continue
  if not PLselectPhotons(c, newVars): 
    # log.debug('event failed pl selection')
    continue

  PLgoodJets(c, newVars)
  PLbJets(c, newVars)
  # PLmakeInvariantMasses(c, newVars)
  # PLmakeDeltaR(c, newVars)

  newVars.ph = 99
  newVars.ph_pt = -99.
  reco = selectLeptons(c, newVars, 2)
  if reco:
    reco = selectPhotons(c, newVars, 2, False)
  

  if reco:
    goodJets(c, newVars)
    bJets(c, newVars)
    makeInvariantMasses(c, newVars)
    makeDeltaR(c, newVars)
  
  newVars.failReco = not reco
  #checkMatches(c, newVars)

# to start with already do PL skim I guess

# store match (bool or match id) ? 

  newVars.genWeight    = c._weight*lumiWeights[0]


  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
log.info('Finished')
