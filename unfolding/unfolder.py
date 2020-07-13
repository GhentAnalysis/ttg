#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',     help='Specify type of reducedTuple')
argParser.add_argument('--var',       action='store',      default='phPt',               help='variable to unfold')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
# argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.tools.style import drawLumi
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR
from ttg.samples.Sample import createSampleList, getSampleFromList
import copy
import pickle

lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
# unfVars = {'phPt': ['_ph_pt', [10, 220, 20], 'plPhPt', [30, 220, 20]]}
reduceType = 'UnfphoCBNew'


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  jobs = [args.year]
  submitJobs(__file__, ('year'), [jobs], argParser, subLog=args.tag, jobLabel = "UF")
  exit(0)

sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/NEWtuples_' + args.year + '.conf'))
stack = createStack(tuplesFile   = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/NEWtuples_' + args.year + '.conf'),
                  styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/unfolding/data/unfTTG.stack'),
                  # channel      = args.channel,
                  channel      = 'noData',
                  # replacements = getReplacementsForStack(args.sys, args.year)
                  )

def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  ttgHist = None
  otherHist = None
  dataHist = None
  for name, hist in hists.iteritems():
    if 'ttgamma' in name.lower():
      if not ttgHist: ttgHist = hist
      else: ttgHist.Add(hist)
    elif 'data' in name:
      if not dataHist: dataHist = hist
      else: dataHist.Add(hist)
    else:
      if not otherHist: otherHist = hist
      else: otherHist.Add(hist)
  return (ttgHist, otherHist, dataHist)



########## RECO SELECTION ##########
def checkRec(c):
  if c.failReco:                                          return False
  if not c._phCutBasedMedium[c.ph]:                       return False
  if abs(c._phEta[c.ph]) > 1.4442:                        return False
  c.checkMatch, c.genuine = True, True
  c.misIdEle,c.hadronicPhoton,c.hadronicFake,c.magicPhoton,c.mHad,c.mFake,c.unmHad,c.unmFake,c.nonPrompt = False,False,False,False,False,False,False,False,False
  if not checkMatch(c):                                   return False
  if not c.ph_pt > 20:                                    return False
  if not ((c.njets>1) or (c.njets==1 and c.ndbjets==1)):  return False
  return True


########## FIDUCIAL REGION ##########
def checkFid(c):
  if c.failFid:                                                 return False
  # TODO CHECK
  if abs(c._pl_phEta[c.PLph]) > 1.4442:                              return False
  if not c.PLph_pt > 20:                                        return False
  if not ((c.PLnjets>1) or (c.PLnjets==1 and c.PLndbjets==1)):  return False
  return True



########## PREPARE PLOTS ##########
Plot.setDefaults(stack=stack, texY = 'Events')
Plot2D.setDefaults(stack=stack)
from ttg.plots.plotHelpers  import *

def ifRec(c, val, under):
  if c.rec: return val
  else: return under-1.


