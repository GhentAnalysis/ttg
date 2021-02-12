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

# egammaEffi.txt_EGM2D_2016.root
# egammaEffi.txt_EGM2D_2017.root
# egammaEffi.txt_EGM2D_2018.root
# muonTOPLeptonMVAVLoose2016.root
# muonTOPLeptonMVAVLoose2017.root
# muonTOPLeptonMVAVLoose2018.root

class LeptonSF_MVA:
  def __init__(self, year): 
    self.elSF     = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'EGamma_SF2D')
    self.elSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'sys')
    self.elStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'stat')
    self.muSF     = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLoose' + year + '.root')), 'SF')
    self.muSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLoose' + year + '.root')), 'SFTotSys')
    self.muStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLoose' + year + '.root')), 'SFTotStat')
    assert self.elSF
    assert self.elSyst
    assert self.elStat
    assert self.muSF
    assert self.muSyst
    assert self.muStat

# NOTE syst component is correlated between years and flavours, stat component is uncorrelated

  def getSF(self, tree, index, pt, sigmaSyst=0, elSigmaStat=0, muSigmaStat=0):
    flavor = tree._lFlavor[index]
    eta    = tree._lEta[index] if flavor == 1 else tree._lEtaSC[index]

    if abs(flavor) == 1:
      if pt >= 120.: pt = 119. # last bin is valid to infinity
      elif pt <= 5.: pt = 6.
      eta = abs(eta)
      sf      = self.muSF.GetBinContent(  self.muSF.GetXaxis().FindBin(eta),   self.muSF.GetYaxis().FindBin(pt))
      errSyst = self.muSyst.GetBinContent(self.muSyst.GetXaxis().FindBin(eta), self.muSyst.GetYaxis().FindBin(pt))
      errStat = self.muStat.GetBinContent(self.muStat.GetXaxis().FindBin(eta), self.muStat.GetYaxis().FindBin(pt))
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (1. + errSyst*sigmaSyst + errStat*muSigmaStat)*sf
    elif abs(flavor) == 0:
      if pt >= 200.: pt = 199. # last bin is valid to infinity
      elif pt <= 10.: pt = 11.
      sf      = self.elSF.GetBinContent(  self.elSF.GetXaxis().FindBin(eta),   self.elSF.GetYaxis().FindBin(pt))
      errSyst = self.elSyst.GetBinContent(self.elSyst.GetXaxis().FindBin(eta), self.elSyst.GetYaxis().FindBin(pt))
      errStat = self.elStat.GetBinContent(self.elStat.GetXaxis().FindBin(eta), self.elStat.GetYaxis().FindBin(pt))
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (1. + errSyst*sigmaSyst + errStat*elSigmaStat)*sf
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)
