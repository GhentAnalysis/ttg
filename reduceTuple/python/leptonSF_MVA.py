from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton SF class for lepton MVA
# TODO: probably wants to merge with the Lepton SF class into a more general code where the keys and boundaries are defined together in some small snippet
#

import os
from ttg.tools.uncFloat import UncFloat
from ttg.tools.helpers  import getObjFromFile, multiply
from math import sqrt

dataDir  = "$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData"

# FIXME no 2018 MVA lepton SF available yet, using 2017 for now

keys_mu =  {'2016': 'MVAtZqSFMu16.root',
            '2017': 'MVAtZqSFMu17.root',
            '2018': 'MVAtZqSFMu17.root'}

keys_ele = {'2016': 'MVAtZqSFEl16.root',
            '2017': 'MVAtZqSFEl17.root',
            '2018': 'MVAtZqSFEl17.root'}

class LeptonSF_MVA:
  def __init__(self, year): 
    self.mu   = getObjFromFile(os.path.expandvars(os.path.join(dataDir, keys_mu[year])), 'MuonToTTVLeptonMvattZ4l_stat')
    self.ele  = getObjFromFile(os.path.expandvars(os.path.join(dataDir, keys_ele[year])), 'EleToTTVLeptonMvattZ4l_stat')
    assert self.mu
    assert self.ele

  def getSF(self, tree, index, pt, elSigma=0, muSigma=0):
    flavor = tree._lFlavor[index]
    eta    = tree._lEta[index] if flavor == 1 else tree._lEtaSC[index]

    if pt >= 200: pt = 199 # last bin is valid to infinity
    elif pt <= 10: pt = 11
    if abs(flavor) == 1:
      sf  = self.mu.GetBinContent(self.mu.GetXaxis().FindBin(pt), self.mu.GetYaxis().FindBin(eta))
      err = self.mu.GetBinError(self.mu.GetXaxis().FindBin(pt), self.mu.GetYaxis().FindBin(eta))
      sf = UncFloat(sf, err)
      return (1+sf.sigma*muSigma)*sf.val
    elif abs(flavor) == 0:
      sf  = self.ele.GetBinContent(self.ele.GetXaxis().FindBin(pt), self.ele.GetYaxis().FindBin(eta))
      err = self.ele.GetBinError(self.ele.GetXaxis().FindBin(pt), self.ele.GetYaxis().FindBin(eta))
      sf = UncFloat(sf, err)
      return (1+sf.sigma*elSigma)*sf.val
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)
    # REMOVED 1% additional uncertainty to account for phase space differences between Z and ttbar (uncorrelated with TnP sys)
