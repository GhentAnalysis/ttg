from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton SF class
#

import ROOT, os
from ttg.tools.u_float import u_float
from ttg.tools.helpers import getObjFromFile
from math import sqrt

dataDir  = "$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData"
keys_mu  = [("TnP_NUM_MediumID_DENOM_generalTracks_VAR_map_pt_eta.root", "SF"),
            ("TnP_NUM_TightIP2D_DENOM_MediumID_VAR_map_pt_eta.root",     "SF"),
            ("TnP_NUM_TightIP3D_DENOM_MediumID_VAR_map_pt_eta.root",     "SF"),
            ("ratio_NUM_RelIsoVTight_DENOM_MediumID_VAR_map_pt_eta_v2.root","pt_abseta_ratio")]
keys_ele = [("scaleFactors.root", "GsfElectronToCutBasedStopsDilepton"),
            ("scaleFactors.root", "CutBasedStopsDileptonToRelIso012")]

class leptonSF:
  def __init__(self):
    self.mu  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, file)), key) for (file, key) in keys_mu]
    self.ele = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, file)), key) for (file, key) in keys_ele]
    for effMap in self.mu + self.ele: assert effMap

  def getPartialSF(self, effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    return u_float(sf, err)

  def mult(self, list):
    res = list[0]
    for i in list[1:]: res = res*i
    return res

  def getSF(self, tree, index, sigma=0):
    flavor = tree._lFlavor[index]
    pt     = tree._lPt[index]
    eta    = abs(tree._lEta[index])

    if abs(flavor)==1:   
      if pt >= 120: pt = 119 # last bin is valid to infinity
      sf = self.mult([self.getPartialSF(effMap, pt, eta) for effMap in self.mu])
      sf.sigma = 0.03 # Recommendation for Moriond17
    elif abs(flavor)==0:
      if pt >= 200: pt = 199 # last bin is valid to infinity
      sf = self.mult([self.getPartialSF(effMap, pt, eta) for effMap in self.ele])
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)

    return (1+sf.sigma*sigma)*sf.val
