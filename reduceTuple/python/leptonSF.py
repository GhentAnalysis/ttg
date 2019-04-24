from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton SF class
#

import os
from ttg.tools.uncFloat import UncFloat
from ttg.tools.helpers  import getObjFromFile, multiply
from math import sqrt

dataDir  = "$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData"

# currently using electron POG tight or electronMVA90, muon pog medium, 
# current muon SF correspond to a tight isolation cut 

# mu 16 pt y                17, 18 pt x        ele pt y 16, 17, 18 
# lumi: B-F: 19.717640795 GH: 16.146177653  total: 35.863818448 -> fractions  0.549792   0.450208

# FIXME Muon SF for 2018 are not yet final, leave this comment in the file 
keys_mu_ISO  = {('16','POG'):[("2016LegRunBCDEF_Mu_SF_ISO.root",      "NUM_TightRelIso_DEN_MediumID_eta_pt")],
                ('16','POGGH'):[("2016LegRunGH_Mu_SF_ISO.root",       "NUM_TightRelIso_DEN_MediumID_eta_pt")],
                ('17','POG'):[("2017RunBCDEF_Mu_SF_ISO.root",         "NUM_TightRelIso_DEN_MediumID_pt_abseta")],
                ('18','POG'):[("2018RunABCD_Mu_SF_ISO.root",          "NUM_TightRelIso_DEN_MediumID_pt_abseta")]}

keys_mu_ID  = {('16','POG'):[("2016LegRunBCDEF_Mu_SF_ID.root",                  "NUM_MediumID_DEN_genTracks_eta_pt")],
               ('16','POGGH'):[("2016LegRunGH_Mu_SF_ID.root",                   "NUM_MediumID_DEN_genTracks_eta_pt")],
               ('17','POG'):[("2017RunBCDEF_Mu_SF_ID.root",                     "NUM_MediumID_DEN_genTracks_pt_abseta")],
               ('18','POG'):[("2018RunABCD_Mu_SF_ID.root",                      "NUM_MediumID_DEN_TrackerMuons_pt_abseta")]}


keys_ele = {('16','POG'):[("2016LegacyReReco_ElectronTight_Fall17V2.root",      "EGamma_SF2D")],
            ('17','POG'):[("2017_ElectronTight.root",                           "EGamma_SF2D")],
            ('18','POG'):[("2018_ElectronTight.root",                           "EGamma_SF2D")],
            ('16','elMva'):[("2016LegacyReReco_ElectronMVA90_Fall17V2.root",    "EGamma_SF2D")],
            ('17','elMva'):[("2017_ElectronMVA90.root",                         "EGamma_SF2D")],
            ('18','elMva'):[("2018_ElectronMVA90.root",                         "EGamma_SF2D")]}

class LeptonSF:
  def __init__(self, year, elID = 'POG'): 
    self.year = year
    self.mu_ISO  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ISO[(year, elID)]]
    self.mu_ID  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ID[(year, elID)]]
    if year = '16':
      self.mu_ISOGH  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ISOGH[(year, elID)]]
      self.mu_IDGH  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_IDGH[(year, elID)]]
    self.ele = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_ele[(year, elID)]]

    for effMap in self.mu_ID + self.mu_ISO + self.ele: assert effMap

  @staticmethod
  def getPartialSF(effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetYaxis().FindBin(abs(eta)), effMap.GetXaxis().FindBin(pt))
    err = effMap.GetBinError(  effMap.GetYaxis().FindBin(abs(eta)), effMap.GetXaxis().FindBin(pt))
    return UncFloat(sf, err)
  @staticmethod
  def getPartialSFInv(effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    return UncFloat(sf, err)

  def getSF(self, tree, index, sigma=0):
    flavor = tree._lFlavor[index]
    pt     = tree._lPt[index] if flavor == 1 else tree._lPtCorr[index]
    eta    = abs(tree._lEta[index])

    if abs(flavor) == 1 and self.year == '16':   
      if pt >= 120: pt = 119 # last bin is valid to infinity
      sf = 0.549792 * multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.mu_ISO + self.mu_ID) + \
           0.450208 * multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.mu_ISOGH + self.mu_IDGH)
    elif abs(flavor) == 1:
      if pt >= 120: pt = 119 # last bin is valid to infinity
      sf = multiply( self.getPartialSFInv(effMap, pt, eta) for effMap in self.mu_ISO + self.mu_ID)
    elif abs(flavor) == 0:
      if pt >= 500: pt = 499 # last bin is valid to infinity
      sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.ele)
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)

    return (1+sqrt(sf.sigma**2+(0.01*sf.val)**2)*sigma)*sf.val                # 1% additional uncertainty to account for phase space differences between Z and ttbar (uncorrelated with TnP sys)