# TODO  normalize along code might not be a great combo with the underflow system
plotListRecFid = []
# keep the unfolding matrix as the first entry!
plotListRecFid.append(Plot('RecFidnphoton',                         'number of photons',               lambda c : c.nphotons,                                         (4,  -0.5, 3.5)))
plotListRecFid.append(Plot('RecFidnjets',                           'number of jets',                  lambda c : c.njets,                                            (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidnbjets',                          'number of bjets',                 lambda c : c.ndbjets,                                          (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidPLnphoton',                       'number of PL photons',            lambda c : c.PLnphotons,                                       (4,  -0.5, 3.5)))
plotListRecFid.append(Plot('RecFidPLnjets',                         'number of PL jets',               lambda c : c.PLnjets,                                          (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidPLnbjets',                        'number of PL bjets',              lambda c : c.PLndbjets,                                        (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidsignalRegionsZoom',               'signal region',                   lambda c : createSignalRegionsZoom(c),                        (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))

plotListRec = []
plotListRec.append(Plot('Rec_nphoton',                  'number of photons',               lambda c : c.nphotons,                                       (4,  -0.5, 3.5)))
plotListRec.append(Plot('Rec_njets',                    'number of jets',                  lambda c : c.njets,                                          (9,  -0.5, 8.5)))
plotListRec.append(Plot('Rec_nbjets',                   'number of bjets',                 lambda c : c.ndbjets,                                        (9,  -0.5, 8.5)))
plotListRec.append(Plot('Rec_PLnphoton',                'number of PL photons',            lambda c : c.PLnphotons,                                     (4,  -0.5, 3.5)))
plotListRec.append(Plot('Rec_PLnjets',                  'number of PL jets',               lambda c : c.PLnjets,                                        (9,  -0.5, 8.5)))
plotListRec.append(Plot('Rec_PLnbjets',                 'number of PL bjets',              lambda c : c.PLndbjets,                                      (9,  -0.5, 8.5)))
plotListRec.append(Plot('Rec_signalRegionsZoom',        'signal region',                   lambda c : createSignalRegionsZoom(c),                       (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))

plotListFid = []
plotListFid.append(Plot('Fid_nphoton',                  'number of photons',               lambda c : c.nphotons,                                       (4,  -0.5, 3.5)))
plotListFid.append(Plot('Fid_njets',                    'number of jets',                  lambda c : c.njets,                                          (9,  -0.5, 8.5)))
plotListFid.append(Plot('Fid_nbjets',                   'number of bjets',                 lambda c : c.ndbjets,                                        (9,  -0.5, 8.5)))
plotListFid.append(Plot('Fid_PLnphoton',                'number of PL photons',            lambda c : c.PLnphotons,                                     (4,  -0.5, 3.5)))
plotListFid.append(Plot('Fid_PLnjets',                  'number of PL jets',               lambda c : c.PLnjets,                                        (9,  -0.5, 8.5)))
plotListFid.append(Plot('Fid_PLnbjets',                 'number of PL bjets',              lambda c : c.PLndbjets,                                      (9,  -0.5, 8.5)))
plotListFid.append(Plot('Fid_signalRegionsZoom',        'signal region',                   lambda c : createSignalRegionsZoom(c),                       (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))

plotListOut = []
plotListOut.append(Plot('Out_nphoton',                  'number of photons',               lambda c : c.nphotons,                                       (4,  -0.5, 3.5)))
plotListOut.append(Plot('Out_njets',                    'number of jets',                  lambda c : c.njets,                                          (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_nbjets',                   'number of bjets',                 lambda c : c.ndbjets,                                        (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_PLnphoton',                'number of PL photons',            lambda c : c.PLnphotons,                                     (4,  -0.5, 3.5)))
plotListOut.append(Plot('Out_PLnjets',                  'number of PL jets',               lambda c : c.PLnjets,                                        (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_PLnbjets',                 'number of PL bjets',              lambda c : c.PLndbjets,                                      (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_signalRegionsZoom',        'signal region',                   lambda c : createSignalRegionsZoom(c),                       (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))


plotListRecFid.append(Plot2D('response',                      'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) , (23, 20, 135), 'PL p_{T}(#gamma) (GeV)', lambda c : c.PLph_pt , (12, 20, 140)))
plotListRecFid.append(Plot2D('photon_pt_vsplx',               'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) , (23, 20, 135), 'PL p_{T}(#gamma) (GeV)', lambda c : c.PLph_pt , (12, 20, 140), histModifications=normalizeAlong('x') ))



########## EVENTLOOP ##########
# TODO setIDSelection(c, args.tag) nodig?
from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
lumiScale = lumiScales[args.year]
log.info("using reduceType " + reduceType)

for sample in sum(stack, []):
  c = sample.initTree(reducedType = reduceType)
  for i in sample.eventLoop():
    c.GetEntry(i)

    fid = checkFid(c)
    c.rec = checkRec(c)


    eventWeight = lumiScale * c.genWeight

    if c.rec and fid:
      fillPlots(plotListRecFid, sample, eventWeight)
    if c.rec:
      fillPlots(plotListRec, sample, eventWeight)
    if fid:
      fillPlots(plotListFid, sample, eventWeight)
    if c.rec and not fid:
      fillPlots(plotListOut, sample, eventWeight)


########## UNFOLDING ##########

# ##### setup ##### 
# response = plotList[0].histos.values()[0]
# regMode = ROOT.TUnfold.kRegModeCurvature
# constraintMode = ROOT.TUnfold.kEConstraintArea
# mapping = ROOT.TUnfold.kHistMapOutputVert
# densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
# unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )

# logTauX = ROOT.TSpline3()
# logTauY = ROOT.TSpline3()
# lCurve  = ROOT.TGraph()



# ##### unfold MC #####  sanity check
# recoMC = response.ProjectionX("recoMC")
# unfold.SetInput(recoMC)
# log.info('scan L curve')
# iBest   = unfold.ScanLcurve(30,1e-04,1e-03,lCurve,logTauX,logTauY)
# unfolded = unfold.GetOutput("unfolded")

# responseNU = response.Clone()
# for j in range(1, responseNU.GetYaxis().GetNbins()+1):
#   responseNU.SetBinContent(0, j, 0.)

# cunf = ROOT.TCanvas()
# unfolded.Draw()
# plMC = responseNU.ProjectionY("PLMC")
# plMC.SetLineColor(ROOT.kRed)
# plMC.Draw('same')
# # recoMC.SetLineColor(ROOT.kOrange)
# # recoMC.Draw('same')
# cunf.SaveAs('unfTestMC.pdf')


# ##### unfold data #####
# picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD-JUN/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt.pkl'
# ttgHist, otherHist, dataHist = sumHists(picklePath, 'photon_pt')
# dataHist.Add(otherHist, -1.)
# # TODO subtract outside migration fraction
# unfold.SetInput(dataHist)
# iBest   = unfold.ScanLcurve(30,1e-04,1e-03,lCurve,logTauX,logTauY)
# unfolded = unfold.GetOutput("unfoldedData")
# cunf = ROOT.TCanvas()
# # draw PL MC as well. don't expect a match if cuts are different though
# plMC = responseNU.ProjectionY("PLMC")
# plMC.SetLineColor(ROOT.kRed)
# plMC.Draw()
# unfolded.Draw('same')
# cunf.SaveAs('unfTestData.pdf')


# ##### plot MC vs data scaled to match total yeild #####
# cunf = ROOT.TCanvas()
# plMC = responseNU.ProjectionY("PLMC")
# plMC.SetLineColor(ROOT.kRed)
# plMC.Scale(unfolded.Integral()/ plMC.Integral())
# plMC.Draw()
# # plMC.Draw('same')
# unfolded.Draw('same')
# cunf.SaveAs('unfTestDataScaled.pdf')



########## PLOTTING ##########
plotList = plotListRecFid + plotListRec + plotListFid + plotListOut
noWarnings = True

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
  for drawOUFlow in [False, True]:
    if drawOUFlow: 
        plot.name += '_overflow'
        plot.histos.values()[0].GetXaxis().SetRange(0, plot.histos.values()[0].GetNbinsX() + 1)
        plot.histos.values()[0].GetYaxis().SetRange(0, plot.histos.values()[0].GetNbinsY() + 1)
    if not hasattr(plot, 'varY'): continue
    plot.applyMods()
    plot.saveToCache(os.path.join(plotDir, args.year, args.tag, 'noData', 'placeholderSelection'), '')
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ', 'COLZ TEXT']:
        plot.draw(plot_directory = os.path.join(plotDir, args.year, args.tag, 'noData' + ('-log' if logY else ''), 'placeholderSelection', option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScales[args.year], isOnlySim=('noData'=='noData')))


if noWarnings: 
  log.info('Plots made for ' + args.year)
  log.info('Finished')
else:          
  log.info('Could not produce all plots for ' + args.year)