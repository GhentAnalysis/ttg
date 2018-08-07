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

samples     = [('TTGamma', None), ('TTJets', 5.5), ('ZG', 30), ('DY', 30), ('other', 30)]
samplesZG   = [('ZG',      None), ('other', 30)]

#
# Helper functions
#
def protectHist(hist):
  if hist.Integral() < 0.00001:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
  return hist

def applyNonPromptSF(histTemp, nonPromptSF, sys=None):
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

def writeHist(file, name, template, histTemp, statVariations=None, norm=None, removeBins = [], shape=None, mergeBins=False):
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
  file.cd()
  if statVariations is not None:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) == 0 and hist.GetBinError(i) == 0: continue
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

#############################################################################################################################################

# 
# ROOT file for Zgamma fit
#
def writeRootFileForZG(name, systematics):
  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  baseSelection = 'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20'
  writeHist(f, 'zg_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull', 'SF',  baseSelection), 'njets', '', ['DoubleEG'],['DoubleMuon']), mergeBins=True)

  statVariations = []
  for sys in [''] + systematics:
    ZG    = getHistFromPkl(('eleSusyLoose-phoCBfull', 'SF', baseSelection), 'njets', sys, ['ZG'])
    other = getHistFromPkl(('eleSusyLoose-phoCBfull', 'SF', baseSelection), 'njets', sys, ['TTJets_pow'], ['TTGamma'], ['Drell-Yan'], ['single-t'],['other'])
    writeHist(f, 'zg_SF' + sys, 'ZG',    ZG,    (statVariations if sys=='' else None), mergeBins=True)
    writeHist(f, 'zg_SF' + sys, 'other', other, (statVariations if sys=='' else None), mergeBins=True)

  f.Close()
  return set(statVariations)

#
# ZGamma fit
#
cardName    = 'zgFit'
templates   = [s for s,_ in samplesZG]
extraLines  = [(s + '_norm rateParam * ' + s + '* 1')   for s,_   in samplesZG[1:]]
extraLines += [(s + '_norm param 1.0 ' + str(unc/100.)) for s,unc in samplesZG[1:]]

statVariations = writeRootFileForZG(cardName, systematics.keys())
writeCard(cardName, ['zg_SF'], templates, [], extraLines, systematics.keys(), statVariations, linearSystematics)

results = runFitDiagnostics(cardName, trackParameters = ['r'], toys=None, statOnly=False)
zgSF = results['r']
runFitDiagnostics(cardName, trackParameters = ['r'], toys=None, statOnly=True)
runImpacts(cardName)

log.info('ZGamma fit results in %.2f (+%.2f, %.2f)' % zgSF)



#############################################################################################################################################


