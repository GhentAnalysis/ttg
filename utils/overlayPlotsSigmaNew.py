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


offZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-forNPest-nonpromptErr/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_SigmaIetaIeta_small.pkl'
onZfile = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-forNPest-nonpromptErr/noData/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_SigmaIetaIeta_small.pkl'
offZ = sumHists(offZfile, 'photon_SigmaIetaIeta_small')[0]
onZ = sumHists(onZfile, 'photon_SigmaIetaIeta_small')[0]
c1 = ROOT.TCanvas('c', 'c', 1000, 800)
offZ.Scale(1./offZ.Integral())
onZ.Scale(1./onZ.Integral())
offZ.SetTitle('')
offZ.SetLineColor(ROOT.kBlue)
onZ.SetLineColor(ROOT.kRed)
offZ.SetLineWidth(2)
onZ.SetLineWidth(2)
offZ.GetXaxis().SetRangeUser(0., 0.025)
offZ.GetYaxis().SetRangeUser(0., 0.18)
offZ.GetXaxis().SetTitle("#sigma_{i#etai#eta}(#gamma)")  
offZ.GetYaxis().SetTitle("(1/N) dN")  
legend = ROOT.TLegend(0.6,0.74,0.88,0.9)
legend.AddEntry(offZ,"application region","L")
legend.AddEntry(onZ,"measurement region","L")
offZ.Draw('E ')
onZ.Draw('E same')
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