import ROOT, os, pickle
from ttg.tools.logger import getLogger
from ttg.tools.helpers import multiply
log = getLogger()


#binning in pt and eta
def getPtBins():
  ptBorders = [30, 50, 70, 100, 140, 200, 300, 600, 1000]
  ptBins = []
  for i in range(len(ptBorders)-1):
    ptBins.append([ptBorders[i], ptBorders[i+1]])
  ptBins.append([ptBorders[-1], -1])
  return ptBins

def getEtaBins():
  return [[0, 0.8], [0.8, 1.6], [1.6, 2.4]]

def toFlavorKey(pdgId):
  if abs(pdgId)==5:   return ROOT.BTagEntry.FLAV_B
  elif abs(pdgId)==4: return ROOT.BTagEntry.FLAV_C
  else:               return ROOT.BTagEntry.FLAV_UDSG

class BtagEfficiency:
  def __init__(self, wp = ROOT.BTagEntry.OP_MEDIUM):
    # Input files
    self.scaleFactorFile    = '$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_Moriond17_B_H.csv'
    self.scaleFactorFileCSV = '$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/CSVv2_Moriond17_B_H.csv'
    self.mcEffFileCSV       = '$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/CSVv2.pkl'
    self.mcEffFileDeepCSV   = '$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV.pkl'

    self.mcEffCSV     = pickle.load(file(os.path.expandvars(self.mcEffFileCSV)))
    self.mcEffDeepCSV = pickle.load(file(os.path.expandvars(self.mcEffFileDeepCSV)))

    ROOT.gSystem.Load('libCondFormatsBTauObjects')
    ROOT.gSystem.Load('libCondToolsBTau')
    self.calib    = ROOT.BTagCalibration("deepCSV", os.path.expandvars(self.scaleFactorFile))
    self.calibCSV = ROOT.BTagCalibration("csvv2",   os.path.expandvars(self.scaleFactorFileCSV))

    # Get readers
    #recommended measurements for different jet flavors given here: https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation80X#Data_MC_Scale_Factors
    v_sys = getattr(ROOT, 'vector<string>')()
    v_sys.push_back('up')
    v_sys.push_back('down')
    self.reader = ROOT.BTagCalibrationReader(wp, "central", v_sys)
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_B, "comb")
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_C, "comb")
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_UDSG, "incl")
    self.readerCSV = ROOT.BTagCalibrationReader(wp, "central", v_sys)
    self.readerCSV.load(self.calibCSV, ROOT.BTagEntry.FLAV_B, "comb")
    self.readerCSV.load(self.calibCSV, ROOT.BTagEntry.FLAV_C, "comb")
    self.readerCSV.load(self.calibCSV, ROOT.BTagEntry.FLAV_UDSG, "incl")




  # Get MC efficiency for a given jet
  def getMCEff(self, tree, index, isCSV):
    pt     = tree._jetPt[index]
    eta    = abs(tree._jetEta[index])
    flavor = abs(tree._jetHadronFlavor[index])
    for ptBin in getPtBins():
      if pt >= ptBin[0] and (pt < ptBin[1] or ptBin[1] < 0):
        for etaBin in getEtaBins():
          if abs(eta) >= etaBin[0] and abs(eta) < etaBin[1]:
            mcEff = self.mcEffCSV if isCSV else self.mcEffDeepCSV
            if abs(flavor)==5:   return  mcEff[tuple(ptBin)][tuple(etaBin)]["b"]
            elif abs(flavor)==4: return  mcEff[tuple(ptBin)][tuple(etaBin)]["c"]
            else:                return  mcEff[tuple(ptBin)][tuple(etaBin)]["other"]

    log.warning("No MC efficiency for pt %f eta %f pdgId %i", pt, eta, flavor)
    return 1

  def getJetSF(self, tree, index, sys, isCSV):
    pt      = tree._jetPt[index]
    eta     = abs(tree._jetEta[index])
    flavor  = abs(tree._jetHadronFlavor[index])
    if   sys == 'bUp'   and flavor >= 4: sysType = 'up'
    elif sys == 'bDown' and flavor >= 4: sysType = 'down'
    elif sys == 'lUp'   and flavor <= 3: sysType = 'up'
    elif sys == 'lDown' and flavor <= 3: sysType = 'down'
    elif sys == '':                      sysType = 'central'
    else:                                return 1.
    if isCSV: return self.readerCSV.eval_auto_bounds(sysType, toFlavorKey(flavor), eta, pt)
    else:     return self.reader.eval_auto_bounds(sysType, toFlavorKey(flavor), eta, pt)
 
  def getBtagSF_1a(self, sysType, tree, bjets, isCSV):
    mcEff_bJets = [self.getMCEff(tree, j, isCSV) for j in bjets]
    mcEff_lJets = [(1-self.getMCEff(tree, j, isCSV)) for j in tree.jets if j not in bjets]
    sf_bJets    = [self.getMCEff(tree, j, isCSV)*self.getJetSF(tree, j, sysType, isCSV) for j in bjets]
    sf_lJets    = [(1-self.getMCEff(tree, j, isCSV)*self.getJetSF(tree, j, sysType, isCSV)) for j in tree.jets if j not in bjets]

    ref = multiply(mcEff_bJets + mcEff_lJets)
    if ref > 0: return multiply(sf_bJets + sf_lJets)/ref
    else:     
      log.warning('MC efficiency is zero. Return SF 1')
      return 1


  def getBtagSF_1c(self, sysType, tree, bjets, isCSV):
    btagSF = [self.getJetSF(tree, j, sysType, isCSV) for j in bjets]

    if   len(btagSF) == 0: return (1.0,         0.0, 0.0)
    elif len(btagSF) == 1: return (1-btagSF[0], btagSF[0], 0)
    else:
      weight0tag = multiply([1-sf for sf in btagSF])
      weight1tag = 0
      for i in range(len(btagSF)):
        prod = btagSF[i]
        for j in range(len((btagSF))):
          if i != j: prod = (1-btagSF[j])
        weight1tag += prod
      return (weight0tag, weight1tag, 1-weight0tag-weight1tag) 
