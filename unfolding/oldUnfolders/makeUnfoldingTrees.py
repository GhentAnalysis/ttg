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


c.egvar = ([var for var in ['ScaleUp', 'ScaleDown', 'ResUp', 'ResDown'] if 'eph' + var in args.type] + ['Corr'])[0]
c.muvar = ([var for var in ['ScaleUp', 'ScaleDown'] if 'mu' + var in args.type] + ['Corr'])[0]

pcut = sample.name.count('PCUT')

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

unusedBranches = ["HLT", "Flag", "HN", "tau", "lMuon", "decay", "tau", "Up", "Down", "_closest"]
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
newBranches += ['njets/I', 'j1/I', 'j2/I', 'ndbjets/I', 'dbj1/I', 'dbj2/I']
newBranches += ['PLnjets/I', 'PLndbjets/I', 'PLj1/I', 'PLj2/I']
newBranches += ['l1/I', 'l2/I', 'looseLeptonVeto/O', 'l1_pt/F', 'l2_pt/F']
newBranches += ['PLl1/I', 'PLl2/I', 'PLl1_pt/F', 'PLl2_pt/F']
newBranches += ['mll/F', 'mllg/F', 'ml1g/F', 'ml2g/F', 'phL1DeltaR/F', 'phL2DeltaR/F', 'l1JetDeltaR/F', 'l2JetDeltaR/F', 'jjDeltaR/F']
newBranches += ['PLmll/F', 'PLmllg/F', 'PLml1g/F', 'PLml2g/F', 'PLphL1DeltaR/F', 'PLphL2DeltaR/F', 'PLl1JetDeltaR/F', 'PLl2JetDeltaR/F', 'PLjjDeltaR/F']
newBranches += ['isEE/O', 'isMuMu/O', 'isEMu/O']
newBranches += ['PLisEE/O', 'PLisMuMu/O', 'PLisEMu/O']
newBranches += ['failReco/O','failFid/O']
# newBranches += ['failReco/O', 'failPLMatch/O']
# newBranches += ['genWeight/F']
newBranches += ['genWeight/F', 'lTrackWeight/F', 'lWeight/F', 'puWeight/F', 'triggerWeight/F', 'phWeight/F', 'bTagWeight/F', 'PVWeight/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)

newVars.egvar = c.egvar
newVars.muvar = c.muvar

from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR
from ttg.unfolding.PLobjectSelection import PLselectLeptons, PLselectPhotons, PLgoodJets, PLbJets, PLmakeInvariantMasses, PLmakeDeltaR
#
# Start selection
#

setIDSelection(c, 'phoCB')


##### load weight getters #####
from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting     = getReweightingFunction(sample.year, 'central')

from ttg.reduceTuple.leptonTrackingEfficiency import LeptonTrackingEfficiency
from ttg.reduceTuple.leptonSF import LeptonSF as LeptonSF
from ttg.reduceTuple.leptonSF_MVA import LeptonSF_MVA as LeptonSF_MVA
from ttg.reduceTuple.photonSF import PhotonSF as PhotonSF
from ttg.reduceTuple.pixelVetoSF import pixelVetoSF as pixelVetoSF
from ttg.reduceTuple.triggerEfficiency import TriggerEfficiency
from ttg.reduceTuple.btagEfficiency import BtagEfficiency
leptonTrackingSF = LeptonTrackingEfficiency(sample.year)

# leptonID = 'MVA' if args.type.lower().count('leptonmva') else 'POG'

# leptonSF         = LeptonSF_MVA(sample.year) if leptonID=='MVA' else LeptonSF(sample.year)
leptonSF         = LeptonSF_MVA(sample.year)
photonSF         = PhotonSF(sample.year, "MVA" if (args.type.lower().count("photonmva") or args.type.lower().count("phomvasb")) else "CB")
pixelVetoSF      = pixelVetoSF(sample.year)
triggerEff       = TriggerEfficiency(sample.year, id = "MVA") 
btagSF           = BtagEfficiency(sample.year, id = "MVA")



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
  # This needs to remove events regardless of reco and fid cuts
  if pcut and not newVars.lhePhPt<100: continue


  newVars.ph = 99
  newVars.ph_pt = -99.
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

##### reco selection and storing values #####
  lepSel = selectLeptons(c, newVars, 2)
  if lepSel:
    phoSel = selectPhotons(c, newVars, 2, False)
  else: phoSel = False
  reco = phoSel
  if reco:
    if newVars.isEE   and not (c._passTrigger_ee or c._passTrigger_e):                        reco = False
    if newVars.isEMu  and not (c._passTrigger_em or c._passTrigger_e or c._passTrigger_m):    reco = False
    if newVars.isMuMu and not (c._passTrigger_mm or c._passTrigger_m):                        reco = False
    if not  c._passMETFilters:                                                                reco = False
  if reco:
    goodJets(c, newVars)
    bJets(c, newVars)
    makeInvariantMasses(c, newVars)
    makeDeltaR(c, newVars)
  newVars.failReco = not reco

  if not reco and not fid: continue    #events failing both reco and fiducial selection are not needed


  newVars.puWeight     = puReweighting(c._nTrueInt)

  if lepSel:
    l1, l2, l1_pt, l2_pt   = newVars.l1, newVars.l2, newVars.l1_pt, newVars.l2_pt
    newVars.lWeight        = leptonSF.getSF(c, l1, l1_pt)*leptonSF.getSF(c, l2, l2_pt)
    newVars.lTrackWeight = leptonTrackingSF.getSF(c, l1, l1_pt)*leptonTrackingSF.getSF(c, l2, l2_pt)
    trigWeight, trigErr        = triggerEff.getSF(c, l1, l2, l1_pt, l2_pt)
    newVars.triggerWeight      = trigWeight
  else:
    newVars.lWeight        = 1.
    newVars.lTrackWeight   = 1.
    newVars.triggerWeight      = 1.
  if phoSel:
    ph, ph_pt = newVars.ph, newVars.ph_pt
    newVars.phWeight     = photonSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
    newVars.PVWeight     = pixelVetoSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
  else:
    newVars.phWeight     = 1.
    newVars.PVWeight     = 1.

  # method 1a
  if reco:
    newVars.bTagWeight =  btagSF.getBtagSF_1a('', c, c.dbjets)
  else:
    newVars.bTagWeight =  1.

  newVars.genWeight    = c._weight*lumiWeights[0]

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
log.info('Finished')

