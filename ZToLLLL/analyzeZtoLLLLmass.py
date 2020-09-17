#!/usr/bin/env python
import ROOT
import sys, os
import array
import math

#
# Argument parser and logging
#
import os, argparse, sys
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',         nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--year',           action='store',      default=None)
argParser.add_argument('--sample',         action='store',      default=None,           help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--subJob',         action='store',      default=None,           help='The xth subjob for a sample')
argParser.add_argument('--splitData',      action='store',      default=None,           help='Splits the data in its separate runs')
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--dyExternal',     action='store_true', default=False)
argParser.add_argument('--overlapRemoved', action='store_true', default=False)
argParser.add_argument('--dyInternal',     action='store_true', default=False)
argParser.add_argument('--dyExternalAll',  action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,          help='do not launch subjobs')
argParser.add_argument('--overwrite',      action='store_true', default=False,          help='overwrite if valid output file already exists')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


#
# Retrieve sample list, reducedTuples need to be created for the samples listed in tuples.conf
#
from ttg.samples.Sample import createSampleList, getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/ZToLLLL/tuples_%s.conf' % args.year))

#
# Submit subjobs
#
if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = [s for s in sampleList if s.name == args.sample]

  jobs = []
  for sample in sampleList:
    if args.dyExternal or args.dyInternal or args.dyExternalAll or args.overlapRemoved:
      if not ('ZG' in sample.name or 'DY' in sample.name): continue
    if sample.isData:
      if args.splitData:                     splitData = [args.splitData]
      elif '2016' in sample.productionLabel: splitData = ['B', 'C', 'D', 'E', 'F', 'G', 'H']
      elif '2017' in sample.productionLabel: splitData = ['B', 'C', 'D', 'E', 'F']
      elif '2018' in sample.productionLabel: splitData = ['A', 'B', 'C', 'D']
    else:                                    splitData = [None]
    jobs += [(sample.name, args.year, str(i), j) for i in xrange(sample.splitJobs) for j in splitData]
  submitJobs(__file__, ('sample', 'year', 'subJob', 'splitData'), jobs, argParser, jobLabel = "HN")
  exit(0)

#
# From now on, we are in the subjobs
# Initialize the sample and tree
#
sample = getSampleFromList(sampleList, args.sample)
tree   = sample.initTree(shortDebug=False, splitData=args.splitData)


#
# Helper functions
#
def getLorentzVector(t, index):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(t._lPt[index], t._lEta[index], t._lPhi[index], t._lE[index])
  return vector

def deltaPhi(phi1, phi2):
  dphi = phi2-phi1
  if dphi >math. pi:   dphi -= 2.0*math.pi
  if dphi <= -math.pi: dphi += 2.0*math.pi
  return abs(dphi)

def deltaR(t, l1, l2):
  return math.sqrt(deltaPhi(t._lPhi[l1], t._lPhi[l2])**2 + (t._lEta[l1]-t._lEta[l1])**2)

#
# Lepton workingpoints
#
def passEleMVA(ept, sceta, emva):
    mvaRaw = -0.5 * math.log((1. - emva)/(1. + emva))
    if ept < 10:
        if sceta < 0.800:   return (mvaRaw > (2.77072387339 - math.exp(-ept/3.81500912145) * 8.16304860178))
        elif sceta < 1.479: return (mvaRaw > (1.85602317813 - math.exp(-ept/2.18697654938) * 11.8568936824))
        else:               return (mvaRaw > (1.73489307814 - math.exp(-ept/2.0163211971 ) * 17.013880078 ))
    else:
        if sceta < 0.800:   return (mvaRaw > (5.9175992258  - math.exp(-ept/13.4807294538) * 9.31966232685))
        elif sceta < 1.479: return (mvaRaw > (5.01598837255 - math.exp(-ept/13.1280451502) * 8.79418193765))
        else:               return (mvaRaw > (4.16921343208 - math.exp(-ept/13.2017224621) * 9.00720913211))


def passEleLoose(tree, i):
  if tree._lEleIsEB[i]:
    if tree._lElefull5x5SigmaIetaIeta[i]           >= 0.11    : return False
    if tree._lEleDEtaInSeed[i]                     >= 0.00477 : return False
    if tree._lEleDeltaPhiSuperClusterTrackAtVtx[i] >= 0.222   : return False
    if tree._lElehadronicOverEm[i]                 >= 0.298   : return False
    if tree._lEleInvMinusPInv[i]                   >= 0.241   : return False
  elif tree._lEleIsEE[i]:
    if tree._lElefull5x5SigmaIetaIeta[i]           >= 0.0314  : return False
    if tree._lEleDEtaInSeed[i]                     >= 0.00868 : return False
    if tree._lEleDeltaPhiSuperClusterTrackAtVtx[i] >= 0.213   : return False
    if tree._lElehadronicOverEm[i]                 >= 0.101   : return False
    if tree._lEleInvMinusPInv[i]                   >= 0.14    : return False
  else:                                                         return False
  if tree._relIso[i]>0.2: return False
  return True

def passEleTight(tree, i, mva):
    if not passEleLoose(tree, i):                          return False
    if not passEleMVA(tree._lPt[i], tree._lEtaSC[i], mva): return False
    if tree._lPt[i]<10:                                    return False
    if tree._relIso[i]>0.1:                                return False
    if abs(tree._dxy[i])>0.05:                             return False
    if abs(tree._dz[i])>0.1:                               return False
    if abs(tree._3dIPSig[i])>4:                            return False
    return True

def passMuonTight(tree, i):
    if tree._lPt[i]<5:                                     return False
    if tree._relIso[i]>0.1:                                return False
    if abs(tree._dxy[i])>0.05:                             return False
    if abs(tree._dz[i])>0.1:                               return False
    if abs(tree._3dIPSig[i])>4:                            return False
    return tree._lPOGMedium[i]


def passMuoDisplMedium(tree, i):
    isGoodGlb = (tree._lGlobalMuon[i] and tree._lCQChi2Position[i]<12. and tree._lCQTrackKink[i]<20.)
    return ((tree._lPOGLoose[i] and isGoodGlb and tree._lMuonSegComp[i]>0.303) or (tree._lPOGLoose[i] and tree._lMuonSegComp[i]>0.451))


#
# Custom dxy binning
#
dxybins = array.array('f', [0.0, 0.01, 0.011, 0.013, 0.015, 0.017, 0.019, 0.022, 0.025, 0.028, 0.032, 0.037, 0.042, 0.048, 0.055, 0.062, 0.071, 0.081, 0.092,
                            0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.23, 0.26, 0.3, 0.34, 0.39, 0.44, 0.5, 0.57, 0.65, 0.74, 0.85, 0.96, 
                            1.1, 1.3, 1.4, 1.6, 1.9, 2.1, 2.4, 2.7, 3.1, 3.6, 4.1, 4.6, 5.3, 6])

#
# Requiring trigger
# this is bullshit, how someone thought this was a good way to code things like this, I can't understand
# everything is so messed up in HNL
#
trigmaskEle = 3 if args.year==2017 else 1
trigmaskMuo = 3 if args.year==2016 else 1

#
# Output file creation
#
outName = sample.name 
if args.dyExternal:     outName += '_external'
if args.dyExternalAll:  outName += '_externalAll'
if args.dyInternal:     outName += '_internal'
if args.overlapRemoved: outName += '_overlapRemoved'
outName = '%s/%s/%s_%s.root' % (args.year, outName, outName, str(args.subJob))

try:    os.makedirs(os.path.dirname(outName))
except: pass

from ttg.tools.helpers import isValidRootFile
if not args.overwrite and isValidRootFile(outName):
  log.info('Finished: valid outputfile already exists')
  exit(0)

fout = ROOT.TFile(outName, 'recreate')


#
# The lumi weights
#
if not sample.isData:
  lumiWeights  = [(float(sample.xsec)*1000/totalWeight) for totalWeight in sample.getTotalWeights()]


#
# Definition of the histograms to be filled (for different flavour combinations, onZ/offZ, 3-leptons or 4-leptons
#
hists = {}
def addHist(name, title, nbins=None, minX=None, maxX=None, bins=None):
  if bins: hists[name] = ROOT.TH1F(name , ';%s;Entries' % title, len(bins)-1, bins)
  else:    hists[name] = ROOT.TH1F(name , ';%s;Entries' % title, nbins, minX, maxX)


promptflavs = ['_promptEE', '_promptMM']
displflavs  = ['_displEE' , '_displMM' ]
for promptflav in promptflavs:
  for displflav in displflavs:
    suff = promptflav+displflav
    addHist('zmass'+suff,  '4-lepton mass [GeV]', nbins=180, minX=20., maxX=200.)
    addHist('zmass3'+suff, '3-lepton mass [GeV]', nbins=180, minX=20., maxX=200.)
    for onz in ['', '_onz']:
      for type in ['3', '']:
        addHist('dxy'+type+onz+suff, '|#it{d}_{xy}(lep)| [cm]', bins=dxybins)
        addHist('dz'+type+onz+suff, '|#it{d}_{z}(lep)| [cm]', bins=dxybins)
        addHist('pt'+type+onz+suff, 'p_{t}(lep) [GeV]', nbins=40, minX=0, maxX=100)
        addHist('eta'+type+onz+suff, '|#eta(lep)|', nbins=25, minX=0, maxX=2.5)
        addHist('photonPt'+type+onz+suff, 'p_{t}(#gamma) [GeV]', nbins=25, minX=0, maxX=100)
        addHist('3dIP'+type+onz+suff, '3dIP(lep)', nbins=20, minX=0, maxX=10)
        addHist('3dIPSig'+type+onz+suff, '3dIPSig(lep)', nbins=20, minX=0, maxX=10)
        addHist('relIso'+type+onz+suff, 'relIso(lep)', nbins=16, minX=0, maxX=0.16)
        addHist('closestDeltaR'+type+onz+suff, '#DeltaR(lep,other)', nbins=50, minX=0, maxX=5)
        if 'displEE' in suff:
          addHist('lmisshits'+type+onz+suff,  'Inner missing hits', nbins=10, minX=0., maxX=10.)
          addHist('hovere'+type+onz+suff,  'H/E', nbins=100, minX=0., maxX=0.1)
          addHist('sigmaIetaIeta'+type+onz+suff,  '#sigma_{i#etai#eta}', nbins=50, minX=0., maxX=.018)
          addHist('ooEmoop'+type+onz+suff,  '1/E-1/P', nbins=50, minX=0., maxX=0.15)
          addHist('dEtaInSeed'+type+onz+suff,  'dEtaInSeed', nbins=50, minX=-.01, maxX=.01)


#
# The event loop
#
from ttg.tools.progressBar import progressbar
log.info('Starting event loop')
for i in sample.eventLoop(totalJobs=sample.splitJobs, subJob=int(args.subJob)):
    if tree.GetEntry(i) < 0: 
      log.warning("problem reading entry, skipping")
      continue

    if tree._nEle<1:   continue
    if tree._nLight<3: continue

    if args.overlapRemoved:
      if 'DY' in args.sample and tree._zgEventType>=3: continue
      if 'ZG' in args.sample and tree._hasInternalConversion: continue

    # Select at least 2 tight leptons and 1 loose/displaced
    tightIndices = []
    looseIndices = []
    for i in range(0, tree._nLight):
      if tree._lFlavor[i]==0:
        imva = tree._lElectronMvaFall17Iso[i]
        if abs(imva) > 0.9999999: imva = (imva/abs(imva)) * 0.9999999
        if passEleTight(tree, i, imva):
          tightIndices.append(i)
        if passEleLoose(tree, i):
          looseIndices.append(i)
      elif tree._lFlavor[i]==1:
        if passMuonTight(tree, i):      tightIndices.append(i)
        if passMuoDisplMedium(tree, i): looseIndices.append(i)

    if len(tightIndices)<2: continue
    if len(looseIndices)<1: continue

    # Select tight pair with highest sum pt
    tightPair = None
    for i in tightIndices:
      for j in tightIndices:
        if i>=j: continue
        if tree._lFlavor[i]==tree._lFlavor[j] and tree._lCharge[i]*tree._lCharge[j]<0:
          if not tightPair:
            tightPair = [i, j]
          else:
            oldPt = tree._lPt[tightPair[0]]+tree._lPt[tightPair[1]]
            newPt = tree._lPt[i]+tree._lPt[j]
            if newPt>oldPt:
              tightPair = [i, j]
    if not tightPair: continue

    npromptleptwithtrig = 0
    for il in tightPair:
      if   tree._lFlavor[il]==0 and tree._lPt[il]>35 and (tree._lHasTrigger[il] & trigmaskEle)>0: npromptleptwithtrig += 1
      elif tree._lFlavor[il]==1 and tree._lPt[il]>28 and (tree._lHasTrigger[il] & trigmaskMuo)>0: npromptleptwithtrig += 1
    if npromptleptwithtrig==0: continue

    for i in tightPair:
      if i in looseIndices: looseIndices.remove(i)
    if len(looseIndices)<1: continue

    # Select loose pair or single loose lepton
    loosePair = None
    if len(looseIndices)>1:
      for i in looseIndices:
        for j in looseIndices:
          if i>=j: continue
          if tree._lFlavor[i]==tree._lFlavor[j] and tree._lCharge[i]*tree._lCharge[j]<0 and deltaR(tree, i, j)<1.0:
            if not loosePair:
              loosePair = [i, j]
            else:
              oldPt = tree._lPt[loosePair[0]]+tree._lPt[loosePair[1]]
              newPt = tree._lPt[i]+tree._lPt[j]
              if newPt>oldPt:
                loosePair = [i, j]

    if not loosePair:
      for i in looseIndices:
        if not loosePair:                            loosePair = [i]
        elif tree._lPt[i] > tree._lPt[loosePair[0]]: loosePair = [i]

    if not loosePair: continue

    suffix = promptflavs[tree._lFlavor[tightPair[0]]] + displflavs[tree._lFlavor[loosePair[0]]]

    ##
    ## Historic "overlap removal" between DY and Zgamma --> this is not an overlap algorithm?????????????????????????????? Should be reviewed at some point
    ## And I need to try to correct this bullshit as there's no time to make decent tuples with overlap removal variables included
    ## It's still bullshit, do never copy this part if you have time to do things in a correct way
    ##
    def getExternalPhotonPt(tree, lepIndex):
      try:
        if tree._lIsPrompt[lepIndex] and tree._lMatchPdgId[lepIndex]==22: return tree._lMatchPt[lepIndex]  # lepton could be matched to photon -> assume external
        else:                                                             return -1
      except:                                                             return -1

    if not args.overlapRemoved:
      if ('DY' in args.sample):
        photonPt = max([getExternalPhotonPt(tree, i) for i in looseIndices + tightIndices])

        if args.dyExternal:
          if photonPt > 15 or photonPt < 0: continue
        elif args.dyExternalAll:
          if photonPt < 0: continue
        elif args.dyInternal:
          if photonPt > 0: continue
        elif not args.overlapRemoved:
          if photonPt > 15: continue

      if ('ZG' in args.sample):
        photonPt = max([getExternalPhotonPt(tree, i) for i in looseIndices + tightIndices])
        if photonPt < 15: continue

    def closestDeltaR(index):
      return min([deltaR(tree, index, i) for i in tightIndices])

    # Fill the hists
    scl = 1 if sample.isData else lumiWeights[0]*tree._weight
    def fillVariables(suffixes, index):
      hists['photonPt'+suffixes].Fill(getExternalPhotonPt(tree, index), scl)
      hists['dxy'+suffixes].Fill(abs(tree._dxy[index]), scl)
      hists['pt'+suffixes].Fill(tree._lPt[index], scl)
      hists['eta'+suffixes].Fill(abs(tree._lEta[index]), scl)
      hists['dz'+suffixes].Fill(abs(tree._dz[index]), scl)
      hists['3dIP'+suffixes].Fill(abs(tree._3dIP[index]), scl)
      hists['3dIPSig'+suffixes].Fill(abs(tree._3dIPSig[index]), scl)
      hists['relIso'+suffixes].Fill(tree._relIso[index], scl)
      hists['closestDeltaR'+suffixes].Fill(closestDeltaR(index), scl)
      if 'displEE' in suffix: 
        hists['lmisshits'+suffixes].Fill(tree._lElectronMissingHits[index], scl)
        hists['hovere'+suffixes].Fill(tree._lElehadronicOverEm[index], scl)
        hists['sigmaIetaIeta'+suffixes].Fill(tree._lElefull5x5SigmaIetaIeta[index], scl)
        hists['ooEmoop'+suffixes].Fill(tree._lEleInvMinusPInv[index], scl)
        hists['dEtaInSeed'+suffixes].Fill(tree._lEleDEtaInSeed[index], scl)

    if len(loosePair)==1:
      zmass = (getLorentzVector(tree, tightPair[0]) + getLorentzVector(tree, tightPair[1]) + getLorentzVector(tree, loosePair[0])).M()
      hists['zmass3'+suffix].Fill(zmass, scl)
      fillVariables('3'+suffix, loosePair[0])
      if abs(zmass-91.)<10.: fillVariables('3_onz'+suffix, loosePair[0])

    if len(loosePair)>1:
      zmass = (getLorentzVector(tree, tightPair[0]) + getLorentzVector(tree, tightPair[1]) + getLorentzVector(tree, loosePair[0]) + getLorentzVector(tree, loosePair[1])).M()
      hists['zmass'+suffix].Fill(zmass, scl)
      for i in loosePair: 
        fillVariables(suffix, i)
        if abs(zmass-91.)<10.: fillVariables('_onz'+suffix, i)


fout.cd()
for label,hist in hists.items(): hist.Write()
fout.Close()
log.info('Finished')
