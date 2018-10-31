from ttg.tools.logger import getLogger
log = getLogger()

#
# Class for trigger efficiencies
#
from ttg.tools.helpers import getObjFromFile
from math import sqrt
import os


scaleFactorFile = "$CMSSW_BASE/src/ttg/reduceTuple/data/triggerEff/triggerSF.root"

class TriggerEfficiency:
  def __init__(self):
    self.mumu   = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-mumu")
    self.ee     = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-ee")
    self.mue    = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-mue")
    self.emu    = getObjFromFile(os.path.expandvars(scaleFactorFile), "SF-emu")

    h_ = [self.mumu, self.ee, self.mue, self.emu]
    assert False not in [bool(x) for x in h_], "Could not load trigger SF: %r"%h_

    self.ptMax = self.mumu.GetXaxis().GetXmax()

  def __getSF(self, map_, pt1, pt2, sysUnc):
    if pt1 > self.ptMax: pt1 = self.ptMax - 1 
    if pt2 > self.ptMax: pt2 = self.ptMax - 1 
    val    = map_.GetBinContent(map_.FindBin(pt1, pt2))
    valErr = map_.GetBinError(  map_.FindBin(pt1, pt2))
    valErr = sqrt(valErr**2+sysUnc**2)
    return (val, valErr)

  def getSF(self, tree, l1, l2):
    eta1    = abs(tree._lEta[l1])
    eta2    = abs(tree._lEta[l2])
    flavor1 = tree._lFlavor[l1]
    flavor2 = tree._lFlavor[l2]
    pt1     = tree._lPt[l1] if flavor1 else tree._lPtCorr[l1]
    pt2     = tree._lPt[l2] if flavor2 else tree._lPtCorr[l2]

    if pt1 < pt2: raise ValueError ( "Sort leptons wrt pt." )

    # Uncertainty: 0.01 + 0.03 for each muon above > 1.2 (studies show only slight eta dependence of SF for muons, not for electrons)
    if abs(flavor1)==abs(flavor2)==1:         return self.__getSF(self.mumu, pt1, pt2, 0.01 + (0.03 if eta1>1.2 and pt1>50 else 0.) + (0.03 if eta2>1.2 and pt2>50 else 0.))
    elif abs(flavor1)==abs(flavor2)==0:       return self.__getSF(self.ee,   pt1, pt2, 0.01)
    elif abs(flavor1)==1 and abs(flavor2)==0: return self.__getSF(self.mue,  pt1, pt2, 0.01)
    elif abs(flavor1)==0 and abs(flavor2)==1: return self.__getSF(self.emu,  pt1, pt2, 0.01)
    raise ValueError( "Did not find trigger SF for pt1 %3.2f eta %3.2f flavor %i pt2 %3.2f eta2 %3.2f flavor %i"%( pt1, eta1, flavor1, pt2, eta2, flavor2 ) )
