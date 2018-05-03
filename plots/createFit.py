#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--bigFit',         action='store_true', default=False)
args = argParser.parse_args()

from ttg.tools.logger       import getLogger
log = getLogger(logLevel=args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts
from ttg.plots.systematics  import systematics, linearSystematics

import os, ROOT, shutil
ROOT.gROOT.SetBatch(True)

from math import sqrt

samples     = ['TTGamma','TTJets','ZG','DY','other']

#
# Helper functions
#
def protectHist(hist):
  if hist.Integral() < 0.00001:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
  return hist

def applyNonPromptSF(hist, nonPromptSF):
  srMap = {1:'njet1-deepbtag0', 2:'njet1-deepbtag1p', 3:'njet2p-deepbtag0', 4:'njet2p-deepbtag1', 5:'njet2p-deepbtag2p'}
  for bin, sr in srMap.iteritems():
    hist.SetBinContent(bin, hist.GetBinContent(bin)*(nonPromptSF[sr][0]))
  return hist

def replaceShape(hist, shape):
  normalization = hist.Integral("width")/shape.Integral("width")
  hist = shape.Clone()
  hist.Scale(normalization)
  return hist

def writeHist(file, name, template, hist, statVariations=None, norm=None, removeBins = [], shape=None):
  if norm:  normalizeBinWidth(hist, norm)
  if shape: hist = replaceShape(hist, shape)
  for i in removeBins:
    hist.SetBinContent(i, 0)
    hist.SetBinError(i, 0)
  if not file.GetDirectory(name): file.mkdir(name)
  file.cd(name)
  protectHist(hist).Write(template)
  file.cd()
  if statVariations is not None:
    for i in range(1, hist.GetNbinsX()+1):
      up   = hist.Clone()
      down = hist.Clone()
      up.SetBinContent(  i, hist.GetBinContent(i)+hist.GetBinError(i))
      down.SetBinContent(i, hist.GetBinContent(i)-hist.GetBinError(i))
      writeHist(file, name + name + template + 'Stat' + str(i) + 'Up',   template, up)
      writeHist(file, name + name + template + 'Stat' + str(i) + 'Down', template, down)
      statVariations.append(name + template + 'Stat' + str(i))

# Create combine directory
try:    os.makedirs('combine')
except: pass



#
# One big simultaneous fit
#
if args.bigFit:
  def writeRootFileForSimultaneousFit(name, systematics):
    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')
    shapes = []
    statVariations = []
    for channel in ['SF', 'emu']:
     #for sr, selection in enumerate(['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag1p']):
      for sr, selection in enumerate(['njet2p-deepbtag1', 'njet2p-deepbtag1p']):
        plot      = 'photon_chargedIso_bins_NO'
        selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'
        name      = 'sr' + str(sr) + channel
        shapes.append(name)

        writeHist(f, name, 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', channel, selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']),norm=1)

        if name.count('dd'):
          sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-failSigmaIetaIeta', channel, selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
          normalizeBinWidth(sideBandShape, 1)
        else:
          sideBandShape = None

        for sample in samples:
          for splitType in ['_p', '_np']:
            if   splitType=='_p':  selector = [sample, '(genuine,misIdEle)']
            elif splitType=='_np': selector = [sample, '(hadronicPhoton,hadronicFake)']
            for sys in [''] + systematics:
              writeHist(f, name+sys, sample+splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', channel, selection), plot, sys, selector), (statVariations if sys=='' else None), norm=1, shape=(sideBandShape if splitType=='_np' else None))
    f.Close()
    return shapes, set(statVariations)

  cardName    = 'simultaneousFit'
  templates   = [s + '_p' for s in samples] + [s + '_np' for s in samples]
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
  extraLines += [(s + '_norm param 1.0 0.1')            for s in samples[1:]]
  extraLines += ['nonPrompt rateParam * *_np 1']
  #extraLines += ['nonPrompt param 1.0 0.2']
  #extraLines += ['* autoMCStats 0'] # does not work

  shapes, statVariations = writeRootFileForSimultaneousFit(cardName, systematics.keys())
  writeCard(cardName, shapes, templates, extraLines, systematics.keys(), statVariations, linearSystematics)

  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  runImpacts(cardName)
  #runSignificance(cardName)
  #runSignificance(cardName, expected=True)

#
# 2-stage fit, take hadronic photons from MC
#
else:
  # ROOT File for a charged isolation only fit
  def writeRootFileForChgIso(name, systematics, selection):
    tag       = 'eleSusyLoose-phoCBnoChgIso-newMatch-central'
    selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'
    plot      = 'photon_chargedIso_bins_NO'

    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    writeHist(f, 'chgIso' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-newMatch-central', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']),norm=1)

    statVariations = []
    from ttg.plots.plot import applySidebandUnc
    for splitType in ['_g', '_f', '_h']:
      if   splitType=='_g': selectors = [[sample, '(genuine,misIdEle)'] for sample in samples]
      elif splitType=='_f': selectors = [[sample, '(hadronicFake)']     for sample in samples]
      elif splitType=='_h': selectors = [[sample, '(hadronicPhoton)']   for sample in samples]

      if name.count('dd') and splitType=='_f':
        sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-central', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
        normalizeBinWidth(sideBandShape, 1)
        sideBandShapeUp   = applySidebandUnc(sideBandShape, plot, selection, True)
        sideBandShapeDown = applySidebandUnc(sideBandShape, plot, selection, False)
        writeHist(f, 'chgIso',                'all' + splitType, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors), (statVariations if sys=='' else None), norm=1, shape=sideBandShape)
        writeHist(f, 'chgIsoSideBandUncUp',   'all' + splitType, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors), None,                                  norm=1, shape=sideBandShapeUp)
        writeHist(f, 'chgIsoSideBandUncDown', 'all' + splitType, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors), None,                                  norm=1, shape=sideBandShapeDown)
      else:
        for sys in [''] + systematics:
          writeHist(f, 'chgIso'+sys,  'all' + splitType, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors), (statVariations if sys=='' else None), norm=1)

    f.Close()
    return set(statVariations)


  # Post-fit plots
  from ttg.plots.plot import Plot
  from ttg.tools.style import drawLumi
  import ttg.tools.style as styles
  def plot(name, name2, results):
    f = ROOT.TFile('combine/' + name + '.root')
    all_f      = f.Get('chgIso/all_f')
    all_g      = f.Get('chgIso/all_g')
    all_h      = f.Get('chgIso/all_h')
    data       = f.Get('chgIso/data_obs')

    if results:
      all_f.Scale(results['r'][0])
 #    all_h.Scale(results['hadronic_norm'][0])
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

  # Charged isolation fit
  templates   = ['all_f', 'all_g', 'all_h']
  extraLines  = ['prompt_norm   rateParam * all_g 1']
 # extraLines += ['hadronic_norm rateParam * all_h 1']

  nonPromptSF = {}
  for selection in ['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p']:
    for dataDriven in [True]:
      cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + selection
      statVariations = writeRootFileForChgIso(cardName, [], selection)
      writeCard(cardName, ['chgIso'], templates, extraLines, ['SideBandUncUp:all_f'], statVariations, {})
      results = runFitDiagnostics(cardName, toys=None, statOnly=False, trackParameters = ['prompt_norm'])
      nonPromptSF[selection] = results['r']
      plot(cardName, '_prefit',  None)
      plot(cardName, '_postfit', results)
      runImpacts(cardName)

  for i,j in nonPromptSF.iteritems():
    log.info('Charged isolation fit for ' + i + ' results in %.2f (+%.2f, %.2f)' % j)




  # ROOT file for a signal regions fit
  def writeRootFile(name, systematics, nonPromptSF):
    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'
    writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-newMatch-central', 'emu', baseSelection), 'signalRegions', '', ['MuonEG']))
    writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-newMatch-central', 'SF',  baseSelection), 'signalRegions', '', ['DoubleEG'],['DoubleMuon']))

    statVariations = []
    for sample in samples:
      promptSelectors   = [[sample, '(genuine,misIdEle)']]
      fakeSelectors     = [[sample, '(hadronicFake)']]
      hadronicSelectors = [[sample, '(hadronicPhoton)']]
      for sys in [''] + systematics:
        for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF')]:
          prompt   = getHistFromPkl(('eleSusyLoose-phoCBfull-newMatch-central', channel, baseSelection), 'signalRegions', sys, *promptSelectors)
          fake     = getHistFromPkl(('eleSusyLoose-phoCBfull-newMatch-central', channel, baseSelection), 'signalRegions', sys, *fakeSelectors)
          hadronic = getHistFromPkl(('eleSusyLoose-phoCBfull-newMatch-central', channel, baseSelection), 'signalRegions', sys, *hadronicSelectors)
          if nonPromptSF: fake = applyNonPromptSF(fake, nonPromptSF)
          total = prompt.Clone()
          total.Add(fake)
          total.Add(hadronic)

          writeHist(f, shape+sys, sample, total, (statVariations if sys=='' else None))

    f.Close()
    return set(statVariations)


  # Signal regions fit
  cardName    = 'srFit'
  templates   = samples
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
  extraLines += [(s + '_norm param 1.0 0.1')            for s in samples[1:]]
  #extraLines += ['* autoMCStats 0'] # does not work

  statVariations = writeRootFile(cardName, systematics.keys(), nonPromptSF)
  writeCard(cardName, ['sr_OF', 'sr_SF'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)

  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=True)
  runImpacts(cardName)
  runSignificance(cardName)
  runSignificance(cardName, expected=True)
