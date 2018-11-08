#! /usr/bin/env python

#
# Script to make the trigger SF histogram, provided the trigger efficiencies calculated by the calcTriggerEff.py script
#


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--pu',       action='store_true', default=False,  help='Use pile-up reweighting (no use of CP intervals)')
argParser.add_argument('--select',   action='store',      default='',     help='Additional selection for systematic studies')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.tools.style import commonStyle, setDefault
from ttg.tools.helpers import copyIndexPHP
from math import sqrt
import ROOT

setDefault()
ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gROOT.ForceStyle()

outFile = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerSF' + args.select + ('_puWeighted' if args.pu else '') + '.root'), 'update')
inFile  = ROOT.TFile.Open(os.path.join('data', 'triggerEff', 'triggerEfficiencies' + args.select + ('_puWeighted' if args.pu else '') + '.root'))
for t in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
  for channel in ['ee', 'emu', 'mue', 'mumu']:
    effData = inFile.Get('MET-'     + channel + t)
    effMC   = inFile.Get('TTGamma-' + channel + t)
    effData.SetStatisticOption(ROOT.TEfficiency.kFCP)
    effMC.SetStatisticOption(ROOT.TEfficiency.kFCP)
    effData.Draw()
    ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
    hist = effData.GetPaintedHistogram()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        globalBin = effData.GetGlobalBin(i, j)
        if effMC.GetEfficiency(globalBin) > 0:
          hist.SetBinContent(i, j, effData.GetEfficiency(globalBin)/effMC.GetEfficiency(globalBin))
          errUp  = sqrt(effData.GetEfficiencyErrorUp(globalBin)**2+effMC.GetEfficiencyErrorUp(globalBin)**2)
          errLow = sqrt(effData.GetEfficiencyErrorLow(globalBin)**2+effMC.GetEfficiencyErrorLow(globalBin)**2)
          hist.SetBinError(i, j, max(errUp, errLow))

    canvas = ROOT.TCanvas(effData.GetName(), effData.GetName())
    canvas.cd()
    ROOT.gStyle.SetPaintTextFormat("2.5f" if 'integral' in t else "2.2f")
    commonStyle(hist)
    hist.GetXaxis().SetTitle("leading lepton p_{T} [Gev]")
    hist.GetYaxis().SetTitle("trailing lepton p_{T} [Gev]")
    hist.SetTitle("")
    hist.SetMarkerSize(0.8)
    hist.Draw("COLZ TEXT")
    canvas.RedrawAxis()
    if not ('etaBinning' in t or 'integral' in t):
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
    directory = '/user/tomc/www/ttG/triggerEfficiency/' + ('puWeighted/' if args.pu else '') + 'SF' + '/' + args.select
    try:    os.makedirs(directory)
    except: pass
    copyIndexPHP(directory)
    canvas.Print(os.path.join(directory, channel + t + '.pdf'))
    canvas.Print(os.path.join(directory, channel + t + '.png'))
    outFile.cd()
    hist.Write('SF-' + channel + t)

log.info('Finished')
