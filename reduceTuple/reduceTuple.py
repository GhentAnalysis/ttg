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
argParser.add_argument('--type',           action='store',      default='eleSusyLoose-phoCB')
argParser.add_argument('--subJob',         action='store',      default=None)
argParser.add_argument('--splitData',      action='store',      default=None)
argParser.add_argument('--subProdLabel',   action='store',      default=None)
argParser.add_argument('--QCD',            action='store_true', default=False)
argParser.add_argument('--singleLep',      action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--debug',          action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Create sample list
#
from ttg.samples.Sample import createSampleList,getSampleFromList
if args.QCD:         tuples = 'tuplesQCD.conf'
elif args.singleLep: tuples = 'tuplesSingleLep.conf'
else:                tuples = 'tuples.conf'
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + tuples))

#
# Submit subjobs: for each sample split in args.splitJobs
#
if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = filter(lambda s: s.name == args.sample, sampleList)
  splitData = args.splitData
  for sample in sampleList:
    args.sample = sample.name
    if splitData and sample.isData:                                                                # Chains become very slow for data, so we split them
      for dataRun in (['B','C','D','E','F','G','H'] if splitData not in ['B','C','D','E','F','G','H'] else [splitData]):
        args.splitData = dataRun
        submitJobs(__file__, 'subJob', xrange(sample.splitJobs), args, subLog=sample.name+args.splitData)
        args.subProdLabel=None
        args.splitData=None
    else:
      submitJobs(__file__, 'subJob', xrange(sample.splitJobs), args, subLog=sample.name)
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#

import ROOT
ROOT.gROOT.SetBatch(True)

sample     = getSampleFromList(sampleList, args.sample)
c          = sample.initTree(skimType=('singlePhoton' if args.QCD else 'dilepton'), shortDebug=args.debug, splitData=args.splitData, subProductionLabel=args.subProdLabel)
lumiWeight = float(sample.xsec)*1000/sample.getTotalEvents() if not sample.isData else 1


#
# Create new reduced tree
#
reducedTupleDir = os.path.join('/user/tomc/public/TTG/reducedTuples', sample.productionLabel, args.type, sample.name)
try:    os.makedirs(reducedTupleDir)
except: pass

outputId   = (args.splitData if args.splitData in ['B','C','D','E','F','G','H'] else '') + str(args.subJob)
outputFile = ROOT.TFile(os.path.join(reducedTupleDir, sample.name + '_' + outputId + '.root'),"RECREATE")
outputFile.cd()

#
# Switch off unneeded branches
#
delBranches = ["HLT","Flag","HN","tau","Ewk","lMuon","miniIso","WOIso","leptonMva","closest","_pt","decay"]
if not sample.isData: delBranches += ["heWeight","gen*Charge","gen*Flavor","gen_met","gen*Status","gen*Pdg"]
for i in delBranches: sample.chain.SetBranchStatus("*"+i+"*", 0)
outputTree = sample.chain.CloneTree(0)



#
# Initialize reweighting functions
#
from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting     = getReweightingFunction(data="PU_2016_36000_XSecCentral")
puReweightingUp   = getReweightingFunction(data="PU_2016_36000_XSecUp")
puReweightingDown = getReweightingFunction(data="PU_2016_36000_XSecDown")

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
newBranches  = ['ph/I','phJetDeltaR/F','matchedGenPh/I', 'matchedGenEle/I', 'nphotons/I']
newBranches += ['njets/I','j1/I','j2/I','nbjets/I','ndbjets/I']
newBranches += ['l1/I','l2/I','looseLeptonVeto/O']
newBranches += ['mll/F','mllg/F','ml1g/F','ml2g/F','phL1DeltaR/F','phL2DeltaR/F']

if args.singleLep: newBranches += ['isE/O','isMu/O']
elif not args.QCD: newBranches += ['isEE/O','isMuMu/O','isEMu/O']

