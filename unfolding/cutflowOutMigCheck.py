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
argParser.add_argument('--rec',       action='store_true', default=False,                help='run for reco instead')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Retrieve sample list, reducedTuples need to be created for the samples listed in tuples.conf
#
from ttg.samples.Sample import createSampleList, getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/flowtuples_2016.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/flowtuples_2017.conf'),
                              os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/flowtuples_2018.conf')
                              )

#
# Submit subjobs:
#   - each sample is splitted by the splitJobs parameter defined in tuples.conf, if a sample runs too slow raise the splitJobs parameter
#   - data is additional splitted per run to avoid too heavy chains to be loaded
#

args.subJob = 0

if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]
  if args.year:   sampleList = [s for s in sampleList if s.year == args.year]

  jobs = []
  for sample in sampleList:
    if not sample.splitJobs == 1: 
      log.warning('Do not split jobs here')
      continue
    jobs += [(sample.name, sample.year, 0)]
  submitJobs(__file__, ('sample', 'year', 'subJob'), jobs, argParser, subLog=args.type + ('_Rec' if args.rec else ''), jobLabel = "CF")
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

# if not args.overwrite and isValidRootFile(outputName):
#   log.info('Finished: valid outputfile already exists')
#   exit(0)

# outputFile = ROOT.TFile(outputName ,"RECREATE")
# outputFile.cd()


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



from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets, bJets, makeDeltaR
# from ttg.unfolding.PLobjectSelection import PLselectLeptons, PLselectPhotons, PLgoodJets, PLbJets, PLmakeInvariantMasses, PLmakeDeltaR
from ttg.unfolding.PLobjectSelection import PLselectLeptons, PLgoodJets, PLbJets, PLmakeInvariantMasses, PLmakeDeltaR
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

from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso



# PHOTON
# def PLphotonSelector(tree, index, n):
#   if abs(tree._pl_phEta[index]) > 2.5:                                                                 return False
#   if tree._pl_phPt[index] < 20:                                                                        return False
#   for i in [n.PLl1, n.PLl2]:
#     if deltaR(tree._pl_lEta[i], tree._pl_phEta[index], tree._pl_lPhi[i], tree._pl_phPhi[index]) < 0.4: return False
#   return True

# def PLselectPhotons(t, n):
#   t.PLphotons  = [p for p in range(t._pl_nPh) if PLphotonSelector(t, p, n)]
#   n.PLnphotons = len(t.PLphotons)
#   if n.PLnphotons == 1:
#     n.PLph    = t.PLphotons[0]
#     n.PLph_pt = t._pl_phPt[n.PLph]
#     n.PLph_Eta = t._pl_phEta[n.PLph]
#     return True
#   else:
#     return False

from ttg.tools.helpers import deltaR


def PLphotonSelector(tree, index, n):
  log.info('photon selector')
  if abs(tree._pl_phEta[index]) > 2.5:                                                                 return False
  log.info('photon passed eta cut')
  if tree._pl_phPt[index] < 20:                                                                        return False
  log.info('photon passed pt')
  for i in [n.PLl1, n.PLl2]:
    if deltaR(tree._pl_lEta[i], tree._pl_phEta[index], tree._pl_lPhi[i], tree._pl_phPhi[index]) < 0.4: return False
  log.info('photon passed cleaning cut')
  return True

leptonSF         = LeptonSF_MVA(sample.year)
photonSF         = PhotonSF(sample.year, "MVA" if (args.type.lower().count("photonmva") or args.type.lower().count("phomvasb")) else "CB")
pixelVetoSF      = pixelVetoSF(sample.year)
triggerEff       = TriggerEfficiency(sample.year, id = "MVA") 
btagSF           = BtagEfficiency(sample.year, id = "MVA")


# lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
lumiScales = {'2016':1., '2017':1., '2018':1.}
lumiScale = lumiScales[args.year]

########## START EVENT LOOP ##########
plCounter = [0. for i in range(20)]
recoCounter = [0. for i in range(20)]
plRecoCounter = [0. for i in range(20)]

