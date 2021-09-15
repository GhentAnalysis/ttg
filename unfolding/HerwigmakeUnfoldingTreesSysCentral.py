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
argParser.add_argument('--type',      action='store',      default='UnfphoCB',           help='Specify type of reducedTuple')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
argParser.add_argument('--singleJob', action='store_true', default=False,                help='submit one single subjob, be careful with this')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Retrieve sample list, reducedTuples need to be created for the samples listed in tuples.conf
#
from ttg.samples.Sample import createSampleList, getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_2016.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_2017.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_2018.conf'))

#
# Submit subjobs:
#   - each sample is splitted by the splitJobs parameter defined in tuples.conf, if a sample runs too slow raise the splitJobs parameter
#   - data is additional splitted per run to avoid too heavy chains to be loaded
#
forSys = args.type.count('Scale') or args.type.count('Res')  # Tuple is created for specific sys


if args. singleJob and args.subJob and not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [(args.sample, args.year, args.subJob)]
  submitJobs(__file__, ('sample', 'year', 'subJob'), jobs, argParser, subLog=args.type, jobLabel = "RT")
  exit(0)

if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]
  if args.year:   sampleList = [s for s in sampleList if s.year == args.year]



  jobs = []
  for sample in sampleList:
    if forSys: 
      if any([sample.name.count(sname) for sname in ['uedown', 'ueup', 'erd', 'CR1', 'CR2', 'ttgjets']]): continue
    jobs += [(sample.name, sample.year, str(i)) for i in xrange(sample.splitJobs)]
  submitJobs(__file__, ('sample', 'year', 'subJob'), jobs, argParser, subLog=args.type, jobLabel = "RT")
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#
import ROOT
ROOT.gROOT.SetBatch(True)

def initTreeHack(sample, shortDebug=False, reducedType=None, splitData=None):
  if reducedType:
    sample.chain        = ROOT.TChain('blackJackAndHookersTree')
    sample.listOfFiles  = []
    for sample, productionLabel in sample.addSamples:
      sample.listOfFiles += glob.glob(os.path.join(reducedTupleDir, productionLabel, reducedType, sample[4:] if sample[:4] in ['2016', '2017', '2018'] else sample, '*.root'))
  else:
    sample.chain = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
    sample.listOfFiles = sample.getListOfFiles(splitData)
  if shortDebug: sample.listOfFiles = sample.listOfFiles[:3]
  if not len(sample.listOfFiles): log.error('No tuples to run over for ' + sample.name)
  for path in sample.listOfFiles:
    log.debug("Adding " + path)
    sample.chain.Add(path)
  return sample.chain

sample = getSampleFromList(sampleList, args.sample, args.year)
# c      = sample.initTree(shortDebug=args.debug)
c      = initTreeHack(sample, shortDebug=args.debug)
c.year = sample.year #access to year wherever chain is passed to function, prevents having to pass year every time



def getTotalWeightsHack(sample):
  totals = 0
  for f in sample.listOfFiles:
    fileName = f
    f = ROOT.TFile(f)
    try:
      totals += f.Get('blackJackAndHookers/blackJackAndHookersTree').GetEntriesFast()
      # log.info(totals)
    except:
      log.warning('problem in getting weights for file, skipping')
      sample.listOfFiles.remove(fileName)
  return totals

lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in [getTotalWeightsHack(sample)]]

# lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in sample.getTotalWeights()]

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

unusedBranches = ["HLT", "Flag", "HN", "tau", "lMuon", "decay", "tau", "_closest", "JECSources", 'jetPt_', 'corrMET']
deleteBranches = ["Scale", "Res", "pass", "met", "lElectron", "_gen", '_lhe']
deleteBranches += ["heWeight"]
for i in unusedBranches + deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 0)
outputTree = sample.chain.CloneTree(0)
for i in deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 1)


#
# Define new branches
#

newBranches  = ['ph/I', 'ph_pt/F', 'phJetDeltaR/F', 'phBJetDeltaR/F', 'matchedGenPh/I', 'matchedGenEle/I', 'nphotons/I']
newBranches += ['PLph/I', 'PLph_pt/F', 'PLph_Eta/F', 'PLnphotons/I','PLphBJetDeltaR/F', 'PLphJetDeltaR/F']
newBranches += ['PLnjets/I', 'PLndbjets/I', 'PLj1/I', 'PLj2/I']
newBranches += ['PLl1/I', 'PLl2/I', 'PLl1_pt/F', 'PLl2_pt/F']
newBranches += ['PLmll/F', 'PLmllg/F', 'PLml1g/F', 'PLml2g/F', 'PLphL1DeltaR/F', 'PLphL2DeltaR/F', 'PLl1JetDeltaR/F', 'PLl2JetDeltaR/F', 'PLjjDeltaR/F']
newBranches += ['PLisEE/O', 'PLisMuMu/O', 'PLisEMu/O']
newBranches += ['failFid/O']
newBranches += ['genWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)

# newVars.egvar = c.egvar
# newVars.muvar = c.muvar

from ttg.unfolding.PLobjectSelectionHackCentral import PLselectLeptons, PLselectPhotons, PLgoodJets, PLbJets, PLmakeInvariantMasses, PLmakeDeltaR
#
# Start selection
#

# setIDSelection(c, 'phoCB')


########## START EVENT LOOP ##########
log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString=None):
  if c.GetEntry(i) < 0: 
    log.warning("problem reading entry, skipping")
    continue


  try:
    newVars.lhePhPt = c._lhePt[[i for i in c._lhePdgId].index(22)]
  except:
    newVars.lhePhPt = 0.


  newVars.PLph = 99
  newVars.PLph_pt = -99.
  
  newVars.PLphJetDeltaR = 999
  newVars.PLphBJetDeltaR = 999
  newVars.PLjjDeltaR = -1


##### PL selection and storing values #####
  fid = PLselectLeptons(c, newVars)
  if fid:
    fid = PLselectPhotons(c, newVars)
  if fid:
    PLgoodJets(c, newVars)
    PLbJets(c, newVars)
    PLmakeInvariantMasses(c, newVars)
    PLmakeDeltaR(c, newVars)

  newVars.failFid = not fid

  if not fid: continue


  newVars.genWeight    = c._weight*lumiWeights[0]
  # newVars.genWeight    = c._weight*lumiWeights[0]

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()

f = ROOT.TFile.Open(outputName)
try:
  for event in f.blackJackAndHookersTree:
    continue
except:
  print 'produced a corrupt file, exiting'
  exit(1)

log.info('Finished')