if not sample.isData:
  for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']: newBranches += ['njets_' + sys + '/I', 'nbjets_' + sys + '/I', 'ndbjets_' + sys +'/I', 'j1_' + sys + '/I', 'j2_' + sys + '/I']
  for sys in ['', 'Up', 'Down']:                       newBranches += ['lWeight' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeight' + sys + '/F', 'phWeight' + sys + '/F']
  for sys in ['', 'lUp', 'lDown', 'bUp', 'bDown']:     newBranches += ['bTagWeightCSV' + sys + '/F', 'bTagWeight' + sys + '/F']
  newBranches += ['genWeight/F', 'lTrackWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)

minLeptons            = 0 if args.QCD else (1 if args.singleLep else 2)
doPhotonCut           = args.type.count('pho')
c.photonCutBased      = args.type.count('phoCB')
c.photonMva           = args.type.count('photonMva')
c.eleMva              = args.type.count('eleMva')
c.cbLoose             = args.type.count('eleCBLoose')
c.cbMedium            = args.type.count('eleCBMedium')
c.cbVeto              = args.type.count('eleCBVeto')
c.susyLoose           = args.type.count('eleSusyLoose')

for var in ['ScaleUp','ScaleDown','ResUp','ResDown']:
  if args.type.count('e'  + var): setattr(c, '_lPtCorr',  '_lPt' + var)
  if args.type.count('ph' + var): setattr(c, '_phPtCorr', '_phPt' + var)

#
# Loop over the tree and make new vars
#
log.info('Starting event loop')
from ttg.reduceTuple.objectSelection import selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None):
  c.GetEntry(i)
  if not selectLeptons(c, newVars, minLeptons):                                            continue
  if not selectPhotons(c, newVars, doPhotonCut, minLeptons):                               continue

  if sample.isData and minLeptons > 1:
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

  if sample.isData and minLeptons == 1:
    if sample.name.count('SingleMuon')     and newVars.isMu and not c._passTTG_m: continue
    if sample.name.count('SingleElectron') and newVars.isE  and not c._passTTG_e: continue


  goodJets(c, newVars)
  bJets(c, newVars)
  makeInvariantMasses(c, newVars)
  makeDeltaR(c, newVars)

  if not sample.isData:
    newVars.genWeight          = c._weight*lumiWeight
    newVars.puWeight           = puReweighting(c._nTrueInt)
    newVars.puWeightUp         = puReweightingUp(c._nTrueInt)
    newVars.puWeightDown       = puReweightingDown(c._nTrueInt)

    if minLeptons > 1:
      l1 = newVars.l1
      l2 = newVars.l2
      newVars.lWeight          = leptonSF.getSF(c, l1)*leptonSF.getSF(c, l2)
      newVars.lWeightUp        = leptonSF.getSF(c, l1, sigma=+1)*leptonSF.getSF(c, l2, sigma=+1)
      newVars.lWeightDown      = leptonSF.getSF(c, l1, sigma=-1)*leptonSF.getSF(c, l2, sigma=-1)
      newVars.lTrackWeight     = leptonTrackingSF.getSF(c, l1)*leptonTrackingSF.getSF(c, l2)
    elif minLeptons > 0:
      l1 = newVars.l1
      newVars.lWeight          = leptonSF.getSF(c, l1)
      newVars.lWeightUp        = leptonSF.getSF(c, l1, sigma=+1)
      newVars.lWeightDown      = leptonSF.getSF(c, l1, sigma=-1)
      newVars.lTrackWeight     = leptonTrackingSF.getSF(c, l1)
    else:
      newVars.lWeight          = 1.
      newVars.lWeightUp        = 1.
      newVars.lWeightDown      = 1.
      newVars.lTrackWeight     = 1.

    newVars.phWeight           = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
    newVars.phWeightUp         = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
    newVars.phWeightDown       = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
 
    # method 1a
    for sys in ['', 'lUp', 'lDown', 'bUp', 'bDown']:
      setattr(newVars, 'bTagWeightCSV' + sys, btagSF.getBtagSF_1a(sys, c, c.bjets, isCSV = True))
      setattr(newVars, 'bTagWeight'    + sys, btagSF.getBtagSF_1a(sys, c, c.bjets, isCSV = False))

    trigWeight, trigErr        = triggerEff.getSF(c, l1, l2) if minLeptons > 1 else (1., 0.)
    newVars.triggerWeight      = trigWeight
    newVars.triggerWeightUp    = trigWeight+trigErr
    newVars.triggerWeightDown  = trigWeight-trigErr

  outputTree.Fill()
outputTree.AutoSave()

if not sample.isData:
  trueIntHist = sample.getTrueInteractions()
  outputFile.cd()
  trueIntHist.Write('nTrue')
outputFile.Close()
log.info('Finished')
