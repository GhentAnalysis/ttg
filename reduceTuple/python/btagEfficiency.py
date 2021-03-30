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

  scaleFactorFileHeavy   = {'2016':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_2016LegacySF_V1_YearCorrelation-V1.csv',
                            '2017':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_94XSF_V4_B_F_YearCorrelation-V1.csv',
                            '2018':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_102XSF_V1_YearCorrelation-V1.csv'}
  scaleFactorFileLight   = {'2016':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_2016LegacySF_V1.csv',
                            '2017':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_94XSF_V4_B_F.csv',
                            '2018':'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/DeepCSV_102XSF_V1.csv'}
  mcEffFileDeepCSV   = {('POG','2016'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/deepCSV_TT_Dil+TT_Sem+TT_Had_2016.pkl',
                        ('POG','2017'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/deepCSV_TT_Dil+TT_Sem+TT_Had_2017.pkl',
                        ('POG','2018'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/deepCSV_TT_Dil+TT_Sem+TT_Had_2018.pkl',
                        ('MVA','2016'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/NewdeepCSV_phoCB_TT_Dil_2016.pkl',
                        ('MVA','2017'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/NewdeepCSV_phoCB_TT_Dil_2017.pkl',
                        ('MVA','2018'):'$CMSSW_BASE/src/ttg/reduceTuple/data/btagEfficiencyData/NewdeepCSV_phoCB_TT_Dil_2018.pkl'}



  def __init__(self, year, id, wp = ROOT.BTagEntry.OP_MEDIUM):

    self.sysTranslateHeavy = {'': 'central', 'lUp': 'central', 'lDown': 'central', 'bCOUp': 'up_correlated', 'bCODown': 'down_correlated', 'bUCUp': 'up_uncorrelated', 'bUCDown': 'down_uncorrelated'}
    self.sysTranslateLight = {'': 'central', 'lUp': 'up', 'lDown': 'down', 'bCOUp': 'central', 'bCODown': 'central', 'bUCUp': 'central', 'bUCDown': 'central'}
    # Input files

    self.mcEffDeepCSV = pickle.load(file(os.path.expandvars(self.mcEffFileDeepCSV[(id, year)])))

    ROOT.gSystem.Load('libCondFormatsBTauObjects')
    ROOT.gSystem.Load('libCondToolsBTau')

    # for heavy flavor there are correlated and uncorrelated components, stored in different files
    self.calibLight = ROOT.BTagCalibration("deepCSV", os.path.expandvars(self.scaleFactorFileLight[year]))
    self.calibHeavy = ROOT.BTagCalibration("deepCSV", os.path.expandvars(self.scaleFactorFileHeavy[year]))
    # Get readers
    #recommended measurements for different jet flavors given here: https://twiki.cern.ch/twiki/bin/view/CMS/BtagRecommendation
    v_sysLight = getattr(ROOT, 'vector<string>')()
    v_sysLight.push_back('up')
    v_sysLight.push_back('down')
    self.readerLight = ROOT.BTagCalibrationReader(wp, "central", v_sysLight)
    self.readerLight.load(self.calibLight, ROOT.BTagEntry.FLAV_UDSG, "incl")

    v_sysHeavy = getattr(ROOT, 'vector<string>')()
    v_sysHeavy.push_back('up_uncorrelated')
    v_sysHeavy.push_back('up_correlated')
    v_sysHeavy.push_back('down_uncorrelated')
    v_sysHeavy.push_back('down_correlated')
    self.readerHeavy = ROOT.BTagCalibrationReader(wp, "central", v_sysHeavy)
    self.readerHeavy.load(self.calibHeavy, ROOT.BTagEntry.FLAV_B, "comb")
    self.readerHeavy.load(self.calibHeavy, ROOT.BTagEntry.FLAV_C, "comb")

  # Get MC efficiency for a given jet
  def getMCEff(self, tree, index):
    # NOTE beyond testing <30 pt should be treated properly
    pt      = max(tree._jetSmearedPt[index], 30.1)
    # pt     = tree._jetSmearedPt[index]
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
    # NOTE beyond testing <30 pt should be treated properly
    pt      = max(tree._jetSmearedPt[index], 30.1)
    eta     = abs(tree._jetEta[index])
    absFlavor  = abs(tree._jetHadronFlavor[index])
    if absFlavor >= 4: 
      return self.readerHeavy.eval_auto_bounds(self.sysTranslateHeavy[sys], toFlavorKey(absFlavor), eta, pt)
    else: 
      return self.readerLight.eval_auto_bounds(self.sysTranslateLight[sys], toFlavorKey(absFlavor), eta, pt)

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

if __name__ == '__main__':
  years = ['2016', '2017', '2018']
  for year in years:
    testClass = BtagEfficiency(year, 'MVA')
    for ptBin in getPtBins():
      for etaBin in getEtaBins():
        print ptBin, etaBin, testClass.mcEffDeepCSV[tuple(ptBin)][tuple(etaBin)]