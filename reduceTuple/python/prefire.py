#
# Photon SF class
#

import os
from ttg.tools.helpers import getObjFromFile

dataDir       = "$CMSSW_BASE/src/ttg/reduceTuple/data/prefire"
files = {'16':("Map_Jet_L1FinOReff_bxm1_looseJet_SingleMuon_Run2016B-H.root", "prefireEfficiencyMap"),
         '17':("Map_Jet_L1FinOReff_bxm1_looseJet_SingleMuon_Run2016B-H.root", "prefireEfficiencyMap"),
         '18':("Map_Jet_L1FinOReff_bxm1_looseJet_SingleMuon_Run2016B-H.root", "prefireEfficiencyMap")}

class Prefire:
  def __init__(self, year):
    filename, key = files[year] 
    self.map = getObjFromFile(os.path.expandvars(os.path.join(dataDir, filename)), key)
    assert self.map

  # Note: this is not a real SF, only a conservative check, for the real SF you need the ECAL component of the jet pt!
  def getSF(self, tree):
    prefireSF = 1.
    for i in xrange(tree._nJets):
      pt  = tree._jetSmearedPt[i]
      eta = abs(tree._jetEta[i])

      if eta > 2 and pt > 40:
        globalBin  = self.map.FindFixBin(eta, pt)
        prefireSF *= (1.- self.map.GetEfficiency(globalBin))
    return prefireSF
