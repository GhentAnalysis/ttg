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
argParser.add_argument('--runNLO',         action='store_true', default=False)

args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong, equalBinning
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.tools.style import drawLumi, drawLumi2D, setDefault, ttgGeneralStyle
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR, lumiScales, lumiScalesRounded
from ttg.plots.plotHelpers  import *
from ttg.samples.Sample import createSampleList, getSampleFromList
import copy
import pickle
from math import pi
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList

setDefault()
ttgGeneralStyle()


reduceType = 'unfEND'

if args.sys.count('ephScale') or args.sys.count('ephRes'):
  reduceType = 'unfBLS'
# reduceType = 'unfFB'

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

args.tag = args.tag + ('_NLO' if args.runNLO else '')


# we just need these for fid level

if args.runNLO:
  systematics.clear()

for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd'):
  systematics['q2Sc_' + i] = [('genWeight', 'weight_q2Sc_'+i)]

for i in range(0, 100):
  systematics['pdfSc_' + str(i)] = [('genWeight', 'weight_pdfSc_' + str(i))]

if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [args.year]
  if args.sys:                   sysList = [args.sys]
  else:                          
    sysList = [None] + (systematics.keys() if args.runSys else [])
    excludeSys = ['NP']
    if sysList[0]:
      sysList = [entry for entry in sysList if not any([entry.count(exc) for exc in excludeSys])]
  submitJobs(__file__, ('sys'), [[s] for s in sysList], argParser, subLog= args.tag + '/' + args.year, jobLabel = "UF", wallTime="15")
  exit(0)

# NOTE WARNING using separate tuple files right now, but not needed, if samples get updated change this
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'))
stack = createStack(tuplesFile   = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'),
                  styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/ttgNLO.stack' if args.runNLO else '$CMSSW_BASE/src/ttg/unfolding/data/unfTTG.stack'),
                  # channel      = args.channel,
                  channel      = 'noData',
                  replacements = getReplacementsForStack(args.sys, args.year)
                  )



########## RECO SELECTION ##########
def checkRec(c):
  if c.failReco:                                          return False
  # if not c._phCutBasedMedium[c.ph]:                       return False
  # if abs(c._phEta[c.ph]) > 1.4442:                        return False
  c.checkMatch, c.genuine = True, True
  c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False
  # if not checkMatch(c):                                   return False
  # if not c.ph_pt > 20:                                    return False
  # if not c.ndbjets>0:                                     return False
  # if not c.mll > 20:                                      return False
  # if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
  # if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False

  # if not c.j1_pt> 150: return False
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



def ifRec(c, val, under):
  if c.rec: return val
  else: return under-1.

def ifFid(c, val, under):
  if c.fid: return val
  else: return under-1.


def protectedGet(arr, ind):
  try: return arr[ind]
  except: return 9999.

def protectedZpt(c, under):
  if c.rec:
    first  = getLorentzVector(leptonPt(c, c.l1), c._lEta[c.l1], c._lPhi[c.l1], leptonE(c, c.l1))
    second = getLorentzVector(leptonPt(c, c.l2), c._lEta[c.l2], c._lPhi[c.l2], leptonE(c, c.l2))
    return (first+second).Pt()
  else: return under-1.


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

ptBinRec = [20., 35., 50., 70., 100., 130., 165., 200., 250., 300.]
ptBinGen = [20., 35., 50., 70., 130., 200., 300.]

dRBinRec = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4]
# dRBinGen = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.4]
dRBinGen = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.4]

absEtaBinRec = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
absEtaBinGen = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.45]

dPhiBinRec = (16, 0., 3.2)
dPhiBinGen = (8, 0., 3.2)

cosBinRec = (16, -1., 1.)
cosBinGen = (8, -1., 1.)

absdEtaBinRec = [0., 0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25, 2.5, 2.75, 3, 3.25, 4.5]
absdEtaBinGen = [0., 0.5, 1., 1.5, 2.,  2.5, 3., 4.5]

dRBinJetRec = [0.4, 0.6, 0.8, 1.05, 1.3, 1.6, 1.9, 2.25, 2.6, 3., 3.4]
dRBinJetGen = [0.4, 0.8, 1.3, 1.9, 2.6, 3.4]

ptBinJetRec = [30., 55., 80., 110., 140., 170., 200., 250., 300., 375., 450.]
ptBinJetGen = [30., 80., 140., 200., 300., 450.]


# l1l2 scalar pt sum should start at 25+15 =40
# pT(ll) could I guess go down to 0, testing



ZptBinRec = [0., 15., 30., 45., 60., 75., 90., 110., 130., 170., 210., 310., 410.]
ZptBinGen = [0., 30., 60., 90., 130., 210., 410.]

l1l2ptBinRec = [40., 55., 70., 85., 100., 120., 140., 165., 190., 220., 250., 290., 330., 400., 500.]
l1l2ptBinGen = [40., 70., 100., 140., 190., 250., 330., 500.]


