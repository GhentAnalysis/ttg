#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.tools.logger       import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts, goodnessOfFit, doLinearityCheck
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, rateParameters
from ttg.plots.replaceShape import replaceShape

import os, ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt

templates       = ['TTGamma', 'TTJets', 'ZG', 'DY', 'other', 'single-t']
templatesChgIso = ['TTGamma', 'TTJets', 'ZG', 'DY', 'other'] # Stacks for chgIso fit have single-t merged into other

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
  for i, sr in srMap.iteritems():
    err = max(abs(nonPromptSF[sr][1]), abs(nonPromptSF[sr][2])) # fix for failed fits
    if sys and sys == "Up":     sf = nonPromptSF[sr][0] + err
    elif sys and sys == "Down": sf = nonPromptSF[sr][0] - err
    else:                       sf = nonPromptSF[sr][0]
    hist.SetBinContent(i, hist.GetBinContent(i)*sf)
  return hist

def writeHist(rootFile, name, template, histTemp, norm=None, removeBins = None, shape=None, mergeBins=False):  # pylint: disable=R0913
  hist = histTemp.Clone()
  if norm:  normalizeBinWidth(hist, norm)
  if shape: hist = replaceShape(hist, shape)
  if removeBins:
    for i in removeBins:
      hist.SetBinContent(i, 0)
      hist.SetBinError(i, 0)
  if mergeBins:
    hist.Rebin(hist.GetNbinsX())
  if not rootFile.GetDirectory(name): rootFile.mkdir(name)
  rootFile.cd(name)
  protectHist(hist).Write(template)

# Create combine directory
try:    os.makedirs('combine')
except: pass


