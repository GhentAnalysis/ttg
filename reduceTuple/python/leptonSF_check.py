from ttg.tools.logger import getLogger
log = getLogger()

#
# Lepton SF class
#

import os
from ttg.tools.uncFloat import UncFloat
from ttg.tools.helpers  import getObjFromFile, multiply
from math import sqrt
import ROOT
ROOT.gROOT.SetBatch(True)

dataDir  = "$CMSSW_BASE/src/ttg/reduceTuple/data/leptonSFData"

# currently using electron POG tight or electronMVA90, muon pog medium, 
# current muon SF correspond to a tight isolation cut 

# mu 16 pt y                17, 18 pt x        ele pt y 16, 17, 18 
# lumi: B-F: 19.717640795 GH: 16.146177653  total: 35.863818448 -> fractions  0.549792   0.450208

# FIXME Muon SF for 2018 are not yet final, leave this comment in the file (no SF including syst unc available)

keys_mu_ISO = {'2016': [("2016LegRunBCDEF_Mu_SF_ISO.root",            "NUM_TightRelIso_DEN_MediumID_eta_pt")],
               '2017': [("2017RunBCDEF_Mu_SF_ISO_syst.root",          "NUM_TightRelIso_DEN_MediumID_pt_abseta")],
               '2018': [("2018RunABCD_Mu_SF_ISO.root",                "NUM_TightRelIso_DEN_MediumID_pt_abseta")]}

keys_mu_GH  = {'ISO': [("2016LegRunGH_Mu_SF_ISO.root",               "NUM_TightRelIso_DEN_MediumID_eta_pt")],
               'ID':  [("2016LegRunGH_Mu_SF_ID.root",                "NUM_MediumID_DEN_genTracks_eta_pt")]}

keys_mu_ID  = {'2016': [("2016LegRunBCDEF_Mu_SF_ID.root",             "NUM_MediumID_DEN_genTracks_eta_pt")],
               '2017': [("2017RunBCDEF_Mu_SF_ID_syst.root",           "NUM_MediumID_DEN_genTracks_pt_abseta")],
               '2018': [("2018RunABCD_Mu_SF_ID.root",                 "NUM_MediumID_DEN_TrackerMuons_pt_abseta")]}

keys_ele = {'2016': [("2016LegacyReReco_ElectronTight_Fall17V2.root", "EGamma_SF2D")],
            '2017': [("2017_ElectronTight.root",                      "EGamma_SF2D")],
            '2018': [("2018_ElectronTight.root",                      "EGamma_SF2D")]}

class LeptonSF:
  def __init__(self, year): 
    self.mu   = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ISO[year]]
    self.mu  += [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_ID[year]]
    self.ele  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_ele[year]]
    if year == '2016':
      self.muGH  = [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_GH['ISO']]
      self.muGH += [getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key) for (filename, key) in keys_mu_GH['ID']]
      for effMap in self.muGH:
        assert effMap
    for effMap in self.mu + self.ele: assert effMap

  @staticmethod
  def getPartialSF(effMap, x, y):
    sf  = effMap.GetBinContent(x, y)
    err = effMap.GetBinError(x, y)
    return UncFloat(sf, err)

  def getTestSF(self, x, y, flavor, elSigma=0, muSigma=0):
    if abs(flavor) == 1:
      sf = multiply( self.getPartialSF(effMap, x, y) for effMap in self.mu)
      if hasattr(self, 'muGH'): # for 2016 self.muGH is defined and needs to be taken into account
        sf = (0.549792*sf + 0.450208*multiply( self.getPartialSF(effMap, x, y) for effMap in self.muGH))
      return sf
    elif abs(flavor) == 0:
      sf = multiply( self.getPartialSF(effMap, x, y) for effMap in self.ele)
      # print sf
      return sf
    else: 
      raise Exception("Lepton SF for flavour %i not known"%flavor)

    # REMOVED 1% additional uncertainty to account for phase space differences between Z and ttbar (uncorrelated with TnP sys)

# draw histrograms of the SF and their errors
if __name__ == '__main__':
  for year in ['2016','2017','2018']:
    SF = LeptonSF(year)
    hist = SF.mu[0].Clone()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        hist.SetBinContent(i, j, round(SF.getTestSF(i,j, 1).val, 4))
    c1 = ROOT.TCanvas('c', 'c', 2400, 700)
    hist.Draw('COLZ TEXT')
    c1.SaveAs('sfMu' + year + '.png')

    hist = SF.mu[0].Clone()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        hist.SetBinContent(i, j, round(SF.getTestSF(i,j, 1).sigma, 4))
    c1 = ROOT.TCanvas('c', 'c', 2400, 700)
    hist.Draw('COLZ TEXT')
    c1.SaveAs('errMu' + year + '.png')

    hist = SF.ele[0].Clone()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        hist.SetBinContent(i, j, round(SF.getTestSF(i,j, 0).val, 4))
    c1 = ROOT.TCanvas('c', 'c', 2400, 700)
    hist.Draw('COLZ TEXT')
    c1.SaveAs('sfEl' + year + '.png')

    hist = SF.ele[0].Clone()
    for i in range(1, hist.GetNbinsX()+1):
      for j in range(1, hist.GetNbinsX()+1):
        print SF.getTestSF(i,j, 0).val
        print SF.getTestSF(i,j, 0).sigma
        hist.SetBinContent(i, j, round(SF.getTestSF(i,j, 0).sigma, 4))
    c2 = ROOT.TCanvas('c', 'c', 2400, 700)
    hist.Draw('COLZ TEXT')
    c2.SaveAs('errEl' + year + '.png')