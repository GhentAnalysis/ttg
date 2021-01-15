#
# Photon PixelSeedVeto SF class
# both electronVeto and pixelSeedVeto are applied, pix SF is tighter so appying that SF
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat

dataDir = "$CMSSW_BASE/src/ttg/reduceTuple/data/pixelVetoSF/"
keys    = {'2016' : ("ScalingFactors_80X_Summer16.root", "Scaling_Factors_HasPix_R9 Inclusive"),
           '2017' : ("PixelSeed_ScaleFactors_2017.root", "Medium_ID"),
           '2018' : ("g2018_HasPix_2018_private.root", "scalefactor")}
class pixelVetoSF:
  def __init__(self, year):
    self.year = year
    self.vetoHist  = getObjFromFile(os.path.expandvars(os.path.join(dataDir, keys[year][0])), keys[year][1])
    if year == '2018':
      self.errs = getObjFromFile(os.path.expandvars(os.path.join(dataDir, keys[year][0])), "uncertainty")
    assert self.vetoHist

  def getSF(self, tree, index, pt, sigma=0):
    eta = abs(tree._phEta[index])
    if pt >= 199: pt = 199
    if pt <= 11: pt = 11
    if self.year == '2016':
      sf  = self.vetoHist.GetBinContent(self.vetoHist.GetXaxis().FindBin(eta), self.vetoHist.GetYaxis().FindBin(pt))
      err = self.vetoHist.GetBinError(  self.vetoHist.GetXaxis().FindBin(eta), self.vetoHist.GetYaxis().FindBin(pt))
    elif self.year == '2017':
      if eta < 1.479 :
        sf  = self.vetoHist.GetBinContent(1)
        err = self.vetoHist.GetBinError(1)
      else:
        sf  = self.vetoHist.GetBinContent(4)
        err = self.vetoHist.GetBinError(4)
    elif self.year == '2018':
      sf  = self.vetoHist.GetBinContent(self.vetoHist.GetXaxis().FindBin(pt), self.vetoHist.GetYaxis().FindBin(eta))
      err  = self.errs.GetBinContent(self.vetoHist.GetXaxis().FindBin(pt), self.vetoHist.GetYaxis().FindBin(eta))
    else: 
      return 1
    sf = UncFloat(sf, err)
    return (1+sf.sigma*sigma)*sf.val

#   def testGetSF(self, pt, eta, sigma=0):
#     if pt >= 199: pt = 199
#     if pt <= 11: pt = 11
#     if self.year == '2016':
#       sf  = self.vetoHist.GetBinContent(self.vetoHist.GetXaxis().FindBin(eta), self.vetoHist.GetYaxis().FindBin(pt))
#       err = self.vetoHist.GetBinError(  self.vetoHist.GetXaxis().FindBin(eta), self.vetoHist.GetYaxis().FindBin(pt))
#     elif self.year == '2017':
#       if eta < 1.479 :    # find actual value
#         sf  = self.vetoHist.GetBinContent(1)
#         err = self.vetoHist.GetBinError(1)
#       else:
#         sf  = self.vetoHist.GetBinContent(4)
#         err = self.vetoHist.GetBinError(4)
#     elif self.year == '2018':
#       sf  = self.vetoHist.GetBinContent(self.vetoHist.GetXaxis().FindBin(pt), self.vetoHist.GetYaxis().FindBin(eta))
#       err  = self.errs.GetBinContent(self.vetoHist.GetXaxis().FindBin(pt), self.vetoHist.GetYaxis().FindBin(eta))
#     else: 
#       log.warning('invalid year')
#       return 1
#     sf = UncFloat(sf, err)
#     return (1+sf.sigma*sigma)*sf.val


# if __name__ == '__main__':
#     testSF = pixelVetoSF('2016')
#     print str(testSF.testGetSF(20, 1,0)) + '   ' + str(testSF.testGetSF(20, 1,1))
#     print str(testSF.testGetSF(40, 1,0)) + '   ' + str(testSF.testGetSF(40, 1,1))
#     print str(testSF.testGetSF(120,1,0)) + '   ' + str(testSF.testGetSF(120,1,1))
#     print str(testSF.testGetSF(20, 2,0)) + '   ' + str(testSF.testGetSF(20, 2,1))
#     print str(testSF.testGetSF(40, 2,0)) + '   ' + str(testSF.testGetSF(40, 2,1))
#     print str(testSF.testGetSF(120,2,0)) + '   ' + str(testSF.testGetSF(120,2,1))