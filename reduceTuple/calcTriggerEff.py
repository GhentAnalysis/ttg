#! /usr/bin/env python

#
# Script to calculate trigger efficiencies using MET reference triggers
#


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--debug',    action='store_true', default=False,  help='Only run over first three files for debugging')
argParser.add_argument('--corr',     action='store_true', default=False,  help='Calculate correlation coefficients')
argParser.add_argument('--pu',       action='store_true', default=False,  help='Use pile-up reweighting (no use of CP intervals)')
argParser.add_argument('--select',   action='store',      default='',     help='Additional selection for systematic studies')
argParser.add_argument('--sample',   action='store',      default=None,   help='Select sample')
argParser.add_argument('--year',     action='store',      default=None,   help='Select year', choices=['2016', '2017', '2018'])
argParser.add_argument('--isChild',  action='store_true', default=False,  help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--runLocal', action='store_true', default=False,  help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='do not launch subjobs, only show them')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.samples.Sample import createSampleList, getSampleFromList
tupleFiles = [os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuplesTrigger_'+ y +'.conf') for y in ['2016', '2017', '2018']] 
sampleList = createSampleList(*tupleFiles)

# Submit subjobs
if not args.isChild:
  from ttg.tools.jobSubmitter import submitJobs
  if args.sample and args.year: sampleList = [s for s in sampleList if s.name == args.sample and s.year == args.year]
  jobs = []
  for sample in sampleList:
    for select in ['', 'ph', 'offZ', 'njet1p', 'njet2p']:
      for corr in [True, False]:
        for pu in [True, False] if sample.name not in ['MET','JetHT'] else [False]:
          jobs += [(sample.name, sample.year, select, corr, pu)]
  submitJobs(__file__, ('sample', 'year', 'select', 'corr', 'pu'), jobs, argParser, wallTime='60')
  exit(0)


if args.select != '':    args.select = '-' + args.select

# Get sample, chain and event loop
sample    = getSampleFromList(sampleList, args.sample, args.year)
c         = sample.initTree(shortDebug=args.debug)
eventLoop = sample.eventLoop(selectionString='_lheHTIncoming<100' if sample.name.count('HT0to100') else None)
log.info('Sample: ' + sample.name)

from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, makeInvariantMasses, goodJets
setIDSelection(c, 'phoCB')

from ttg.tools.style import commonStyle, setDefault
from ttg.tools.helpers import printCanvas 
from ttg.reduceTuple.puReweighting import getReweightingFunction

reweightingFunctions = {'2016':"PU_2016_36000_XSecCentral", '2017':"PU_2017_41500_XSecCentral", '2018':"PU_2018_60000_XSecCentral"}
puReweighting = getReweightingFunction(sample.year, data=reweightingFunctions[sample.year])

import ROOT, numpy

setDefault()
ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gROOT.ForceStyle()

# Select for which the trigger efficiencies are measured
def passSelection():
  if not selectLeptons(c, c, 2): return False
  if args.select.count('ph'):
    c.doPhotonCut = True
    if selectPhotons(c, c, 2, True): return False
  if args.select.count('offZ') and not c.isEMu:
    c.doPhotonCut = False
    selectPhotons(c, c, 2, True)
    makeInvariantMasses(c, c)
    if abs(c.mll  - 91.1876) < 15 : return False
    if abs(c.mllg - 91.1876) < 15 : return False
  if args.select.count('jet'):
    c.doPhotonCut = False
    selectPhotons(c, c, 2, True)
    goodJets(c, c)
    if args.select.count('1p') and not c.njets >= 1: return False
    if args.select.count('2p') and not c.njets >= 2: return False
  return True

# How to pass our triggers
def passTrigger():
  if c.isEE   and (c._passTrigger_ee or c._passTrigger_e):                 return True
  if c.isEMu  and (c._passTrigger_em or c._passTrigger_e or c._passTrigger_m): return True
  if c.isMuMu and (c._passTrigger_mm or c._passTrigger_m):                 return True
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
    if not passSelection(): continue

    if c.isEE:   channel = 'ee'
    if c.isEMu:  channel = 'emu'
    if c.isMuMu: channel = 'mumu'
    puWeight = puReweighting(c._nTrueInt) if args.pu else 1.

    countAll[channel] += puWeight
    if c._passTrigger_ref:                   countMET[channel] += puWeight
    if passTrigger():                        countLep[channel] += puWeight
    if c._passTrigger_ref and passTrigger(): countBoth[channel] += puWeight

  for channel in ['ee', 'emu', 'mumu']:
    log.info('Efficiency  for channel ' + channel + ' is ' + str(countBoth[channel]/countMET[channel]))
    log.info('Correlation for channel ' + channel + ' is ' + str((countMET[channel]*countLep[channel])/(countBoth[channel]*countAll[channel])))

# Trigger efficiency in bins
else:
  hPass, hTotal = {}, {}
  for t in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
    hPass[t], hTotal[t] = {}, {}
    for channel in ['ee', 'emu', 'mue', 'mumu']:
      if 'etaBinning' in t:
        binningX = numpy.array([0., .8, 1.442, 1.566, 2., 2.4]) if channel.startswith('e') else numpy.array([0., 0.9, 1.2, 2.1, 2.4])
        binningY = numpy.array([0., .8, 1.442, 1.566, 2., 2.4]) if channel.endswith('e')   else numpy.array([0., 0.9, 1.2, 2.1, 2.4])
      elif 'integral' in t:
        binningX = numpy.array([25., 9999.])
        binningY = numpy.array([15., 9999.])
      else:
        binningX = numpy.array([25., 35, 50, 100, 150, 250])
        binningY = numpy.array([15., 20, 25, 35, 50, 100, 150, 250])
      name    = sample.name + ' ' + channel + ' ' + t
      hPass[t][channel]  = ROOT.TH2D(name + 'Pass',  name, len(binningX)-1, binningX, len(binningY)-1, binningY)
      hTotal[t][channel] = ROOT.TH2D(name + 'Total', name, len(binningX)-1, binningX, len(binningY)-1, binningY)


  for i in eventLoop:
    c.GetEntry(i)
    if not c._passTrigger_ref: continue
    if not passSelection():  continue

    if c.isEE:   channel = 'ee'
    if c.isEMu:  channel = 'emu' if c._lFlavor[c.l1] == 0 else 'mue'
    if c.isMuMu: channel = 'mumu'
    puWeight = puReweighting(c._nTrueInt) if args.pu else 1.

    for t in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
      if 'l1c' in t and abs(c._lEta[c.l1]) > 1.5: continue
      if 'l1e' in t and abs(c._lEta[c.l1]) < 1.5: continue
      if 'l2c' in t and abs(c._lEta[c.l2]) > 1.5: continue
      if 'l2e' in t and abs(c._lEta[c.l2]) < 1.5: continue

      if 'etaBinning' in t: hTotal[t][channel].Fill(c._lEta[c.l1], c._lEta[c.l2], puWeight)
      else:                 hTotal[t][channel].Fill(c.l1_pt, c.l2_pt, puWeight)
      if passTrigger():
        if 'etaBinning' in t: hPass[t][channel].Fill(c._lEta[c.l1], c._lEta[c.l2], puWeight)
        else:                 hPass[t][channel].Fill(c.l1_pt, c.l2_pt, puWeight)

  outFile = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerEfficiencies' + args.select + ('_puWeighted' if args.pu else '') + '_' + args.year + '.root'), 'update')
  for t in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
    for channel in ['ee', 'emu', 'mue', 'mumu']:
      eff = ROOT.TEfficiency(hPass[t][channel], hTotal[t][channel])
      eff.SetStatisticOption(ROOT.TEfficiency.kFCP)
      eff.Draw()
      ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
      effDraw = eff.GetPaintedHistogram()

      for i in range(1, effDraw.GetNbinsX()+1):
        for j in range(1, effDraw.GetNbinsY()+1):
          globalBin = eff.GetGlobalBin(i, j)
          effDraw.SetBinError(i, j, max(eff.GetEfficiencyErrorUp(globalBin), eff.GetEfficiencyErrorLow(globalBin)))

      canvas = ROOT.TCanvas(eff.GetName(), eff.GetName())
      canvas.cd()
      ROOT.gStyle.SetPaintTextFormat("2.5f" if 'integral' in t else "2.2f")
      commonStyle(effDraw)
      if 'etaBinning' in t:
        effDraw.GetXaxis().SetTitle("leading lepton #eta")
        effDraw.GetYaxis().SetTitle("trailing lepton #eta")
      else:
        effDraw.GetXaxis().SetTitle("leading lepton p_{T} [Gev]")
        effDraw.GetYaxis().SetTitle("trailing lepton p_{T} [Gev]")
      effDraw.SetTitle("")
      effDraw.SetMarkerSize(0.8)
      effDraw.Draw("COLZ TEXT")
      canvas.RedrawAxis()
      if not ('etaBinning' in t or 'integral' in t):
        canvas.SetLogy()
        canvas.SetLogx()
        effDraw.GetXaxis().SetMoreLogLabels()
        effDraw.GetYaxis().SetMoreLogLabels()
        effDraw.GetXaxis().SetNoExponent()
        effDraw.GetYaxis().SetNoExponent()
      effDraw.SetMinimum(0.)
      effDraw.SetMaximum(1.)
      effDraw.Draw("COLZ TEXTE")
      canvas.RedrawAxis()
      directory = os.path.expandvars('/user/$USER/public_html/ttG/triggerEfficiency/' + sample.year + ('/puWeighted/' if args.pu else '/') + sample.name + '_' + sample.year + '/' + args.select)
      printCanvas(canvas, directory, channel + t, ['pdf', 'png'])
      outFile.cd()
      eff.Write(sample.name + '-' + channel + t)

log.info('Finished')
