#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse, numpy
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
# argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',     help='Specify type of reducedTuple')
# argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--dryRun',    action='store_true', default=False,                help='do not launch subjobs, only show them')
argParser.add_argument('--sys',            action='store',      default='')
argParser.add_argument('--runSys',         action='store_true', default=False)
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
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList, getSigmaSyst


lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
reduceType = 'unfJan'

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [args.year]
  if args.sys:                   sysList = [args.sys]
  else:                          
    sysList = [None] + (systematics.keys() if args.runSys else [])
    excludeSys = ['NP']
    excludeSys = ['trigger'] # NOTE temporary
    if sysList[0]:
      sysList = [entry for entry in sysList if not any([entry.count(exc) for exc in excludeSys])]
  # log.info(sysList)
  # subJobArgs, subJobList = getVariations(args, sysList)
  # sysList = [None, 'JECUp', 'JECDown', 'lSFSyUp', 'lSFSyDown']
  # sysList = [None,'lSFSyUp', 'lSFSyDown','fsrDown','fsrUp']
  # sysList = ['isrUp','isrDown','fsrUp','fsrDown','puUp','puDown','pfUp','pfDown','phSFUp','phSFDown','pvSFUp','pvSFDown','lSFSyUp','lSFSyDown','lSFElUp','lSFElDown','lSFMuUp','lSFMuDown','triggerUp','triggerDown','bTaglUp','bTaglDown','bTagbUp','bTagbDown','ephResDown', 'NPDown', 'fsrUp', 'JECUp', 'fsrDown', 'lSFElDown', 'NPUp', 'lSFElUp', 'pfUp', 'isrDown', 'bTaglUp', 'ueUp', 'erdUp', 'puDown', 'phSFUp', 'lSFSyDown', 'triggerUp', 'triggerDown', 'pvSFDown', 'lSFSyUp', 'lSFMuDown', 'puUp', 'ephScaleDown', 'JERDown', 'erdDown', 'JERUp', 'pvSFUp', 'ephScaleUp', 'bTagbUp', 'phSFDown', 'ueDown', 'ephResUp', 'bTagbDown', 'isrUp', 'bTaglDown', 'pfDown', 'lSFMuUp', 'JECDown']

  # log.info(sysList)
  submitJobs(__file__, ('sys'), [[s] for s in sysList], argParser, subLog= args.tag + '/' + args.year, jobLabel = "UF", wallTime="15")
  exit(0)

# NOTE WARNING using separate tuple files right now, but not needed, if samples get updated change this
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'))
stack = createStack(tuplesFile   = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'),
                  styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unfTTG.stack'),
                  # channel      = args.channel,
                  channel      = 'noData',
                  replacements = getReplacementsForStack(args.sys, args.year)
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
  if not c.ndbjets>0:                                     return False
  if not c.mll > 20:                                      return False
  if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
  if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False
  return True


########## FIDUCIAL REGION ##########
def checkFid(c):
  if c.failFid:                                                 return False
  if abs(c._pl_phEta[c.PLph]) > 1.4442:                             return False
  if not c.PLph_pt > 20:                                            return False
  if not c.PLndbjets>0:                                             return False
  if not c.PLmll > 20:                                              return False
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


def kickUnder(under, threshold, val):
  if val > threshold: return under - 1.
  else:               return val

def theta(eta):
  return 2.*numpy.arctan(numpy.e**(-1* eta))

def angle(theta1, theta2, phi1, phi2):
  return ((theta1-theta2)**2. + deltaPhi(phi1,phi2)**2.)**0.5




plotListRecFid = []
plotListRec = []
plotListOut = []
plotListFid = []
mList = []


ptBinRec = [20., 35., 50., 65., 80., 100., 120., 140., 160., 180., 200., 230., 260., 290., 320., 380.]
ptBinGen = [20., 35., 50., 65., 80., 120., 160., 200., 260., 320., 400.]

dRBinRec = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4]
dRBinGen = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.4]

