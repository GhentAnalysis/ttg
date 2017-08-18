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
argParser.add_argument('--QCD',            action='store_true', default=False)
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
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + ('tuplesQCD.conf' if args.QCD else 'tuples.conf')))

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
c          = sample.initTree(skimType=('singlePhoton' if args.QCD else 'dilepton'))
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
from ttg.reduceTuple.btagEfficiency import btagEfficiency
leptonTrackingSF = leptonTrackingEfficiency()
leptonSF         = leptonSF_()
photonSF         = photonSF_()
triggerEff       = triggerEfficiency()
btagSF           = btagEfficiency()


#
# Define new branches
#
newBranches  = ['l1/I','l2/I','isEE/O','isMuMu/O','isEMu/O','ph/I','looseLeptonVeto/O']
newBranches += ['mll/F','mllg/F','ml1g/F','ml2g/F','phL1DeltaR/F','phL2DeltaR/F','phJetDeltaR/F']
newBranches += ['njets/I','j1/I','j2/I','nbjets/I','dbjets/I']
newBranches += ['matchedGenPh/I', 'matchedGenEle/I']

if not sample.isData:
  for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']: newBranches += ['njets' + sys + '/I', 'nbjets' + sys + '/I', 'dbjets' + sys +'/I']
  for sys in ['', 'Up', 'Down']:                       newBranches += ['lWeight' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeight' + sys + '/F', 'phWeight' + sys + '/F']
  for sys in ['', 'lUp', 'lDown', 'bUp', 'bDown']:     newBranches += ['bTagWeightCSV' + sys + '/F', 'bTagWeight' + sys + '/F']
# for bmult in ['0','1','2']:                  # if 1c is used
#   for sys in ['', 'Up', 'Down']:
#     newBranches += ['bTagWeightCSV' + bmult + sys + '/F', 'bTagWeight' + bmult + sys + '/F']
  newBranches += ['genWeight/F', 'lTrackWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)

doPhotonCut           = args.type.count('pho')
c.photonCutBased      = args.type.count('phoCB')
c.photonMva           = args.type.count('photonMva')
c.hnTight             = args.type.count('eleHN')
c.hnFO                = args.type.count('eleFO')
c.eleMva              = args.type.count('eleMva')
c.cbLoose             = args.type.count('eleCBLoose')
c.cbMedium            = args.type.count('eleCBMedium')
c.cbVeto              = args.type.count('eleCBVeto')
c.susyLoose           = args.type.count('eleSusyLoose')
c.QCD                 = args.QCD
#
# Loop over the tree and make new vars
#
from ttg.reduceTuple.objectSelection import select2l, selectPhoton, makeInvariantMasses, goodJets, bJets, makeDeltaR
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None):
  c.GetEntry(i)
  if not (select2l(c, newVars) or args.QCD):                                               continue
  if not selectPhoton(c, newVars, doPhotonCut):                                            continue
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

  if not args.QCD: makeInvariantMasses(c, newVars)
  goodJets(c, newVars)
  bJets(c, newVars)
  if not args.QCD: makeDeltaR(c, newVars)


  if not sample.isData:
    newVars.genWeight          = c._weight*lumiWeight
    newVars.puWeight           = puReweighting(c._nTrueInt)
    newVars.puWeightUp         = puReweightingUp(c._nTrueInt)
    newVars.puWeightDown       = puReweightingDown(c._nTrueInt)

    if len(c.leptons) > 1:
      l1 = newVars.l1
      l2 = newVars.l2
      newVars.lWeight            = leptonSF.getSF(c, l1)*leptonSF.getSF(c, l2)
      newVars.lWeightUp          = leptonSF.getSF(c, l1, sigma=+1)*leptonSF.getSF(c, l2, sigma=+1)
      newVars.lWeightDown        = leptonSF.getSF(c, l1, sigma=-1)*leptonSF.getSF(c, l2, sigma=-1)
      newVars.lTrackWeight       = leptonTrackingSF.getSF(c, l1)*leptonTrackingSF.getSF(c, l2)
    else:
      newVars.lWeight            = 1.
      newVars.lWeightUp          = 1.
      newVars.lWeightDown        = 1.
      newVars.lTrackWeight       = 1.

    newVars.phWeight           = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
    newVars.phWeightUp         = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
    newVars.phWeightDown       = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
 
    # method 1a
    for sys in ['', 'lUp', 'lDown', 'bUp', 'bDown']:
      setattr(newVars, 'bTagWeightCSV' + sys, btagSF.getBtagSF_1a(sys, c, c.bjets, isCSV = True))
      setattr(newVars, 'bTagWeight'    + sys, btagSF.getBtagSF_1a(sys, c, c.bjets, isCSV = False))

    # method 1c
    #for sys in ['','Up','Down']:
    #  if sys == 'Up':   sysType = 'up'
    #  if sys == 'Down': sysType = 'down'
    #  else:             sysType = 'central'
    #  btagWeightsCSV = btagSF.getBtagSF_1c(sysType, c, c.bjets, isCSV=True)    # returns (0j weight, 1j weight, 2j weight)
    #  btagWeights    = btagSF.getBtagSF_1c(sysType, c, c.dbjets, isCSV=False)
    #  print btagWeights, btagWeightsCSV
    #  for bmult in range(3):
    #    setattr(newVars, 'bTagWeightCSV' + str(bmult) + sys, btagWeightsCSV[bmult])
    #    setattr(newVars, 'bTagWeight'    + str(bmult) + sys, btagWeights[bmult])

    trigWeight, trigErr        = triggerEff.getSF(c, l1, l2) if len(c.leptons) > 1 else (1., 0.)
    newVars.triggerWeight      = trigWeight
    newVars.triggerWeightUp    = trigWeight+trigErr
    newVars.triggerWeightDown  = trigWeight-trigErr

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
