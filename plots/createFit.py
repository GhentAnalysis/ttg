#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.tools.logger       import getLogger
log = getLogger(logLevel=args.logLevel)

from ttg.tools.helpers      import addHist
from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts
from ttg.plots.systematics  import systematics, linearSystematics

import os, ROOT, shutil
ROOT.gROOT.SetBatch(True)

from math import sqrt

samples     = [('TTGamma', None), ('TTJets', 5.5), ('ZG', 10), ('DY', 10), ('other', 50)]

#
# Helper functions
#
def protectHist(hist):
  if hist.Integral() < 0.00001:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
  return hist

def applyNonPromptSF(histTemp, nonPromptSF, sys=None):
  if not nonPromptSF: 
    return histTemp
  hist = histTemp.Clone()
# srMap = {1:'njet1-deepbtag1p', 2:'njet2p-deepbtag0', 3:'njet2p-deepbtag1', 4:'njet2p-deepbtag2p'}
  srMap = {1:'all', 2:'all', 3:'all', 4:'all'}
  for bin, sr in srMap.iteritems():
    if sys and sys=="Up":     sf = nonPromptSF[sr][0] + nonPromptSF[sr][1]
    elif sys and sys=="Down": sf = nonPromptSF[sr][0] + nonPromptSF[sr][2]
    else:                     sf = nonPromptSF[sr][0]
    hist.SetBinContent(bin, hist.GetBinContent(bin)*sf)
  return hist

def replaceShape(hist, shape):
  normalization = hist.Integral("width")/shape.Integral("width")
  hist = shape.Clone()
  hist.Scale(normalization)
  return hist

def writeHist(file, name, template, histTemp, norm=None, removeBins = [], shape=None, mergeBins=False):
  hist = histTemp.Clone()
  if norm:  normalizeBinWidth(hist, norm)
  if shape: hist = replaceShape(hist, shape)
  for i in removeBins:
    hist.SetBinContent(i, 0)
    hist.SetBinError(i, 0)
  if mergeBins:
    hist.Rebin(hist.GetNbinsX())
  if not file.GetDirectory(name): file.mkdir(name)
  file.cd(name)
  protectHist(hist).Write(template)

# Create combine directory
try:    os.makedirs('combine')
except: pass


#
# ROOT File for a charged isolation only fit
#
def writeRootFileForChgIso(name, systematics, selection):
  tag       = 'eleSusyLoose-phoCBnoChgIso-match'
  plot      = 'photon_chargedIso_bins_NO'

  if selection=='all': selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'
  else:                selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'

  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  dataHist = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
  writeHist(f, 'chgIso' , 'data_obs', dataHist,norm=1)

  from ttg.plots.plot import applySidebandUnc
  for splitType in ['_g', '_f', '_h']:
    if   splitType=='_g': selectors = [[sample, '(genuine,misIdEle)'] for sample,_ in samples]
    elif splitType=='_f': selectors = [[sample, '(hadronicFake)']     for sample,_ in samples]
    elif splitType=='_h': selectors = [[sample, '(hadronicPhoton)']   for sample,_ in samples]

    if name.count('dd') and splitType=='_f':
      sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
      normalizeBinWidth(sideBandShape, 1)
      sideBandShapeUp   = applySidebandUnc(sideBandShape, plot, selection, True)
      sideBandShapeDown = applySidebandUnc(sideBandShape, plot, selection, False)
      
      chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, sys, *selectors)
      writeHist(f, 'chgIso',                'all' + splitType, chgIsoHist, norm=1, shape=sideBandShape)
      writeHist(f, 'chgIsoSideBandUncUp',   'all' + splitType, chgIsoHist, norm=1, shape=sideBandShapeUp)
      writeHist(f, 'chgIsoSideBandUncDown', 'all' + splitType, chgIsoHist, norm=1, shape=sideBandShapeDown)
    else:
      for sys in [''] + systematics:
        chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, sys, *selectors)
        writeHist(f, 'chgIso'+sys,  'all' + splitType, chgIsoHist, norm=1)

  f.Close()

