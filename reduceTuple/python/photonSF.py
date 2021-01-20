#
# Photon SF class
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat

dataDir = "$CMSSW_BASE/src/ttg/reduceTuple/data/photonSFData"
keys    = {('2016','CB') : [("g2016_egammaPlots_MWP_PhoSFs_2016_LegacyReReco_New_private.root", "EGamma_SF2D")],
           ('2017','CB') : [("g2017_PhotonsMedium_mod_private_BostonAdded.root"               , "EGamma_SF2D")],
           ('2018','CB') : [("g2018_PhotonsMedium_mod_private_BostonAdded.root"               , "EGamma_SF2D")],
           ('2016','MVA') : [("80X_2016_MVAwp90_photons.root", "EGamma_SF2D")]}


class PhotonSF:
  def __init__(self, year, phoID):
    self.pho  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys[(year, phoID)]]
    for effMap in self.pho: assert effMap

  @staticmethod
  def getPartialSF(effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(eta), effMap.GetYaxis().FindBin(pt))
    return UncFloat(sf, err)

  def getSF(self, tree, index, pt, sigma=0):
    eta = abs(tree._phEta[index])
    if pt >= 499: pt = 499 # last bin is valid to infinity
    sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.pho )

    return (1+sf.sigma*sigma)*sf.val
