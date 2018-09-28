#! /usr/bin/env python

#
# Script to calculate trigger efficiencies using MET reference triggers
#


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--debug',          action='store_true', default=False,                help='Only run over first three files for debugging')
argParser.add_argument('--corr',           action='store_true', default=False,                help='Calculate correlation coefficients')
argParser.add_argument('--pu',             action='store_true', default=False,                help='Use pile-up reweighting (no use of CP intervals)')
argParser.add_argument('--select',         action='store',      default='',                   help='Additional selection for systematic studies')
argParser.add_argument('--sample',         action='store',      default=None,                 help='Select sample')
argParser.add_argument('--isChild',        action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--runLocal',       action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',         action='store_true', default=False,                help='do not launch subjobs, only show them')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.samples.Sample import createSampleList,getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuplesTrigger.conf'))

# Submit subjobs
if not args.isChild and not args.sample:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample: sampleList = filter(lambda s: s.name == args.sample, sampleList)

  jobs = []
  for sample in sampleList:
    for select in ['', 'ph', 'offZ', 'njet1p', 'njet2p']:
      for corr in [True, False]:
        for pu in [True, False]:
          jobs += [(sample.name, select, corr, pu)]

  submitJobs(__file__, ('sample', 'select', 'corr', 'pu'), jobs, argParser)
  exit(0)


if args.select != '': args.select = '-' + args.select

# Get sample, chain and event loop
sample    = getSampleFromList(sampleList, args.sample)
c         = sample.initTree(skimType='dilepton', shortDebug=args.debug)
eventLoop = sample.eventLoop(selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None)
log.info('Sample: ' + sample.name)

from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets
setIDSelection(c, 'eleSusyLoose-phoCB')

from ttg.tools.style import commonStyle
from ttg.tools.helpers import copyIndexPHP
from ttg.reduceTuple.puReweighting import getReweightingFunction
puReweighting = getReweightingFunction(data="PU_2016_36000_XSecCentral")

import ROOT, numpy
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/ttg/tools/scripts/tdrstyle.C")
ROOT.setTDRStyle()
ROOT.gROOT.SetStyle('tdrStyle')
ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gROOT.ForceStyle()

# Select for which the trigger efficiencies are measured
def passSelection(c):
  if not selectLeptons(c, c, 2): return False
  if args.select.count('ph')   and not selectPhotons(c, c, True, 2, False): return False
  if args.select.count('offZ') and not c.isEMu:
    makeInvariantMasses(c, c)
    if abs(c.mll  - 91.1876) < 15 : return False
    if abs(c.mllg - 91.1876) < 15 : return False
  if args.select.count('jet'):
    goodJets(c, c, 30)
    if args.select.count('1p') and not c.njets >= 1: return False
    if args.select.count('2p') and not c.njets >= 2: return False
  return True

# How to pass our triggers
def passTrigger(c):
  if c.isEE   and (c._passTTG_ee or c._passTTG_e):                 return True 
  if c.isEMu  and (c._passTTG_em or c._passTTG_e or c._passTTG_m): return True
  if c.isMuMu and (c._passTTG_mm or c._passTTG_m):                 return True
  return False

# Efficiency and correlation for the whole selection
if args.corr:
  countAll, countMET, countLep, countBoth = {}, {}, {}, {}
  for channel in ['ee', 'emu', 'mumu']:
    countAll[channel]  = 0.
    countMET[channel]  = 0.
    countLep[channel]  = 0.
    countBoth[channel] = 0.

  for i in eventLoop:
    c.GetEntry(i)
    if not passSelection(c): continue
 
    if c.isEE:   channel = 'ee'
    if c.isEMu:  channel = 'emu'
    if c.isMuMu: channel = 'mumu'
    puWeight = puReweighting(c._nTrueInt) if args.pu else 1.

    countAll[channel] += puWeight
    if c._passTTG_cross:                    countMET[channel] += puWeight
    if passTrigger(c):                      countLep[channel] += puWeight 
    if c._passTTG_cross and passTrigger(c): countBoth[channel] += puWeight
    
  for channel in ['ee', 'emu', 'mumu']:
    log.info('Efficiency  for channel ' + channel + ' is ' + str(countBoth[channel]/countMET[channel]))
    log.info('Correlation for channel ' + channel + ' is ' + str((countMET[channel]*countLep[channel])/(countBoth[channel]*countAll[channel])))

