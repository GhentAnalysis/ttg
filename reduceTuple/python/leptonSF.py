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

# FIXME Muon SF for 2018 are not yet final, leave this comment in the file (no SF including syst unc available)

keys_mu_ISO = {('2016','POG')   : [("2016LegRunBCDEF_Mu_SF_ISO.root",            "NUM_TightRelIso_DEN_MediumID_eta_pt")],
               ('2016','POGGH') : [("2016LegRunGH_Mu_SF_ISO.root",               "NUM_TightRelIso_DEN_MediumID_eta_pt")],
               ('2017','POG')   : [("2017RunBCDEF_Mu_SF_ISO_syst.root",          "NUM_TightRelIso_DEN_MediumID_pt_abseta")],
               ('2018','POG')   : [("2018RunABCD_Mu_SF_ISO.root",                "NUM_TightRelIso_DEN_MediumID_pt_abseta")]}

keys_mu_ID  = {('2016','POG')   : [("2016LegRunBCDEF_Mu_SF_ID.root",             "NUM_MediumID_DEN_genTracks_eta_pt")],
               ('2016','POGGH') : [("2016LegRunGH_Mu_SF_ID.root",                "NUM_MediumID_DEN_genTracks_eta_pt")],
               ('2017','POG')   : [("2017RunBCDEF_Mu_SF_ID_syst.root",           "NUM_MediumID_DEN_genTracks_pt_abseta")],
               ('2018','POG')   : [("2018RunABCD_Mu_SF_ID.root",                 "NUM_MediumID_DEN_TrackerMuons_pt_abseta")]}

keys_ele = {('2016','POG')   : [("2016LegacyReReco_ElectronTight_Fall17V2.root", "EGamma_SF2D")],
            ('2017','POG')   : [("2017_ElectronTight.root",                      "EGamma_SF2D")],
            ('2018','POG')   : [("2018_ElectronTight.root",                      "EGamma_SF2D")],
            ('2016','elMva') : [("2016LegacyReReco_ElectronMVA90_Fall17V2.root", "EGamma_SF2D")],
            ('2017','elMva') : [("2017_ElectronMVA90.root",                      "EGamma_SF2D")],
            ('2018','elMva') : [("2018_ElectronMVA90.root",                      "EGamma_SF2D")]}

# TODO:
#   use syntax of [(filename, key), (filename, key),...] or simplify if we do not use it
class LeptonSF:
  def __init__(self, year, id = 'POG'): 
    self.mu   = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ISO[(year, id)]]
    self.mu  += [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ID[(year, id)]]
    self.ele  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_ele[(year, id)]]
    if year == '2016':
      self.muGH  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ISO[(year, id + 'GH')]]
      self.muGH += [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ID[(year, id + 'GH')]]
      for effMap in self.muGH:
        assert effMap
        effMap.ptY = (year == '2016')
      

    for effMap in self.mu:  effMap.ptY = (year == '2016')
    for effMap in self.ele: effMap.ptY = True

    for effMap in self.mu + self.ele: assert effMap

  @staticmethod
  def getPartialSF(effMap, x, y):
    if effMap.ptY: x, y = y, x
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(x), effMap.GetYaxis().FindBin(y))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(x), effMap.GetYaxis().FindBin(y))
    return UncFloat(sf, err)

  def getSF(self, tree, index, sigma=0):
    flavor = tree._lFlavor[index]
    pt     = tree._lPt[index] if flavor == 1 else tree._lPtCorr[index]
    eta    = abs(tree._lEta[index])

    if abs(flavor) == 1:
      if pt >= 120: pt = 119 # last bin is valid to infinity
      sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.mu)
      if hasattr(self, 'muGH'): # for 2016 self.muGH is defined and needs to be taken into account
        sf = (0.549792*sf + 0.450208*multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.muGH))
    elif abs(flavor) == 0:
      if pt >= 500: pt = 499 # last bin is valid to infinity
      sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.ele)
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)

    return (1+sqrt(sf.sigma**2+(0.01*sf.val)**2)*sigma)*sf.val                # 1% additional uncertainty to account for phase space differences between Z and ttbar (uncorrelated with TnP sys)
