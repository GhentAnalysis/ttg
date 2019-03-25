#! /usr/bin/env python

#
# Script to create additional variables in the trees and reduce it to manageable size
#


#
# Argument parser and logging
#
import os, argparse, itertools
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='year corresponding to the sample (16,17,18), * in samples/data/tuples_*.conf', choices=['16', '17', '18'])
argParser.add_argument('--type',      action='store',      default='eleSusyLoose-phoCB', help='Specify type of reducedTuple')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--splitData', action='store',      default=None,                 help='Splits the data in its separate runs')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

if args.sample and not args.year:
  log.info("If the sample is specified, the year needs to be specified as well, exiting")
  exit(0)

#
# Retrieve sample list, reducedTuples need to be created for the samples listed in tuples.conf
#
from ttg.samples.Sample import createSampleList, getSampleFromList
tupleFiles = {'16':os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_16.conf'),
              '17':os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_17.conf'),
              '18':os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_18.conf')}
sampleList = itertools.chain.from_iterable([createSampleList(tupleFiles[y], y) for y in tupleFiles.keys()])
runs = {"16":['B', 'C', 'D', 'E', 'F', 'G', 'H'], "17":['B', 'C', 'D', 'E', 'F'], "18":['A', 'B', 'C', 'D', 'E']}
#
# Submit subjobs:
#   - each sample is splitted by the splitJobs parameter defined in tuples.conf, if a sample runs too slow raise the splitJobs parameter
#   - data is additional splitted per run to avoid too heavy chains to be loaded
#   - skips the isr and fsr systematic samples when tuples for scale and resolution systematics are prepared
#
if not args.isChild and not args.subJob:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample and args.year: sampleList = [s for s in sampleList if s.name == args.sample and s.year == args.year]

  jobs = []
  for sample in sampleList:
    if (args.type.count('Scale') or args.type.count('Res')) and (sample.name.count('isr') or sample.name.count('fsr')): continue

    if sample.isData:
      if args.splitData in runs: splitData = [args.splitData]
      else:                      splitData = runs[args.year]
    else:                        splitData = [None]
    jobs += [(sample.name, sample.year, str(i), j) for i in xrange(sample.splitJobs) for j in splitData]
  submitJobs(__file__, ('sample', 'year', 'subJob', 'splitData'), jobs, argParser, subLog=args.type)
  exit(0)

#
# From here on we are in the subjob, first init the chain and the lumiWeight
#
import ROOT
ROOT.gROOT.SetBatch(True)

sample = getSampleFromList(sampleList, args.sample, args.year)
c      = sample.initTree(shortDebug=args.debug, splitData=args.splitData)
forSys = (args.type.count('Scale') or args.type.count('Res')) and (sample.name.count('isr') or sample.name.count('fsr'))  # Tuple is created for specific sys

if not sample.isData:
  lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in sample.getTotalWeights()]


#
# Create new reduced tree (except if it already exists and overwrite option is not used)
#
from ttg.tools.helpers import reducedTupleDir, isValidRootFile
outputId   = (args.splitData if args.splitData in runs[sample.year] else '') + str(args.subJob)
outputName = os.path.join(reducedTupleDir, sample.year, sample.productionLabel, args.type, sample.name, sample.name + '_' + outputId + '.root')

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
unusedBranches = ["HLT", "Flag", "HN", "tau", "Ewk", "lMuon", "miniIso", "leptonMva", "closest", "_pt", "decay"]
deleteBranches = ["Scale", "Res", "pass", "met", "POG", "lElectron"]
if not sample.isData:
  unusedBranches += ["gen_nL", "gen_l", "gen_met"]
  deleteBranches += ["heWeight", "gen_ph"]
for i in unusedBranches + deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 0)
outputTree = sample.chain.CloneTree(0)
for i in deleteBranches: sample.chain.SetBranchStatus("*"+i+"*", 1)


#
# Initialize reweighting functions
#

puData = {('16','central'):"PU_2016_36000_XSecCentral", ('16','up'):"PU_2016_36000_XSecUp", ('16','down'):"PU_2016_36000_XSecDown",
          ('17','central'):"PU_2016_36000_XSecCentral", ('17','up'):"PU_2016_36000_XSecUp", ('17','down'):"PU_2016_36000_XSecDown",
          ('18','central'):"PU_2016_36000_XSecCentral", ('18','up'):"PU_2016_36000_XSecUp", ('18','down'):"PU_2016_36000_XSecDown"}