#
# ROOT File for a charged isolation only fit
#
def writeRootFileForChgIso(name, systematicVariations, selection):
  tag       = 'eleSusyLoose-phoCBnoChgIso-match'
  plot      = 'photon_chargedIso_bins_NO'

  if selection == 'all': selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'
  else:                  selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'

  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  dataHist = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
  writeHist(f, 'chgIso', 'data_obs', dataHist, norm=1)

  from ttg.plots.plot import applySidebandUnc
  for splitType in ['_g', '_f', '_h']:
    if   splitType == '_g': selectors = [[t, '(genuine,misIdEle)'] for t in templatesChgIso]
    elif splitType == '_f': selectors = [[t, '(hadronicFake)']     for t in templatesChgIso]
    elif splitType == '_h': selectors = [[t, '(hadronicPhoton)']   for t in templatesChgIso]

    if name.count('dd') and splitType=='_f':
      sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
      normalizeBinWidth(sideBandShape, 1)
      sideBandShapeUp   = applySidebandUnc(sideBandShape, plot, selection, True)
      sideBandShapeDown = applySidebandUnc(sideBandShape, plot, selection, False)
      
      chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, '', *selectors)
      writeHist(f, 'chgIso',                'all' + splitType, chgIsoHist, norm=1, shape=sideBandShape)
      writeHist(f, 'chgIsoSideBandUncUp',   'all' + splitType, chgIsoHist, norm=1, shape=sideBandShapeUp)
      writeHist(f, 'chgIsoSideBandUncDown', 'all' + splitType, chgIsoHist, norm=1, shape=sideBandShapeDown)
    else:
      for sys in [''] + systematicVariations:
        chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, sys, *selectors)
        writeHist(f, 'chgIso'+sys,  'all' + splitType, chgIsoHist, norm=1)

  # Add also sigmaIetaIeta sideband itself for fake normalization [assume that it is similar in sideband as in nominal region] 
  # In this way, the charged isolation fit can focus on the hadronic normalization
  plot = 'photon_SigmaIetaIeta'
  dataHist = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-matchCombined', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
  writeHist(f, 'sigEtaEta', 'data_obs', dataHist)
  for splitType in ['_g', '_f', '_h']:
    if   splitType == '_g': selectors = [[sample, '(genuine photons)'] for sample in ['TTGamma', 'TTJets', 'DY']] + [[sample, '(misidentified electrons)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    if   splitType == '_h': selectors = [[sample, '(hadronic photons)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    if   splitType == '_f': selectors = [[sample, '(hadronic fakes)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    for sys in [''] + systematicVariations:
      hist = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-matchCombined', 'all', selection), plot, sys, *selectors)
      writeHist(f, 'sigEtaEta'+sys,  'all' + splitType, hist)
  f.Close()

#
# Post-fit plots for charged isolation fit
#
from ttg.plots.plot import Plot
from ttg.tools.style import drawLumi
import ttg.tools.style as styles
def plotPostFit(filename, name, name2, res):
  f = ROOT.TFile('combine/' + filename + '_shapes.root')
  all_f      = f.Get(name + '/all_f')
  all_g      = f.Get(name + '/all_g')
  all_h      = f.Get(name + '/all_h')
  data       = f.Get(name + '/data_obs')

  if res:
    all_g.Scale(res['r'][0])
    all_f.Scale(res['fake_norm'][0])
    all_h.Scale(res['hadronic_norm'][0])

  data.style  = styles.errorStyle(ROOT.kBlack)
  all_g.style = styles.fillStyle(ROOT.kYellow) 
  all_h.style = styles.fillStyle(ROOT.kRed) 
  all_f.style = styles.fillStyle(ROOT.kGreen)

  data.texName  = 'data (dilepton)'
  all_g.texName = 'genuine'
  all_h.texName = 'hadronic photons'
  all_f.texName = 'hadronic fakes (from sideband)' if name == 'chgIso' else 'hadronic fakes'

  plot       = Plot(name + name2, 'Photon Ch. Had. Isolation (GeV)' if name=='chgIso' else '#sigma_{i#eta i#eta}', None, None, overflowBin=None, stack=[[]], texY='Events / GeV')
  plot.stack = [[all_g, all_h, all_f], [data]]
  plot.histos = {i:i for i in sum(plot.stack, [])}

  plot.draw(plot_directory = '/user/tomc/www/ttG/combinePlots/',
    ratio   = {'yRange':(0.1,1.9),'texY': 'data/MC'},
    logX    = False, logY = False, sorting = False,
    yRange  = (0.0001, "auto"),
    drawObjects = drawLumi(None, 35.9),
  )

#
# Charged isolation fit
#
fakeSF, hadronicSF = {}, {}
def doChgIsoFit():
  log.info(' --- Charged isolation fit --- ')
  templatesPh = ['all_g', 'all_f', 'all_h']
  extraLines  = ['fake_norm     rateParam * all_f 1']
  extraLines += ['hadronic_norm rateParam * all_h 1']#, 'hadronic_norm param 1.0 0.3']
  extraLines += ['* autoMCStats 0 1 1']

  #for sel in ['njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p','all']:
  for sel in ['all']:
    for dataDriven in [True]:
      cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + sel
      writeRootFileForChgIso(cardName, [], sel)
      writeCard(cardName, ['chgIso', 'sigEtaEta'], templatesPh, None, extraLines, ['all_f:chgIso:SideBandUnc'], {})
      results = runFitDiagnostics(cardName, toys=False, statOnly=False, trackParameters = ['hadronic_norm','fake_norm'])
      fakeSF[sel]     = results['fake_norm']
      hadronicSF[sel] = results['hadronic_norm']
      plotPostFit(cardName, 'chgIso', '_prefit',  None)
      plotPostFit(cardName, 'chgIso', '_postfit', results)
      plotPostFit(cardName, 'sigEtaEta', '_prefit',  None)
      plotPostFit(cardName, 'sigEtaEta', '_postfit', results)
      runImpacts(cardName)

  for j, k in fakeSF.iteritems():
    log.info('Charged isolation fit for ' + j + ' results in fakes: %.2f (+%.2f, %.2f)' % k)
  for j, k in hadronicSF.iteritems():
    log.info('Charged isolation fit for ' + j + ' results in hadronics: %.2f (+%.2f, %.2f)' % k)

doChgIsoFit()

#############################################################################################################################################

#
# ROOT file for a signal regions fit
#
def writeRootFile(name, systematicVariations, merged=False):
  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'
  onZSelection  = 'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20'
  ttSelection   = 'll-looseLeptonVeto-mll40-offZ-signalRegion-nphoton0'
  tag           = 'eleSusyLoose-phoCBfull-matchNew'
  tagTT         = 'eleSusyLoose'
  writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl((tag, 'emu', baseSelection), 'signalRegionsSmall', '', ['MuonEG']), mergeBins=merged)
  writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl((tag, 'SF',  baseSelection), 'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon']), mergeBins=merged, removeBins=([1, 2] if merged else []))
  writeHist(f, 'sr_ee', 'data_obs', getHistFromPkl((tag, 'ee',  baseSelection), 'signalRegionsSmall', '', ['DoubleEG']), mergeBins=merged, removeBins=([1, 2] if merged else []))
  writeHist(f, 'sr_mm', 'data_obs', getHistFromPkl((tag, 'mumu',  baseSelection), 'signalRegionsSmall', '', ['DoubleMuon']), mergeBins=merged, removeBins=([1, 2] if merged else []))
  writeHist(f, 'zg_SF', 'data_obs', getHistFromPkl((tag, 'SF',  onZSelection),  'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon']), mergeBins=True)
  writeHist(f, 'tt',    'data_obs', getHistFromPkl((tagTT, 'all', ttSelection),   'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon'], ['MuonEG']), mergeBins=True)

  for t in templates:
    promptSelectors   = [[t, '(genuine,misIdEle)']]
    fakeSelectors     = [[t, '(hadronicFake)']]
    hadronicSelectors = [[t, '(hadronicPhoton)']]
    for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF'), ('sr_ee', 'ee'), ('sr_mm'), ('zg_SF', 'SF')]:
      q2Variations = []
      pdfVariations = []
      for sys in [''] + systematicVariations:
        prompt   = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *promptSelectors)
        fake     = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *fakeSelectors)
        hadronic = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *hadronicSelectors)
        if sys == '':
          fakeUp, fakeDown         = applyNonPromptSF(fake, fakeSF, 'Up'),         applyNonPromptSF(fake, fakeSF, 'Down')
          hadronicUp, hadronicDown = applyNonPromptSF(hadronic, hadronicSF, 'Up'), applyNonPromptSF(hadronic, hadronicSF, 'Down')
        fake     = applyNonPromptSF(fake, fakeSF)
        hadronic = applyNonPromptSF(hadronic, hadronicSF)
        if sys == '':
          totalUp   = prompt.Clone()
          totalDown = prompt.Clone()
          totalUp.Add(fakeUp)
          totalDown.Add(fakeDown)
          totalUp.Add(hadronicUp)
          totalDown.Add(hadronicDown)
          writeHist(f, shape+'nonPromptUp',   t, totalUp, mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))
          writeHist(f, shape+'nonPromptDown', t, totalDown, mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))
        total = prompt.Clone()
        total.Add(hadronic)
        total.Add(fake)

        if sys == '':     nominal = total
        if 'pdf' in sys:  pdfVariations += [total]
        elif 'q2' in sys: q2Variations += [total]
        else:             writeHist(f, shape+sys, t, total, mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))

      if len(pdfVariations) > 0:
        up, down = pdfSys(pdfVariations, nominal)
        writeHist(f, shape+'pdfUp',   t, up,   mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))
        writeHist(f, shape+'pdfDown', t, down, mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))

      if len(q2Variations) > 0:
        up, down = q2Sys(q2Variations)
        writeHist(f, shape+'q2Up',   t, up,   mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))
        writeHist(f, shape+'q2Down', t, down, mergeBins = ('zg' in shape or merged), removeBins=([1, 2] if (merged and 'sr_SF' in shape) else []))


    for shape, channel in [('tt', 'all')]:
      q2Variations = []
      pdfVariations = []
      selector = [[t,]]
      for sys in [''] + systematicVariations:
        if 'ue' in sys: continue
        if 'erd' in sys: continue
        if 'hdamp' in sys: continue
        total = getHistFromPkl((tagTT, channel, ttSelection), 'signalRegionsSmall', sys, *selector)

        if sys == '':     nominal = total
        if 'pdf' in sys:  pdfVariations += [total]
        elif 'q2' in sys: q2Variations += [total]
        else:             writeHist(f, shape+sys, t, total, mergeBins = True)

      if len(pdfVariations) > 0:
        up, down = pdfSys(pdfVariations, nominal)
        writeHist(f, shape+'pdfUp',   t, up,   mergeBins=True)
        writeHist(f, shape+'pdfDown', t, down, mergeBins=True)

      if len(q2Variations) > 0:
        up, down = q2Sys(q2Variations)
        writeHist(f, shape+'q2Up',   t, up,   mergeBins=True)
        writeHist(f, shape+'q2Down', t, down, mergeBins=True)


  f.Close()

