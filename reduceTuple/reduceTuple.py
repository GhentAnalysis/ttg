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
argParser.add_argument('--type',      action='store',      default='phoCB',              help='Specify type of reducedTuple')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--splitData', action='store',      default=None,                 help='Splits the data in its separate runs')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
argParser.add_argument('--recTops',   action='store_true', default=False,                help='reconstruct tops, save top and neutrino kinematics')
argParser.add_argument('--singleJob', action='store_true', default=False,                help='submit one single subjob, be careful with this')
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
#   - skips the isr and fsr systematic samples when tuples for scale and resolution systematics are prepared
#

forSys = args.type.count('Scale') or args.type.count('Res')  # Tuple is created for specific sys


if args.singleJob and args.subJob and not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [(args.sample, args.year, args.subJob, args.splitData)]
  submitJobs(__file__, ('sample', 'year', 'subJob', 'splitData'), jobs, argParser, subLog=args.type, jobLabel = "RT")
  exit(0)

if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]
  if args.year:   sampleList = [s for s in sampleList if s.year == args.year]

  jobs = []
  for sample in sampleList:
    if (args.type.count('Scale') or args.type.count('Res')) and (sample.name.count('isr') or sample.name.count('fsr')): continue
    if (args.type.count('Scale') or args.type.count('Res')) and sample.isData: continue

    if sample.isData:
      if forSys: continue #no need to have data for systematics
      if args.splitData:          splitData = [args.splitData]
      elif sample.year == '2016': splitData = ['B', 'C', 'D', 'E', 'F', 'G', 'H']
      elif sample.year == '2017': splitData = ['B', 'C', 'D', 'E', 'F']
      elif sample.year == '2018': splitData = ['A', 'B', 'C', 'D']
    else:                         splitData = [None]
    jobs += [(sample.name, sample.year, str(i), j) for i in xrange(sample.splitJobs) for j in splitData]
  submitJobs(__file__, ('sample', 'year', 'subJob', 'splitData'), jobs, argParser, subLog=args.type, jobLabel = "RT")
  exit(0)


#
# From here on we are in the subjob, first init the chain and the lumiWeight
#
import ROOT
ROOT.gROOT.SetBatch(True)

sample = getSampleFromList(sampleList, args.sample, args.year)
c      = sample.initTree(shortDebug=args.debug, splitData=args.splitData)
c.year = sample.year #access to year wherever chain is passed to function, prevents having to pass year every time


if not sample.isData:
  lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in sample.getTotalWeights()]


#
# Create new reduced tree (except if it already exists and overwrite option is not used)
#
from ttg.tools.helpers import reducedTupleDir, isValidRootFile
outputId   = (args.splitData if args.splitData else '') + str(args.subJob)
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
# FIXME NOTE temporarily saving extra vars for MVA input check
# unusedBranches = ["HLT", "Flag", "HN", "tau", "Ewk", "lMuon", "miniIso", "closest", "_pt", "decay"]
# unusedBranches = ["HLT", "Flag", "HN", "tau", "Ewk", "lMuon", "decay"]
# deleteBranches = ["Scale", "Res", "pass", "met", "POG", "lElectron"]
# deleteBranches = ["Scale", "Res", "pass", "met", "lElectron"]
# deleteBranches = ["Scale", "Res", "pass", "met"]

unusedBranches = ["HLT", "Flag", "flag", "HN", "tau", "Ewk", "lMuon", "WOIso", "closest", "decay", "JECSources", 'jetPt_', 'corrMET' ]
deleteBranches = ["Scale", "Res", "pass", "met", "POG", "lElectron", "JECGrouped"]
if not sample.isData:
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
newBranches += ['njets/I', 'j1/I', 'j2/I', 'ndbjets/I', 'dbj1/I', 'dbj2/I']
newBranches += ['l1/I', 'l2/I', 'looseLeptonVeto/O', 'l1_pt/F', 'l2_pt/F']
newBranches += ['mll/F', 'mllg/F', 'ml1g/F', 'ml2g/F', 'phL1DeltaR/F', 'phL2DeltaR/F', 'l1JetDeltaR/F', 'l2JetDeltaR/F', 'jjDeltaR/F', 'j1_pt/F']
newBranches += ['isEE/O', 'isMuMu/O', 'isEMu/O']
if args.recTops:
  newBranches += ['top1Pt/F', 'top1Eta/F', 'top2Pt/F', 'top2Eta/F', 'nu1Pt/F', 'nu1Eta/F', 'nu2Pt/F', 'nu2Eta/F', 'topsReconst/O', 'liHo/F']