from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting     = getReweightingFunction(sample.year, data=puData[(sample.year,'central')])
puReweightingUp   = getReweightingFunction(sample.year, data=puData[(sample.year,'up')])
puReweightingDown = getReweightingFunction(sample.year, data=puData[(sample.year,'down')])

from ttg.reduceTuple.leptonTrackingEfficiency import LeptonTrackingEfficiency
from ttg.reduceTuple.leptonSF import LeptonSF as LeptonSF
from ttg.reduceTuple.photonSF import PhotonSF as PhotonSF
# from ttg.reduceTuple.prefire  import Prefire  as Prefire
from ttg.reduceTuple.triggerEfficiency import TriggerEfficiency
from ttg.reduceTuple.btagEfficiency import BtagEfficiency
leptonTrackingSF = LeptonTrackingEfficiency(sample.year)
leptonSF         = LeptonSF(sample.year)
photonSF         = PhotonSF(sample.year)
# prefire          = Prefire(sample.year)
triggerEff       = TriggerEfficiency(sample.year)
btagSF           = BtagEfficiency(sample.year)


#
# Define new branches
#
newBranches  = ['ph/I', 'ph_pt/F', 'phJetDeltaR/F', 'phBJetDeltaR/F', 'matchedGenPh/I', 'matchedGenEle/I', 'nphotons/I']
newBranches += ['njets/I', 'j1/I', 'j2/I', 'ndbjets/I', 'dbj1/I', 'dbj2/I']
newBranches += ['l1/I', 'l2/I', 'looseLeptonVeto/O', 'l1_pt/F', 'l2_pt/F']
newBranches += ['mll/F', 'mllg/F', 'ml1g/F', 'ml2g/F', 'phL1DeltaR/F', 'phL2DeltaR/F', 'l1JetDeltaR/F', 'l2JetDeltaR/F', 'jjDeltaR/F']
newBranches += ['isEE/O', 'isMuMu/O', 'isEMu/O']

if not sample.isData:
  newBranches += ['genWeight/F', 'lTrackWeight/F', 'lWeight/F', 'puWeight/F', 'triggerWeight/F', 'phWeight/F', 'bTagWeight/F']
  newBranches += ['genPhDeltaR/F', 'genPhPassParentage/O', 'genPhMinDeltaR/F', 'genPhRelPt/F', 'genPhPt/F', 'genPhEta/F']
  # newBranches += ['prefireSF/F']
  if not forSys:
    for sys in ['JECUp', 'JECDown', 'JERUp', 'JERDown']:
      newBranches += ['njets_' + sys + '/I', 'ndbjets_' + sys +'/I', 'j1_' + sys + '/I', 'j2_' + sys + '/I', 'dbj1_' + sys + '/I', 'dbj2_' + sys + '/I']
      newBranches += ['phJetDeltaR_' + sys + '/F', 'phBJetDeltaR_' + sys + '/F', 'l1JetDeltaR_' + sys + '/F', 'l2JetDeltaR_' + sys + '/F']
    for var in ['Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd']:   newBranches += ['weight_q2_' + var + '/F']
    for i in range(0, 100):                              newBranches += ['weight_pdf_' + str(i) + '/F']
    for sys in ['Up', 'Down']:                           newBranches += ['lWeight' + sys + '/F', 'puWeight' + sys + '/F', 'triggerWeight' + sys + '/F', 'phWeight' + sys + '/F']
    for sys in ['lUp', 'lDown', 'bUp', 'bDown']:         newBranches += ['bTagWeight' + sys + '/F']

from ttg.tools.makeBranches import makeBranches
newVars = makeBranches(outputTree, newBranches)


#
# Replace branches for systematic runs
#
def switchBranches(default, variation):
  return lambda chain: setattr(chain, default, getattr(chain, variation))

branchModifications = []
for var in ['ScaleUp', 'ScaleDown', 'ResUp', 'ResDown']:
  if args.type.count('e'  + var): branchModifications += [switchBranches('_lPtCorr',  '_lPt' + var),  switchBranches('_lECorr',  '_lE' + var)]
  if args.type.count('ph' + var): branchModifications += [switchBranches('_phPtCorr', '_phPt' + var), switchBranches('_phECorr', '_phE' + var)]


#
# Get function calls to object selections and set selections based on the reducedTuple type
#
from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR
setIDSelection(c, args.type)


