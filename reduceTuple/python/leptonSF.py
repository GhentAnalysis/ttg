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
keys_mu  = {'16':[("scaleFactorsMuons_16.root",     "MuonToTTGamma")],
            '17':[("scaleFactorsMuons_17.root",     "MuonToTTGamma")],
            '18':[("scaleFactorsMuons_18.root",     "MuonToTTGamma")]}    # Includes both id and iso
keys_ele = {'16':[("scaleFactorsElectrons_16.root", "GsfElectronToTTG")],
            '17':[("scaleFactorsElectrons_17.root", "GsfElectronToTTG")],
            '18':[("scaleFactorsElectrons_18.root", "GsfElectronToTTG")]} # Includes everything, also emulation and isolation cuts

class LeptonSF:
  def __init__(self, year):
    self.mu  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu[year]]
    self.ele = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_ele[year]]
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
