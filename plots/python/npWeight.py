#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle
import time

sourceHists ={'2016': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl'),
              '2017': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl'),
              '2018': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-passSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-sidebandSigmaIetaIeta-newE/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20/photon_pt_etaB.pkl'),
}

#   A/B             ch Iso  BD         ch Iso     BD
#   C/D                     AC                    AC
#   A= B*(C/D)             sigma               onZ-offZ
# def __init__(self, year, selection):


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
  def __init__(self, year, dataDriven, sigma):
    self.sigma = sigma
    self.dataDriven = dataDriven
    # get Nevents estimate using ABCD in data, turn into weights by dividing by SR MC prediction
    # systematic uncertainty via relative uncertainty between ABCD prediction in MC vs MC in SR
    if dataDriven:
      A, B, C, D = (sumHists(file, 'photon_pt_etaB') for file in sourceHists[year])
      B[2].Add(B[1] ,-1.)
      C[2].Add(C[1] ,-1.)
      D[2].Add(D[1], -1.)
      C[2].Divide(D[2])
      B[2].Multiply(C[2])
      AestData = B[2]
      C[0].Divide(D[0])                 # A est MC = B*C/D
      B[0].Multiply(C[0])
      B[0].Add(A[0], -1.)               # relative deviation MC prediction A from MC A  (AMC -ApredMC)/AMC
      B[0].Divide(A[0])
      AestData.Divide(A[0])             # divide by A MC to get weights
      B[0].Multiply(AestData)           # error on A prediction data = rel deviation in MC * A data prediction
      for i in range(1, B[0].GetNbinsX()+1):
        for j in range(1, B[0].GetNbinsX()+1):
          AestData.SetBinError(i, j, abs(B[0].GetBinContent(i, j)))
      self.est = AestData
      assert self.est
    # for ABCD closure checking, purely in MC
    else:
      A, B, C, D = (sumHists(file, 'photon_pt_etaB') for file in sourceHists[year])
      # A est MC = B*C/D
      C[0].Divide(D[0])
      B[0].Multiply(C[0])
      # deviation MC prediction A from MC A is estimate of syst error
      est = B[0].Clone("est")
      est.Divide(A[0])
      B[0].Add(A[0], -1.)
      B[0].Divide(A[0])
      self.est = est
      assert self.est

  def getWeight(self, tree, index):
    if (tree.MCreweight or self.dataDriven) and tree.nonPrompt:
      pt  = tree.ph_pt
      eta = abs(tree._phEta[tree.ph])
      if pt >= 120: pt = 119 # last bin is valid to infinity
      sf  = self.est.GetBinContent(self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
      err = self.est.GetBinError(  self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
      return (1+err*self.sigma)*sf
    else: return 1.


  def getTestWeight(self, pt, eta):
    if pt >= 120: pt = 119 # last bin is valid to infinity
    sf  = self.est.GetBinContent(self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
    err = self.est.GetBinError(  self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
    return (1+err*self.sigma)*sf


if __name__ == '__main__':
  from ROOT import TCanvas
  tester = npWeight('2016', True, 1.)
  c1 = TCanvas('c', 'c', 800, 800)
  tester.est.Draw('COLZ TEXT')
  c1.SaveAs('sf16.png')