absEtaBinRec = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
absEtaBinGen = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.45]

dPhiBinRec = (16, 0., 3.2)
dPhiBinGen = (8, 0., 3.2)

cosBinRec = (16, -1., 1.)
cosBinGen = (8, -1., 1.)

absdEtaBinRec = [0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25, 2.5, 2.75, 3, 3.25, 4.5]
absdEtaBinGen = [0., 0.5, 1., 1.5, 2.,  2.5, 3., 4.5]

dRBinJetRec = [0.4, 0.6, 0.8, 1.05, 1.3, 1.6, 1.9, 2.25, 2.6, 3., 3.4]
dRBinJetGen = [0.4, 0.8, 1.3, 1.9, 2.6, 3.4]

ptBinJetGen = [30., 60., 100., 150., 250., 400.]
ptBinJetRec = [30., 45., 60., 80., 100., 125., 150., 200., 250., 325., 400.]


# plotList.append(Plot('unfReco_ll_cosTheta',     '#cos(theta(ll))',                lambda c : numpy.cos(angle(theta(c._lEta[c.l1]), theta(c._lEta[c.l2]), c._lPhi[c.l1], c._lPhi[c.l2]))   ,          cosBinRec    ))

# for systematic variations we only want the response matrices
plotListOut.append(Plot('out_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
plotListOut.append(Plot('out_unfReco_jetPt',           'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
plotListOut.append(Plot('out_unfReco_jetLepDeltaR',    '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListOut.append(Plot('out_unfReco_phLepDeltaR',     '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phLep1DeltaR',    '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phLep2DeltaR',    '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phBJetDeltaR',    '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListOut.append(Plot('out_unfReco_ll_absDeltaEta',  '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
plotListOut.append(Plot('out_unfReco_ll_deltaPhi',     '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
plotListOut.append(Plot('out_unfReco_phAbsEta',        '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))

if not args.sys:
  plotListRec.append(Plot('rec_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
  plotListRec.append(Plot('rec_unfReco_jetPt',           'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
  plotListRec.append(Plot('rec_unfReco_jetLepDeltaR',    '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  plotListRec.append(Plot('rec_unfReco_phLepDeltaR',     '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRec.append(Plot('rec_unfReco_phLep1DeltaR',    '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRec.append(Plot('rec_unfReco_phLep2DeltaR',    '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRec.append(Plot('rec_unfReco_phBJetDeltaR',    '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  plotListRec.append(Plot('rec_unfReco_ll_absDeltaEta',  '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
  plotListRec.append(Plot('rec_unfReco_ll_deltaPhi',     '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
  plotListRec.append(Plot('rec_unfReco_phAbsEta',        '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))

  plotListRecFid.append(Plot('recFid_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
  plotListRecFid.append(Plot('recFid_unfReco_jetPt',           'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
  plotListRecFid.append(Plot('recFid_unfReco_jetLepDeltaR',    '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  plotListRecFid.append(Plot('recFid_unfReco_phLepDeltaR',     '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRecFid.append(Plot('recFid_unfReco_phLep1DeltaR',    '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRecFid.append(Plot('recFid_unfReco_phLep2DeltaR',    '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  plotListRecFid.append(Plot('recFid_unfReco_phBJetDeltaR',    '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  plotListRecFid.append(Plot('recFid_unfReco_ll_absDeltaEta',  '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
  plotListRecFid.append(Plot('recFid_unfReco_ll_deltaPhi',     '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
  plotListRecFid.append(Plot('recFid_unfReco_phAbsEta',        '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))


  plotListFid.append(Plot('fid_unfReco_phPt',            'gen p_{T}(#gamma) (GeV)', lambda c : min(       c.PLph_pt                                                                     ,ptBinGen[-1]       -0.001 )   ,ptBinGen     ))
  plotListFid.append(Plot('fid_unfReco_jetPt',           'gen p_{T}(j1) (GeV)',     lambda c : min(       c._pl_jetPt[c.PLj1]                                                           ,ptBinJetGen[-1]       -0.001 )   ,ptBinJetGen     ))
  plotListFid.append(Plot('fid_unfReco_jetLepDeltaR',    'gen #DeltaR(l, j)',       lambda c : min(       min(c.PLl1JetDeltaR, c.PLl2JetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  ))
  plotListFid.append(Plot('fid_unfReco_phLepDeltaR',     'gen #DeltaR(#gamma, l)',  lambda c : min(       min(c.PLphL1DeltaR, c.PLphL2DeltaR)                                           ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
  plotListFid.append(Plot('fid_unfReco_phLep1DeltaR',    'gen #DeltaR(#gamm1a, l)', lambda c : min(       c.PLphL1DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
  plotListFid.append(Plot('fid_unfReco_phLep2DeltaR',    'gen #DeltaR(#gamm2a, l)', lambda c : min(       c.PLphL2DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
  plotListFid.append(Plot('fid_unfReco_phBJetDeltaR',    'gen #DeltaR(#gamma, b)',  lambda c : min(       kickUnder(0., 900., c.PLphBJetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  ))
  plotListFid.append(Plot('fid_unfReco_ll_absDeltaEta',  'gen |#Delta#eta(ll)|',    lambda c : min(       abs(protectedGet(c._pl_lEta, c.PLl1) - protectedGet(c._pl_lEta, c.PLl2))      ,absdEtaBinGen[-1]  -0.001 )   ,absdEtaBinGen))
  plotListFid.append(Plot('fid_unfReco_ll_deltaPhi',     'gen #Delta#phi(ll)',      lambda c : min(       deltaPhi(protectedGet(c._pl_lPhi, c.PLl1), protectedGet(c._pl_lPhi, c.PLl2))  ,dPhiBinGen[-1]     -0.001 )   ,dPhiBinGen   ))
  plotListFid.append(Plot('fid_unfReco_phAbsEta',        'gen |#eta|(#gamma)',      lambda c : min(       abs(protectedGet(c._pl_phEta, c.PLph))                                        ,absEtaBinGen[-1]   -0.001 )   ,absEtaBinGen ))


  mList.append(Plot2D('respNorm_unfReco_phPt',           'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     , 'gen p_{T}(#gamma) (GeV)', lambda c : min(       c.PLph_pt                                                                     ,ptBinGen[-1]       -0.001 )   ,ptBinGen     , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_jetPt',          'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     , 'gen p_{T}(j1) (GeV)',     lambda c : min(       c._pl_jetPt[c.PLj1]                                                           ,ptBinJetGen[-1]       -0.001 )   ,ptBinJetGen     , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_jetLepDeltaR',   '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(l, j)',       lambda c : min(       min(c.PLl1JetDeltaR, c.PLl2JetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_phLepDeltaR',    '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l)',  lambda c : min(       min(c.PLphL1DeltaR, c.PLphL2DeltaR)                                           ,dRBinGen[-1]       -0.001 )   ,dRBinGen     , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_phLep1DeltaR',   '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l1)', lambda c : min(       c.PLphL1DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_phLep2DeltaR',   '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l2)', lambda c : min(       c.PLphL2DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_phBJetDeltaR',   '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(#gamma, b)',  lambda c : min(       kickUnder(0., 900., c.PLphBJetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_ll_absDeltaEta', '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec, 'gen |#Delta#eta(ll)|',    lambda c : min(       abs(protectedGet(c._pl_lEta, c.PLl1) - protectedGet(c._pl_lEta, c.PLl2))      ,absdEtaBinGen[-1]  -0.001 )   ,absdEtaBinGen, histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_ll_deltaPhi',    '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   , 'gen #Delta#phi(ll)',      lambda c : min(       deltaPhi(protectedGet(c._pl_lPhi, c.PLl1), protectedGet(c._pl_lPhi, c.PLl2))  ,dPhiBinGen[-1]     -0.001 )   ,dPhiBinGen   , histModifications=normalizeAlong('x')))
  mList.append(Plot2D('respNorm_unfReco_phAbsEta',       '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec , 'gen |#eta|(#gamma)',      lambda c : min(       abs(protectedGet(c._pl_phEta, c.PLph))                                        ,absEtaBinGen[-1]   -0.001 )   ,absEtaBinGen , histModifications=normalizeAlong('x')))


  mList.append(Plot2D('perf_unfReco_phPt',           'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     , 'gen p_{T}(#gamma) (GeV)', lambda c : min(       c.PLph_pt                                                                     ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
  mList.append(Plot2D('perf_unfReco_jetPt',          'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     , 'gen p_{T}(j1) (GeV)',     lambda c : min(       c._pl_jetPt[c.PLj1]                                                           ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
  mList.append(Plot2D('perf_unfReco_jetLepDeltaR',   '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(l, j)',       lambda c : min(       min(c.PLl1JetDeltaR, c.PLl2JetDeltaR)                                         ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  mList.append(Plot2D('perf_unfReco_phLepDeltaR',    '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l)',  lambda c : min(       min(c.PLphL1DeltaR, c.PLphL2DeltaR)                                           ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  mList.append(Plot2D('perf_unfReco_phLep1DeltaR',   '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c,  c.phL1DeltaR                                                        , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l1)', lambda c : min(       c.PLphL1DeltaR                                                                ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  mList.append(Plot2D('perf_unfReco_phLep2DeltaR',   '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c,  c.phL2DeltaR                                                        , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l2)', lambda c : min(       c.PLphL2DeltaR                                                                ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
  mList.append(Plot2D('perf_unfReco_phBJetDeltaR',   '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(#gamma, b)',  lambda c : min(       kickUnder(0., 900., c.PLphBJetDeltaR)                                         ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
  mList.append(Plot2D('perf_unfReco_ll_absDeltaEta', '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec, 'gen |#Delta#eta(ll)|',    lambda c : min(       abs(protectedGet(c._pl_lEta, c.PLl1) - protectedGet(c._pl_lEta, c.PLl2))      ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
  mList.append(Plot2D('perf_unfReco_ll_deltaPhi',    '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   , 'gen #Delta#phi(ll)',      lambda c : min(       deltaPhi(protectedGet(c._pl_lPhi, c.PLl1), protectedGet(c._pl_lPhi, c.PLl2))  ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
  mList.append(Plot2D('perf_unfReco_phAbsEta',       '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec , 'gen |#eta|(#gamma)',      lambda c : min(       abs(protectedGet(c._pl_phEta, c.PLph))                                        ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))


mList.append(Plot2D('response_unfReco_phPt',           'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     , 'gen p_{T}(#gamma) (GeV)', lambda c : min(       c.PLph_pt                                                                     ,ptBinGen[-1]       -0.001 )   ,ptBinGen     ))
mList.append(Plot2D('response_unfReco_jetPt',          'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, protectedGet(c._jetSmearedPt, c.j1)                                  , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     , 'gen p_{T}(j1) (GeV)',     lambda c : min(       c._pl_jetPt[c.PLj1]                                                           ,ptBinJetGen[-1]       -0.001 )   ,ptBinJetGen     ))
mList.append(Plot2D('response_unfReco_jetLepDeltaR',   '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(l, j)',       lambda c : min(       min(c.PLl1JetDeltaR, c.PLl2JetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  ))
mList.append(Plot2D('response_unfReco_phLepDeltaR',    '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l)',  lambda c : min(       min(c.PLphL1DeltaR, c.PLphL2DeltaR)                                           ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
mList.append(Plot2D('response_unfReco_phLep1DeltaR',   '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l1)', lambda c : min(       c.PLphL1DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
mList.append(Plot2D('response_unfReco_phLep2DeltaR',   '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     , 'gen #DeltaR(#gamma, l2)', lambda c : min(       c.PLphL2DeltaR                                                                ,dRBinGen[-1]       -0.001 )   ,dRBinGen     ))
mList.append(Plot2D('response_unfReco_phBJetDeltaR',   '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  , 'gen #DeltaR(#gamma, b)',  lambda c : min(       kickUnder(0., 900., c.PLphBJetDeltaR)                                         ,dRBinJetGen[-1]    -0.001 )   ,dRBinJetGen  ))
mList.append(Plot2D('response_unfReco_ll_absDeltaEta', '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec, 'gen |#Delta#eta(ll)|',    lambda c : min(       abs(protectedGet(c._pl_lEta, c.PLl1) - protectedGet(c._pl_lEta, c.PLl2))      ,absdEtaBinGen[-1]  -0.001 )   ,absdEtaBinGen))
mList.append(Plot2D('response_unfReco_ll_deltaPhi',    '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   , 'gen #Delta#phi(ll)',      lambda c : min(       deltaPhi(protectedGet(c._pl_lPhi, c.PLl1), protectedGet(c._pl_lPhi, c.PLl2))  ,dPhiBinGen[-1]     -0.001 )   ,dPhiBinGen   ))
mList.append(Plot2D('response_unfReco_phAbsEta',       '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec , 'gen |#eta|(#gamma)',      lambda c : min(       abs(protectedGet(c._pl_phEta, c.PLph))                                        ,absEtaBinGen[-1]   -0.001 )   ,absEtaBinGen ))


########## EVENTLOOP ##########
# TODO setIDSelection(c, args.tag) nodig?
from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
lumiScale = lumiScales[args.year]
reduceType = applySysToReduceType(reduceType, args.sys)
log.info("using reduceType " + reduceType)

for sample in sum(stack, []):
  c = sample.initTree(reducedType = reduceType)
  for i in sample.eventLoop():
    
    c.GetEntry(i)

    c.ISRWeight = 1.
    c.FSRWeight = 1.
    # log.info(c.lWeight)
    if args.sys:
      applySysToTree(sample.name, args.sys, c)
    # log.info(c.lWeight)
    # log.info('........................')
    c.fid = checkFid(c)
    c.rec = checkRec(c)

    prefireWeight = 1. if args.year == '2018' else c._prefireWeight

    phWeight = 1. if c.phWeight == 0. else c.phWeight
    generWeights = c.genWeight*lumiScale
    recoWeights  = c.puWeight*c.lWeight*c.lTrackWeight*phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*c.ISRWeight*c.FSRWeight*c.PVWeight
    eventWeight = generWeights*recoWeights
    # log.info('...........................')
    # log.info('    c.genWeight'+str(c.genWeight))
    # log.info('    c.puWeight'+str(c.puWeight))
    # log.info('    c.lWeight'+str(c.lWeight))
    # log.info('    c.lTrackWeight'+str(c.lTrackWeight))
    # log.info('    phWeight'+str(phWeight))
    # log.info('    c.bTagWeight'+str(c.bTagWeight))
    # log.info('    c.triggerWeight'+str(c.triggerWeight))
    # log.info('    prefireWeight'+str(prefireWeight))
    # log.info('    c.ISRWeight'+str(c.ISRWeight))
    # log.info('    c.FSRWeight'+str(c.FSRWeight))
    # log.info('    c.PVWeight'+str(c.PVWeight))
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


##### 1D plots #####
for plot in plotList:
  if isinstance(plot, Plot2D): continue
  plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), args.sys)

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
    plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), args.sys)
    for logZ in [False, True]:
      for option in ['SCAT', 'COLZ', 'COLZ TEXT', 'COLZ TEXTclean', 'COLZclean']:
        plot.draw(plot_directory = os.path.join(plotDir, args.year, args.tag, 'noData' + ('-log' if logZ else ''), 'placeholderSelection', option),
                  logZ           = logZ,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScales[args.year], isOnlySim=('noData'=='noData')))


if noWarnings: 
  log.info('Plots made for ' + args.year)
  log.info('Finished')
else:          
  log.info('Could not produce all plots for ' + args.year)