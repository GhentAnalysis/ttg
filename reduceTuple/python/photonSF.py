#
# Photon SF class
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat

dataDir = "$CMSSW_BASE/src/ttg/reduceTuple/data/photonSFData"
keys    = {'16':[("photonSF_CB_tight.root", "EGamma_SF2D")],
           '17':[("photonSF_CB_tight.root", "EGamma_SF2D")],
           '18':[("photonSF_CB_tight.root", "EGamma_SF2D")]}


class PhotonSF:
  def __init__(self, year):
    self.pho  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys[year]]
    for effMap in self.pho: assert effMap

  @staticmethod
  def getPartialSF(effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    return UncFloat(sf, err)

  def getSF(self, tree, index, sigma=0):
    pt  = tree._phPt[index]
    eta = abs(tree._phEta[index])

    if pt >= 499: pt = 499 # last bin is valid to infinity
    sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.pho )

    return (1+sf.sigma*sigma)*sf.val
