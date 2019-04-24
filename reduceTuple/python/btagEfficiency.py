from collections import namedtuple
import itertools
import ROOT, os, pickle
from ttg.tools.logger import getLogger
from ttg.tools.helpers import multiply
log = getLogger()

#class of 2-tuples containing upper and lower binEdges 
BinEdges = namedtuple("BinEdges", ['low', 'high'])

#monkey-patch generated class to have a 'contains' method (last bin edge is -1)
def contains( binEdges, entry ):
  return entry >= binEdges.low and ( entry < binEdges.high or binEdges.high < 0 )
BinEdges.contains = contains

#generator factory constructed from list of bin edges 
def getBins( binning ):
  for low, high in zip( binning[:-1], binning[1:] ):
    yield BinEdges( low, high )


def getPtBins():
  ptBorders = [30, 50, 70, 100, 140, 200, 300, 600, 1000, -1]
  return getBins( ptBorders )


def getEtaBins():
  etaBorders = [0, 0.8, 1.6, 2.4, -1]
  return getBins( etaBorders )


def toFlavorKey(pdgId):
  if abs(pdgId)==5:   return ROOT.BTagEntry.FLAV_B
  elif abs(pdgId)==4: return ROOT.BTagEntry.FLAV_C
  else:               return ROOT.BTagEntry.FLAV_UDSG


class BtagEfficiency:
#FIXME replace once samples generated, pkl files produced
  scaleFactorFile    = {'2016':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_Moriond17_B_H.csv',
                        '2017':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_Moriond17_B_H.csv',
                        '2018':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_Moriond17_B_H.csv'}
  mcEffFileDeepCSV   = {'2016':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_TTGamma.pkl',
                        '2017':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_TTGamma.pkl',
                        '2018':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_TTGamma.pkl'}

  def __init__(self, year, wp = ROOT.BTagEntry.OP_MEDIUM):
    # Input files

    self.mcEffDeepCSV = pickle.load(file(os.path.expandvars(self.mcEffFileDeepCSV[year])))

    ROOT.gSystem.Load('libCondFormatsBTauObjects')
    ROOT.gSystem.Load('libCondToolsBTau')
    self.calib = ROOT.BTagCalibration("deepCSV", os.path.expandvars(self.scaleFactorFile[year]))

    # Get readers
    #recommended measurements for different jet flavors given here: https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation80X#Data_MC_Scale_Factors
    v_sys = getattr(ROOT, 'vector<string>')()
    v_sys.push_back('up')
    v_sys.push_back('down')
    self.reader = ROOT.BTagCalibrationReader(wp, "central", v_sys)
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_B, "comb")
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_C, "comb")
    self.reader.load(self.calib, ROOT.BTagEntry.FLAV_UDSG, "incl")


  # Get MC efficiency for a given jet
  def getMCEff(self, tree, index):
    pt     = tree._jetSmearedPt[index]
    eta    = abs(tree._jetEta[index])
    absFlavor = abs(tree._jetHadronFlavor[index])

    for ptBin, etaBin in itertools.product( getPtBins(), getEtaBins() ):
      if ptBin.contains( pt ) and etaBin.contains( eta ):
        mcEff = self.mcEffDeepCSV
        
        effMap = mcEff[tuple(ptBin)][tuple(etaBin)]
        if absFlavor == 5 : return effMap['b']
        elif absFlavor == 4 : return effMap['c']
        else : return effMap['other']
        
        log.warning("No MC efficiency for pt %f eta %f pdgId %i", pt, eta, absFlavor)
        return 1


  def getJetSF(self, tree, index, sys):
    pt      = tree._jetSmearedPt[index]
    eta     = abs(tree._jetEta[index])
    absFlavor  = abs(tree._jetHadronFlavor[index])
    if   sys == 'bUp'   and absFlavor >= 4: sysType = 'up'
    elif sys == 'bDown' and absFlavor >= 4: sysType = 'down'
    elif sys == 'lUp'   and absFlavor <= 3: sysType = 'up'
    elif sys == 'lDown' and absFlavor <= 3: sysType = 'down'
    elif sys == '':                      sysType = 'central'
    else:                                return 1.
    return self.reader.eval_auto_bounds(sysType, toFlavorKey(absFlavor), eta, pt)

 
  def getBtagSF_1a(self, sysType, tree, bjets):
    mcEff_bJets = ( self.getMCEff(tree, j) for j in bjets )
    mcEff_lJets = ( (1-self.getMCEff(tree, j)) for j in tree.jets if j not in bjets )
    sf_bJets    = ( self.getMCEff(tree, j)*self.getJetSF(tree, j, sysType) for j in bjets )
    sf_lJets    = ( (1-self.getMCEff(tree, j)*self.getJetSF(tree, j, sysType)) for j in tree.jets if j not in bjets )

    ref = multiply( itertools.chain( mcEff_bJets, mcEff_lJets ) )
    if ref > 0: return multiply( itertools.chain(sf_bJets, sf_lJets) )/ref
    else:     
      log.warning('MC efficiency is zero. Return SF 1')
      return 1


  def getBtagSF_1c(self, sysType, tree, bjets):
    btagSF = ( self.getJetSF(tree, j, sysType) for j in bjets )

    if   len(btagSF) == 0: return (1.0,         0.0, 0.0)
    elif len(btagSF) == 1: return (1 - btagSF[0], btagSF[0], 0)
    else:
      weight0tag = multiply( 1-sf for sf in btagSF )
      weight1tag = 0
      for i in range(len(btagSF)):
        prod = btagSF[i]
        for j in range(len((btagSF))):
          if i != j: prod = (1-btagSF[j])
        weight1tag += prod
      return (weight0tag, weight1tag, 1-weight0tag-weight1tag)

if __name__ == '__main__':
  years = ['16', '17', '18']
  for year in years:
    testClass = BtagEfficiency(year)
    for ptBin in getPtBins():
      for etaBin in getEtaBins():
        print ptBin, etaBin, testClass.mcEffDeepCSV[tuple(ptBin)][tuple(etaBin)]