# Trigger efficiency in bins
else:
  hPass, hTotal = {}, {}
  for type in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e','-etaBinning','-integral']:
    hPass[type], hTotal[type] = {}, {}
    for channel in ['ee','emu','mue','mumu']:
      if 'etaBinning' in type:
        binningX = numpy.array([0., .8, 1.442, 1.566, 2., 2.4]) if channel.startswith('e') else numpy.array([0., 0.9, 1.2, 2.1, 2.4]) 
        binningY = numpy.array([0., .8, 1.442, 1.566, 2., 2.4]) if channel.endswith('e')   else numpy.array([0., 0.9, 1.2, 2.1, 2.4])
      elif 'integral' in type:
        binningX = numpy.array([25., 9999.])
        binningY = numpy.array([15., 9999.])
      else:
        binningX = numpy.array([25., 35, 50, 100, 150, 250])
        binningY = numpy.array([15., 20, 25, 35, 50, 100, 150, 250])
      name    = sample.name + ' ' + channel + ' ' + type
      hPass[type][channel]  = ROOT.TH2D(name + 'Pass',  name, len(binningX)-1, binningX, len(binningY)-1, binningY)
      hTotal[type][channel] = ROOT.TH2D(name + 'Total', name, len(binningX)-1, binningX, len(binningY)-1, binningY)
      

  for i in eventLoop:
    c.GetEntry(i)

    if not c._passTTG_cross: continue
    if not passSelection(c): continue

    if c.isEE:   channel = 'ee'
    if c.isEMu:  channel = 'emu' if c._lFlavor[c.l1] == 0 else 'mue'
    if c.isMuMu: channel = 'mumu'
    puWeight = puReweighting(c._nTrueInt) if args.pu else 1.

    for type in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
      if 'l1c' in type and abs(c._lEta[c.l1]) > 1.5: continue
      if 'l1e' in type and abs(c._lEta[c.l1]) < 1.5: continue
      if 'l2c' in type and abs(c._lEta[c.l2]) > 1.5: continue
      if 'l2e' in type and abs(c._lEta[c.l2]) < 1.5: continue

      if 'etaBinning' in type: hTotal[type][channel].Fill(c._lEta[c.l1], c._lEta[c.l2], puWeight)
      else:                    hTotal[type][channel].Fill(c.l1_pt, c.l2_pt, puWeight)
      if passTrigger(c):
        if 'etaBinning' in type: hPass[type][channel].Fill(c._lEta[c.l1], c._lEta[c.l2], puWeight)
        else:                    hPass[type][channel].Fill(c.l1_pt, c.l2_pt, puWeight)

  outFile = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerEfficiencies' + args.select + ('_puWeighted' if args.pu else '') + '.root'), 'update')
  for type in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
    for channel in ['ee', 'emu', 'mue', 'mumu']:
      eff = ROOT.TEfficiency(hPass[type][channel], hTotal[type][channel])
      eff.SetStatisticOption(ROOT.TEfficiency.kFCP)
      eff.Draw()
      ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
      effDraw = eff.GetPaintedHistogram()

      for i in range(1, effDraw.GetNbinsX()+1):
        for j in range(1, effDraw.GetNbinsY()+1):
          bin = eff.GetGlobalBin(i, j)
          effDraw.SetBinError(i, j, max(eff.GetEfficiencyErrorUp(bin), eff.GetEfficiencyErrorLow(bin)))

      canvas = ROOT.TCanvas(eff.GetName(), eff.GetName())
      canvas.cd()
      ROOT.gStyle.SetPaintTextFormat("2.2f")
      commonStyle(effDraw)
      effDraw.GetXaxis().SetTitle("leading lepton p_{T} [Gev]")
      effDraw.GetYaxis().SetTitle("trailing lepton p_{T} [Gev]")
      effDraw.SetTitle("")
      effDraw.SetMarkerSize(0.8)
      effDraw.Draw("COLZ TEXT")
      canvas.RedrawAxis()
      canvas.SetLogy()
      canvas.SetLogx()
      effDraw.GetXaxis().SetMoreLogLabels()
      effDraw.GetYaxis().SetMoreLogLabels()
      effDraw.GetXaxis().SetNoExponent()
      effDraw.GetYaxis().SetNoExponent()
      effDraw.Draw("COLZ TEXTE")
      canvas.RedrawAxis()
      dir = '/user/tomc/www/ttG/triggerEfficiency/' + ('puWeighted/' if args.pu else '') + sample.name + '/' + args.select
      try:    os.makedirs(dir)
      except: pass
      copyIndexPHP(dir)
      canvas.Print(os.path.join(dir, channel + type + '.pdf'))
      canvas.Print(os.path.join(dir, channel + type + '.png'))
      outFile.cd()
      eff.Write(sample.name + '-' + channel + type)


log.info('Finished')
