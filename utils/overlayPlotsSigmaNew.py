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
  nHist = None
  gHist = None
  dHist = None
  for name, hist in hists.iteritems():
    if 'nonprompt' in name:
      if not nHist: nHist = hist
      else: nHist.Add(hist)
    elif 'genuine' in name:
      if not gHist: gHist = hist
      else: gHist.Add(hist)
    elif 'data' in name:
      if not dHist: dHist = hist
      else: dHist.Add(hist)
    else:
      print 'warning ' + name
  return (nHist, gHist, dHist)

onZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-forNPest/all/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_SigmaIetaIeta_small.pkl'
offZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_SigmaIetaIeta_small.pkl'
offZ = sumHists(offZfile, 'photon_SigmaIetaIeta_small')[0]
onZ = sumHists(onZfile, 'photon_SigmaIetaIeta_small')[0]
c1 = ROOT.TCanvas('c', 'c', 1300, 800)
# ROOT.gPad.SetLogy()
offZ.Scale(1./offZ.Integral())
onZ.Scale(1./onZ.Integral())
offZ.SetTitle('')
offZ.SetLineColor(ROOT.kBlue)
onZ.SetLineColor(ROOT.kRed)
offZ.SetLineWidth(2)
onZ.SetLineWidth(2)
offZ.GetXaxis().SetRangeUser(0.005, 0.020)
offZ.GetYaxis().SetRangeUser(0., 0.15)
offZ.GetXaxis().SetTitle("#sigma_{i#etai#eta}(#gamma)")  
offZ.GetYaxis().SetTitle("(1/N) dN")  
legend = ROOT.TLegend(0.48,0.74,0.88,0.89)
legend.SetBorderSize(0)
# legend.AddEntry(offZ,"application region: m(ll) off-Z, pass Ch. Iso","L")
# legend.AddEntry(onZ,"measurement region: m(ll) on-Z, fail Ch. Iso","L")
legend.AddEntry(offZ,"application region: pass Ch. Iso, N_{b} #geq 1  ","L")
legend.AddEntry(onZ,"measurement region: fail Ch. Iso, N_{j} #geq 1 (SF)  ","L")


offZ.Draw('HIST E')
onZ.Draw('HIST E same')
l1 = ROOT.TLine(0.01015,0.0,0.01015,0.15)
l1.SetLineStyle(2)
l1.SetLineWidth(4)
l1.Draw()
l2 = ROOT.TLine(0.012,0.0,0.012,0.15)
l2.SetLineStyle(2)
l2.SetLineWidth(4)
l2.Draw()
legend.Draw()
c1.SaveAs('newSigmaOnOffZsmall.png')

# offZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-NPcontrib-passChgIso-normalize-norat/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_SigmaIetaIeta.pkl'
# onZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-NPcontrib-passChgIso-normalize-norat/noData/llg-mll40-signalRegion-onZ-llgNoZ-photonPt20/photon_SigmaIetaIeta.pkl'
# offZ = sumHists(offZfile, 'photon_SigmaIetaIeta')[0]
# onZ = sumHists(onZfile, 'photon_SigmaIetaIeta')[0]
# c1 = ROOT.TCanvas('c', 'c', 1000, 800)
# offZ.Scale(1./offZ.Integral())
# onZ.Scale(1./onZ.Integral())
# offZ.SetTitle('')
# offZ.SetLineColor(ROOT.kBlue)
# onZ.SetLineColor(ROOT.kRed)
# offZ.SetLineWidth(2)
# onZ.SetLineWidth(2)
# offZ.GetXaxis().SetRangeUser(0., 0.025)
# offZ.GetYaxis().SetRangeUser(0., 0.45)
# offZ.GetXaxis().SetTitle("#sigma_{i#etai#eta}(#gamma)")  
# offZ.GetYaxis().SetTitle("(1/N) dN")
# legend = ROOT.TLegend(0.7,0.74,0.88,0.9)
# legend.AddEntry(offZ,"off-DY","L")
# legend.AddEntry(onZ,"on-DY","L")
# offZ.Draw('hist ')
# onZ.Draw('hist same')
# legend.Draw()
# c1.SaveAs('sigmaOnOffZ.png')