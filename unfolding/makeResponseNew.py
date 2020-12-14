#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse, numpy
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',     help='Specify type of reducedTuple')
# argParser.add_argument('--var',       action='store',      default='phPt',               help='variable to unfold')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
# argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong, equalBinning
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.tools.style import drawLumi
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR
from ttg.samples.Sample import createSampleList, getSampleFromList
import copy
import pickle
from math import pi

lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
reduceType = 'UnfphoCBlmva'
# reduceType = 'UnfphoCBdink'

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [args.year]
  submitJobs(__file__, ('year'), [jobs], argParser, subLog=args.tag, jobLabel = "UF")
  exit(0)

# NOTE WARNING using separate tuple files right now, but not needed, if samples get updated change this
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'))
stack = createStack(tuplesFile   = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'),
                  styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unfTTG.stack'),
                  # channel      = args.channel,
                  channel      = 'noData',
                  # replacements = getReplacementsForStack(args.sys, args.year)
                  )

########## RECO SELECTION ##########
def checkRec(c):
  if c.failReco:                                          return False
  if not c._phCutBasedMedium[c.ph]:                       return False
  if abs(c._phEta[c.ph]) > 1.4442:                        return False
  c.checkMatch, c.genuine = True, True
  c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False
  if not checkMatch(c):                                   return False
  if not c.ph_pt > 20:                                    return False
  if not ((c.isEMu and c.njets>0) or (c.ndbjets>0)):             return False
  if not c.mll > 20:                                      return False
  if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
  if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False
  return True


########## FIDUCIAL REGION ##########
def checkFid(c):
  if c.failFid:                                                 return False
  if abs(c._pl_phEta[c.PLph]) > 1.4442:                             return False
  if not c.PLph_pt > 20:                                            return False
  if not ((c.PLisEMu and c.PLnjets>0) or (c.PLndbjets>0)):                 return False
  if not c.PLmll > 20:                                              return False
  if not (abs(c.PLmll-91.1876)>15 or c.PLisEMu):                    return False
  if not (abs(c.PLmllg-91.1876)>15 or c.PLisEMu):                   return False
  return True



########## PREPARE PLOTS ##########
Plot.setDefaults(stack=stack, texY = 'Events')
Plot2D.setDefaults(stack=stack)
from ttg.plots.plotHelpers  import *

def ifRec(c, val, under):
  if c.rec: return val
  else: return under-1.

def ifFid(c, val, under):
  if c.fid: return val
  else: return under-1.


def protectedGet(arr, ind):
  try: return arr[ind]
  except: return 9999.


dRBinRec = [ 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 4.2 ]
dRBinGen = [ 0.4, 1.0, 1.6, 2.2, 2.8, 3.4, 4.2 ]

etaBinRec = (15, -1.5, 1.5)
etaBinGen = (5, -1.5, 1.5)

absEtaBinRec = (15, 0., 1.5)
absEtaBinGen = (5, 0., 1.5)

ptBinRec = (31, 20, 330)
ptBinGen = (11, 20, 350)

# NOTE delta phi binning was own choice, SL group didn't propose any
dPhiBinRec = (15, 0., pi)
dPhiBinGen = (5, 0., pi)



plotListRecFid = []
plotListRec = []
plotListOut = []
plotListFid = []
mList = []



