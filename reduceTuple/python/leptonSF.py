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

# FIXME electrons: for sure we will not use the susy mva, the POG cut-based or mva's would be a good start, 
# though Didar really wants to have the leptonMva used once it is developed (even though the dilepton analysis has simply no fakes, so it is questionable if it brings some gain)
# FIXME muons: ISO and ID SF are speparately given, and for 16 runs G and H are also separate

# FIXME Muon SF for 2018 are not yet final, leave this comment in the file 
keys_mu  = {('16','POG'):[("scaleFactorsMuons_16.root",     "MuonToTTGamma")],
            ('17','POG'):[("scaleFactorsMuons_17.root",     "MuonToTTGamma")],
            ('18','POG'):[("scaleFactorsMuons_18.root",     "MuonToTTGamma")],
            ('16','elMva'):[("scaleFactorsMuons_16.root",     "MuonToTTGamma")],
            ('17','elMva'):[("scaleFactorsMuons_17.root",     "MuonToTTGamma")],
            ('18','elMva'):[("scaleFactorsMuons_18.root",     "MuonToTTGamma")]}

keys_ele = {('16','POG'):[("scaleFactorsElectrons_16.root", "GsfElectronToTTG")],
            ('17','POG'):[("scaleFactorsElectrons_17.root", "GsfElectronToTTG")],
            ('18','POG'):[("scaleFactorsElectrons_18.root", "GsfElectronToTTG")],
            ('16','elMva'):[("scaleFactorsMuons_16.root",     "MuonToTTGamma")],
            ('17','elMva'):[("scaleFactorsMuons_17.root",     "MuonToTTGamma")],
            ('18','elMva'):[("scaleFactorsMuons_18.root",     "MuonToTTGamma")]}

class LeptonSF:
  def __init__(self, year, elID = 'POG'): 
    self.mu  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu[(year, elID)]]
    self.ele = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_ele[(year, elID)]]
    for effMap in self.mu + self.ele: assert effMap

  @staticmethod
  def getPartialSF(effMap, pt, eta):
    sf  = effMap.GetBinContent(effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    err = effMap.GetBinError(  effMap.GetXaxis().FindBin(pt), effMap.GetYaxis().FindBin(abs(eta)))
    return UncFloat(sf, err)

  def getSF(self, tree, index, sigma=0):
    flavor = tree._lFlavor[index]
    pt     = tree._lPt[index] if flavor == 1 else tree._lPtCorr[index]
    eta    = abs(tree._lEta[index])

    if abs(flavor)==1:   
      if pt >= 150: pt = 149 # last bin is valid to infinity
      sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.mu)
    elif abs(flavor)==0:
      if pt >= 200: pt = 199 # last bin is valid to infinity
      sf = multiply( self.getPartialSF(effMap, pt, eta) for effMap in self.ele)
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)

    return (1+sqrt(sf.sigma**2+(0.01*sf.val)**2)*sigma)*sf.val                # 1% additional uncertainty to account for phase space differences between Z and ttbar (uncorrelated with TnP sys)