log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob), selectionString=None):
  if c.GetEntry(i) < 0: 
    log.warning("problem reading entry, skipping")
    continue


  prefireWeight = 1. if args.year == '2018' else c._prefireWeight
  # phWeight = 1. if c.phWeight == 0. else c.phWeight
  # # eventWeight = generWeights*recoWeights

  try:
    c.lhePhPt = c._lhePt[[i for i in c._lhePdgId].index(22)]
  except:
    c.lhePhPt = 0.
  # This needs to remove events regardless of reco and fid cuts
  if pcut and not c.lhePhPt<100: continue


  c.puWeight     = puReweighting(c._nTrueInt)
  c.genWeight    = c._weight*lumiWeights[0]
  pli = iter(range(20))
  reci = iter(range(20))
  eventWeight = c.genWeight*lumiScale * c.puWeight*prefireWeight
  eventWeight = c.genWeight*lumiScale * c.puWeight*prefireWeight
# template
# eventWeight = c.genWeight*lumiScale * c.puWeight*c.lWeight*c.lTrackWeight*phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*c.PVWeight

##### reco selection and storing values #####


  recoCounter[reci.next()]+=eventWeight
  if not c._ttgEventType>2: continue
  recoCounter[reci.next()]+=eventWeight
  rec = selectLeptons(c, c, 2)
  if not rec: continue
  else:
    l1, l2, l1_pt, l2_pt   = c.l1, c.l2, c.l1_pt, c.l2_pt

    # c.lWeight        = leptonSF.getSF(c, l1, l1_pt)*leptonSF.getSF(c, l2, l2_pt)
    
    sf1, errSyst1, errStat1, errPS1, isMu1, isEl1 = leptonSF.getSF(c, l1, l1_pt)
    sf2, errSyst2, errStat2, errPS2, isMu2, isEl2 = leptonSF.getSF(c, l2, l2_pt)
    # newVars.lWeight            = sf1*sf2
    c.lWeight = sf1*sf2

    c.lTrackWeight = leptonTrackingSF.getSF(c, l1, l1_pt)*leptonTrackingSF.getSF(c, l2, l2_pt)

    # NOTE temporary fix 
    trigWeight, trigErrStat, trigErrSyst = triggerEff.getSF(c, l1_pt, l2_pt, c.isMuMu, c.isEMu, c.isEE)
    c.triggerWeight      = trigWeight

    eventWeight = c.genWeight*lumiScale *c.lWeight*c.lTrackWeight*c.triggerWeight*prefireWeight
    recoCounter[reci.next()]+=eventWeight
    rec = selectPhotons(c, c, 2, False)
  # trigger stuff is channel dependent --> must be done after lep sel
  trig = True
  if c.isEE   and not (c._passTrigger_ee or c._passTrigger_e):                        trig = False
  if c.isEMu  and not (c._passTrigger_em or c._passTrigger_e or c._passTrigger_m):    trig = False
  if c.isMuMu and not (c._passTrigger_mm or c._passTrigger_m):                        trig = False
  if not trig: continue
  else: recoCounter[reci.next()]+=eventWeight

  if not  c._passMETFilters:continue
  else: recoCounter[reci.next()]+=eventWeight

# pho selectionrion/requirement happens here
  if not rec: continue
  else:
    goodJets(c, c)
    bJets(c, c)
    makeInvariantMasses(c, c)
    makeDeltaR(c, c)
    c.bTagWeight =  btagSF.getBtagSF_1a('', c, c.dbjets)
    ph, ph_pt = c.ph, c.ph_pt
    c.phWeight     = photonSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1.
    c.PVWeight     = pixelVetoSF.getSF(c, ph, ph_pt) if len(c.photons) > 0 else 1.
    eventWeight = c.genWeight*lumiScale * c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*c.PVWeight
    recoCounter[reci.next()]+=eventWeight

    c.checkMatch, c.genuine = True, True
    c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False

    # log.info(c.ph)
    # log.info(c._phCutBasedMedium)
    if not c._phCutBasedMedium[c.ph]:                       continue
    else: recoCounter[reci.next()]+=eventWeight
    if abs(c._phEta[c.ph]) > 1.4442:                        continue
    else: recoCounter[reci.next()]+=eventWeight
    if not checkMatch(c):                                   continue
    else: recoCounter[reci.next()]+=eventWeight
    if not c.mll > 20:                                      continue
    else: recoCounter[reci.next()]+=eventWeight
    if not (abs(c.mll-91.1876)>15 or c.isEMu):              continue
    else: recoCounter[reci.next()]+=eventWeight
    if not (abs(c.mllg-91.1876)>15 or c.isEMu):             continue
    else: recoCounter[reci.next()]+=eventWeight
    # if not ((c.isEMu and c.njets>0) or (c.ndbjets>0)):      continue
    # else: recoCounter[reci.next()]+=eventWeight
    if not c.ndbjets>0:                                     continue
    else: recoCounter[reci.next()]+=eventWeight

  if c._jetPt[c.j1] < 300: continue
  recoCounter[reci.next()]+=eventWeight


