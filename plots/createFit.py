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

  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  runImpacts(cardName)
  #runSignificance(cardName)
  #runSignificance(cardName, expected=True)

#
# 2-stage fit: chgIso separately before SR
#
elif False:
  # ROOT File for a charged isolation only fit
  def writeRootFileForChgIso(name, systematics, selection):
    selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'
    plot      = 'photon_chargedIso_bins_NO'

    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    writeHist(f, 'chgIso' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']),norm=1)

    statVariations = []
    for splitType in ['_p', '_np']:
      if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)']            for sample in samples]
      elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)'] for sample in samples]

      if name.count('dd') and splitType=='_np':
        sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-failSigmaIetaIeta', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
        normalizeBinWidth(sideBandShape, 1)
      else:
        sideBandShape = None

      for sys in [''] + systematics:
        writeHist(f, 'chgIso'+sys,  'all' + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', selection), plot, sys, *selectors), (statVariations if sys=='' else None), norm=1, shape=sideBandShape)

    f.Close()
    return set(statVariations)


  # Charged isolation fit
  templates   = ['all_np', 'all_p'] 
  extraLines  = ['prompt_norm rateParam * all_p 1']

  nonPromptSF = {}
  for selection in ['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p']:
    for dataDriven in [True]:
      cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + selection
      statVariations = writeRootFileForChgIso(cardName, [], selection)
      writeCard(cardName, ['chgIso'], templates, extraLines, [], statVariations, {})
      result = runFitDiagnostics(cardName, toys=None, statOnly=False)
      nonPromptSF[selection] = (result[0], -sqrt((result[1]/result[0])**2+0.25**2)*result[0], sqrt((result[2]/result[0])**2+0.25**2)*result[0])    # Add extra uncertainty of 25% based on different chgIso shape in sigmaIetaIeta sideband
      runImpacts(cardName)

  for i,j in nonPromptSF.iteritems():
    log.info('Charged isolation fit for ' + i + ' results in %.2f (+%.2f, %.2f)' % j)





  # ROOT file for a signal regions fit
  def writeRootFile(name, systematics, nonPromptSF):
    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'
    writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull', 'emu', baseSelection), 'signalRegions', '', ['MuonEG']))
    writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull', 'SF',  baseSelection), 'signalRegions', '', ['DoubleEG'],['DoubleMuon']))

    statVariations = []
    for sample in samples:
      promptSelectors    = [[sample, '(genuine,misIdEle)']]
      nonPromptSelectors = [[sample, '(hadronicPhoton,hadronicFake)']]
      for sys in [''] + systematics:
        for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF')]:
          prompt    = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection), 'signalRegions', sys, *promptSelectors)
          nonPrompt = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection), 'signalRegions', sys, *nonPromptSelectors)
          if sample.count('TTJets') and nonPromptSF: nonPrompt = applyNonPromptSF(nonPrompt, nonPromptSF)   # Currently only for TTJets, could in principle do this for all non-prompt contributions
          total = prompt.Clone()
          total.Add(nonPrompt)

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

  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=True)
  runImpacts(cardName)
  runSignificance(cardName)
  runSignificance(cardName, expected=True)


#
# 2-stage fit, but take hadronic photons from MC
#
else:
  # ROOT File for a charged isolation only fit
  def writeRootFileForChgIso(name, systematics, selection):
    selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'
    plot      = 'photon_chargedIso_bins_NO'

    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    writeHist(f, 'chgIso' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-newMatch-central', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']),norm=1)

    statVariations = []
    for splitType in ['_g', '_f', '_h']:
      if   splitType=='_g': selectors = [[sample, '(genuine,misIdEle)'] for sample in samples]
      elif splitType=='_f': selectors = [[sample, '(hadronicFake)']     for sample in samples]
      elif splitType=='_h': selectors = [[sample, '(hadronicPhoton)']   for sample in samples]

      if name.count('dd') and splitType=='_f':
        sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-central', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])
        normalizeBinWidth(sideBandShape, 1)
      else:
        sideBandShape = None

      for sys in [''] + systematics:
        writeHist(f, 'chgIso'+sys,  'all' + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-newMatch-central', 'all', selection), plot, sys, *selectors), (statVariations if sys=='' else None), norm=1, shape=sideBandShape)

    f.Close()
    return set(statVariations)


  # Charged isolation fit
  templates   = ['all_g', 'all_f', 'all_h'] 
  extraLines  = ['prompt_norm   rateParam * all_g 1']
  extraLines  = ['hadronic_norm rateParam * all_h 1']

  nonPromptSF = {}
  for selection in ['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p']:
    for dataDriven in [True]:
      cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + selection
      statVariations = writeRootFileForChgIso(cardName, [], selection)
      writeCard(cardName, ['chgIso'], templates, extraLines, [], statVariations, {})
      result = runFitDiagnostics(cardName, toys=None, statOnly=False)
      nonPromptSF[selection] = (result[0], -sqrt((result[1]/result[0])**2+0.25**2)*result[0], sqrt((result[2]/result[0])**2+0.25**2)*result[0])    # Add extra uncertainty of 25% based on different chgIso shape in sigmaIetaIeta sideband
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

  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=True)
  runImpacts(cardName)
  runSignificance(cardName)
  runSignificance(cardName, expected=True)
