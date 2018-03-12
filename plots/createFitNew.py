#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--checkStability', action='store_true', default=False)
args = argParser.parse_args()

from ttg.plots.plot         import getHistFromPkl
from ttg.tools.logger       import getLogger
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts
from ttg.plots.systematics  import systematics, linearSystematics
log = getLogger(args.logLevel)

import os, ROOT, shutil
ROOT.gROOT.SetBatch(True)

#shapes      = ['chgIso','sr_SF','sr_OF']
samples     = ['TTGamma','TTJets','ZG','DY','other']


cardName = 'test'


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

def writeHist(file, shape, template, hist, statVariations=None):
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

#
# For a full simultaneous fit
#
def writeRootFile(name, systematics):
  try:    os.makedirs('combine')
  except: pass

  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

#  writeHist(f, 'chgIso1' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'photon_chargedIso', '', ['MuonEG'],['DoubleEG'],['DoubleMuon']))
#  writeHist(f, 'chgIso2', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'photon_chargedIso', '', ['MuonEG'],['DoubleEG'],['DoubleMuon']))
  writeHist(f, 'sr_OF',   'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             '', ['MuonEG']))
  writeHist(f, 'sr_SF',   'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             '', ['DoubleEG'],['DoubleMuon']))

  statVariations = []
  for splitType in ['_p', '_np']:
    for sample in samples:
      for sys in [''] + systematics:
        if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)']]
        elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)']]
        else:                  selectors = [[sample, '(genuine,misIdEle)'], [sample, '(hadronicPhoton,hadronicFake)']]
#        writeHist(f, 'chgIso1'+sys,  sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'photon_chargedIso', sys, *selectors), (statVariations if sys=='' else None))
#        writeHist(f, 'chgIso2'+sys, sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'photon_chargedIso', sys, *selectors), (statVariations if sys=='' else None))
        writeHist(f, 'sr_OF'+sys,   sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             sys, *selectors), (statVariations if sys=='' else None))
        writeHist(f, 'sr_SF'+sys,   sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'),                   'signalRegions',             sys, *selectors), (statVariations if sys=='' else None))

  return set(statVariations)
  f.Close()

#
# For a charged isolation only fit
#
def writeRootFileForChgIso(name, systematics):
  try:    os.makedirs('combine')
  except: pass

  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  writeHist(f, 'chgIso' , 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'photon_chargedIso', '', ['MuonEG'],['DoubleEG'],['DoubleMuon']))

  statVariations = []
  for splitType in ['_p', '_np']:
    for sys in [''] + systematics:
      if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)'] for sample in samples]
      elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)'] for sample in samples]
      writeHist(f, 'chgIso'+sys,  'all' + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'), 'photon_chargedIso', sys, *selectors), (statVariations if sys=='' else None))

  return set(statVariations)
  f.Close()

chgIsoFit = True
if chgIsoFit:
  templates   = ['all_np', 'all_p'] 
  extraLines  = ['prompt_norm rateParam * all_p 1', 'prompt_norm param 1.0 0.2']

  statVariations = writeRootFileForChgIso(cardName, systematics.keys())
  writeCard(cardName, ['chgIso'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)
  result = runFitDiagnostics(cardName, toys=None, statOnly=False)
  runImpacts(cardName)
else:
  templates   = [(s + '_p') for s in samples] + [(s + '_np') for s in samples]
  extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
  extraLines += [(s + '_norm param 1.0 0.1')            for s in samples[1:]]
  extraLines += ['nonPrompt rateParam * *_np 1'] 
  extraLines += ['nonPrompt param 1.0 0.2'] 
  #extraLines += ['* autoMCStats 0'] # does not work

  statVariations = writeRootFile(cardName, systematics.keys())
  #writeCard(cardName, ['sr_OF', 'sr_SF', 'chgIso1', 'chgIso2'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)
  writeCard(cardName, ['sr_OF', 'sr_SF'], templates, extraLines, systematics.keys(), statVariations, linearSystematics)


  result = runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','nonPrompt','r'], toys=None, statOnly=False)
#runSignificance(cardName)
#runSignificance(cardName, expected=True)
