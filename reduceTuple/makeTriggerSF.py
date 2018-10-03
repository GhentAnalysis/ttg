#! /usr/bin/env python

#
# Script to make the trigger SF histogram, provided the trigger efficiencies calculated by the calcTriggerEff.py script
#


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--pu',             action='store_true', default=False,                help='Use pile-up reweighting (no use of CP intervals)')
argParser.add_argument('--select',         action='store',      default='',                   help='Additional selection for systematic studies')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.tools.style import commonStyle
from ttg.tools.helpers import copyIndexPHP
from math import sqrt
import ROOT, numpy
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/ttg/tools/scripts/tdrstyle.C")
ROOT.setTDRStyle()
ROOT.gROOT.SetStyle('tdrStyle')
ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gROOT.ForceStyle()

outFile = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerSF' + args.select + ('_puWeighted' if args.pu else '') + '.root'), 'update')
inFile  = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerEfficiencies' + args.select + ('_puWeighted' if args.pu else '') + '.root'))
for type in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e','-etaBinning','-integral']:
  for channel in ['ee','emu','mue','mumu']:
    effData = inFile.Get('MET-'     + channel + type)
    effMC   = inFile.Get('TTGamma-' + channel + type)
    effData.SetStatisticOption(ROOT.TEfficiency.kFCP)
    effMC.SetStatisticOption(ROOT.TEfficiency.kFCP)
    effData.Draw()
    ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
    hist = effData.GetPaintedHistogram()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        bin = effData.GetGlobalBin(i, j)
        if effMC.GetEfficiency(bin) > 0:
          hist.SetBinContent(i, j, effData.GetEfficiency(bin)/effMC.GetEfficiency(bin))
          errUp  = sqrt(effData.GetEfficiencyErrorUp(bin)**2+effMC.GetEfficiencyErrorUp(bin)**2)
          errLow = sqrt(effData.GetEfficiencyErrorLow(bin)**2+effMC.GetEfficiencyErrorLow(bin)**2)
          hist.SetBinError(i, j, max(errUp, errLow))

    canvas = ROOT.TCanvas(effData.GetName(), effData.GetName())
    canvas.cd()
    ROOT.gStyle.SetPaintTextFormat("2.5f" if 'integral' in type else "2.2f")
    commonStyle(hist)
    hist.GetXaxis().SetTitle("leading lepton p_{T} [Gev]")
    hist.GetYaxis().SetTitle("trailing lepton p_{T} [Gev]")
    hist.SetTitle("")
    hist.SetMarkerSize(0.8)
    hist.Draw("COLZ TEXT")
    canvas.RedrawAxis()
    if not ('etaBinning' in type or 'integral' in type):
      canvas.SetLogy()
      canvas.SetLogx()
      hist.GetXaxis().SetMoreLogLabels()
      hist.GetYaxis().SetMoreLogLabels()
      hist.GetXaxis().SetNoExponent()
      hist.GetYaxis().SetNoExponent()
    hist.SetMinimum(0.8)
    hist.SetMaximum(1.2)
    hist.Draw("COLZ TEXTE")
    canvas.RedrawAxis()
    dir = '/user/tomc/www/ttG/triggerEfficiency/' + ('puWeighted/' if args.pu else '') + 'SF' + '/' + args.select
    try:    os.makedirs(dir)
    except: pass
    copyIndexPHP(dir)
    canvas.Print(os.path.join(dir, channel + type + '.pdf'))
    canvas.Print(os.path.join(dir, channel + type + '.png'))
    outFile.cd()
    hist.Write('SF-' + channel + type)

log.info('Finished')
