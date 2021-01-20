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


sourceHists ={'2016': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl'),
              '2017': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl'),
              '2018': ( '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl',
                        '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll20-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaC.pkl'),
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

      histA, histB, histC, histD = (sumHists(file, 'photon_pt_etaC') for file in sourceHists[year])
      histC[2].Add(histC[1], -1.)
      histD[2].Add(histD[1], -1.)

      self.DC = histC[2].Clone()
      self.DD = histD[2].Clone()
      self.MCC = histC[0].Clone()
      self.MCD = histD[0].Clone()

      histC[2].Divide(histD[2])
      # genuine subtracted C/D, or data np C/D

      # need to do this to subtract genuine in sideband
      dataB = histB[2].Clone()
      histB[2].Add(histB[1], -1.)
      # genuine subtracted B, or data np in B
      histB[2].Divide(dataB)
      # fraction of np in B
      histC[2].Multiply(histB[2])
      # estimation factor C/D compensated for the fact we apply to total data, not np only
      # estimate works with any selection where nonprompt fraction is about the same. but close to 100% anywhere so ok
      self.dataEst = histC[2]
      assert self.dataEst
  
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
    tester.dataEst.SetTitle('')
    tester.dataEst.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.dataEst.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.dataEst.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/sfData' + year + '.png')
    c1.SaveAs('estMaps/sfData' + year + '.pdf')
    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.mcEst.SetTitle('')
    tester.mcEst.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.mcEst.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.mcEst.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/sfMC' + year + '.png')
    c1.SaveAs('estMaps/sfMC' + year + '.pdf')

    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.DC.SetTitle('')
    tester.DC.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.DC.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.DC.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/CData' + year + '.png')
    c1.SaveAs('estMaps/CData' + year + '.pdf')
    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.MCC.SetTitle('')
    tester.MCC.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.MCC.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.MCC.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/CMC' + year + '.png')
    c1.SaveAs('estMaps/CMC' + year + '.pdf')

    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.DD.SetTitle('')
    tester.DD.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.DD.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.DD.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/DData' + year + '.png')
    c1.SaveAs('estMaps/DData' + year + '.pdf')
    c1 = ROOT.TCanvas('c', 'c', 900, 800)
    tester.MCD.SetTitle('')
    tester.MCD.GetYaxis().SetTitle('|#eta(#gamma)|')
    tester.MCD.GetXaxis().SetTitle('p_{T}(#gamma)')
    tester.MCD.Draw("COLZ TEXT E")
    c1.SaveAs('estMaps/DMC' + year + '.png')
    c1.SaveAs('estMaps/DMC' + year + '.pdf')