#
# Post-fit plots for charged isolation fit
#
from ttg.plots.plot import Plot
from ttg.tools.style import drawLumi
import ttg.tools.style as styles
def plotChgIso(name, name2, results):
  f = ROOT.TFile('combine/' + name + '_shapes.root')
  all_f      = f.Get('chgIso/all_f')
  all_g      = f.Get('chgIso/all_g')
  all_h      = f.Get('chgIso/all_h')
  data       = f.Get('chgIso/data_obs')

  if results:
    all_f.Scale(results['r'][0])
    all_g.Scale(results['prompt_norm'][0])

  data.style  = styles.errorStyle(ROOT.kBlack)
  all_g.style = styles.fillStyle(ROOT.kYellow) 
  all_h.style = styles.fillStyle(ROOT.kRed) 
  all_f.style = styles.fillStyle(ROOT.kGreen)

  data.texName  = 'data'
  all_g.texName = 'genuine'
  all_h.texName = 'hadronic photons'
  all_f.texName = 'hadronic fakes (from sideband)'

  plot       = Plot(name + name2, 'chargedIso(#gamma) (GeV)', None, None, overflowBin=None, stack=[[]], texY='Events')
  plot.stack = [[all_g, all_h, all_f], [data]]
  plot.histos = {i:i for i in sum(plot.stack, [])}

  plot.draw(plot_directory = '/user/tomc/www/ttG/combinePlots/',
    ratio   = {'yRange':(0.1,1.9),'texY': 'ratio'},
    logX    = False, logY = False, sorting = False,
    yRange  = (0.0001, "auto"),
    drawObjects = drawLumi(None, 35.9),
  )

#
# Charged isolation fit
#
log.info(' --- Charged isolation fit --- ')
templates   = ['all_f', 'all_g', 'all_h']
extraLines  = ['prompt_norm   rateParam * all_g 1']
extraLines += ['* autoMCStats 0 1 1']

nonPromptSF = {}
#for selection in ['njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p','all']:
for selection in ['all']:
  for dataDriven in [True]:
    cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + selection
    writeRootFileForChgIso(cardName, [], selection)
    writeCard(cardName, ['chgIso'], templates, [], extraLines, ['all_f:SideBandUncUp'], {})
    results = runFitDiagnostics(cardName, toys=None, statOnly=False, trackParameters = ['prompt_norm'])
    nonPromptSF[selection] = results['r']
    plotChgIso(cardName, '_prefit',  None)
    plotChgIso(cardName, '_postfit', results)
    runImpacts(cardName)

for i,j in nonPromptSF.iteritems():
  log.info('Charged isolation fit for ' + i + ' results in %.2f (+%.2f, %.2f)' % j)

#############################################################################################################################################

#
# ROOT file for a signal regions fit
#
def writeRootFile(name, systematics, nonPromptSF):
  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'
  onZSelection  = 'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20'
  writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-match', 'emu', baseSelection), 'signalRegionsSmall', '', ['MuonEG']))
  writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-match', 'SF',  baseSelection), 'signalRegionsSmall', '', ['DoubleEG'],['DoubleMuon']))
  writeHist(f, 'zg_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-match', 'SF',  onZSelection),  'signalRegionsSmall', '', ['DoubleEG'],['DoubleMuon']), mergeBins=True)

  for sample,_ in samples:
    promptSelectors   = [[sample, '(genuine,misIdEle)']]
    fakeSelectors     = [[sample, '(hadronicFake)']]
    hadronicSelectors = [[sample, '(hadronicPhoton)']]
    for sys in [''] + systematics:
      for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF'), ('zg_SF', 'SF')]:
        prompt   = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *promptSelectors)
        fake     = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *fakeSelectors)
        hadronic = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *hadronicSelectors)
        if sys=='':
          fakeUp   = applyNonPromptSF(fake, nonPromptSF, 'Up')
          fakeDown = applyNonPromptSF(fake, nonPromptSF, 'Down')
        fake     = applyNonPromptSF(fake, nonPromptSF)
        total = prompt.Clone()
        total.Add(hadronic)
        if sys=='':
          totalUp   = total.Clone()
          totalDown = total.Clone()
          totalUp.Add(fakeUp)
          totalDown.Add(fakeDown)
          writeHist(f, shape+'fakeUp',   sample, totalUp, mergeBins = ('zg' in shape))
          writeHist(f, shape+'fakeDown', sample, totalDown, mergeBins = ('zg' in shape))
        total.Add(fake)

        if sample=='ZG' and False:
          for i in range(total.GetNbinsX()):
            total.SetBinContent(i, total.GetBinContent(i)*(zgSF[0]))
        writeHist(f, shape+sys, sample, total, mergeBins = ('zg' in shape))

  f.Close()