#
# Signal regions fit
#
def doSignalRegionFit(cardName, shapes, perPage=30, merged=False, doRatio=False):
  log.info(' --- Signal regions fit (' + cardName + ') --- ')
  extraLines  = [(t + '_norm rateParam * ' + t + '* 1')                 for t in templates[1:]]
  extraLines += [(t + '_norm param 1.0 ' + str(rateParameters[t]/100.)) for t in templates[1:]]
  extraLines += ['* autoMCStats 0 1 1']

  if doRatio:
    log.info(' --- Ratio ttGamma/ttBar fit (' + cardName + ') --- ')
    from ttg.samples.Sample import createSampleList, getSampleFromList
    sampleList   = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples.conf'))
    xsec_ttGamma = sum([getSampleFromList(sampleList, s).xsec for s in ['TTGamma', 'TTGamma_t', 'TTGamma_tbar', 'TTGamma_had']])
    xsec_tt      = getSampleFromList(sampleList, 'TTJets_pow').xsec
    extraLines += ['renormTTGamma rateParam * TTGamma* %.7f' % (1./(100*xsec_ttGamma)), 'nuisance edit freeze renormTTGamma ifexists']
    extraLines += ['renormTTbar rateParam * TTJets* %.7f' % (1./xsec_tt),               'nuisance edit freeze renormTTbar ifexists']
    extraLines += ['TTbar_norm rateParam * TT* %.7f' % xsec_tt]
  else:
    log.info(' --- Signal regions fit (' + cardName + ') --- ')

  writeRootFile(cardName, systematics.keys(), merged)
  writeCard(cardName, shapes, templates, None, extraLines, showSysList + ['nonPrompt'], linearSystematics, scaleShape={'fsr': 1/sqrt(2)})

  runFitDiagnostics(cardName, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=False)
  runFitDiagnostics(cardName, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=True)
  runImpacts(cardName, perPage)
  runImpacts(cardName, perPage, toys=True)
  runSignificance(cardName)
  runSignificance(cardName, expected=True)


doSignalRegionFit('srFit', ['sr_OF', 'sr_SF', 'zg_SF'], 35)
doSignalRegionFit('srFit_SF', ['sr_SF', 'zg_SF'], 35)
doSignalRegionFit('srFit_OF', ['sr_OF', 'zg_SF'], 35)
doSignalRegionFit('srFit_ee', ['sr_ee', 'zg_SF'], 35)
doSignalRegionFit('srFit_mm', ['sr_mm', 'zg_SF'], 35)

doSignalRegionFit('ratioFit', ['sr_OF', 'sr_SF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_SF', ['sr_SF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_OF', ['sr_OF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_ee', ['sr_ee', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_mm', ['sr_mm', 'zg_SF'], 35, doRatio=True)
#goodnessOfFit('srFit')
#doLinearityCheck('srFit')