#
# Loop over the tree, skim, make new vars and add the weights
# --> for more details about the skims and new variables check the called functions in ttg.reduceTuple.objectSelection
#
log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None):
  c.GetEntry(i)
  for s in branchModifications: s(c)

  if not selectLeptons(c, newVars, 2):                continue
  if not selectPhotons(c, newVars, 2, sample.isData): continue

  if sample.isData:
    if not c._passMETFilters:                                                          continue
    if sample.name.count('DoubleMuon') and not c._passTrigger_mm:                              continue
    if sample.name.count('DoubleEG')   and not c._passTrigger_ee:                              continue
    if sample.name.count('MuonEG')     and not c._passTrigger_em:                              continue
    if sample.name.count('SingleMuon'):
      if newVars.isMuMu and not (not c._passTrigger_mm and c._passTrigger_m):                      continue
      if newVars.isEMu  and not (not c._passTrigger_em and c._passTrigger_m):                      continue
    if sample.name.count('SingleElectron'):
      if newVars.isEE   and not (not c._passTrigger_ee and c._passTrigger_e):                      continue
      if newVars.isEMu  and not (not c._passTrigger_em and c._passTrigger_e and not c._passTrigger_m): continue
  else:
    if not c._passMETFilters:                                                            continue
    if newVars.isEE   and not (c._passTrigger_ee or c._passTrigger_e):                             continue
    if newVars.isEMu  and not (c._passTrigger_em or c._passTrigger_e or c._passTrigger_m):             continue
    if newVars.isMuMu and not (c._passTrigger_mm or c._passTrigger_m):                             continue

  goodJets(c, newVars)
  bJets(c, newVars)
  makeInvariantMasses(c, newVars)
  makeDeltaR(c, newVars)

  if not sample.isData:
    newVars.genWeight    = c._weight*lumiWeights[0]
    # newVars.prefireSF    = prefire.getSF(c)

    # See https://twiki.cern.ch/twiki/bin/view/CMS/TopSystematics#Factorization_and_renormalizatio and https://twiki.cern.ch/twiki/bin/viewauth/CMS/LHEReaderCMSSW for order (index 0->id 1001, etc...)
    # Except when a sample does not have those weights stored (could occur for the minor backgrounds)
    if not forSys:
      for var, i in [('Fu', 1), ('Fd', 2), ('Ru', 3), ('RFu', 4), ('Rd', 6), ('RFd', 8)]:
        try:    setattr(newVars, 'weight_q2_' + var, c._weight*c._lheWeight[i]*lumiWeights[i])
        except: setattr(newVars, 'weight_q2_' + var, newVars.genWeight)

      for i in range(0, 100):
        try:    setattr(newVars, 'weight_pdf_' + str(i), c._weight*c._lheWeight[i+9]*lumiWeights[i+9])
        except: setattr(newVars, 'weight_pdf_' + str(i), newVars.genWeight)

    newVars.puWeight     = puReweighting(c._nTrueInt)
    newVars.puWeightUp   = puReweightingUp(c._nTrueInt)
    newVars.puWeightDown = puReweightingDown(c._nTrueInt)

    l1, l2               = newVars.l1, newVars.l2
    newVars.lWeight      = leptonSF.getSF(c, l1)*leptonSF.getSF(c, l2)
    newVars.lWeightUp    = leptonSF.getSF(c, l1, sigma=+1)*leptonSF.getSF(c, l2, sigma=+1)
    newVars.lWeightDown  = leptonSF.getSF(c, l1, sigma=-1)*leptonSF.getSF(c, l2, sigma=-1)
    newVars.lTrackWeight = leptonTrackingSF.getSF(c, l1)*leptonTrackingSF.getSF(c, l2)

    newVars.phWeight     = photonSF.getSF(c, newVars.ph) if len(c.photons) > 0 else 1
    newVars.phWeightUp   = photonSF.getSF(c, newVars.ph, sigma=+1) if len(c.photons) > 0 else 1
    newVars.phWeightDown = photonSF.getSF(c, newVars.ph, sigma=-1) if len(c.photons) > 0 else 1

    # method 1a
    for sys in ['', 'lUp', 'lDown', 'bUp', 'bDown']:
      setattr(newVars, 'bTagWeight' + sys, btagSF.getBtagSF_1a(sys, c, c.dbjets))

    trigWeight, trigErr        = triggerEff.getSF(c, l1, l2)
    newVars.triggerWeight      = trigWeight
    newVars.triggerWeightUp    = trigWeight+trigErr
    newVars.triggerWeightDown  = trigWeight-trigErr

  outputTree.Fill()
outputTree.AutoSave()
outputFile.Close()
log.info('Finished')
