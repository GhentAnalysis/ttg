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
forSys = args.type.count('Scale') or args.type.count('Res')  # Tuple is created for specific sys
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

sample = getSampleFromList(sampleList, args.sample, args.year)
c      = sample.initTree(shortDebug=args.debug)
c.year = sample.year #access to year wherever chain is passed to function, prevents having to pass year every time


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
newBranches += ['njets/I', 'j1/I', 'j2/I', 'ndbjets/I', 'dbj1/I', 'dbj2/I']
newBranches += ['PLnjets/I', 'PLndbjets/I', 'PLj1/I', 'PLj2/I']
newBranches += ['l1/I', 'l2/I', 'looseLeptonVeto/O', 'l1_pt/F', 'l2_pt/F']
newBranches += ['PLl1/I', 'PLl2/I', 'PLl1_pt/F', 'PLl2_pt/F']
newBranches += ['mll/F', 'mllg/F', 'ml1g/F', 'ml2g/F', 'phL1DeltaR/F', 'phL2DeltaR/F', 'l1JetDeltaR/F', 'l2JetDeltaR/F', 'jjDeltaR/F', 'j1_pt/F']
newBranches += ['PLmll/F', 'PLmllg/F', 'PLml1g/F', 'PLml2g/F', 'PLphL1DeltaR/F', 'PLphL2DeltaR/F', 'PLl1JetDeltaR/F', 'PLl2JetDeltaR/F', 'PLjjDeltaR/F']
newBranches += ['isEE/O', 'isMuMu/O', 'isEMu/O']
newBranches += ['PLisEE/O', 'PLisMuMu/O', 'PLisEMu/O']
newBranches += ['failReco/O','failFid/O']
# newBranches += ['failReco/O', 'failPLMatch/O']
# newBranches += ['genWeight/F']
newBranches += ['genWeight/F', 'lTrackWeight/F', 'lWeight/F', 'puWeight/F', 'triggerWeight/F', 'phWeight/F', 'bTagWeight/F', 'PVWeight/F']
if not forSys:
  for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']:
    newBranches += ['njets_' + sys + '/I', 'ndbjets_' + sys +'/I', 'j1_' + sys + '/I', 'j2_' + sys + '/I', 'dbj1_' + sys + '/I', 'dbj2_' + sys + '/I']
    newBranches += ['phJetDeltaR_' + sys + '/F', 'phBJetDeltaR_' + sys + '/F', 'l1JetDeltaR_' + sys + '/F', 'l2JetDeltaR_' + sys + '/F', 'j1_pt_' + sys + '/F']
  for sys in ['Absolute','BBEC1','EC2','FlavorQCD','HF','RelativeBal','Total','HFUC','AbsoluteUC','BBEC1UC','EC2UC','RelativeSampleUC']:
    for direc in ['Up','Down']:
      newBranches += ['njets_' + sys + direc +  '/I', 'ndbjets_' + sys + direc + '/I', 'j1_' + sys + direc +  '/I', 'j2_' + sys + direc +  '/I', 'dbj1_' + sys + direc +  '/I', 'dbj2_' + sys + direc +  '/I']
      newBranches += ['phJetDeltaR_' + sys + direc +  '/F', 'phBJetDeltaR_' + sys + direc +  '/F', 'l1JetDeltaR_' + sys + direc +  '/F', 'l2JetDeltaR_' + sys + direc +  '/F', 'j1_pt_' + sys + direc + '/F']

  for var in ['Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd']:   newBranches += ['weight_q2_' + var + '/F']
  for var in ['Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd']:   newBranches += ['weight_q2Sc_' + var + '/F']
  for i in range(0, 100):                              newBranches += ['weight_pdf_' + str(i) + '/F']
  for i in range(0, 100):                              newBranches += ['weight_pdfSc_' + str(i) + '/F']
  for sys in ['Up', 'Down']:                           newBranches += ['lWeightPSSys' + sys + '/F', 'lWeightElSyst' + sys + '/F','lWeightMuSyst' + sys + '/F','lWeightElStat' + sys + '/F','lWeightMuStat' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeightStatMM' + sys + '/F', 'triggerWeightStatEM' + sys + '/F', 'triggerWeightStatEE' + sys + '/F', 'triggerWeightSyst' + sys + '/F', 'phWeight' + sys + '/F', 'ISRWeight' + sys + '/F', 'FSRWeight' + sys + '/F',  'PVWeight' + sys + '/F', 'lTrackWeight' + sys + '/F']
  for sys in ['lUp', 'lDown', 'bCOUp', 'bCODown', 'bUCUp', 'bUCDown']:         newBranches += ['bTagWeight' + sys + '/F']


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
puReweightingUp   = getReweightingFunction(sample.year, 'up')
puReweightingDown = getReweightingFunction(sample.year, 'down')

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

isNLO = sample.name.count('ttgjets')

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
    goodJets(c, newVars, forSys = forSys)
    bJets(c, newVars, forSys = forSys)
    makeInvariantMasses(c, newVars)
    makeDeltaR(c, newVars, forSys = forSys)
  newVars.failReco = not reco

  if not reco and not fid: continue    #events failing both reco and fiducial selection are not needed


  if not forSys:
    if not isNLO:
      for var, i in [('Fu', 15), ('Fd', 30), ('Ru', 5), ('RFu', 20), ('Rd', 10), ('RFd', 40)]:
        try:    
          setattr(newVars, 'weight_q2_' + var, c._weight*c._lheWeight[i]*lumiWeights[i])
          setattr(newVars, 'weight_q2Sc_' + var, c._weight*c._lheWeight[i]*lumiWeights[0])
        except: 
          setattr(newVars, 'weight_q2_' + var, newVars.genWeight)
          setattr(newVars, 'weight_q2Sc_' + var, newVars.genWeight)

      for i in range(0, 100):
        try:    
          setattr(newVars, 'weight_pdf_' + str(i), c._weight*c._lheWeight[i+45]*lumiWeights[i+45])
          setattr(newVars, 'weight_pdfSc_' + str(i), c._weight*c._lheWeight[i+45]*lumiWeights[0])
        except: 
          setattr(newVars, 'weight_pdf_' + str(i), newVars.genWeight)
          setattr(newVars, 'weight_pdfSc_' + str(i), newVars.genWeight)
    else: # numbering is different for NLO samples
      for var, i in [('Fu', 1), ('Fd', 2), ('Ru', 3), ('RFu', 4), ('Rd', 6), ('RFd', 8)]:
        try:    
          setattr(newVars, 'weight_q2_' + var, c._weight*c._lheWeight[i]*lumiWeights[i])
          setattr(newVars, 'weight_q2Sc_' + var, c._weight*c._lheWeight[i]*lumiWeights[0])
        except: 
          setattr(newVars, 'weight_q2_' + var, newVars.genWeight)
          setattr(newVars, 'weight_q2Sc_' + var, newVars.genWeight)

      for i in range(0, 100):
        try:    
          setattr(newVars, 'weight_pdf_' + str(i), c._weight*c._lheWeight[i+9]*lumiWeights[i+9])
          setattr(newVars, 'weight_pdfSc_' + str(i), c._weight*c._lheWeight[i+9]*lumiWeights[0])
        except: 
          setattr(newVars, 'weight_pdf_' + str(i), newVars.genWeight)
          setattr(newVars, 'weight_pdfSc_' + str(i), newVars.genWeight)


    try:
      # corresponds to 2 - 1/2 variations, recommended see talk  
      # https://indico.cern.ch/event/848486/contributions/3610537/attachments/1948613/3233682/TopSystematics_2019_11_20.pdf
      newVars.ISRWeightDown = c._psWeight[6]
      newVars.FSRWeightDown = c._psWeight[7]
      newVars.ISRWeightUp   = c._psWeight[8]
      newVars.FSRWeightUp   = c._psWeight[9]
    except:
      newVars.ISRWeightDown = 1.
      newVars.FSRWeightDown = 1.
      newVars.ISRWeightUp   = 1.
      newVars.FSRWeightUp   = 1.


  newVars.puWeight     = puReweighting(c._nTrueInt)
  newVars.puWeightUp   = puReweightingUp(c._nTrueInt)
  newVars.puWeightDown = puReweightingDown(c._nTrueInt)


  if lepSel:
    l1, l2, l1_pt, l2_pt   = newVars.l1, newVars.l2, newVars.l1_pt, newVars.l2_pt

    sf1, errSyst1, errStat1, errPS1, isMu1, isEl1 = leptonSF.getSF(c, l1, l1_pt)
    sf2, errSyst2, errStat2, errPS2, isMu2, isEl2 = leptonSF.getSF(c, l2, l2_pt)
    newVars.lWeight            = sf1*sf2
    newVars.lWeightElSystUp    = sf1*(1. + ( 1*errSyst1*isEl1)) * sf2*(1. +  (1*errSyst2*isEl2))
    newVars.lWeightElSystDown  = sf1*(1. + (-1*errSyst1*isEl1)) * sf2*(1. + (-1*errSyst2*isEl2))
    newVars.lWeightMuSystUp    = sf1*(1. +  (1*errSyst1*isMu1)) * sf2*(1. +  (1*errSyst2*isMu2))
    newVars.lWeightMuSystDown  = sf1*(1. + (-1*errSyst1*isMu1)) * sf2*(1. + (-1*errSyst2*isMu2))
    newVars.lWeightElStatUp    = sf1*(1. +  (1*errStat1*isEl1)) * sf2*(1. +  (1*errStat2*isEl2))
    newVars.lWeightElStatDown  = sf1*(1. + (-1*errStat1*isEl1)) * sf2*(1. + (-1*errStat2*isEl2))
    newVars.lWeightMuStatUp    = sf1*(1. +  (1*errStat1*isMu1)) * sf2*(1. +  (1*errStat2*isMu2))
    newVars.lWeightMuStatDown  = sf1*(1. + (-1*errStat1*isMu1)) * sf2*(1. + (-1*errStat2*isMu2))
    newVars.lWeightPSSysUp     = sf1*(1. +  (1*errPS1*isMu1))   * sf2*(1. +  (1*errPS2*isMu2))
    newVars.lWeightPSSysDown   = sf1*(1. + (-1*errPS1*isMu1))   * sf2*(1. + (-1*errPS2*isMu2))


    newVars.lTrackWeight = leptonTrackingSF.getSF(c, l1, l1_pt)*leptonTrackingSF.getSF(c, l2, l2_pt)
    newVars.lTrackWeightUp   = leptonTrackingSF.getSF(c, l1, l1_pt, sigma=1) *leptonTrackingSF.getSF(c, l2, l2_pt, sigma=1)
    newVars.lTrackWeightDown = leptonTrackingSF.getSF(c, l1, l1_pt, sigma=-1)*leptonTrackingSF.getSF(c, l2, l2_pt, sigma=-1)

    trigWeight, trigErrStat, trigErrSyst = triggerEff.getSF(c, l1_pt, l2_pt, newVars.isMuMu, newVars.isEMu, newVars.isEE)
    newVars.triggerWeight           = trigWeight
    newVars.triggerWeightStatMMUp   = trigWeight + (+trigErrStat if newVars.isMuMu else 0.)
    newVars.triggerWeightStatMMDown = trigWeight + (-trigErrStat if newVars.isMuMu else 0.)
    newVars.triggerWeightStatEMUp   = trigWeight + (+trigErrStat if newVars.isEMu  else 0.)
    newVars.triggerWeightStatEMDown = trigWeight + (-trigErrStat if newVars.isEMu  else 0.)
    newVars.triggerWeightStatEEUp   = trigWeight + (+trigErrStat if newVars.isEE   else 0.)
    newVars.triggerWeightStatEEDown = trigWeight + (-trigErrStat if newVars.isEE   else 0.)
    newVars.triggerWeightSystUp     = trigWeight+trigErrSyst
    newVars.triggerWeightSystDown   = trigWeight-trigErrSyst

  else:
    newVars.lWeight            = 1.
    newVars.lWeightElSystUp    = 1.
    newVars.lWeightElSystDown  = 1.
    newVars.lWeightMuSystUp    = 1.
    newVars.lWeightMuSystDown  = 1.
    newVars.lWeightElStatUp    = 1.
    newVars.lWeightElStatDown  = 1.
    newVars.lWeightMuStatUp    = 1.
    newVars.lWeightMuStatDown  = 1.
    newVars.lWeightPSSysUp     = 1.
    newVars.lWeightPSSysDown   = 1.
    newVars.lTrackWeight = 1.
    newVars.triggerWeight           = 1.
    newVars.triggerWeightStatMMUp   = 1.
    newVars.triggerWeightStatMMDown = 1.
    newVars.triggerWeightStatEMUp   = 1.
    newVars.triggerWeightStatEMDown = 1.
    newVars.triggerWeightStatEEUp   = 1.
    newVars.triggerWeightStatEEDown = 1.
    newVars.triggerWeightSystUp     = 1.
    newVars.triggerWeightSystDown   = 1.

  if phoSel:
    ph, ph_pt = newVars.ph, newVars.ph_pt
    newVars.phWeight     = photonSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
    newVars.phWeightUp   = photonSF.getSF(c, ph, ph_pt, sigma=+1) if len(c.photons) > 0 else 1
    newVars.phWeightDown = photonSF.getSF(c, ph, ph_pt, sigma=-1) if len(c.photons) > 0 else 1

    newVars.PVWeight     = pixelVetoSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
    newVars.PVWeightUp   = pixelVetoSF.getSF(c, ph, ph_pt, sigma=+1) if len(c.photons) > 0 else 1
    newVars.PVWeightDown = pixelVetoSF.getSF(c, ph, ph_pt, sigma=-1) if len(c.photons) > 0 else 1
  else:
    newVars.phWeight     = 1.
    newVars.phWeightUp   = 1.
    newVars.phWeightDown = 1.
    newVars.PVWeight     = 1.
    newVars.PVWeightUp   = 1.
    newVars.PVWeightDown = 1.


    # method 1a
  if reco:
    for sys in ['', 'lUp', 'lDown', 'bCOUp', 'bCODown', 'bUCUp', 'bUCDown']:
      setattr(newVars, 'bTagWeight' + sys, btagSF.getBtagSF_1a(sys, c, c.dbjets))
  else:
    for sys in ['', 'lUp', 'lDown', 'bCOUp', 'bCODown', 'bUCUp', 'bUCDown']:
      setattr(newVars, 'bTagWeight' + sys, 1.)

  newVars.genWeight    = c._weight*lumiWeights[0]

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
log.info('Finished')

