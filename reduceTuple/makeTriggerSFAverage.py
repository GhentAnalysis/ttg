#! /usr/bin/env python

#
# Script to make the trigger SF histogram, provided the trigger efficiencies calculated by the calcTriggerEff.py script
#
import pdb

#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--pu',       action='store_true', default=False,  help='Use pile-up reweighting (no use of CP intervals)')
argParser.add_argument('--select',   action='store',      default='',     help='Additional selection for systematic studies')
argParser.add_argument('--selectID', action='store',      default='POG',  help='Selection of lepton ID, as in the trigger efficiency file names', choices=['phoCB', 'phoCBfull', 'leptonMVA-phoCB', 'phoCB-new'])
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.tools.style import commonStyle, setDefault
from ttg.tools.helpers import printCanvas, getObjFromFile
from math import sqrt
import ROOT

setDefault()
ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gROOT.ForceStyle()


def mkTriggerSF(year):
  mcFile   = os.path.join('data', 'triggerEff', 'triggerEfficiencies' + '_' + args.selectID + '_' + args.select + ('_puWeighted' if args.pu else '') + '_' + year  + '.root')
  dataFile = os.path.join('data', 'triggerEff', 'triggerEfficiencies' + '_' + args.selectID + '_' + args.select + '_' + year  + '.root')
  sfFile   = os.path.join('data', 'triggerEff', 'triggerSFAveraged'           + '_' + args.selectID + '_' + args.select + ('_puWeighted' if args.pu else '') + '_' + year  + '.root')
  sfFile   = ROOT.TFile(sfFile, 'update')
  for t in ['', '-l1cl2c', '-l1cl2e', '-l1el2c', '-l1el2e', '-l1c', '-l1e', '-l2c', '-l2e', '-etaBinning', '-integral']:
    # for channel in ['ee', 'emu', 'mue', 'mumu']:
    for channel in ['ee', 'emu', 'mumu']:
      effData = getObjFromFile(dataFile, 'MET-'  + channel + t) # Could also use JETHT
      effMC   = getObjFromFile(mcFile,   'TT_Dil-' + channel + t)
      if not effData: log.warning('MET-'    + channel + t + ' missing in ' + dataFile + ', skipping ')
      if not effMC:   log.warning('TT_Dil-' + channel + t + ' missing in ' + mcFile + ', skipping ')
      effData.SetStatisticOption(ROOT.TEfficiency.kFCP)
      effMC.SetStatisticOption(ROOT.TEfficiency.kFCP)
      effData.Draw()
      ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
      hist = effData.GetPaintedHistogram().Clone()
      for i in range(1, hist.GetNbinsX()+1):
        for j in range(1, hist.GetNbinsX()+1):
          globalBin = effData.GetGlobalBin(i, j)
          if effMC.GetEfficiency(globalBin) > 0:
            hist.SetBinContent(i, j, effData.GetEfficiency(globalBin)/effMC.GetEfficiency(globalBin))
            errUp  = sqrt(effData.GetEfficiencyErrorUp(globalBin)**2+effMC.GetEfficiencyErrorUp(globalBin)**2)
            errLow = sqrt(effData.GetEfficiencyErrorLow(globalBin)**2+effMC.GetEfficiencyErrorLow(globalBin)**2)
            hist.SetBinError(i, j, max(errUp, errLow))

      effData = getObjFromFile(dataFile, 'JetHT-'  + channel + t) # Could also use JETHT
      effMC   = getObjFromFile(mcFile,   'TT_Dil-' + channel + t)
      if not effData: log.warning('JetHT-'    + channel + t + ' missing in ' + dataFile + ', skipping ')
      if not effMC:   log.warning('TT_Dil-' + channel + t + ' missing in ' + mcFile + ', skipping ')
      effData.SetStatisticOption(ROOT.TEfficiency.kFCP)
      effMC.SetStatisticOption(ROOT.TEfficiency.kFCP)

      effData.Draw()
      ROOT.gPad.Update() # Important, otherwise ROOT throws null pointers
      hist2 = effData.GetPaintedHistogram()
      for i in range(1, hist2.GetNbinsX()+1):
        for j in range(1, hist2.GetNbinsX()+1):
          globalBin = effData.GetGlobalBin(i, j)
          if effMC.GetEfficiency(globalBin) > 0:
            hist2.SetBinContent(i, j, effData.GetEfficiency(globalBin)/effMC.GetEfficiency(globalBin))
            errUp  = sqrt(effData.GetEfficiencyErrorUp(globalBin)**2+effMC.GetEfficiencyErrorUp(globalBin)**2)
            errLow = sqrt(effData.GetEfficiencyErrorLow(globalBin)**2+effMC.GetEfficiencyErrorLow(globalBin)**2)
            hist2.SetBinError(i, j, max(errUp, errLow))


          
      # pdb.set_trace()


      hist.Add(hist2)
      hist.Scale(0.5)

      canvas = ROOT.TCanvas(effData.GetName() + year, effData.GetName())
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

      directory = os.path.expandvars('/user/$USER/public_html/ttG/triggerEfficiency/' + ('puWeighted/' if args.pu else '') + 'SF_' + args.selectID + '_' + year +  '/' + args.select)
      printCanvas(canvas, directory, channel + t, ['pdf', 'png'])
      sfFile.cd()
      hist.Write('SF-' + channel + t)

for y in ['2016', '2017', '2018']:
  log.info('making trigger ScaleFactors for ' + y)
  mkTriggerSF(y)

log.info('Finished')