if not sample.isData:
  newBranches += ['genWeight/F', 'lTrackWeight/F', 'lWeight/F', 'puWeight/F', 'triggerWeight/F', 'phWeight/F', 'bTagWeight/F', 'PVWeight/F']
  newBranches += ['genPhDeltaR/F', 'genPhPassParentage/O', 'genPhMinDeltaR/F', 'genPhRelPt/F', 'genPhPt/F', 'genPhEta/F', 'lhePhPt/F', 'genPhMomPdg/I']
  if not forSys:

    for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']:
      newBranches += ['njets_' + sys + '/I', 'ndbjets_' + sys +'/I', 'j1_' + sys + '/I', 'j2_' + sys + '/I', 'dbj1_' + sys + '/I', 'dbj2_' + sys + '/I']
      newBranches += ['phJetDeltaR_' + sys + '/F', 'phBJetDeltaR_' + sys + '/F', 'l1JetDeltaR_' + sys + '/F', 'l2JetDeltaR_' + sys + '/F', 'j1_pt_' + sys + '/F']
    for sys in ['Absolute','BBEC1','EC2','FlavorQCD','HF','RelativeBal','Total','HFUC','AbsoluteUC','BBEC1UC','EC2UC','RelativeSampleUC']:
      for direc in ['Up','Down']:
        newBranches += ['njets_' + sys + direc +  '/I', 'ndbjets_' + sys + direc + '/I', 'j1_' + sys + direc +  '/I', 'j2_' + sys + direc +  '/I', 'dbj1_' + sys + direc +  '/I', 'dbj2_' + sys + direc +  '/I']
        newBranches += ['phJetDeltaR_' + sys + direc +  '/F', 'phBJetDeltaR_' + sys + direc +  '/F', 'l1JetDeltaR_' + sys + direc +  '/F', 'l2JetDeltaR_' + sys + direc +  '/F', 'j1_pt_' + sys + direc + '/F']

    for var in ['Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd']:   newBranches += ['weight_q2_' + var + '/F']
    for i in range(0, 100):                              newBranches += ['weight_pdf_' + str(i) + '/F']
    for sys in ['Up', 'Down']:                           newBranches += ['lWeightPSSys' + sys + '/F', 'lWeightElSyst' + sys + '/F','lWeightMuSyst' + sys + '/F','lWeightElStat' + sys + '/F','lWeightMuStat' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeightStatMM' + sys + '/F', 'triggerWeightStatEM' + sys + '/F', 'triggerWeightStatEE' + sys + '/F', 'triggerWeightSyst' + sys + '/F', 'phWeight' + sys + '/F', 'ISRWeight' + sys + '/F', 'FSRWeight' + sys + '/F',  'PVWeight' + sys + '/F', 'lTrackWeight' + sys + '/F']
    for sys in ['lUp', 'lDown', 'bCOUp', 'bCODown', 'bUCUp', 'bUCDown']:         newBranches += ['bTagWeight' + sys + '/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)


#
# Replace branches for systematic runs
#
# def switchBranches(default, variation):
#   return lambda chain: setattr(chain, default, getattr(chain, variation))


c.egvar = ([var for var in ['ScaleUp', 'ScaleDown', 'ResUp', 'ResDown'] if 'eph' + var in args.type] + ['Corr'])[0]
c.muvar = ([var for var in ['ScaleUp', 'ScaleDown'] if 'mu' + var in args.type] + ['Corr'])[0]

newVars.egvar = c.egvar
newVars.muvar = c.muvar

pcut = sample.name.count('PCUT')

# branchModifications = []
# for var in ['ScaleUp', 'ScaleDown', 'ResUp', 'ResDown']:
#   if args.type.count('eph'  + var): branchModifications += [switchBranches('_lPtCorr',  '_lPt' + var),  switchBranches('_lECorr',  '_lE' + var), switchBranches('_phPtCorr', '_phPt' + var), switchBranches('_phECorr', '_phE' + var)]

#
# Get function calls to object selections and set selections based on the reducedTuple type
#
from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR, reconstTops, getTopKinFit
setIDSelection(c, args.type)


#
# Initialize pile-up reweighting functions
#
from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting     = getReweightingFunction(sample.year, 'central')
puReweightingUp   = getReweightingFunction(sample.year, 'up')
puReweightingDown = getReweightingFunction(sample.year, 'down')

from ttg.reduceTuple.leptonTrackingEfficiency import LeptonTrackingEfficiency
from ttg.reduceTuple.leptonSF_MVA import LeptonSF_MVA as LeptonSF_MVA
from ttg.reduceTuple.photonSF import PhotonSF as PhotonSF
from ttg.reduceTuple.pixelVetoSF import pixelVetoSF as pixelVetoSF
from ttg.reduceTuple.triggerEfficiency import TriggerEfficiency
from ttg.reduceTuple.btagEfficiency import BtagEfficiency
leptonTrackingSF = LeptonTrackingEfficiency(sample.year)

leptonID = 'MVA'

leptonSF         = LeptonSF_MVA(sample.year)
photonSF         = PhotonSF(sample.year, "MVA" if (args.type.lower().count("photonmva") or args.type.lower().count("phomvasb")) else "CB")
pixelVetoSF      = pixelVetoSF(sample.year)
triggerEff       = TriggerEfficiency(sample.year, id = leptonID) 
btagSF           = BtagEfficiency(sample.year, id = leptonID)

#
# Loop over the tree, skim, make new vars and add the weights
# --> for more details about the skims and new variables check the called functions in ttg.reduceTuple.objectSelection
#
if args.recTops:
  kf = getTopKinFit()


isTTG = sample.name.count('TTGamma')

log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None):
  if c.GetEntry(i) < 0: 
    log.warning("problem reading entry, skipping")
    continue
  # for s in branchModifications: s(c)

  if not selectLeptons(c, newVars, 2):                continue
  if not selectPhotons(c, newVars, 2, sample.isData): continue
  if not c._passMETFilters:                           continue

  if pcut and not newVars.lhePhPt<100: continue
  
  if sample.isData:
    if sample.name.count('DoubleMuon') and not c._passTrigger_mm:                                      continue
    if sample.name.count('DoubleEG')   and not c._passTrigger_ee:                                      continue  #does not exist in 2018
    if sample.name.count('MuonEG')     and not c._passTrigger_em:                                      continue
    if sample.name.count('SingleMuon'):
      if newVars.isMuMu and not (not c._passTrigger_mm and c._passTrigger_m):                          continue
      if newVars.isEMu  and not (not c._passTrigger_em and c._passTrigger_m):                          continue
    if sample.name.count('SingleElectron'):  #does not exist in 2018
      if newVars.isEE   and not (not c._passTrigger_ee and c._passTrigger_e):                          continue
      if newVars.isEMu  and not (not c._passTrigger_em and c._passTrigger_e and not c._passTrigger_m): continue
    if sample.name.count('EGamma'):   # 2018 only
      if newVars.isEE   and not (c._passTrigger_ee or c._passTrigger_e):                               continue
      # if newVars.isEMu  and not (not c._passTrigger_em and c._passTrigger_e and not c._passTrigger_m): continue
      if newVars.isEMu  and not ((c._passTrigger_e or c._passTrigger_ee) and not c._passTrigger_em and not c._passTrigger_m): continue
  else:
    if newVars.isEE   and not (c._passTrigger_ee or c._passTrigger_e):                                 continue
    if newVars.isEMu  and not (c._passTrigger_em or c._passTrigger_e or c._passTrigger_m):             continue
    if newVars.isMuMu and not (c._passTrigger_mm or c._passTrigger_m):                                 continue

  # if it's data we don't want JEC variations either
  goodJets(c, newVars, forSys=(forSys or sample.isData))
  bJets(c, newVars, forSys=(forSys or sample.isData))
  makeInvariantMasses(c, newVars)
  makeDeltaR(c, newVars, forSys=(forSys or sample.isData))

  if not sample.isData:
    newVars.genWeight    = c._weight*lumiWeights[0]

    # See https://twiki.cern.ch/twiki/bin/view/CMS/TopSystematics#Factorization_and_renormalizatio and https://twiki.cern.ch/twiki/bin/viewauth/CMS/LHEReaderCMSSW for order (index 0->id 1001, etc...)
    # Except when a sample does not have those weights stored (could occur for the minor backgrounds)
    if not forSys:
      # TTG
      if isTTG:
        for var, i in [('Fu', 15), ('Fd', 30), ('Ru', 5), ('RFu', 20), ('Rd', 10), ('RFd', 40)]:
          try:    setattr(newVars, 'weight_q2_' + var, c._weight*c._lheWeight[i]*lumiWeights[i])
          except: setattr(newVars, 'weight_q2_' + var, newVars.genWeight)

        for i in range(0, 100):
          try:    setattr(newVars, 'weight_pdf_' + str(i), c._weight*c._lheWeight[i+45]*lumiWeights[i+45])
          except: setattr(newVars, 'weight_pdf_' + str(i), newVars.genWeight)

        # alpha s variations needed separately, or = isr, fsr variations?
        # 146 and 147, but need to check which is up, which is down
        # try:    
        #   setattr(newVars, 'weight_asDown' + str(i), c._weight*c._lheWeight[i+45]*lumiWeights[i+45])
        #   setattr(newVars, 'weight_asUp' + str(i), c._weight*c._lheWeight[i+45]*lumiWeights[i+45])
        # except: 
        #   setattr(newVars, 'weight_asDown' + str(i), newVars.genWeight)
        #   setattr(newVars, 'weight_asUp' + str(i), newVars.genWeight)


      # other samples
      else:
        for var, i in [('Fu', 1), ('Fd', 2), ('Ru', 3), ('RFu', 4), ('Rd', 6), ('RFd', 8)]:
          try:    setattr(newVars, 'weight_q2_' + var, c._weight*c._lheWeight[i]*lumiWeights[i])
          except: setattr(newVars, 'weight_q2_' + var, newVars.genWeight)

        for i in range(0, 100):
          try:    setattr(newVars, 'weight_pdf_' + str(i), c._weight*c._lheWeight[i+9]*lumiWeights[i+9])
          except: setattr(newVars, 'weight_pdf_' + str(i), newVars.genWeight)

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



    l1, l2, l1_pt, l2_pt   = newVars.l1, newVars.l2, newVars.l1_pt, newVars.l2_pt
    # newVars.lWeight        = leptonSF.getSF(c, l1, l1_pt)*leptonSF.getSF(c, l2, l2_pt)
    # newVars.lWeightElSystUp    = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst=+1., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst=+1., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightElSystDown  = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst=-1., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst=-1., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightMuSystUp    = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst=+1., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst=+1., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightMuSystDown  = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst=-1., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst=-1., elSigmaStat= 0., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightElStatUp    = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat=+1., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat=+1., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightElStatDown  = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat=-1., muSigmaStat= 0., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat=-1., muSigmaStat= 0., muSigmaPSSys=0)
    # newVars.lWeightMuStatUp    = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=+1., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=+1., muSigmaPSSys=0)
    # newVars.lWeightMuStatDown  = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=-1., muSigmaPSSys=0)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=-1., muSigmaPSSys=0)
    # newVars.lWeightPSSysUp     = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=0., muSigmaPSSys=+1.)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=0., muSigmaPSSys=+1.)
    # newVars.lWeightPSSysDown   = leptonSF.getSF(c, l1, l1_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=0., muSigmaPSSys=-1.)*leptonSF.getSF(c, l2, l2_pt, elSigmaSyst= 0., muSigmaSyst= 0., elSigmaStat= 0., muSigmaStat=0., muSigmaPSSys=-1.)

    sf1, errSyst1, errStat1, errPS1, isMu1, isEl1 = leptonSF.getSF(c, l1, l1_pt)
    sf2, errSyst2, errStat2, errPS2, isMu2, isEl2 = leptonSF.getSF(c, l2, l2_pt)
    newVars.lWeight        = sf1*sf2
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

    ph, ph_pt = newVars.ph, newVars.ph_pt
    newVars.phWeight     = photonSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
    newVars.phWeightUp   = photonSF.getSF(c, ph, ph_pt, sigma=+1) if len(c.photons) > 0 else 1
    newVars.phWeightDown = photonSF.getSF(c, ph, ph_pt, sigma=-1) if len(c.photons) > 0 else 1

    newVars.PVWeight     = pixelVetoSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1
    newVars.PVWeightUp   = pixelVetoSF.getSF(c, ph, ph_pt, sigma=+1) if len(c.photons) > 0 else 1
    newVars.PVWeightDown = pixelVetoSF.getSF(c, ph, ph_pt, sigma=-1) if len(c.photons) > 0 else 1

    # method 1a
    for sys in ['', 'lUp', 'lDown', 'bCOUp', 'bCODown', 'bUCUp', 'bUCDown']:
      setattr(newVars, 'bTagWeight' + sys, btagSF.getBtagSF_1a(sys, c, c.dbjets))

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

    if args.recTops:
      reconstTops(kf, c, newVars)

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
