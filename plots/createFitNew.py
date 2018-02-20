#! /usr/bin/env python
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--checkStability', action='store_true', default=False)
args = argParser.parse_args()

from ttg.plots.plot         import Plot, getHistFromPkl
from ttg.tools.logger       import getLogger
from ttg.plots.combineTools import handleCombine,writeCard
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

def writeHist(file, shape, template, hist):
  if not file.GetDirectory(shape): file.mkdir(shape)
  file.cd(shape)
  hist.Write(template)
  file.cd()

def writeRootFile(name):
  f = ROOT.TFile(name + '.root', 'RECREATE')

  writeHist(f, 'chgIso', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'photon_chargedIso', ['MuonEG'],['DoubleEG'],['DoubleMuon']))
  writeHist(f, 'sr_OF',  'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'njets',             ['MuonEG']))
  writeHist(f, 'sr_SF',  'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'njets',             ['DoubleEG'],['DoubleMuon']))

  for splitType in ['', '_p', '_np']:
    for sample in samples:
      if   splitType=='_p':  selectors = [[sample, '(genuine,misIdEle)']]
      elif splitType=='_np': selectors = [[sample, '(hadronicPhoton,hadronicFake)']]
      else:                  selectors = [[sample, '(genuine,misIdEle)'], [sample, '(hadronicPhoton,hadronicFake)']]
      writeHist(f, 'chgIso', sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso-match', 'all', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'photon_chargedIso', *selectors))
      writeHist(f, 'sr_OF',  sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'emu', 'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'njets',             *selectors))
      writeHist(f, 'sr_SF',  sample + splitType, getHistFromPkl(('eleSusyLoose-phoCBfull-match',     'SF',  'llg-looseLeptonVeto-mll40-offZ-llgNoZ'), 'njets',             *selectors))
  f.Close()


templates = [(s + '_p') for s in samples] + [(s + '_np') for s in samples]

extraLines  = [(s + '_norm rateParam * ' + s + '* 1') for s in samples[1:]]
extraLines += [(s + '_norm param 1.0 0.2')            for s in samples[1:]]
#extraLines += ['nonPrompt rateParam * *_np 1'] 

writeRootFile(cardName)
writeCard(cardName, ['sr_OF', 'sr_SF'], templates, extraLines)


result = handleCombine(cardName, trackParameters = ['TTJets_norm', 'ZG_norm'])