# for systematic variations we only want the response matrices
plotListOut.append(Plot('out_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
plotListOut.append(Plot('out_unfReco_jetPt',           'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, c.j1_pt                                                              , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
plotListOut.append(Plot('out_unfReco_jetLepDeltaR',    '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListOut.append(Plot('out_unfReco_phLepDeltaR',     '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phLep1DeltaR',    '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phLep2DeltaR',    '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListOut.append(Plot('out_unfReco_phBJetDeltaR',    '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListOut.append(Plot('out_unfReco_ll_absDeltaEta',  '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
plotListOut.append(Plot('out_unfReco_ll_deltaPhi',     '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
plotListOut.append(Plot('out_unfReco_phAbsEta',        '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))
plotListOut.append(Plot('out_unfReco_Z_pt',            'p_{T}(ll) (GeV)',              lambda c : min(protectedZpt(c                                                              , 0. ) ,ZptBinRec[-1]       -0.001 )   ,ZptBinRec     ))
plotListOut.append(Plot('out_unfReco_l1l2_ptsum',      'p_{T}(l1)+p_{T}(l2) (GeV)',    lambda c : min(ifRec(c, c.l1_pt+c.l2_pt                                                              , 0. ) ,l1l2ptBinRec[-1]       -0.001 )   ,l1l2ptBinRec     ))

plotListRecFid.append(Plot('recFid_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))
plotListRecFid.append(Plot('recFid_unfReco_jetPt',           'p_{T}(j1) (GeV)',        lambda c : min(ifRec(c, c.j1_pt                                                              , 0. ) ,ptBinJetRec[-1]       -0.001 )   ,ptBinJetRec     ))
plotListRecFid.append(Plot('recFid_unfReco_jetLepDeltaR',    '#DeltaR(l, j)',          lambda c : min(ifRec(c, min(c.l1JetDeltaR, c.l2JetDeltaR)                                    , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListRecFid.append(Plot('recFid_unfReco_phLepDeltaR',     '#DeltaR(#gamma, l)',     lambda c : min(ifRec(c, min(c.phL1DeltaR, c.phL2DeltaR)                                      , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListRecFid.append(Plot('recFid_unfReco_phLep1DeltaR',    '#DeltaR(#gamma, l1)',    lambda c : min(ifRec(c, c.phL1DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListRecFid.append(Plot('recFid_unfReco_phLep2DeltaR',    '#DeltaR(#gamma, l2)',    lambda c : min(ifRec(c, c.phL2DeltaR                                                         , 0. ) ,dRBinRec[-1]       -0.001 )   ,dRBinRec     ))
plotListRecFid.append(Plot('recFid_unfReco_phBJetDeltaR',    '#DeltaR(#gamma, b)',     lambda c : min(ifRec(c, kickUnder(0., 900., c.phBJetDeltaR)                                  , 0. ) ,dRBinJetRec[-1]    -0.001 )   ,dRBinJetRec  ))
plotListRecFid.append(Plot('recFid_unfReco_ll_absDeltaEta',  '|#Delta#eta(ll)|',       lambda c : min(ifRec(c, abs(protectedGet(c._lEta, c.l1) - protectedGet(c._lEta, c.l2))       , 0. ) ,absdEtaBinRec[-1]  -0.001 )   ,absdEtaBinRec))
plotListRecFid.append(Plot('recFid_unfReco_ll_deltaPhi',     '#Delta#phi(ll)',         lambda c : min(ifRec(c, deltaPhi(protectedGet(c._lPhi, c.l1), protectedGet(c._lPhi, c.l2))   , 0. ) ,dPhiBinRec[-1]     -0.001 )   ,dPhiBinRec   ))
plotListRecFid.append(Plot('recFid_unfReco_phAbsEta',        '|#eta|(#gamma)',         lambda c : min(ifRec(c, abs(protectedGet(c._phEta, c.ph))                                    , 0. ) ,absEtaBinRec[-1]   -0.001 )   ,absEtaBinRec ))
plotListRecFid.append(Plot('recFid_unfReco_Z_pt',            'p_{T}(ll) (GeV)',    lambda c : min(protectedZpt(c                                                              , 0. ) ,ZptBinRec[-1]       -0.001 )   ,ZptBinRec     ))
plotListRecFid.append(Plot('recFid_unfReco_l1l2_ptsum',            'p_{T}(l1)+p_{T}(l2) (GeV)',    lambda c : min(ifRec(c, c.l1_pt+c.l2_pt                                                              , 0. ) ,l1l2ptBinRec[-1]       -0.001 )   ,l1l2ptBinRec     ))



plotListOut.append(Plot('out_phpt',               'out_phpt',                                 lambda c : c.ph_pt                                       , (10, 0., 350.)     ))
plotListOut.append(Plot('out_phEta',              'out_phEta',                                lambda c : abs(c._phEta[c.ph])                           , (12, 0., 2.4)     ))
plotListOut.append(Plot('out_phCutBasedMedium',   'out_phCutBasedMedium',                     lambda c : int(c._phCutBasedMedium[c.ph])                , (2,  -0.5, 1.5)    ))
plotListOut.append(Plot('out_phGenuine',          'out_phGenuine',                            lambda c : int(checkMatch(c))                            , (2,  -0.5, 1.5)    ))
plotListOut.append(Plot('out_njets',              'out_Number of jets',                       lambda c : c.njets                                       , (8, -.5, 7.5)))
plotListOut.append(Plot('out_nbtag',              'out_Number of b-tagged jets',              lambda c : c.ndbjets                                     , (4, -.5, 3.5)))
plotListOut.append(Plot('out_dl_mass',            'out_m(ll) [GeV]',                          lambda c : c.mll                                         , (20, 0, 200)))
plotListOut.append(Plot('out_dlg_mass',           'out_m(ll#gamma) [GeV]',                    lambda c : c.mllg                                        , (40, 0, 500)))


plotListRecFid.append(Plot('recFid_phpt',               'recFid_phpt',                        lambda c : c.ph_pt                                      , (10, 0., 350.)     ))
plotListRecFid.append(Plot('recFid_phEta',              'recFid_phEta',                       lambda c : abs(c._phEta[c.ph])                          , (12, 0, 2.4)     ))
plotListRecFid.append(Plot('recFid_phCutBasedMedium',   'recFid_phCutBasedMedium',            lambda c : int(c._phCutBasedMedium[c.ph])               , (2,  -0.5, 1.5)    ))
plotListRecFid.append(Plot('recFid_phGenuine',          'recFid_phGenuine',                   lambda c : int(checkMatch(c))                           , (2,  -0.5, 1.5)    ))
plotListRecFid.append(Plot('recFid_njets',              'recFid_Number of jets',              lambda c : c.njets                                      , (8, -.5, 7.5)))
plotListRecFid.append(Plot('recFid_nbtag',              'recFid_Number of b-tagged jets',     lambda c : c.ndbjets                                    , (4, -.5, 3.5)))
plotListRecFid.append(Plot('recFid_dl_mass',            'recFid_m(ll) [GeV]',                 lambda c : c.mll                                        , (20, 0, 200)))
plotListRecFid.append(Plot('recFid_dlg_mass',           'recFid_m(ll#gamma) [GeV]',           lambda c : c.mllg                                       , (40, 0, 500)))



if args.runNLO: # only need fid plots for this
  plotListRecFid = []
  plotListRec = []
  plotListOut = []
  mList = []
  # Need this one for EFT uncertainties
  plotListRec.append(Plot('rec_unfReco_phPt',            'p_{T}(#gamma) (GeV)',    lambda c : min(ifRec(c, c.ph_pt                                                              , 0. ) ,ptBinRec[-1]       -0.001 )   ,ptBinRec     ))



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
    if args.sys:
      applySysToTree(sample.name, args.sys, c)
    c.fid = checkFid(c)
    c.rec = checkRec(c)

    prefireWeight = 1. if args.year == '2018' else c._prefireWeight

    phWeight = 1. if c.phWeight == 0. else c.phWeight

    generWeights = c.genWeight*lumiScale*c.ISRWeight*c.FSRWeight
    recoWeights  = c.lWeight*c.lTrackWeight*phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*c.PVWeight*c.puWeight
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


##### 1D plots #####
for plot in plotList:
  plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), args.sys)
  if args.sys: continue

  err = False
  if isinstance(plot, Plot2D): ##### 2D plots #####
    plot.applyMods()
    for drawOUFlow in [False, True]:
      if drawOUFlow: 
          plot.name += '_overflow'
          plot.histos.values()[0].GetXaxis().SetRange(0, plot.histos.values()[0].GetNbinsX() + 1)
          plot.histos.values()[0].GetYaxis().SetRange(0, plot.histos.values()[0].GetNbinsY() + 1)
      for logZ in [False, True]:
        for option in ['SCAT', 'COLZ', 'COLZ TEXT', 'COLZ TEXTclean', 'COLZclean']:
          err = plot.draw(plot_directory = os.path.join(plotDir, args.year, args.tag, 'noData' + ('-log' if logZ else ''), 'placeholderSelection', option),
                    logZ           = logZ,
                    drawOption     = option,
                    drawObjects    = drawLumi2D(None, lumiScales[args.year], isOnlySim=('noData'=='noData')))
  else: ##### 1D plots #####
    extraArgs = {}
    for logY in [False, True]:
      yRange = None
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



if noWarnings: 
  log.info('Plots made for ' + args.year)
  log.info('Finished')
else:          
  log.info('Could not produce all plots for ' + args.year)