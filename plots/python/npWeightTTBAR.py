#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
from ttg.plots.plotHelpers import createSignalRegions
from ttg.tools.logger import getLogger
log = getLogger()
import pickle
import time
import ROOT
ROOT.TH2.SetDefaultSumw2()
ROOT.TH1.SetDefaultSumw2()

sourceHists ={'A': ('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl'),

              'B': ('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl'),

              'C': ('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl'),

              'D': ('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                    '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl')
}


def sumHists(sourceHists, plot):
  nHist = None
  gHist = None
  dHist = None
  for file in sourceHists:
    hists = pickle.load(open(file))[plot]
    for name, hist in hists.iteritems():
      if 'nonprompt' in name:
        if not nHist: nHist = hist.Clone()
        else: nHist.Add(hist)
      elif 'genuine' in name:
        if not gHist: gHist = hist.Clone()
        else: gHist.Add(hist)
      elif 'data' in name:
        if not dHist: dHist = hist.Clone()
        else: dHist.Add(hist)
      else:
        print 'warning ' + name
  return (nHist, gHist, dHist)

class npWeight:
  def __init__(self, sigmaFlat, sigmaHigh):
    self.sigmaFlat = sigmaFlat
    self.sigmaHigh = sigmaHigh
    try:
        # for data driven estimate
      histA, histB, histC, histD = (sumHists(sourceHists[region], 'photon_pt_etaA') for region in ['A', 'B', 'C', 'D'])

      # for MC based estimate / closure test
      histC[0].Divide(histD[0])
      self.mcEst = histC[0]
      assert self.mcEst
    except:
      log.warning('No NP estimate source plots available, no problem if not used later')

  def getWeight(self, tree, isData):
    if tree.NPestimate:
      pt  = tree.ph_pt
      eta = abs(tree._phEta[tree.ph])
      if pt >= 120: pt = 119 # last bin is valid to infinity
      if isData:
        sf =  self.dataEst.GetBinContent(self.dataEst.GetXaxis().FindBin(pt), self.dataEst.GetYaxis().FindBin(eta))
      else:
        sf =  self.mcEst.GetBinContent(self.mcEst.GetXaxis().FindBin(pt), self.mcEst.GetYaxis().FindBin(eta))
      # return sf*(1.+self.sigma* (0.30 if pt > 100. else 0.05) )
      return sf*(1. +self.sigmaFlat* 0.05 +self.sigmaHigh* (0.50 if pt > 80. else 0.) )
    else: return 1.

if __name__ == '__main__':
  ROOT.gROOT.SetBatch(True)
  ROOT.gStyle.SetPadRightMargin(0.12)
  ROOT.gStyle.SetOptStat('')
  # ROOT.gStyle.SetPaintTextFormat("4.4f")
  ROOT.gStyle.SetPaintTextFormat("3.2f")

  tester = npWeight(0., 0.)

  # c1 = ROOT.TCanvas('c', 'c', 900, 800)
  # tester.dataEst.SetTitle('')
  # tester.dataEst.GetYaxis().SetTitle('|#eta(#gamma)|')
  # tester.dataEst.GetXaxis().SetTitle('p_{T}(#gamma)')
  # tester.dataEst.Draw("COLZ TEXT E")
  # c1.SaveAs('estMaps/sfDataMerged.png')
  # c1.SaveAs('estMaps/sfDataMerged.pdf')
  c1 = ROOT.TCanvas('c', 'c', 900, 800)
  tester.mcEst.SetTitle('')
  tester.mcEst.GetYaxis().SetTitle('|#eta(#gamma)|')
  tester.mcEst.GetXaxis().SetTitle('p_{T}(#gamma)')
  tester.mcEst.Draw("COLZ TEXT E")
  c1.SaveAs('estMaps/sfTTBARMCMerged.png')
  c1.SaveAs('estMaps/sfTTBARMCMerged.pdf')

  # c1 = ROOT.TCanvas('c', 'c', 900, 800)
  # tester.DC.SetTitle('')
  # tester.DC.GetYaxis().SetTitle('|#eta(#gamma)|')
  # tester.DC.GetXaxis().SetTitle('p_{T}(#gamma)')
  # tester.DC.Draw("COLZ TEXT E")
  # c1.SaveAs('estMaps/CDataMerged.png')
  # c1.SaveAs('estMaps/CDataMerged.pdf')
  # c1 = ROOT.TCanvas('c', 'c', 900, 800)
  # tester.MCC.SetTitle('')
  # tester.MCC.GetYaxis().SetTitle('|#eta(#gamma)|')
  # tester.MCC.GetXaxis().SetTitle('p_{T}(#gamma)')
  # tester.MCC.Draw("COLZ TEXT E")
  # c1.SaveAs('estMaps/CMCMerged.png')
  # c1.SaveAs('estMaps/CMCMerged.pdf')

  # c1 = ROOT.TCanvas('c', 'c', 900, 800)
  # tester.DD.SetTitle('')
  # tester.DD.GetYaxis().SetTitle('|#eta(#gamma)|')
  # tester.DD.GetXaxis().SetTitle('p_{T}(#gamma)')
  # tester.DD.Draw("COLZ TEXT E")
  # c1.SaveAs('estMaps/DDataMerged.png')
  # c1.SaveAs('estMaps/DDataMerged.pdf')
  # c1 = ROOT.TCanvas('c', 'c', 900, 800)
  # tester.MCD.SetTitle('')
  # tester.MCD.GetYaxis().SetTitle('|#eta(#gamma)|')
  # tester.MCD.GetXaxis().SetTitle('p_{T}(#gamma)')
  # tester.MCD.Draw("COLZ TEXT E")
  # c1.SaveAs('estMaps/DMCMerged.png')
  # c1.SaveAs('estMaps/DMCMerged.pdf')