#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle
import time
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.12)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  sumHist = None
  for name, hist in hists.iteritems():
    if not sumHist: sumHist = hist
    else: sumHist.Add(hist)
  return sumHist

offZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-onlyZG-normalize-norat/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl'
onZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-onlyZG-normalize-norat/noData/llg-mll40-signalRegion-offZ-llgOnZ-photonPt20/signalRegions.pkl'
offZ = sumHists(offZfile, 'signalRegions')
onZ = sumHists(onZfile, 'signalRegions')
c1 = ROOT.TCanvas('c', 'c', 1000, 800)
offZ.Scale(1./offZ.Integral())
onZ.Scale(1./onZ.Integral())
offZ.SetTitle('')
offZ.SetLineColor(ROOT.kBlue)
onZ.SetLineColor(ROOT.kRed)
offZ.SetLineWidth(2)
onZ.SetLineWidth(2)
# offZ.GetXaxis().SetRangeUser(0., 0.025)
# offZ.GetYaxis().SetRangeUser(0., 0.18)
offZ.GetXaxis().SetTitle("signal regions")
labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
for i, l in enumerate(labels):
  offZ.GetXaxis().SetBinLabel(i+1, l)
offZ.GetYaxis().SetTitle("(1/N) dN")  
legend = ROOT.TLegend(0.7,0.74,0.88,0.9)
legend.AddEntry(offZ,"off-DY","L")
legend.AddEntry(onZ,"on-DY","L")
offZ.Draw('hist ')
onZ.Draw('hist same')
legend.Draw()
c1.SaveAs('signalRegions.png')
