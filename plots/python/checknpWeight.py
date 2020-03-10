#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle

import time

fileA = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passSigmaIetaIeta-passChgIso/all/llg-mll40-njet1p-photonPt20/photon_pt_eta.pkl'
fileB = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passSigmaIetaIeta-failChgIso/all/llg-mll40-njet1p-photonPt20/photon_pt_eta.pkl'
fileC = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-sidebandSigmaIetaIeta-passChgIso/all/llg-mll40-njet1p-photonPt20/photon_pt_eta.pkl'
fileD = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-sidebandSigmaIetaIeta-failChgIso/all/llg-mll40-njet1p-photonPt20/photon_pt_eta.pkl'


  
#   A/B             ch Iso  BD         ch Iso     BD
#   C/D                     AC                    AC
#   A= B*(C/D)             sigma               onZ-offZ
# def __init__(self, year, selection):

# TODO !!!!!!!!!!!!!!!!!!!!
# how to deal with empty bins?
# make year specific
# split per channel? no ars.channel! us values like t.isMuMu
# make selection specific?  NO

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
      A = sumHists(fileA, 'photon_pt_eta')
      B = sumHists(fileB, 'photon_pt_eta')
      C = sumHists(fileC, 'photon_pt_eta')
      D = sumHists(fileD, 'photon_pt_eta')
      # TODO check if one step doesn't modify a histogram we use later

      # B*(C/D) for data, subtracting genuine in each
      # self.est = B[0]
      # return
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
      # set A data prediction
      # c2 = TCanvas('c', 'c', 800, 800)
      # AestData.Draw('COLZ TEXT')
      # c2.SaveAs('weights.png')
      # c3 = TCanvas('c', 'c', 800, 800)
      # A[0].Draw('COLZ TEXT')
      # c3.SaveAs('azero.png')
      for i in range(1, B[0].GetNbinsX()+1):
        for j in range(1, B[0].GetNbinsX()+1):
          AestData.SetBinError(i, j, abs(B[0].GetBinContent(i, j)))
      self.est = AestData
      assert self.est
    # for ABCD closure checking, purely in MC
    else:
      A = sumHists(fileA, 'photon_pt_eta')
      B = sumHists(fileB, 'photon_pt_eta')
      C = sumHists(fileC, 'photon_pt_eta')
      D = sumHists(fileD, 'photon_pt_eta')
      # A est MC = B*C/D
      C[0].Divide(D[0])
      B[0].Multiply(C[0])
      # deviation MC prediction A from MC A is estimate of syst error
      est = B[0].Clone("est")
      est.Divide(A[0])
      B[0].Add(A[0], -1.)
      B[0].Divide(A[0])
      for i in range(1, B[0].GetNbinsX()+1):
        for j in range(1, B[0].GetNbinsX()+1):
          est.SetBinError(i, j, abs(B[0].GetBinContent(i, j)))
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
  tester = npWeight('2016', True, -1.)
  c1 = TCanvas('c', 'c', 800, 800)
  # tester.est.Draw('COLZ TEXT')
  # tester.est.Draw('TEXT SAME')
  # c1.SaveAs('npSFh.png')
  print tester.getTestWeight(25., 0.4)
  # print tester.getTestWeight(25., 0.4, -1.)
  # print tester.getTestWeight(25., 0.4, 1.)

















# baseFolder = 'CMSSW_BASE/src/ttg/plots/data/nonPrompt/'

# fileA = 'photon_pt_eta_A.pkl'
# fileB = 'photon_pt_eta_B.pkl'
# fileC = 'photon_pt_eta_C.pkl'
# fileD = 'photon_pt_eta_D.pkl'

  # TODO  NO year thingy implemented yet, not selection speficific either
  
#   A/B             ch Iso  BD         ch Iso     BD
#   C/D                     AC                    AC
#   A= B*(C/D)             sigma               onZ-offZ
# def __init__(self, year, selection):

# TODO how to deal with empty bins?

# class npWeight:
#   def __init__(self, year, ):
#     # A = pickle.load(open(os.path.expandvars(baseFolder + fileA )))['photon_pt_eta']['TT_Dilt#bar{t}']
#     # B = pickle.load(open(os.path.expandvars(baseFolder + fileB )))['photon_pt_eta']['TT_Dilt#bar{t}']
#     # C = pickle.load(open(os.path.expandvars(baseFolder + fileC )))['photon_pt_eta']['TT_Dilt#bar{t}']
#     # D = pickle.load(open(os.path.expandvars(baseFolder + fileD )))['photon_pt_eta']['TT_Dilt#bar{t}']
#     A = pickle.load(open(os.path.expandvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passSigmaIetaIeta-passChgIso-onlyTTDILNPM/noData/llg-njet1p-photonPt20/photon_pt_eta.pkl')))['photon_pt_eta']['TT_Dilt#bar{t}']
#     B = pickle.load(open(os.path.expandvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passSigmaIetaIeta-failChgIso-onlyTTDILNPM/noData/llg-njet1p-photonPt20/photon_pt_eta.pkl')))['photon_pt_eta']['TT_Dilt#bar{t}']
#     C = pickle.load(open(os.path.expandvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-sidebandSigmaIetaIeta-passChgIso-onlyTTDILNPM/noData/llg-njet1p-photonPt20/photon_pt_eta.pkl')))['photon_pt_eta']['TT_Dilt#bar{t}']
#     D = pickle.load(open(os.path.expandvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-sidebandSigmaIetaIeta-failChgIso-onlyTTDILNPM/noData/llg-njet1p-photonPt20/photon_pt_eta.pkl')))['photon_pt_eta']['TT_Dilt#bar{t}']
#     C.Divide(D)
#     B.Multiply(C)
#     B.Draw()
#     self.est = C
#     assert self.est

#   def getWeight(self, tree, index, sigma=0):
#     pt  = tree._phPt[index]
#     eta = abs(tree._phEta[index])
#     if pt >= 120: pt = 119 # last bin is valid to infinity
#     sf  = self.est.GetBinContent(self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
#     err = self.est.GetBinError(  self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
#     return (1+err*sigma)*sf


#   def getTestWeight(self, pt, eta, sigma=0):
#     if pt >= 120: pt = 119 # last bin is valid to infinity
#     sf  = self.est.GetBinContent(self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
#     err = self.est.GetBinError(  self.est.GetXaxis().FindBin(pt), self.est.GetYaxis().FindBin(eta))
#     return (1+err*sigma)*sf


# if __name__ == '__main__':
#   from ROOT import TCanvas
#   tester = npWeight('2016')
#   c1 = TCanvas('c', 'c', 800, 800)
#   tester.est.Draw('COLZ TEXT')
#   # tester.est.Draw('TEXT SAME')
#   c1.SaveAs('npSF.png')
#   print tester.getTestWeight(25., 0.4)
#   print tester.getTestWeight(25., 0.4, -1.)
#   print tester.getTestWeight(25., 0.4, 1.)