mList.append(Plot2D('response_phPt',          'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(c.PLph_pt                                       , ptBinGen[-1]-0.001    )  , ptBinGen                ))
mList.append(Plot2D('response_phEta',         '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(c._pl_phEta[c.PLph]                             , etaBinGen[-1]-0.001   )  , etaBinGen               ))
mList.append(Plot2D('response_phAbsEta',      '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(abs(c._pl_phEta[c.PLph])                        , absEtaBinGen[-1]-0.001)  , absEtaBinGen            ))
mList.append(Plot2D('response_ll_deltaPhi',   '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   , 'PL #Delta#phi(ll)',              lambda c : min(deltaPhi(c._pl_lPhi[c.PLl1], c._pl_lPhi[c.PLl2]), dPhiBinGen[-1]-0.001  )  , dPhiBinGen              ))
mList.append(Plot2D('response_phLepDeltaR',   '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     , 'PL #DeltaR(#gamma, l)',          lambda c : min(min(c.PLphL1DeltaR,c.PLphL2DeltaR)              , dRBinGen[-1]-0.001    )  , dRBinGen                ))

mList.append(Plot2D('respNorm_phPt',          'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(c.PLph_pt                                       , ptBinGen[-1]-0.001    )  , ptBinGen                , histModifications=normalizeAlong('x')))
mList.append(Plot2D('respNorm_phEta',         '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(c._pl_phEta[c.PLph]                             , etaBinGen[-1]-0.001   )  , etaBinGen               , histModifications=normalizeAlong('x')))
mList.append(Plot2D('respNorm_phAbsEta',      '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec , 'PL p_{T}(#gamma) (GeV)',         lambda c : min(abs(c._pl_phEta[c.PLph])                        , absEtaBinGen[-1]-0.001)  , absEtaBinGen            , histModifications=normalizeAlong('x')))
mList.append(Plot2D('respNorm_ll_deltaPhi',   '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   , 'PL #Delta#phi(ll)',              lambda c : min(deltaPhi(c._pl_lPhi[c.PLl1], c._pl_lPhi[c.PLl2]), dPhiBinGen[-1]-0.001  )  , dPhiBinGen              , histModifications=normalizeAlong('x')))
mList.append(Plot2D('respNorm_phLepDeltaR',   '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     , 'PL #DeltaR(#gamma, l)',          lambda c : min(min(c.PLphL1DeltaR,c.PLphL2DeltaR)              , dRBinGen[-1]-0.001    )  , dRBinGen                , histModifications=normalizeAlong('x')))

mList.append(Plot2D('response_plx_phPt',              'PL p_{T}(#gamma) (GeV)',         lambda c : min(c.PLph_pt                                       , ptBinGen[-1]-0.001    )  , ptBinGen,               'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     ))
mList.append(Plot2D('response_plx_phEta',             'PL p_{T}(#gamma) (GeV)',         lambda c : min(c._pl_phEta[c.PLph]                             , etaBinGen[-1]-0.001   )  , etaBinGen,              '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    ))
mList.append(Plot2D('response_plx_phAbsEta',          'PL p_{T}(#gamma) (GeV)',         lambda c : min(abs(c._pl_phEta[c.PLph])                        , absEtaBinGen[-1]-0.001)  , absEtaBinGen,           '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec ))
mList.append(Plot2D('response_plx_ll_deltaPhi',       'PL #Delta#phi(ll)',              lambda c : min(deltaPhi(c._pl_lPhi[c.PLl1], c._pl_lPhi[c.PLl2]), dPhiBinGen[-1]-0.001  )  , dPhiBinGen,             '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   ))
mList.append(Plot2D('response_plx_phLepDeltaR',       'PL #DeltaR(#gamma, l)',          lambda c : min(min(c.PLphL1DeltaR,c.PLphL2DeltaR)              , dRBinGen[-1]-0.001    )  , dRBinGen,               '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     ))

mList.append(Plot2D('respNorm_plx_phPt',              'PL p_{T}(#gamma) (GeV)',         lambda c : min(c.PLph_pt                                       , ptBinGen[-1]-0.001    )  , ptBinGen,               'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     , histModifications=normalizeAlong('y')))
mList.append(Plot2D('respNorm_plx_phEta',             'PL p_{T}(#gamma) (GeV)',         lambda c : min(c._pl_phEta[c.PLph]                             , etaBinGen[-1]-0.001   )  , etaBinGen,              '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    , histModifications=normalizeAlong('y')))
mList.append(Plot2D('respNorm_plx_phAbsEta',          'PL p_{T}(#gamma) (GeV)',         lambda c : min(abs(c._pl_phEta[c.PLph])                        , absEtaBinGen[-1]-0.001)  , absEtaBinGen,           '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec , histModifications=normalizeAlong('y')))
mList.append(Plot2D('respNorm_plx_ll_deltaPhi',       'PL #Delta#phi(ll)',              lambda c : min(deltaPhi(c._pl_lPhi[c.PLl1], c._pl_lPhi[c.PLl2]), dPhiBinGen[-1]-0.001  )  , dPhiBinGen,             '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   , histModifications=normalizeAlong('y')))
mList.append(Plot2D('respNorm_plx_phLepDeltaR',       'PL #DeltaR(#gamma, l)',          lambda c : min(min(c.PLphL1DeltaR,c.PLphL2DeltaR)              , dRBinGen[-1]-0.001    )  , dRBinGen,               '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     , histModifications=normalizeAlong('y')))



# mList.append(Plot2D('respNorm_phPt',              'PL p_{T}(#gamma) (GeV)',         lambda c : c.PLph_pt ,                                              ptBinGen,               'p_{T}(#gamma) (GeV)',            lambda c : ifRec(c, c.ph_pt, 20.) ,                                         ptBinRec     , histModifications=normalizeAlong('y')))
# mList.append(Plot2D('respNorm_phEta',             'PL p_{T}(#gamma) (GeV)',         lambda c : c._pl_phEta[c.PLph] ,                                    etaBinGen,              '#eta(#gamma)',                   lambda c : ifRec(c, protectedGet(c._phEta, c.ph), -1.5) ,                                etaBinRec    , histModifications=normalizeAlong('y')))
# mList.append(Plot2D('respNorm_phAbsEta',          'PL p_{T}(#gamma) (GeV)',         lambda c : abs(c._pl_phEta[c.PLph]) ,                               absEtaBinGen,           '|#eta|(#gamma)',                 lambda c : ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.) ,                              absEtaBinRec , histModifications=normalizeAlong('y')))
# mList.append(Plot2D('respNorm_ll_deltaPhi',       'PL #Delta#phi(ll)',              lambda c : deltaPhi(c._pl_lPhi[c.PLl1], c._pl_lPhi[c.PLl2]) ,       dRBinGen,               '#Delta#phi(ll)',                 lambda c : ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4) ,          dRBinRec     , histModifications=normalizeAlong('y')))
# mList.append(Plot2D('respNorm_phLepDeltaR',       'PL #DeltaR(#gamma, l)',          lambda c : min(c.PLphL1DeltaR,c.PLphL2DeltaR) ,                     dRBinGen,               '#DeltaR(#gamma, l)',             lambda c : ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4) ,                                    dRBinRec     , histModifications=normalizeAlong('y')))

plotListOut.append(Plot('out_phPt',            'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     ))
plotListOut.append(Plot('out_phEta',           '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    ))
plotListOut.append(Plot('out_phAbsEta',        '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec ))
plotListOut.append(Plot('out_ll_deltaPhi',     '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   ))
plotListOut.append(Plot('out_phLepDeltaR',     '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     ))

plotListRec.append(Plot('rec_phPt',            'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     ))
plotListRec.append(Plot('rec_phEta',           '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    ))
plotListRec.append(Plot('rec_phAbsEta',        '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec ))
plotListRec.append(Plot('rec_ll_deltaPhi',     '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   ))
plotListRec.append(Plot('rec_phLepDeltaR',     '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     ))

plotListRecFid.append(Plot('recFid_phPt',            'p_{T}(#gamma) (GeV)',            lambda c : min(ifRec(c, c.ph_pt, 20.)                                                           , ptBinRec[-1]-0.001    )   , ptBinRec     ))
plotListRecFid.append(Plot('recFid_phEta',           '#eta(#gamma)',                   lambda c : min(ifRec(c, protectedGet(c._phEta, c.ph), -1.5)                                     , etaBinRec[-1]-0.001   )   , etaBinRec    ))
plotListRecFid.append(Plot('recFid_phAbsEta',        '|#eta|(#gamma)',                 lambda c : min(ifRec(c, abs(protectedGet(c._phEta,c.ph)), 0.)                                   , absEtaBinRec[-1]-0.001)   , absEtaBinRec ))
plotListRecFid.append(Plot('recFid_ll_deltaPhi',     '#Delta#phi(ll)',                 lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2)), 0.4), dPhiBinRec[-1]-0.001  )   , dPhiBinRec   ))
plotListRecFid.append(Plot('recFid_phLepDeltaR',     '#DeltaR(#gamma, l)',             lambda c : min(ifRec(c, min(c.phL1DeltaR,c.phL2DeltaR), 0.4)                                    , dRBinRec[-1]-0.001    )   , dRBinRec     ))


plotListRec.append(Plot('rec_eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))
plotListFid.append(Plot('fid_eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))
plotListOut.append(Plot('out_eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))




########## EVENTLOOP ##########
# TODO setIDSelection(c, args.tag) nodig?
from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
lumiScale = lumiScales[args.year]
log.info("using reduceType " + reduceType)

for sample in sum(stack, []):
  c = sample.initTree(reducedType = reduceType)
  for i in sample.eventLoop():
    c.GetEntry(i)
    c.ISRWeight = 1.
    c.FSRWeight = 1.

    c.fid = checkFid(c)
    c.rec = checkRec(c)

    prefireWeight = 1. if args.year == '2018' else c._prefireWeight

    phWeight = 1. if c.phWeight == 0. else c.phWeight
    generWeights = c.genWeight*lumiScale
    recoWeights  = c.puWeight*c.lWeight*c.lTrackWeight*phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*c.ISRWeight*c.FSRWeight*c.PVWeight

    eventWeight = generWeights*recoWeights

    if c.rec and c.fid:
      fillPlots(plotListRecFid, sample, eventWeight)
    if c.rec:
      fillPlots(plotListRec, sample, eventWeight)
    if c.fid:
      fillPlots(plotListFid, sample, generWeights)
    if c.rec and not c.fid:
      fillPlots(plotListOut, sample, eventWeight)

    if c.fid:
      if c.rec:
        fillPlots(mList, sample, eventWeight)
        c.rec = False
        fillPlots(mList, sample, generWeights*(1.-recoWeights))
      else:
        fillPlots(mList, sample, generWeights)




########## PLOTTING ##########
plotList = plotListRecFid + plotListRec + plotListFid + plotListOut + mList
noWarnings = True

def getBinning(a):
  return numpy.linspace(a[1],a[2],a[0]-1)


binnings = [('response_phPt',        getBinning(ptBinGen)),
            ('response_phEta',       getBinning(etaBinGen)),
            ('response_phAbsEta',    getBinning(absEtaBinGen)),
            ('response_ll_deltaPhi', getBinning(dRBinGen)),
            ('response_phLepDeltaR', getBinning(dRBinGen))]


# NOTE make clones, otherwise you're changing the saved hists 

# x-axis = reco, y-axis = particle level
for binning in binnings:
  matrix = [i for i in mList if i.name==binning[0]][0]
  matrix = matrix.histos.values()[0]
  reco   = matrix.ProjectionY("reco",1, matrix.GetXaxis().GetNbins()) # pl not including over/underflows, but they should be empty anyway
  pl = matrix.ProjectionX("pl")                                       # reco underflow bins = events failing reco. Included in this sum
  diag = pl.Clone( "efficiency")
  diag.Reset("ICES")
  for i in range(0, pl.GetXaxis().GetNbins()+1):
    diag.SetBinContent(i, matrix.GetBinContent(i,i))
    diag.SetBinError(i, matrix.GetBinError(i,i))

  # NOTE do not change the order
  log.info('pur')
  purity     = ROOT.TEfficiency(diag, reco)
  log.info('eff')
  reco.SetBinContent(0,0.)
  efficiency = ROOT.TEfficiency(reco, pl)
  log.info('stab')
  stability  = ROOT.TEfficiency(diag, pl)
  efficiency.SetStatisticOption(ROOT.TEfficiency.kFCP)
  stability.SetStatisticOption(ROOT.TEfficiency.kFCP)
  purity.SetStatisticOption(ROOT.TEfficiency.kFCP)
  # exit(0)

  for histo, plotName, ymax in [(efficiency, 'eff',0.5), (stability, 'stab',0.5), (purity, 'pur',1.0)]:
  # for histo, plotName, ymax in [(stability, 'stab',0.5), (purity, 'pur',1.0)]:
    canv = ROOT.TCanvas()
    histo.Draw('A')
    ROOT.gPad.Update(); 
    graph = efficiency.GetPaintedGraph(); 
    graph.SetMinimum(0);
    graph.SetMaximum(1); 
    ROOT.gPad.Update(); 
    canv.SaveAs('plots/' + plotName + binning[0] +'.pdf')

  # Outside migration plots
  # TODO make clones
  # TODO update to naming based on loop
  out = [i for i in plotListOut if i.name==binning[0].replace('response','out')][0].histos.values()[0].Clone()
  rec = [i for i in plotListRec if i.name==binning[0].replace('response','rec')][0].histos.values()[0].Clone()
  out.Divide(rec)
  for i in range(0, out.GetXaxis().GetNbins()+1):
    out.SetBinContent(i, 1. - out.GetBinContent(i))
  canv = ROOT.TCanvas()
  out.GetYaxis().SetRangeUser(0., 1.0)
  out.Draw('E1')
  canv.SaveAs('plots/out'+ binning[0].replace('response_','') +'.pdf')


##### 1D plots #####
for plot in plotList:
  if isinstance(plot, Plot2D): continue
  plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), '')

  extraArgs = {}
  for logY in [False, True]:
    if not logY and args.tag.count('sigmaIetaIeta') and plot.name.count('photon_chargedIso_bins_NO'): yRange = (0.0001, 0.35)
    else:                                                                                             yRange = None
    extraTag  = '-log'    if logY else ''

    err = plot.draw(
              plot_directory    = os.path.join(plotDir, args.year, args.tag, 'noData' + extraTag, 'placeholderSelection', ''),
              logX              = False,
              logY              = logY,
              sorting           = False,
              yRange            = yRange if yRange else (0.003 if logY else 0.0001, "auto"),
              drawObjects       = drawLumi(None, lumiScales[args.year], isOnlySim=('noData'=='noData')),
              **extraArgs
    )
    extraArgs['saveGitInfo'] = False
    if err: noWarnings = False

##### 2D plots #####
for plot in plotList:
  if not hasattr(plot, 'varY'): continue
  plot.applyMods()
  for drawOUFlow in [False, True]:
    if drawOUFlow: 
        plot.name += '_overflow'
        plot.histos.values()[0].GetXaxis().SetRange(0, plot.histos.values()[0].GetNbinsX() + 1)
        plot.histos.values()[0].GetYaxis().SetRange(0, plot.histos.values()[0].GetNbinsY() + 1)
    plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), '')
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ', 'COLZ TEXT', 'COLZ TEXTclean']:
        plot.draw(plot_directory = os.path.join(plotDir, args.year, args.tag, 'noData' + ('-log' if logY else ''), 'placeholderSelection', option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScales[args.year], isOnlySim=('noData'=='noData')))


if noWarnings: 
  log.info('Plots made for ' + args.year)
  log.info('Finished')
else:          
  log.info('Could not produce all plots for ' + args.year)