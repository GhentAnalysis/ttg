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

# /phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest-onlyMC-norat/emu/llg-mll20-photonPt20

sourceHists ={'2016': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl'),
              '2017': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl'),
              '2018': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-onlyTTBAR-passChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-onlyTTBAR-passChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-onlyTTDY-failChgIso-passSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-onlyTTDY-failChgIso-sidebandSigmaIetaIeta-forNPest/noData/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt_etaA.pkl'),
}

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

class npWeight:
  def __init__(self, year, sigma):
    self.sigma = sigma
    try:
      # for data driven estimate

      histA, histB, histC, histD = (sumHists(file, 'photon_pt_etaA') for file in sourceHists[year])

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
      # estimated 15% systematic uncertainty
      return sf*(1.+self.sigma*0.15)
    else: return 1.

if __name__ == '__main__':
  ROOT.gROOT.SetBatch(True)
  ROOT.gStyle.SetPadRightMargin(0.12)
  ROOT.TH2.SetDefaultSumw2()
  ROOT.gStyle.SetOptStat('')
  # ROOT.gStyle.SetPaintTextFormat("4.4f")
  ROOT.gStyle.SetPaintTextFormat("3.2f")

  for year in ['2016', '2017', '2018']:
    tester = npWeight(year, 0.)


    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.mcEst.SetTitle('')
    tester.mcEst.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.mcEst.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.mcEst.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/sfTTBARMC' + year + '.png')
    c1.SaveAs('estMaps/sfTTBARMC' + year + '.pdf')
