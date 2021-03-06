from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton tracking SF class
# NOTE for muons tracking SF are very close to 1, the recommendation is not to apply any SF see: 
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonReferenceSelectionAndCalibrationsRun2

import os
from ttg.tools.helpers import getObjFromFile

baseDir  = '$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData/'
e_file   = {('2016','low'):   baseDir + '2016EGM2D_BtoH_low_RecoSF_Legacy2016.root',
            ('2016','high'):  baseDir + '2016EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root',
            ('2017','low'):   baseDir + '2017egammaEffi.txt_EGM2D_runBCDEF_passingRECO_lowEt.root',
            ('2017','high'):  baseDir + '2017egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root',
            ('2018','low'):   baseDir + '2018egammaEffi.txt_EGM2D_updatedAll.root',
            ('2018','high'):  baseDir + '2018egammaEffi.txt_EGM2D_updatedAll.root'}
e_key    = "EGamma_SF2D"

class LeptonTrackingEfficiency:
  def __init__(self, year):
    self.eLow_sf  = getObjFromFile(os.path.expandvars(e_file[(year, 'low')]),  e_key)
    self.eHigh_sf = getObjFromFile(os.path.expandvars(e_file[(year, 'high')]), e_key)
    for sf in [self.eLow_sf, self.eHigh_sf]: assert sf

    self.e_ptMax  = self.eHigh_sf.GetYaxis().GetXmax()
    self.e_ptMin  = self.eLow_sf.GetYaxis().GetXmin()

    self.e_etaMax = self.eLow_sf.GetXaxis().GetXmax()
    self.e_etaMin = self.eLow_sf.GetXaxis().GetXmin()

  def getSF(self, tree, index, pt, sigma=0):
    flavor = tree._lFlavor[index]
    eta    = abs(tree._lEtaSC[index] if flavor == 0 else tree._lEta[index])

    if abs(flavor) == 0:
      if not eta <= self.e_etaMax: 
        log.warning("Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax)
        eta = self.e_etaMax
      if not eta > self.e_etaMin:
        log.warning("Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax)
        eta = self.e_etaMin + 0.0001

      if pt > self.e_ptMax:    pt = self.e_ptMax - 1 
      elif pt <= self.e_ptMin: pt = self.e_ptMin + 1
      
      if pt < 20: 
        val    = self.eLow_sf.GetBinContent(self.eLow_sf.FindBin(eta, pt))
        valErr = self.eLow_sf.GetBinError(self.eLow_sf.FindBin(eta, pt))
      else:
        val    = self.eHigh_sf.GetBinContent(self.eHigh_sf.FindBin(eta, pt))
        valErr = self.eHigh_sf.GetBinError(self.eHigh_sf.FindBin(eta, pt))
      
    elif abs(flavor) == 1:
      return 1.

    else:
      raise ValueError("Lepton flavor %i neither electron or muon" % flavor)

    return (1+valErr*sigma)*val
