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
argParser.add_argument('--var',       action='store',      default='phPt',               help='variable to unfold')
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

lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
# unfVars = {'phPt': ['_ph_pt', [10, 220, 20], 'plPhPt', [30, 220, 20]]}
reduceType = 'UnfphoCBNewWeights'


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
  if not c.mll > 40:                                      return False
  if not (abs(c.mll-91.1876)>15 or c.isEMu):              return False
  if not (abs(c.mllg-91.1876)>15 or c.isEMu):             return False
  return True


########## FIDUCIAL REGION ##########
def checkFid(c):
  if c.failFid:                                                 return False
  # TODO CHECK
  if abs(c._pl_phEta[c.PLph]) > 1.4442:                             return False
  if not c.PLph_pt > 20:                                            return False
  if not ((c.PLnjets>1) or (c.PLnjets==1 and c.PLndbjets==1)):      return False
  if not c.PLmll > 40:                                              return False
  if not (abs(c.PLmll-91.1876)>15 or c.isEMu):                      return False
  # if not (abs(c.PLmllg-91.1876)>15 or c.isEMu):                     return False
  return True




# def equalizeBins(hist):
#   nx = hist.GetXaxis().GetNbins()
#   ny = hist.GetYaxis().GetNbins()
  
#   newHist = ROOT.TH2F(hist.GetName(), hist.GetName(), nx, numpy.array(range(nx+1)).astype(float), ny, numpy.array(range(ny+1)).astype(float))
#   for i in range(nx+1):
#     for j in range(ny+1):
#       newHist.SetBinContent(i,j, hist.GetBinContent(i, j))
#       newHist.SetBinError(i,j, hist.GetBinError(i, j))
#   return newHist


########## PREPARE PLOTS ##########
Plot.setDefaults(stack=stack, texY = 'Events')
Plot2D.setDefaults(stack=stack)
from ttg.plots.plotHelpers  import *

def ifRec(c, val, under):
  if c.rec: return val
  else: return under-1.


