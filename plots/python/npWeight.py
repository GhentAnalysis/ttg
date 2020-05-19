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

sourceHists ={'2016': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
              '2017': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
              '2018': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
}

closurePlots = {'2016': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-compRewContribMC-forNPclosure/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl',
                '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCBfull-compRewContribMC-forNPclosure/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl',
                '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-compRewContribMC-forNPclosure/noData/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl'
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

def getErrMap(picklePath):
  hists = pickle.load(open(picklePath))['signalRegions']
  est = None
  sim = None
  for name, hist in hists.iteritems():
    if 'estimate' in name:
      if not est: est = hist
      else: est.Add(hist)
    else:
      if not sim: sim = hist
      else: sim.Add(hist)

  for i in range(1, sim.GetNbinsX()+1):
    if est.GetBinContent(i) < 0.00000001 or sim.GetBinContent(i) < 0.00000001: est.SetBinContent(i, 0.)
    else:
      relDev = (est.GetBinContent(i)-sim.GetBinContent(i))/est.GetBinContent(i)
      est.SetBinContent(i, relDev)
  return est

class npWeight:
  def __init__(self, year, sigma):
    self.sigma = sigma
    try:
      # for data driven estimate
      histA, histB, histC, histD = (sumHists(file, 'photon_pt_etaB') for file in sourceHists[year])
      histC[2].Add(histC[1], -1.)
      histD[2].Add(histD[1], -1.)
      histC[2].Divide(histD[2])
      # need to do this to subtract genuine in sideband
      dataB = histB[2].Clone()
      histB[2].Add(histB[1], -1.)
      histB[2].Divide(dataB)
      histC[2].Multiply(histB[2])
      self.dataEst = histC[2]
      assert self.dataEst
  
      # for MC based estimate / closure test
      histC[0].Divide(histD[0])
      self.mcEst = histC[0]
      assert self.mcEst

      # estimate of systematic uncertainty
      self.errHist = getErrMap(closurePlots[year])
    except:
      self.errHist = False
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
      if self.errHist:
        err = self.errHist.GetBinContent(createSignalRegions(tree)+1)
      else:
        err = 0.
      return sf*(1.+self.sigma*err)
    else: return 1.

if __name__ == '__main__':
  tester = npWeight('2016', 0.)
  tester.dataEst.Draw("COLZ TEXT")