#
# ROOT File for a charged isolation only fit
#
def writeRootFileForChgIso(name, systematics, selection):
  tag       = 'eleSusyLoose-phoCBnoChgIso-match'
  plot      = 'photon_chargedIso_bins_NO'

  if selection=='all':
    selections = ['llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag1p-photonPt20', 
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag0-photonPt20',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1-photonPt20',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag2p-photonPt20']
  else:
    selections = ['llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20']

  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  dataHist = None
  for selection in selections:
    dataHist = addHist(dataHist, getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']))
  writeHist(f, 'chgIso' , 'data_obs', dataHist,norm=1)

  statVariations = []
  from ttg.plots.plot import applySidebandUnc
  for splitType in ['_g', '_f', '_h']:
    if   splitType=='_g': selectors = [[sample, '(genuine,misIdEle)'] for sample,_ in samples]
    elif splitType=='_f': selectors = [[sample, '(hadronicFake)']     for sample,_ in samples]
    elif splitType=='_h': selectors = [[sample, '(hadronicPhoton)']   for sample,_ in samples]

    if name.count('dd') and splitType=='_f':
      sideBandShape = None
      for selection in selections:
        sideBandShape = addHist(sideBandShape, getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta', 'all', selection), plot, '', ['MuonEG'],['DoubleEG'],['DoubleMuon']))
      normalizeBinWidth(sideBandShape, 1)
      sideBandShapeUp   = applySidebandUnc(sideBandShape, plot, selection, True)
      sideBandShapeDown = applySidebandUnc(sideBandShape, plot, selection, False)
      
      chgIsoHist = None
      for selection in selections:
        chgIsoHist = addHist(chgIsoHist, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors))
      writeHist(f, 'chgIso',                'all' + splitType, chgIsoHist, (statVariations if sys=='' else None), norm=1, shape=sideBandShape)
      writeHist(f, 'chgIsoSideBandUncUp',   'all' + splitType, chgIsoHist, None,                                  norm=1, shape=sideBandShapeUp)
      writeHist(f, 'chgIsoSideBandUncDown', 'all' + splitType, chgIsoHist, None,                                  norm=1, shape=sideBandShapeDown)
    else:
      for sys in [''] + systematics:
        chgIsoHist = None
        for selection in selections:
          chgIsoHist = addHist(chgIsoHist, getHistFromPkl((tag, 'all', selection), plot, sys, *selectors))
        writeHist(f, 'chgIso'+sys,  'all' + splitType, chgIsoHist, (statVariations if sys=='' else None), norm=1)

  f.Close()
  return set(statVariations)

#
# Post-fit plots for charged isolation fit
#
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
templates   = ['all_f', 'all_g', 'all_h']
extraLines  = ['prompt_norm   rateParam * all_g 1']

nonPromptSF = {}
#for selection in ['njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p','all']:
for selection in ['all']:
  for dataDriven in [True]:
    cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + selection
    statVariations = writeRootFileForChgIso(cardName, [], selection)
    writeCard(cardName, ['chgIso'], templates, [], extraLines, ['SideBandUncUp:all_f'], statVariations, {})
    results = runFitDiagnostics(cardName, toys=None, statOnly=False, trackParameters = ['prompt_norm'])
    nonPromptSF[selection] = results['r']
    plot(cardName, '_prefit',  None)
    plot(cardName, '_postfit', results)
    runImpacts(cardName)

for i,j in nonPromptSF.iteritems():
  log.info('Charged isolation fit for ' + i + ' results in %.2f (+%.2f, %.2f)' % j)


#############################################################################################################################################

#
# ROOT file for a signal regions fit
#
def writeRootFile(name, systematics, nonPromptSF):
  f = ROOT.TFile('combine/' + name + '.root', 'RECREATE')

  baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'
  writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-match', 'emu', baseSelection), 'signalRegionsSmall', '', ['MuonEG']))
  writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl(('eleSusyLoose-phoCBfull-match', 'SF',  baseSelection), 'signalRegionsSmall', '', ['DoubleEG'],['DoubleMuon']))

  statVariations = []
  for sample,_ in samples:
    promptSelectors   = [[sample, '(genuine,misIdEle)']]
    fakeSelectors     = [[sample, '(hadronicFake)']]
    hadronicSelectors = [[sample, '(hadronicPhoton)']]
    for sys in [''] + systematics:
      for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF')]:
        prompt   = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection), 'signalRegionsSmall', sys, *promptSelectors)
        fake     = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection), 'signalRegionsSmall', sys, *fakeSelectors)
        hadronic = getHistFromPkl(('eleSusyLoose-phoCBfull-match', channel, baseSelection), 'signalRegionsSmall', sys, *hadronicSelectors)
        if nonPromptSF:
          if sample=='TTJets' and sys=='':
            fakeUp   = applyNonPromptSF(fake, nonPromptSF, 'Up')
            fakeDown = applyNonPromptSF(fake, nonPromptSF, 'Down')
          fake     = applyNonPromptSF(fake, nonPromptSF)
        total = prompt.Clone()
        total.Add(hadronic)
        if sample=='TTJets' and sys=='':
          totalUp   = total.Clone()
          totalDown = total.Clone()
          totalUp.Add(fakeUp)
          totalDown.Add(fakeDown)
          writeHist(f, shape+'fakeUp',   sample, totalUp, None)
          writeHist(f, shape+'fakeDown', sample, totalDown, None)
        total.Add(fake)

        if sample=='ZG':
          for i in range(total.GetNbinsX()):
            total.SetBinContent(i, total.GetBinContent(i)*(zgSF[0]))
        writeHist(f, shape+sys, sample, total, (statVariations if sys=='' else None))

  f.Close()
  return set(statVariations)

#
# Signal regions fit
#
cardName    = 'srFit'
templates   = [s for s,_ in samples if s!='ZG']
extraLines  = [(s + '_norm rateParam * ' + s + '* 1')   for s,_   in samples[1:]]
extraLines += [(s + '_norm param 1.0 ' + str(unc/100.)) for s,unc in samples[1:] if s!='ZG']
extraLines += ['ZG_norm param 1.0 %.3f' % ((abs(zgSF[1])+abs(zgSF[2]))/2)]

statVariations = writeRootFile(cardName, systematics.keys(), nonPromptSF)
writeCard(cardName, ['sr_OF', 'sr_SF'], templates, ['ZG'], extraLines, systematics.keys() + ['TTJets:fakeUp'], statVariations, linearSystematics)

runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=False)
runFitDiagnostics(cardName, trackParameters = ['TTJets_norm', 'ZG_norm','DY_norm','other_norm','r'], toys=None, statOnly=True)
runImpacts(cardName)
runSignificance(cardName)
runSignificance(cardName, expected=True)
