from ttg.tools.logger import getLogger
log = getLogger()

#
# Class for trigger efficiencies
#
import ROOT
from ttg.tools.helpers import getObjFromFile
import os

basedir = "$CMSSW_BASE/src/ttg/reduceTuple/data/triggerEff/"

#OR of all backup triggers
ee_trigger_SF   = basedir+'Run2016BCDEFGH_HLT_ee_DZ_OR_HLT_ee_33_OR_HLT_ee_33_MW_OR_HLT_SingleEle_noniso_None_measuredInMET_minLeadLepPt0.root'
mue_trigger_SF  = basedir+'Run2016BCDEFGH_HLT_mue_OR_HLT_mu30e30_OR_HLT_SingleEle_noniso_OR_HLT_SingleMu_noniso_None_measuredInMET_minLeadLepPt0.root'
mumu_trigger_SF = basedir+'Run2016BCDEFGH_HLT_mumuIso_OR_HLT_mumuNoiso_OR_HLT_SingleMu_noniso_None_measuredInMET_minLeadLepPt0.root'

class triggerEfficiency:
  def __init__(self):
    self.mumu_highEta   = getObjFromFile(os.path.expandvars(mumu_trigger_SF), "eff_pt1_pt2_highEta1_veryCoarse")
    self.mumu_lowEta    = getObjFromFile(os.path.expandvars(mumu_trigger_SF), "eff_pt1_pt2_lowEta1_veryCoarse")
    self.ee_highEta     = getObjFromFile(os.path.expandvars(ee_trigger_SF),   "eff_pt1_pt2_highEta1_veryCoarse")
    self.ee_lowEta      = getObjFromFile(os.path.expandvars(ee_trigger_SF),   "eff_pt1_pt2_lowEta1_veryCoarse")
    self.mue_highEta    = getObjFromFile(os.path.expandvars(mue_trigger_SF),  "eff_pt1_pt2_highEta1_veryCoarse")
    self.mue_lowEta     = getObjFromFile(os.path.expandvars(mue_trigger_SF),  "eff_pt1_pt2_lowEta1_veryCoarse")

    h_ = [self.mumu_highEta, self.mumu_lowEta, self.ee_highEta, self.ee_lowEta, self.mue_highEta, self.mue_lowEta]
    assert False not in [bool(x) for x in h_], "Could not load trigger SF: %r"%h_

    self.ptMax = self.mumu_highEta.GetXaxis().GetXmax()

  def __getSF(self, map_, pt1, pt2):
    if pt1>self.ptMax: pt1=self.ptMax - 1 
    if pt2>self.ptMax: pt2=self.ptMax - 1 
    val    = map_.GetBinContent(  map_.FindBin(pt1, pt2) )
    valErr = map_.GetBinError( map_.FindBin(pt1, pt2) )
    return (val, valErr)

  def getSF(self, tree, l1, l2):
    pt1     = tree._lPt[l1]
    pt2     = tree._lPt[l2]
    eta1    = abs(tree._lEta[l1])
    eta2    = abs(tree._lEta[l2])
    flavor1 = tree._lFlavor[l1]
    flavor2 = tree._lFlavor[l2]

    if pt1<pt2: raise ValueError ( "Sort leptons wrt pt." )

    #Split in low/high eta of leading lepton for both, ee and mumu channel 
    if abs(flavor1)==abs(flavor2)==1:
      if abs(eta1)<1.5: return self.__getSF(self.mumu_lowEta, pt1, pt2)
      else:             return self.__getSF(self.mumu_highEta, pt1, pt2)
    elif abs(flavor1)==abs(flavor2)==0:
      if abs(eta1)<1.5: return self.__getSF(self.ee_lowEta, pt1, pt2)
      else:             return self.__getSF(self.ee_highEta, pt1, pt2)

    #Split in low/high eta of muon for emu channel 
    elif abs(flavor1)==1 and abs(flavor2)==0:
      if abs(eta1)<1.5: return self.__getSF(self.mue_lowEta, pt1, pt2)
      else:             return self.__getSF(self.mue_highEta, pt1, pt2)
    elif abs(flavor1)==0 and abs(flavor2)==1:
      if abs(eta2)<1.5: return self.__getSF(self.mue_lowEta, pt1, pt2)
      else:             return self.__getSF(self.mue_highEta, pt1, pt2)
    raise ValueError( "Did not find trigger SF for pt1 %3.2f eta %3.2f flavor %i pt2 %3.2f eta2 %3.2f flavor %i"%( pt1, eta1, flavor1, pt2, eta2, flavor2 ) )
