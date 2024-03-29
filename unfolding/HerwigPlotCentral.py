#! /usr/bin/env python


#
# Argument parser and logging
#
import pdb
import os, argparse, numpy, glob
from ttg.tools.helpers import reducedTupleDir

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
argParser.add_argument('--stackName',    action='store',      default=None,                 help='')

argParser.add_argument('--sys',            action='store',      default='')
argParser.add_argument('--runSys',         action='store_true', default=False)
# argParser.add_argument('--runNLO',         action='store_true', default=False)

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
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR, lumiScales, lumiScalesRounded
from ttg.plots.plotHelpers  import *
from ttg.samples.Sample import createSampleList, getSampleFromList
import copy
import pickle
from math import pi
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList


reduceType = 'unfHECen'
# reduceType = 'unfFB'

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

# args.tag = args.tag + ('_NLO' if args.runNLO else '')


#  TODO remove trigger exception when ready 


# we just need these for fid level

# if args.runNLO:
#   systematics.clear()

# for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd'):
#   systematics['q2Sc_' + i] = [('genWeight', 'weight_q2Sc_'+i)]

# for i in range(0, 100):
#   systematics['pdfSc_' + str(i)] = [('genWeight', 'weight_pdfSc_' + str(i))]

if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [args.year]
  if args.sys:                   sysList = [args.sys]
  else:                          
    sysList = [None] + (systematics.keys() if args.runSys else [])
    excludeSys = ['NP']
    # excludeSys = ['trigger'] # NOTE temporary
    if sysList[0]:
      sysList = [entry for entry in sysList if not any([entry.count(exc) for exc in excludeSys])]
  submitJobs(__file__, ('sys'), [[s] for s in sysList], argParser, subLog= args.tag + '/' + args.year, jobLabel = "UF", wallTime="15")
  exit(0)

# NOTE WARNING using separate tuple files right now, but not needed, if samples get updated change this
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'))
stack = createStack(tuplesFile   = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unftuples_' + args.year + '.conf'),
                  styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/' + args.stackName + '.stack'),
                  # channel      = args.channel,
                  channel      = 'noData',
                  # replacements = getReplacementsForStack(args.sys, args.year)
                  )



########## RECO SELECTION ##########
# def checkRec(c):
#   if c.failReco:                                          return False
#   if not c._phCutBasedMedium[c.ph]:                       return False
#   if abs(c._phEta[c.ph]) > 1.4442:                        return False
#   c.checkMatch, c.genuine = True, True
#   c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False
#   if not checkMatch(c):                                   return False
#   if not c.ph_pt > 20:                                    return False
#   if not c.ndbjets>0:                                     return False
#   if not c.mll > 20:                                      return False
#   if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
#   if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False
#   return True


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


# same as in plotHelpers but without the undercores in variables
def plZpt(c):
  first  = getLorentzVector(c.PLl1_pt, c._pl_lEta[c.PLl1], c._pl_lPhi[c.PLl1], c._pl_lE[c.PLl1])
  second = getLorentzVector(c.PLl2_pt, c._pl_lEta[c.PLl2], c._pl_lPhi[c.PLl2], c._pl_lE[c.PLl2])
  return (first+second).Pt()


plotListRecFid = []
plotListRec = []
plotListOut = []
plotListFid = []
mList = []


# ptBinRec = [20., 35., 50., 65., 80., 100., 120., 140., 160., 180., 200., 230., 260., 290., 320., 380.]
# ptBinGen = [20., 35., 50., 65., 80., 120., 160., 200., 260., 320., 400.]

# dRBinRec = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4]
# dRBinGen = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.4]

# absEtaBinRec = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
# absEtaBinGen = [0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.45]

# dPhiBinRec = (16, 0., 3.2)
# dPhiBinGen = (8, 0., 3.2)

# NOTE under should be -1. for this distribution, not 0. like all
# cosBinRec = (16, -1., 1.)
# cosBinGen = (8, -1., 1.)

# absdEtaBinRec = [0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25, 2.5, 2.75, 3, 3.25, 4.5]
# absdEtaBinGen = [0., 0.5, 1., 1.5, 2.,  2.5, 3., 4.5]

# dRBinJetRec = [0.4, 0.6, 0.8, 1.05, 1.3, 1.6, 1.9, 2.25, 2.6, 3., 3.4]
# dRBinJetGen = [0.4, 0.8, 1.3, 1.9, 2.6, 3.4]

# ptBinJetGen = [30., 60., 100., 150., 250., 400.]
# ptBinJetRec = [30., 45., 60., 80., 100., 125., 150., 200., 250., 325., 400.]


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

# absdEtaBinRec = [0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25, 2.5, 3.5, 4.5]
absdEtaBinRec = [0., 0.25, 0.5, 0.75, 1., 1.25, 1.5, 1.75, 2., 2.25, 2.5, 2.75, 3, 3.25, 4.5]
absdEtaBinGen = [0., 0.5, 1., 1.5, 2.,  2.5, 3., 4.5]

