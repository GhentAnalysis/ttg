#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.plots.plot         import getHistFromPkl
from ttg.tools.logger       import getLogger
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts
from ttg.plots.systematics  import systematics, linearSystematics
log = getLogger(args.logLevel)

import os, ROOT, shutil
ROOT.gROOT.SetBatch(True)

from math import sqrt

#shapes      = ['chgIso','sr_SF','sr_OF']
samples     = ['TTGamma','TTJets','ZG','DY','other']



def writeStatVariation(hist, prefix):
  for i in range(hist.GetNbinsX()):
    bin  = i+1
    up   = hist.Clone()
    down = hist.Clone()
    up.SetBinContent(  bin, hist.GetBinContent(bin)+hist.GetBinError(bin))
    down.SetBinContent(bin, hist.GetBinContent(bin)-hist.GetBinError(bin))
    up.Write(prefix + str(i) + 'Up')
    down.Write(prefix + str(i) + 'Down')


def addHists(hists, name, toAdd):
  if not toAdd:     return
  if name in hists: hists[name].Add(toAdd)
  else:             hists[name] = toAdd

def protectHist(hist):
  if hist.Integral() < 0.00001:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
  return hist

def removeFirstBin(hist):
  hist.SetBinContent(1, 0)
  return hist

def applyNonPromptSF(hist, nonPromptSF):
  hist.Scale(nonPromptSF['njet2p-deepbtag1p'][0])  # Currently scaling all SR with same factor from njet2p-deepbtag1p, could be adapted to specific SF for each SR
  return hist

def writeHist(file, shape, template, hist, statVariations=None, nonPromptSF=None):
  if not file.GetDirectory(shape): file.mkdir(shape)
  file.cd(shape)
  if template.count('TTJets_np') and nonPromptSF: hist = applyNonPromptSF(hist, nonPromptSF)   # Currently only for TTJets, could in priniple do this for all non-prompt contributions
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

#
# ROOT file for a full simultaneous fit
#
def writeRootFile(name, systematics, nonPromptSF):
  try:    os.makedirs('combine')
  except: pass

  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  writeHist(f, 'sr_OF',   'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             '', ['MuonEG']))
  writeHist(f, 'sr_SF',   'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             '', ['DoubleEG'],['DoubleMuon']))

  statVariations = []
  for splitType in ['_p', '_np']:
    for sample in samples:
      for sys in [''] + systematics:
        if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)']]
        elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)']]
        else:                  selectors = [[sample, '(genuine,misIdEle)'], [sample, '(hadronicPhoton,hadronicFake)']]
        writeHist(f, 'sr_OF'+sys,   sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             sys, *selectors), (statVariations if sys=='' else None), nonPromptSF=nonPromptSF)
        writeHist(f, 'sr_SF'+sys,   sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             sys, *selectors), (statVariations if sys=='' else None), nonPromptSF=nonPromptSF)

  return set(statVariations)
  f.Close()

#
# ROOT File for a charged isolation only fit
#
def writeRootFileForChgIso(name, systematics, selection):
  try:    os.makedirs('combine')
  except: pass

  selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'

  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  writeHist(f, 'chgIso' , 'data_obs', removeFirstBin(getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', selection), 'photon_chargedIso', '', ['MuonEG'],['DoubleEG'],['DoubleMuon'])))

  statVariations = []
  for splitType in ['_p', '_np']:
    for sys in [''] + systematics:
      if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)'] for sample in samples]
      elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)'] for sample in samples]
      writeHist(f, 'chgIso'+sys,  'all' + splitType, removeFirstBin(getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', selection), 'photon_chargedIso', sys, *selectors)), (statVariations if sys=='' else None))

  return set(statVariations)
  f.Close()


#
# Charged isolation fit
#
templates   = ['all_np', 'all_p'] 
extraLines  = ['prompt_norm rateParam * all_p 1', 'prompt_norm param 1.0 0.2']

nonPromptSF = {}
#  for selection in ['njet1-deepbtag0', 'njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p']:
for selection in ['njet2p-deepbtag1p']:
  cardName = 'chgIsoFit_' + selection
  statVariations = writeRootFileForChgIso(cardName, systematics.keys(), selection)
  writeCard(cardName, ['chgIso'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)
  result = runFitDiagnostics(cardName, toys=None, statOnly=False)
  nonPromptSF[selection] = (result[0], sqrt((result[1]/result[0])**2+0.25**2)*result[0], -sqrt((result[2]/result[0])**2+0.25**2)*result[0])    # Add extra uncertainty of 25% based on different chgIso shape in sigmaIetaIeta sideband
  runImpacts(cardName)

for i,j in nonPromptSF.iteritems():
  log.info('Charged isolation fit for ' + i + ' results in %.2f (+%.2f, %.2f)' % j)


#
# Signal regions fit
#
cardName    = 'srFit'
templates   = [(s + '_p') for s in samples] + [(s + '_np') for s in samples]
extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
extraLines += [(s + '_norm param 1.0 0.1')            for s in samples[1:]]
extraLines += ['nonPrompt rateParam * *_np 1'] 
extraLines += ['nonPrompt param 1.0 0.2'] 
#extraLines += ['* autoMCStats 0'] # does not work

statVariations = writeRootFile(cardName, systematics.keys(), nonPromptSF)
#writeCard(cardName, ['sr_OF', 'sr_SF', 'chgIso1', 'chgIso2'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)
writeCard(cardName, ['sr_OF', 'sr_SF'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)


result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','nonPrompt','r'], toys=None, statOnly=False)
runImpacts(cardName)
#runSignificance(cardName)
#runSignificance(cardName, expected=True)