##### PL selection and storing values #####
  # if not args.rec:

  # 
  
  plCounter[pli.next()]+=eventWeight
  if not c._ttgEventType>2: continue
  plCounter[pli.next()]+=eventWeight
  fid = PLselectLeptons(c, c)
  if not fid: continue
  else:
    plCounter[pli.next()]+=eventWeight

    # fid = PLselectPhotons(c, c)
# =========================
    log.info('========photon selection step=========')
    fid = False
    c.PLphotons  = [p for p in range(c._pl_nPh) if PLphotonSelector(c, p, c)]
    c.PLnphotons = len(c.PLphotons)
    if c.PLnphotons == 1:
      c.PLph    = c.PLphotons[0]
      c.PLph_pt = c._pl_phPt[c.PLph]
      c.PLph_Eta = c._pl_phEta[c.PLph]
      fid = True
    else: log.info('not exactly one photon')
# ============================
    
  if not fid: continue
  else:
    plCounter[pli.next()]+=eventWeight
    PLgoodJets(c, c)
    PLbJets(c, c)
    PLmakeInvariantMasses(c, c)
    PLmakeDeltaR(c, c)

  if abs(c._pl_phEta[c.PLph]) > 1.4442:                             continue
  else: plCounter[pli.next()]+=eventWeight
  if not c.PLmll > 20:                                              continue
  else: plCounter[pli.next()]+=eventWeight
  # if not (abs(c.PLmll-91.1876)>15 or c.PLisEMu):                    continue
  # else: plCounter[pli.next()]+=eventWeight
  # if not (abs(c.PLmllg-91.1876)>15 or c.PLisEMu):                   continue
  # else: plCounter[pli.next()]+=eventWeight
  # if not ((c.PLisEMu and c.PLnjets>0) or (c.PLndbjets>0)):          continue
  # else: plCounter[pli.next()]+=eventWeight
  if not c.PLndbjets>0:          continue
  else: plCounter[pli.next()]+=eventWeight




log.info(plCounter)
log.info(recoCounter)


  # outputTree.Fill()
# outputTree.AutoSave()
# outputFile.Close()
log.info('Finished')





# ########## RECO SELECTION ##########
# # def checkRec(c):
  # if c.failReco:                                          return False
  # if not c._phCutBasedMedium[c.ph]:                       return False
  # if abs(c._phEta[c.ph]) > 1.4442:                        return False
  # c.checkMatch, c.genuine = True, True
  # c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False
  # if not checkMatch(c):                                   return False
  # if not c.ph_pt > 20:                                    return False
  # if not ((c.isEMu and c.njets>0) or (c.ndbjets>0)):             return False
  # if not c.mll > 20:                                      return False
  # if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
  # if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False
  # return True


# ########## FIDUCIAL REGION ##########
# # def checkFid(c):
#   if c.failFid:                                                 return False
#   if abs(c._pl_phEta[c.PLph]) > 1.4442:                             return False
#   if not c.PLph_pt > 20:                                            return False
#   if not ((c.PLisEMu and c.PLnjets>0) or (c.PLndbjets>0)):                 return False
#   if not c.PLmll > 20:                                              return False
#   if not (abs(c.PLmll-91.1876)>15 or c.PLisEMu):                    return False
#   if not (abs(c.PLmllg-91.1876)>15 or c.PLisEMu):                   return False
#   return True













