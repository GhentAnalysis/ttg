from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton SF class for lepton MVA
#

import os
from ttg.tools.uncFloat import UncFloat
from ttg.tools.helpers  import getObjFromFile, multiply
from math import sqrt

dataDir  = "$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData"

class LeptonSF_MVA:
  def __init__(self, year): 
    self.muSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'topmva_mu_VLoose_' + year + '.root')), 'NUM_LeptonMvaVLoose_DEN_genTracks_abseta_pt_syst')
    self.muStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'topmva_mu_VLoose_' + year + '.root')), 'NUM_LeptonMvaVLoose_DEN_genTracks_abseta_pt_stat')
    self.elSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'topmva_eg_VLoose_' + year + '.root')), 'EGamma_SF2D')
    # self.elStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'topmva_eg_VLoose_' + year + '.root')), 'EGamma_SF2D')
    assert self.muSyst
    assert self.muStat
    assert self.elSyst
    # assert self.elStat

# NOTE syst component is correlated between years and flavours, stat component is uncorrelated

  def getSF(self, tree, index, pt, sigmaSyst=0, elSigmaStat=0, muSigmaStat=0):
    flavor = tree._lFlavor[index]
    eta    = tree._lEta[index] if flavor == 1 else tree._lEtaSC[index]

    if abs(flavor) == 1:
      if pt >= 120.: pt = 119. # last bin is valid to infinity
      elif pt <= 10.: pt = 11.
      eta = abs(eta)
      sf  = self.muSyst.GetBinContent(self.muSyst.GetXaxis().FindBin(eta), self.muSyst.GetYaxis().FindBin(pt))
      errSyst = self.muSyst.GetBinError(self.muSyst.GetXaxis().FindBin(eta), self.muSyst.GetYaxis().FindBin(pt))
      errStat = self.muStat.GetBinError(self.muStat.GetXaxis().FindBin(eta), self.muStat.GetYaxis().FindBin(pt))
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (1. + errSyst*sigmaSyst + errStat*muSigmaStat)*sf
    elif abs(flavor) == 0:
      if pt >= 500.: pt = 499. # last bin is valid to infinity
      elif pt <= 10.: pt = 11.
      sf  = self.elSyst.GetBinContent(self.elSyst.GetXaxis().FindBin(eta), self.elSyst.GetYaxis().FindBin(pt))
      errSyst = self.elSyst.GetBinError(self.elSyst.GetXaxis().FindBin(eta), self.elSyst.GetYaxis().FindBin(pt))
      # errStat = self.elStat.GetBinError(self.elStat.GetXaxis().FindBin(eta), self.elStat.GetYaxis().FindBin(pt))
      errStat = 0.
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (1. + errSyst*sigmaSyst + errStat*elSigmaStat)*sf
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)


  # def testGetSF(self, flav, pt, eta, sigmaSyst=0, elSigmaStat=0, muSigmaStat=0):
  #   flavor = flav
    
  #   if abs(flavor) == 1:
  #     if pt >= 120.: pt = 119. # last bin is valid to infinity
  #     elif pt <= 10.: pt = 11.
  #     eta = abs(eta)
  #     sf  = self.muSyst.GetBinContent(self.muSyst.GetXaxis().FindBin(eta), self.muSyst.GetYaxis().FindBin(pt))
  #     log.info(sf)
  #     errSyst = self.muSyst.GetBinError(self.muSyst.GetXaxis().FindBin(eta), self.muSyst.GetYaxis().FindBin(pt))
  #     log.info(errSyst)
  #     errStat = self.muStat.GetBinError(self.muStat.GetXaxis().FindBin(eta), self.muStat.GetYaxis().FindBin(pt))
  #     log.info(errStat)
  #     # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
  #     return (1. + errSyst*sigmaSyst + errStat*muSigmaStat)*sf
  #   elif abs(flavor) == 0:
  #     if pt >= 500.: pt = 499. # last bin is valid to infinity
  #     elif pt <= 10.: pt = 11.
  #     sf  = self.elSyst.GetBinContent(self.elSyst.GetXaxis().FindBin(eta), self.elSyst.GetYaxis().FindBin(pt))
  #     log.info(sf)
  #     errSyst = self.elSyst.GetBinError(self.elSyst.GetXaxis().FindBin(eta), self.elSyst.GetYaxis().FindBin(pt))
  #     log.info(errSyst)
  #     # errStat = self.elStat.GetBinError(self.elStat.GetXaxis().FindBin(eta), self.elStat.GetYaxis().FindBin(pt))
  #     errStat = 0.
  #     # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
  #     return (1. + errSyst*sigmaSyst + errStat*elSigmaStat)*sf
  #   else: 
  #     raise Exception("Lepton SF for flavour %i not known"%flavor)


