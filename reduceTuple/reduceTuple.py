#! /usr/bin/env python

#
# Script to create additional variables in the trees and reduce it to manageable size
#


#
# Argument parser and logging
# 
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--sample',         action='store',      default=None)
argParser.add_argument('--type',           action='store',      default='eleCB-phoCB')
argParser.add_argument('--subJob',         action='store',      default=None)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Create sample list
#
from ttg.samples.Sample import createSampleList,getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples.conf'))

#
# Submit subjobs: for each sample split in args.splitJobs
#
if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = filter(lambda s: s.name == args.sample, sampleList)
  for sample in sampleList:
    args.sample = sample.name
    submitJobs(__file__, 'subJob', xrange(sample.splitJobs), args, subLog=sample.name)
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#

import ROOT
ROOT.gROOT.SetBatch(True)

sample     = getSampleFromList(sampleList, args.sample)
c          = sample.initTree()
lumiWeight = float(sample.xsec)*1000/sample.getTotalEvents() if not sample.isData else 1

#
# Create new reduced tree
#
reducedTupleDir = os.path.join('/user/tomc/public/TTG/reducedTuples', sample.productionLabel, args.type, sample.name)
try:    os.makedirs(reducedTupleDir)
except: pass

outputFile = ROOT.TFile(os.path.join(reducedTupleDir, sample.name + '_' + str(args.subJob) + '.root'),"RECREATE")
outputFile.cd()

#
# Switch off unneeded branches
#
sample.chain.SetBranchStatus("*HLT*", 0)
sample.chain.SetBranchStatus("*HN*", 0)
outputTree = sample.chain.CloneTree(0)




#
# Initialize reweighting functions
#
from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting     = getReweightingFunction(data="PU_2016_36000_XSecCentral", mc="Summer16")
puReweightingUp   = getReweightingFunction(data="PU_2016_36000_XSecUp",      mc="Summer16")
puReweightingDown = getReweightingFunction(data="PU_2016_36000_XSecDown",    mc="Summer16")

from ttg.reduceTuple.leptonTrackingEfficiency import leptonTrackingEfficiency
from ttg.reduceTuple.leptonSF import leptonSF as leptonSF_
from ttg.reduceTuple.photonSF import photonSF as photonSF_
from ttg.reduceTuple.triggerEfficiency import triggerEfficiency
leptonTrackingSF = leptonTrackingEfficiency()
leptonSF         = leptonSF_()
photonSF         = photonSF_()
triggerEff       = triggerEfficiency()


#
# Define new branches
#
newBranches  = ['l1/I','l2/I','isEE/O','isMuMu/O','isEMu/O','ph/I','looseLeptonVeto/O']
newBranches += ['mll/F','mllg/F','ml1g/F','ml2g/F','phL1DeltaR/F','phL2DeltaR/F','phJetDeltaR/F']
newBranches += ['njets/I','j1/I','j2/I','nbjets/I']
newBranches += ['matchedGenPh/I', 'matchedGenEle/I']

if not sample.isData:
  for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']: newBranches += ['njets' + sys + '/I', 'nbjets' + sys + '/I']
  for sys in ['', 'Up', 'Down']:                       newBranches += ['lWeight' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeight' + sys + '/F', 'phWeight' + sys + '/F']
  newBranches += ['genWeight/F', 'lTrackWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)

c.photonCutBasedTight = args.type.count('photonCBT')
c.photonCutBased      = args.type.count('phoCB')
c.photonMva           = args.type.count('photonMva')
c.eleMva              = args.type.count('eleMvaMedium')
c.eleMvaTight         = args.type.count('eleMvaTight')

#
# Loop over the tree and make new vars
#
from ttg.reduceTuple.objectSelection import select2l, selectPhoton, makeInvariantMasses, goodJets, bJets, makeDeltaR, matchPhoton
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob)):
  c.GetEntry(i)
  if not select2l(c, newVars):                                                             continue
  if not selectPhoton(c, newVars):                                                         continue
  if sample.isData:
    if not c._passMETFilters:                                                              continue
    if sample.name.count('DoubleMuon') and not c._passTTG_mm:                              continue
    if sample.name.count('DoubleEG')   and not c._passTTG_ee:                              continue
    if sample.name.count('MuonEG')     and not c._passTTG_em:                              continue
    if sample.name.count('SingleMuon'):
      if newVars.isMuMu and not (not c._passTTG_mm and c._passTTG_m):                      continue
      if newVars.isEMu  and not (not c._passTTG_em and c._passTTG_m):                      continue
    if sample.name.count('SingleElectron'):
      if newVars.isEE   and not (not c._passTTG_ee and c._passTTG_e):                      continue
      if newVars.isEMu  and not (not c._passTTG_em and c._passTTG_e and not c._passTTG_m): continue

  makeInvariantMasses(c, newVars)
  goodJets(c, newVars)
  bJets(c, newVars)
  makeDeltaR(c, newVars)


  if not sample.isData:
    matchPhoton(c, newVars)

    l1 = newVars.l1
    l2 = newVars.l2

    newVars.genWeight          = c._weight*lumiWeight
    newVars.puWeight           = puReweighting(c._nTrueInt)
    newVars.puWeightUp         = puReweightingUp(c._nTrueInt)
    newVars.puWeightDown       = puReweightingDown(c._nTrueInt)

    newVars.lWeight            = leptonSF.getSF(c, l1)*leptonSF.getSF(c, l2)
    newVars.lWeightUp          = leptonSF.getSF(c, l1, sigma=+1)*leptonSF.getSF(c, l2, sigma=+1)
    newVars.lWeightDown        = leptonSF.getSF(c, l1, sigma=-1)*leptonSF.getSF(c, l2, sigma=-1)
    newVars.lTrackWeight       = leptonTrackingSF.getSF(c, l1)*leptonTrackingSF.getSF(c, l2)

    newVars.phWeight           = photonSF.getSF(c, newVars.ph)
    newVars.phWeightUp         = photonSF.getSF(c, newVars.ph)
    newVars.phWeightDown       = photonSF.getSF(c, newVars.ph)
 
    trigWeight, trigErr        = triggerEff.getSF(c, l1, l2)
    newVars.triggerWeight      = trigWeight
    newVars.triggerWeightUp    = trigWeight+trigErr
    newVars.triggerWeightDown  = trigWeight-trigErr

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
