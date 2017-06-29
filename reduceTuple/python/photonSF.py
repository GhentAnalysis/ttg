#
# Photon SF class
#

import ROOT, os
from ttg.tools.helpers import getObjFromFile
from ttg.tools.u_float import u_float
from math import sqrt

dataDir = "$CMSSW_BASE/src/ttg/reduceTuple/data/photonSFData"
keys    = [("photonSF_CB_tight.root", "EGamma_SF2D")]


class photonSF:
  def __init__(self):
    self.pho  = [getObjFromFile(os.path.expandvars(os.path.join(self.dataDir, file)), key) for (file, key) in keys]
    for effMap in self.pho: assert effMap

  def getPartialSF(self, effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    return u_float(sf, err)

  def mult(self, list):
    res = list[0]
    for i in list[1:]: res = res*i
    return res

  def getSF(self, tree, index, sigma=0):
    pt  = tree._phPt[index]
    eta = abs(tree._phEta[index])

    if pt >= 499: pt = 499 # last bin is valid to infinity
    sf = self.mult([self.getPartialSF(effMap, pt, eta) for effMap in self.pho])

    return (1+sf.sigma*sigma)*sf.val