#
# Signal regions fit
#
def doSignalRegionFit(cardName, shapes, perPage=30):
  log.info(' --- Signal regions fit (' + cardName + ') --- ')
  templates   = [s for s,_ in samples]
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1')   for s,_   in samples[1:]]
  extraLines += [(s + '_norm param 1.0 ' + str(unc/100.)) for s,unc in samples[1:]]
  extraLines += ['* autoMCStats 0 1 1']

  writeRootFile(cardName, systematics.keys(), nonPromptSF)
  writeCard(cardName, shapes, templates, [], extraLines, systematics.keys() + ['fakeUp'], linearSystematics, scaleShape={'fsr': 1/sqrt(2)})

  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=True)
  runImpacts(cardName, perPage)
  runSignificance(cardName)
  runSignificance(cardName, expected=True)

doSignalRegionFit('srFit'      , ['sr_OF', 'sr_SF', 'zg_SF'], 32)
doSignalRegionFit('srFit_SF'   , ['sr_SF', 'zg_SF'], 28)
doSignalRegionFit('srFit_OF'   , ['sr_OF', 'zg_SF'], 28)

def doRatioFit(cardName, shapes, perPage=30):
  log.info(' --- Ratio ttGamma/ttBar fit (' + cardName + ') --- ')
  templates   = [s for s,_ in samples]
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1')   for s,_   in samples[1:]]
  extraLines += [(s + '_norm param 1.0 ' + str(unc/100.)) for s,unc in samples[1:]]
  extraLines += ['* autoMCStats 0 1 1']
  from ttg.samples.Sample import createSampleList,getSampleFromList
  sampleList   = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples.conf'))
  xsec_ttGamma = sum([getSampleFromList(sampleList, s).xsec for s in ['TTGamma', 'TTGamma_t', 'TTGamma_tbar', 'TTGamma_had']])
  xsec_tt      = getSampleFromList(sampleList, 'TTJets_pow').xsec
  extraLines += ['renormTTGamma rateParam * TTGamma* %.7f' % (1./xsec_ttGamma), 'nuisance edit freeze renormTTGamma ifexists']
  extraLines += ['renormTTbar rateParam * TTJets* %.7f' % (1./xsec_tt),         'nuisance edit freeze renormTTbar ifexists']
  extraLines += ['TTbar_norm rateParam * TT* %.7f' % xsec_tt]

  writeRootFile(cardName, systematics.keys(), nonPromptSF)
  writeCard(cardName, shapes, templates, [], extraLines, systematics.keys() + ['fakeUp'], linearSystematics, scaleShape={'fsr': 1/sqrt(2)})

  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)


doRatioFit('ratioFit'   , ['sr_OF', 'sr_SF', 'zg_SF'], 32)
doRatioFit('ratioFit_SF', ['sr_SF', 'zg_SF'], 28)
doRatioFit('ratioFit_OF', ['sr_OF', 'zg_SF'], 28)
