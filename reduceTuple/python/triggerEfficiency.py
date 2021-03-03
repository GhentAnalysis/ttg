from ttg.tools.logger import getLogger
log = getLogger()

#
# Class for trigger efficiencies
#
from ttg.tools.helpers import getObjFromFile
from math import sqrt
import os


files = {
  ('MVA', '2016'): '$CMSSW_BASE/src/ttg/reduceTuple/data/triggerEff/triggerSFAveraged_phoCB-new__2016.root',
  ('MVA', '2017'): '$CMSSW_BASE/src/ttg/reduceTuple/data/triggerEff/triggerSFAveraged_phoCB-new__2017.root',
  ('MVA', '2018'): '$CMSSW_BASE/src/ttg/reduceTuple/data/triggerEff/triggerSFAveraged_phoCB-new__2018.root'}

systDict = { 
  '2016': (0.00807  ,  0.003735  , 0.004055),
  '2017': (0.015415 ,  0.00756   , 0.013535),
  '2018': (0.01266  ,  0.00409   , 0.001385)}

# TODO: studies to be repeated for full Run II data, including assesment of systematics
class TriggerEfficiency:
  def __init__(self, year, id ):
    scaleFactorFile = files[(id, year)]
    self.mumu   = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-mumu")
    self.ee     = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-ee")
    self.emu    = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-emu")

    self.eeSyst, self.emuSyst, self.mumuSyst = systDict[year]

    h_ = [self.mumu, self.ee, self.emu]
    assert False not in [bool(x) for x in h_], "Could not load trigger SF: %r"%h_

    self.ptMax = self.mumu.GetXaxis().GetXmax()

  def __getSF(self, map_, pt1, pt2, sysErr):
    if pt1 > self.ptMax: pt1 = self.ptMax - 1 
    if pt2 > self.ptMax: pt2 = self.ptMax - 1 
    val    = map_.GetBinContent(map_.FindBin(pt1, pt2))
    statErr = map_.GetBinError(  map_.FindBin(pt1, pt2))
    return (val, statErr, sysErr)

  def getSF(self, tree, pt1, pt2, isMuMu, isEMu, isEE):
    if pt1 < pt2: raise ValueError ( "Sort leptons wrt pt." )
    # Uncertainty: based on difference between MET and JetHT, table below
    if   isMuMu:     return self.__getSF(self.mumu, pt1, pt2, self.mumuSyst)
    elif isEMu:      return self.__getSF(self.emu,  pt1, pt2, self.emuSyst)
    elif isEE:       return self.__getSF(self.ee,   pt1, pt2, self.eeSyst)
    raise ValueError("event in none of the 3 channels")

# TODO implement stat and syst split



#          ee          emu        mumu
# 2016            
# JetHT    0.95754    0.96515     0.9761
# MET      0.9414     0.95768     0.96799
# average  0.94947    0.961415    0.972045
# diff     0.00807    0.003735    0.004055
            
# 2017            
# JetHT    0.96041    0.96266    0.96897
# MET      0.92958    0.94754    0.9419
# average  0.944995   0.9551     0.955435
# diff     0.015415   0.00756    0.013535
            
# 2018            
# JetHT    0.96601    0.96673    0.97215
# MET      0.94069    0.95855    0.96938
# average  0.95335    0.96264    0.970765
# diff     0.01266    0.00409    0.001385


#OLD
#           ee     emu       mue       mumu
# 2016--------------------------------------
# JetHT  0.95754   0.97006   0.96040   0.97610
# MET    0.94140   0.96162   0.95290   0.96799
# diff   0.01614   0.00844   0.0075    0.00811
# 2017--------------------------------------
# JetHT  0.96041   0.96614   0.95861   0.96897
# MET    0.92958   0.95516   0.93748   0.94190
# diff   0.03083   0.01098   0.02113   0.02707
# 2018--------------------------------------
# JetHT  0.96601   0.97063   0.96152   0.97215
# MET    0.94069   0.96408   0.95150   0.96938
# diff   0.02532   0.00655   0.01002   0.00277