dRBinJetRec = [0.4, 0.6, 0.8, 1.05, 1.3, 1.6, 1.9, 2.25, 2.6, 3., 3.4]
dRBinJetGen = [0.4, 0.8, 1.3, 1.9, 2.6, 3.4]

# ptBinJetRec = [30., 50., 70., 90., 110., 130., 150., 175., 200., 250., 300., 375., 450.]
# ptBinJetGen = [30., 70., 110., 150., 200., 300., 450.]

ptBinJetRec = [30., 55., 80., 110., 140., 170., 200., 250., 300., 375., 450.]
ptBinJetGen = [30., 80., 140., 200., 300., 450.]


# l1l2 scalar pt sum should start at 25+15 =40
# pT(ll) could I guess go down to 0, testing



ZptBinRec = [0., 15., 30., 45., 60., 75., 90., 110., 130., 170., 210., 310., 410.]
ZptBinGen = [0., 30., 60., 90., 130., 210., 410.]

l1l2ptBinRec = [40., 55., 70., 85., 100., 120., 140., 165., 190., 220., 250., 290., 330., 400., 500.]
l1l2ptBinGen = [40., 70., 100., 140., 190., 250., 330., 500.]

# plotList.append(Plot('unfReco_Z_pt',            'p_{T}(ll) (GeV)',                lambda c : Zpt(c),                                            ZptBinRec))
# plotList.append(Plot('unfReco_l1l2_ptsum',      'p_{T}(l1)+p_{T}(l2) (GeV)',      lambda c : c.l1_pt+c.l2_pt,                                   l1l2ptBinRec))





# plotList.append(Plot('unfReco_ll_cosTheta',     '#cos(theta(ll))',                lambda c : numpy.cos(angle(theta(c._lEta[c.l1]), theta(c._lEta[c.l2]), c._lPhi[c.l1], c._lPhi[c.l2]))   ,          cosBinRec    ))

# for systematic variations we only want the response matrices
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
plotListFid.append(Plot('fid_unfReco_Z_pt',            'gen p_{T}(ll) (GeV)', lambda c : min(     plZpt(c)                                                                     ,ZptBinGen[-1]       -0.001 )   ,ZptBinGen     ))
plotListFid.append(Plot('fid_unfReco_l1l2_ptsum',      'gen p_{T}(l1)+p_{T}(l2) (GeV)', lambda c : min(      c.PLl1_pt+c.PLl2_pt                                             ,l1l2ptBinGen[-1]       -0.001 )   ,l1l2ptBinGen     ))


plotListFid.append(Plot('fid_njets',                   'gen number of jets',                        lambda c : c.PLnjets,                                            (8, -.5, 7.5)))
plotListFid.append(Plot('fid_nbtag',                   'gen number of medium b-tags (deepCSV)',     lambda c : c.PLndbjets,                                          (4, -.5, 3.5)))


########## EVENTLOOP ##########
# TODO setIDSelection(c, args.tag) nodig?
from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
lumiScale = lumiScales[args.year]
# reduceType = applySysToReduceType(reduceType, args.sys)
log.info("using reduceType " + reduceType)

def initTreeHack(sample, shortDebug=False, reducedType=None, splitData=None):
  if reducedType:
    sample.chain        = ROOT.TChain('blackJackAndHookersTree')
    sample.listOfFiles  = []
    for samp, productionLabel in sample.addSamples:
      sample.listOfFiles += glob.glob(os.path.join(reducedTupleDir, productionLabel, reducedType, samp[4:] if samp[:4] in ['2016', '2017', '2018'] else samp, '*.root'))
  else:
    sample.chain = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
    sample.listOfFiles = sample.getListOfFiles(splitData)
  if shortDebug: sample.listOfFiles = sample.listOfFiles[:3]
  if not len(sample.listOfFiles): log.error('No tuples to run over for ' + sample.name)
  for path in sample.listOfFiles:
    log.debug("Adding " + path)
    sample.chain.Add(path)
  return sample.chain

for sample in sum(stack, []):
  # pdb.set_trace()
  c = initTreeHack(sample, reducedType = reduceType)
  for i in sample.eventLoop():
    
    c.GetEntry(i)

    # c.ISRWeight = 1.
    # c.FSRWeight = 1.
    # log.info(c.lWeight)
    # log.info(c.lWeight)
    # log.info('........................')
    c.fid = checkFid(c)


    eventWeight = c.genWeight*lumiScale

    if c.fid:
      fillPlots(plotListFid, sample, eventWeight)

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
                    drawObjects    = drawLumi(None, lumiScales[args.year], isOnlySim=('noData'=='noData')))
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