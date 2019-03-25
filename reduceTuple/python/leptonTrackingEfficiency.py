from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton tracking SF class
#
import os, math
from ttg.tools.helpers import getObjFromFile

baseDir  = '$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData/'
e_file   = {'16': baseDir + 'egammaEffi.txt_EGM2D.root',
            '17': baseDir + 'egammaEffi.txt_EGM2D.root',
            '18': baseDir + 'egammaEffi.txt_EGM2D.root'}
e_key    = {'16': "EGamma_SF2D",
            '17': "EGamma_SF2D",
            '18': "EGamma_SF2D"}
m_file   = {'16': baseDir + 'Tracking_EfficienciesAndSF_BCDEFGH.root',
            '17': baseDir + 'Tracking_EfficienciesAndSF_BCDEFGH.root',
            '18': baseDir + 'Tracking_EfficienciesAndSF_BCDEFGH.root'}
m_key    = {'16': "ratio_eff_eta3_dr030e030_corr",
            '17': "ratio_eff_eta3_dr030e030_corr",
            '18': "ratio_eff_eta3_dr030e030_corr"}

class LeptonTrackingEfficiency:
  def __init__(self, year):
    self.e_sf = getObjFromFile(os.path.expandvars(e_file[year]), e_key[year])
    self.m_sf = getObjFromFile(os.path.expandvars(m_file[year]), m_key[year])
    for sf in [self.e_sf, self.m_sf]: assert sf

    self.e_ptMax  = self.e_sf.GetYaxis().GetXmax()
    self.e_ptMin  = self.e_sf.GetYaxis().GetXmin()

    self.e_etaMax = self.e_sf.GetXaxis().GetXmax()
    self.e_etaMin = self.e_sf.GetXaxis().GetXmin()

    self.m_etaMax = self.m_sf.GetXaxis().GetXmax()
    self.m_etaMin = self.m_sf.GetXaxis().GetXmin()

  def getSF(self, tree, index, sigma=0):
    flavor = tree._lFlavor[index]
    pt     = tree._lPt[index] if flavor == 1 else tree._lPtCorr[index]
    eta    = abs(tree._lEtaSC[index] if flavor == 0 else tree._lEta[index])

    if abs(flavor) == 0:
      if not eta <= self.e_etaMax: 
        log.warning("Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax)
        eta = self.e_etaMax
      if not eta >= self.e_etaMin:
        log.warning("Supercluster eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.e_etaMin, self.e_etaMax)
        eta = self.e_etaMin

      if pt > self.e_ptMax:    pt = self.e_ptMax - 1 
      elif pt <= self.e_ptMin: pt = self.e_ptMin + 1

      val    = self.e_sf.GetBinContent(self.e_sf.FindBin(eta, pt))
      valErr = self.e_sf.GetBinError(self.e_sf.FindBin(eta, pt))
      
      if pt > 80: addUnc = 0.01*val # Additional 1% on ele with pt > 80
      else:       addUnc = 0.
      valErr = math.sqrt(valErr**2 + addUnc**2)

    elif abs(flavor) == 1:
      if not eta <= self.m_etaMax:
        log.warning("Muon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.m_etaMin, self.m_etaMax)
        eta = self.m_etaMax
      if not eta >= self.m_etaMin:
        log.warning("Muon eta out of bounds: %3.2f (need %3.2f <= eta <=% 3.2f)", eta, self.m_etaMin, self.m_etaMax)
        eta = self.m_etaMin

      val    = self.m_sf.Eval( eta )
      valErr = 0. # Systematic uncertainty not there yet

    else:
      raise ValueError("Lepton flavor %i neither electron or muon" % flavor)


    return (1+valErr*sigma)*val
