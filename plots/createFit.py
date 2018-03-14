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
  hist.Scale(nonPromptSF['njet2p-deepbtag1p'][0])  # Currently scaling all SR with same factor from njet2p-deepbtag1p, could be adapted to specific SF for each SR
  return hist

def writeHist(file, shape, template, hist, statVariations=None, norm=None, removeBins = []):
  if norm: normalizeBinWidth(hist, norm)
  for i in removeBins:
    hist.SetBinContent(i, 0)
    hist.SetBinError(i, 0)
  if not file.GetDirectory(shape): file.mkdir(shape)
  file.cd(shape)
  protectHist(hist).Write(template)
  file.cd()
  if statVariations is not None:
    for i in range(1, hist.GetNbinsX()+1):
      up   = hist.Clone()
      down = hist.Clone()
      up.SetBinContent(  i, hist.GetBinContent(i)+hist.GetBinError(i))
      down.SetBinContent(i, hist.GetBinContent(i)-hist.GetBinError(i))
      writeHist(file, shape + shape + template + 'Stat' + str(i) + 'Up',   template, up)
      writeHist(file, shape + shape + template + 'Stat' + str(i) + 'Down', template, down)
      statVariations.append(shape + template + 'Stat' + str(i))

# Create combine directory
try:    os.makedirs('combine')
except: pass



#
# One big simultaneous fit
#
if args.bigFit:
  def writeRootFileForSimultaneousFit(name, systematics, selection):
    pass


#
# 2-level fit: chgIso separately before SR
#
else:
  # ROOT File for a charged isolation only fit
  def writeRootFileForChgIso(name, systematics, selection):
    selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'
    plot      = 'photon_chargedIso_bins_NO'

    f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

    writeHist(f, 'chgIso' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']),norm=1, removeBins=[1])

    statVariations = []
    for splitType in ['_p', '_np']:
      if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)']            for sample in samples]
      elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)'] for sample in samples]
      for sys in [''] + systematics:
        writeHist(f, 'chgIso'+sys,  'all' + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', selection), plot, sys, *selectors), (statVariations if sys=='' else None), norm=1, removeBins=[1])

    return set(statVariations)
    f.Close()


  # Charged isolation fit
  templates   = ['all_np', 'all_p'] 
  extraLines  = ['prompt_norm rateParam * all_p 1']

  nonPromptSF = {}
  #for selection in ['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p']:
  for selection in ['njet2p-deepbtag1p']:
    cardName = 'chgIsoFit_' + selection
    statVariations = writeRootFileForChgIso(cardName, systematics.keys(), selection)
    writeCard(cardName, ['chgIso'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)
    systematics = {}
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

    return set(statVariations)
    f.Close()


  # Signal regions fit
  cardName    = 'srFit'
  templates   = samples
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
  extraLines += [(s + '_norm param 1.0 0.1')            for s in samples[1:]]
  #extraLines += ['nonPrompt rateParam * *_np 1']
  #extraLines += ['nonPrompt param 1.0 0.2']
  #extraLines += ['* autoMCStats 0'] # does not work

  statVariations = writeRootFile(cardName, systematics.keys(), nonPromptSF)
  writeCard(cardName, ['sr_OF', 'sr_SF'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)

  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
  #runImpacts(cardName)
  #runSignificance(cardName)
  #runSignificance(cardName, expected=True)
