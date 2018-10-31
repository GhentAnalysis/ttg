from ttg.tools.logger import getLogger
log = getLogger()

#
# PU reweighting class
#
import ROOT, sys, os
from ttg.tools.helpers import getObjFromFile

dataDir = '$CMSSW_BASE/src/ttg/reduceTuple/data/puReweightingData/'

#Define a functio that returns a reweighting-function according to the data 
def getReweightingFunction(data="PU_2016_36000_XSecCentral", useMC=None):

  # Data
  histoData = getObjFromFile(dataDir + data + '.root', 'pileup')
  histoData.Scale(1./histoData.Integral())

  # MC
  if not useMC:
    mcProfile = ROOT.TH1D('mc', 'mc', 100, 0, 100)
    sys.stdout = open(os.devnull, 'w')
    from SimGeneral.MixingModule.mix_2016_25ns_Moriond17MC_PoissonOOTPU_cfi import mix
    sys.stdout = sys.__stdout__
    for i, value in enumerate(mix.input.nbPileupEvents.probValue): mcProfile.SetBinContent(i+1, value)   # pylint: disable=E1101
  else:
    mcProfile = useMC
  mcProfile.Scale(1./mcProfile.Integral())

  # Create reweighting histo
  reweightingHisto = histoData.Clone('reweightingHisto')
  reweightingHisto.Divide(mcProfile)

  # Define reweightingFunc
  def reweightingFunc(nTrueInt):
    return reweightingHisto.GetBinContent(reweightingHisto.FindBin(nTrueInt))
  return reweightingFunc
