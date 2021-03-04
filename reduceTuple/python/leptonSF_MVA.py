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
    self.elSF     = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'EGamma_SF2D')
    self.elSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'sys')
    self.elStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'egammaEffi.txt_EGM2D_' + year + '.root')), 'stat')
    self.muSF     = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLooseNoPS' + year + '.root')), 'SF')
    self.muSyst   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLooseNoPS' + year + '.root')), 'SFTotSys')
    self.muStat   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLooseNoPS' + year + '.root')), 'SFTotStat')

    self.muPSSys   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, 'muonTOPLeptonMVAVLooseNoPS' + year + '.root')), 'SFPSSys')
    assert self.elSF
    assert self.elSyst
    assert self.elStat
    assert self.muSF
    assert self.muSyst
    assert self.muStat
    assert self.muPSSys

  # def getSF(self, tree, index, pt, elSigmaSyst=0, muSigmaSyst=0, elSigmaStat=0, muSigmaStat=0, muSigmaPSSys=0):
  #   flavor = tree._lFlavor[index]
  #   eta    = tree._lEta[index] if flavor == 1 else tree._lEtaSC[index]

  #   if abs(flavor) == 1:
  #     if pt >= 120.: pt = 119. # last bin is valid to infinity
  #     elif pt <= 5.: pt = 6.
  #     eta = abs(eta)
  #     etaBin = self.muSF.GetXaxis().FindBin(eta)
  #     ptBin = self.muSF.GetYaxis().FindBin(pt)
  #     sf      = self.muSF.GetBinContent(    etaBin  ptBin)
  #     errSyst = self.muSyst.GetBinContent(  etaBin, ptBin)
  #     errStat = self.muStat.GetBinContent(  etaBin, ptBin)
  #     errPS   = self.muPSSys.GetBinContent( etaBin, ptBin)
  #     # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
  #     return (1. + errSyst*muSigmaSyst + errStat*muSigmaStat + errPS*muSigmaPSSys)*sf
  #   elif abs(flavor) == 0:
  #     if pt >= 200.: pt = 199. # last bin is valid to infinity
  #     elif pt <= 10.: pt = 11.
  #     etaBin = self.elSF.GetXaxis().FindBin(eta)
  #     ptBin = self.elSF.GetYaxis().FindBin(pt)
  #     sf      = self.elSF.GetBinContent(  etaBin, ptBin)
  #     errSyst = self.elSyst.GetBinContent(etaBin, ptBin)
  #     errStat = self.elStat.GetBinContent(etaBin, ptBin)
  #     # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
  #     return (1. + errSyst*elSigmaSyst + errStat*elSigmaStat)*sf
  #   else: 
  #     raise Exception("Lepton SF for flavour %i not known"%flavor)

  def getSF(self, tree, index, pt):
    flavor = tree._lFlavor[index]
    eta    = tree._lEta[index] if flavor == 1 else tree._lEtaSC[index]

    if abs(flavor) == 1:
      if pt >= 120.: pt = 119. # last bin is valid to infinity
      elif pt <= 5.: pt = 6.
      eta = abs(eta)
      etaBin = self.muSF.GetXaxis().FindBin(eta)
      ptBin = self.muSF.GetYaxis().FindBin(pt)
      sf      = self.muSF.GetBinContent(    etaBin, ptBin)
      errSyst = self.muSyst.GetBinContent(  etaBin, ptBin)
      errStat = self.muStat.GetBinContent(  etaBin, ptBin)
      errPS   = self.muPSSys.GetBinContent( etaBin, ptBin)
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (sf, errSyst, errStat, errPS, 1. , 0.)
    elif abs(flavor) == 0:
      if pt >= 200.: pt = 199. # last bin is valid to infinity
      elif pt <= 10.: pt = 11.
      etaBin = self.elSF.GetXaxis().FindBin(eta)
      ptBin = self.elSF.GetYaxis().FindBin(pt)
      sf      = self.elSF.GetBinContent(  etaBin, ptBin)
      errSyst = self.elSyst.GetBinContent(etaBin, ptBin)
      errStat = self.elStat.GetBinContent(etaBin, ptBin)
      # NOTE stat and sys need to be varied sepatately, code below is wrong if varied together
      return (sf, errSyst, errStat, 0., 0., 1.)
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)