compBinA = [20., 23., 26., 29., 32., 35., 40., 45., 50., 55., 65., 75., 85., 100., 130., 180., 300.]
compBinB = [20., 35., 50., 65., 80., 95., 110., 140., 180., 300.]
# TODO  normalize along code might not be a great combo with the underflow system
plotListRecFid = []
plotListRecFid.append(Plot('RecFidnphoton',                         'number of photons',               lambda c : c.nphotons,                                         (4,  -0.5, 3.5)))
plotListRecFid.append(Plot('RecFidnjets',                           'number of jets',                  lambda c : c.njets,                                            (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidnbjets',                          'number of bjets',                 lambda c : c.ndbjets,                                          (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidPLnphoton',                       'number of PL photons',            lambda c : c.PLnphotons,                                       (4,  -0.5, 3.5)))
plotListRecFid.append(Plot('RecFidPLnjets',                         'number of PL jets',               lambda c : c.PLnjets,                                          (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidPLnbjets',                        'number of PL bjets',              lambda c : c.PLndbjets,                                        (9,  -0.5, 8.5)))
plotListRecFid.append(Plot('RecFidsignalRegionsZoom',               'signal region',                   lambda c : createSignalRegionsZoom(c),                        (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))

plotListRecFid.append(Plot('RecFid_PLph_ptA',                  'PLphoton pT',               lambda c : c.PLph_pt,  compBinA))
plotListRecFid.append(Plot('RecFid_PLph_ptB',                  'PLphoton pT',               lambda c : c.PLph_pt,  compBinB))

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

plotListFid.append(Plot('Fid_PLph_ptA',                  'PLphoton pT',               lambda c : c.PLph_pt,  compBinA))
plotListFid.append(Plot('Fid_PLph_ptB',                  'PLphoton pT',               lambda c : c.PLph_pt,  compBinB))

plotListFid.append(Plot2D('response',                'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  (23, 20, 135),    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , (12, 20, 140)))
plotListFid.append(Plot2D('responseOther',           'PL p_{T}(#gamma) (GeV)',          lambda c : c.PLph_pt ,               (12, 20, 140),    'p_{T}(#gamma) (GeV)',        lambda c : ifRec(c, c.ph_pt, 20.) , (23, 20, 135)))
plotListFid.append(Plot2D('photon_pt_vsplx',         'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  (23, 20, 135),    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , (12, 20, 140), histModifications=normalizeAlong('x') ))


plotListFid.append(Plot2D('compA_response',                'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  compBinA,    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , compBinA, histModifications=[ equalBinning()]                          ))
plotListFid.append(Plot2D('compA_responseOther',           'PL p_{T}(#gamma) (GeV)',          lambda c : c.PLph_pt ,               compBinA,    'p_{T}(#gamma) (GeV)',        lambda c : ifRec(c, c.ph_pt, 20.) , compBinA, histModifications=[ equalBinning()]             ))
plotListFid.append(Plot2D('compA_photon_pt_vsplx',         'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  compBinA,    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , compBinA, histModifications=[normalizeAlong('x'), equalBinning()] ))


plotListFid.append(Plot2D('compB_response',                'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  compBinB,    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , compBinB , histModifications=[equalBinning()]                         ))
plotListFid.append(Plot2D('compB_responseOther',           'PL p_{T}(#gamma) (GeV)',          lambda c : c.PLph_pt ,               compBinB,    'p_{T}(#gamma) (GeV)',        lambda c : ifRec(c, c.ph_pt, 20.) , compBinB, histModifications=[equalBinning()]             ))
plotListFid.append(Plot2D('compB_photon_pt_vsplx',         'p_{T}(#gamma) (GeV)',             lambda c : ifRec(c, c.ph_pt, 20.) ,  compBinB,    'PL p_{T}(#gamma) (GeV)',     lambda c : c.PLph_pt , compBinB, histModifications=[normalizeAlong('x'), equalBinning()] ))


plotListOut = []
plotListOut.append(Plot('Out_nphoton',                  'number of photons',               lambda c : c.nphotons,                                       (4,  -0.5, 3.5)))
plotListOut.append(Plot('Out_njets',                    'number of jets',                  lambda c : c.njets,                                          (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_nbjets',                   'number of bjets',                 lambda c : c.ndbjets,                                        (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_PLnphoton',                'number of PL photons',            lambda c : c.PLnphotons,                                     (4,  -0.5, 3.5)))
plotListOut.append(Plot('Out_PLnjets',                  'number of PL jets',               lambda c : c.PLnjets,                                        (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_PLnbjets',                 'number of PL bjets',              lambda c : c.PLndbjets,                                      (9,  -0.5, 8.5)))
plotListOut.append(Plot('Out_signalRegionsZoom',        'signal region',                   lambda c : createSignalRegionsZoom(c),                       (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))

plotListOut.append(Plot('Out_ph_ptA',                  'photon pT',               lambda c : c.ph_pt,  compBinA))
plotListOut.append(Plot('Out_ph_ptB',                  'photon pT',               lambda c : c.ph_pt,  compBinB))


    # reconstruction = Plot(
    #                    name      = "reconstruction",
    #                    texX      = "p^{gen}_{T}(#gamma) / p^{reco}_{T}(#gamma)",
    #                    attribute = lambda event, sample: getattr( event, args.genPtVariable ) / event.PhotonGood0_pt if selection( event, sample ) else -999,
    #                    binning   = reconstructionBinning,
    #                    read_variables = read_variables,
    #                   )


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

    fid = checkFid(c)
    c.rec = checkRec(c)

    prefireWeight = 1. if args.year == '2018' else c._prefireWeight

    phWeight = 1. if c.phWeight == 0. else c.phWeight
    eventWeight = c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*lumiScale*c.ISRWeight*c.FSRWeight*c.PVWeight
    # eventWeight = lumiScale * c.genWeight

    if c.rec and fid:
      fillPlots(plotListRecFid, sample, eventWeight)
    if c.rec:
      fillPlots(plotListRec, sample, eventWeight)
    if fid:
      fillPlots(plotListFid, sample, eventWeight)
    if c.rec and not fid:
      fillPlots(plotListOut, sample, eventWeight)


########## PLOTTING ##########
plotList = plotListRecFid + plotListRec + plotListFid + plotListOut
noWarnings = True

matrix = [i for i in plotListFid if i.name=='compA_response'][0]
matrix = matrix.histos.values()[0]
reco   = matrix.ProjectionX("recoMC")
pl = matrix.ProjectionY("pl")
efficiency = pl.Clone( "efficiency")
purity     = pl.Clone( "purity")
efficiency.Reset("ICES")
purity.Reset("ICES")

for i in range(1, pl.GetXaxis().GetNbins()+1):
    genPt   = pl.GetBinCenter( i+1 )
    recoBin = reco.FindBin( genPt )
    genVal     = pl.GetBinContent( i+1 )
    eff     = matrix.GetBinContent( i+1, recoBin ) / genVal if genVal else 0.
    efficiency.SetBinContent( i+1, eff )

for i in range(1, reco.GetXaxis().GetNbins()+1):
    recoPt = reco.GetBinCenter( i+1 )
    genBin = pl.FindBin( recoPt )
    recoVal   = reco.GetBinContent( i+1 )
    pur    = matrix.GetBinContent( genBin, i+1 ) / recoVal if recoVal else 0.
    purity.SetBinContent( i+1, pur )

eff = ROOT.TCanvas()
efficiency.Draw()
eff.SaveAs('effA.pdf')

pur = ROOT.TCanvas()
purity.Draw()
pur.SaveAs('purA.pdf')


matrix = [i for i in plotListFid if i.name=='compB_response'][0]
matrix = matrix.histos.values()[0]
reco   = matrix.ProjectionX("recoMC")
pl = matrix.ProjectionY("pl")
efficiency = pl.Clone( "efficiency")
purity     = pl.Clone( "purity")
efficiency.Reset("ICES")
purity.Reset("ICES")

for i in range(1, pl.GetXaxis().GetNbins()+1):
    genPt   = pl.GetBinCenter( i+1 )
    recoBin = reco.FindBin( genPt )
    genVal     = pl.GetBinContent( i+1 )
    eff     = matrix.GetBinContent( i+1, recoBin ) / genVal if genVal else 0.
    efficiency.SetBinContent( i+1, eff )

for i in range(1, reco.GetXaxis().GetNbins()+1):
    recoPt = reco.GetBinCenter( i+1 )
    genBin = pl.FindBin( recoPt )
    recoVal   = reco.GetBinContent( i+1 )
    pur    = matrix.GetBinContent( genBin, i+1 ) / recoVal if recoVal else 0.
    purity.SetBinContent( i+1, pur )

eff = ROOT.TCanvas()
efficiency.Draw()
eff.SaveAs('effB.pdf')

pur = ROOT.TCanvas()
purity.Draw()
pur.SaveAs('purB.pdf')

# respmat = [i for i in plotListFid if i.name=='comp_photon_pt_vsplx'][0]
# respmat = respmat.histos.values()[0]
# respmatB = equalizeBins(respmat)

exit()

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