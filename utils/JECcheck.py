#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle
import time
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.12)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


# plot = 'l1_jetDeltaR'
plot = 'njets'
# plot = 'signalRegions'
file = '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-ttgjec3-noZgCorr/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/'+ plot +'.pkl'
proc = 'ttgject#bar{t}#gammaDil (genuine)'
dic = pickle.load(open(file))

nom = dic[plot][proc]
jecUp = dic[plot+'JECUp'][proc]
jecDown = dic[plot+'JECDown'][proc]

devUp = nom.Clone()
devUp.Reset("ICES")
devDown = devUp.Clone()

# for var in ['Absolute','BBEC1','EC2','FlavorQCD','HF','RelativeBal','Total','HFUC','AbsoluteUC','BBEC1UC','EC2UC','RelativeSampleUC']:
for var in ['Absolute','BBEC1','EC2','FlavorQCD','HF','RelativeBal','HFUC','AbsoluteUC','BBEC1UC','EC2UC','RelativeSampleUC']:
# for var in ['Total']:
  varHistUp = dic[plot+var+'Up'][proc]
  varHistUp.Add(nom, -1.)
  varHistDown = dic[plot+var+'Down'][proc]
  varHistDown.Add(nom, -1.)
  for i in range(0, varHistUp.GetXaxis().GetNbins()+1):
    varHistUp.SetBinContent(i, varHistUp.GetBinContent(i)**2.)
    varHistDown.SetBinContent(i, varHistDown.GetBinContent(i)**2.)
  devUp.Add(varHistUp)
  devDown.Add(varHistDown)

for i in range(0, devUp.GetXaxis().GetNbins()+1):
  devUp.SetBinContent(i, devUp.GetBinContent(i)**0.5)
  devDown.SetBinContent(i, devDown.GetBinContent(i)**0.5)

srcUp = nom.Clone()
srcUp.Reset("ICES")
srcDown = srcUp.Clone()
# for var in ['AbsoluteMPFBias_JECSources','AbsoluteScale_JECSources','AbsoluteStat_JECSources','FlavorPhotonJet_JECSources','FlavorPureBottom_JECSources','FlavorPureCharm_JECSources','FlavorPureGluon_JECSources','FlavorPureQuark_JECSources','FlavorQCD_JECSources','FlavorZJet_JECSources','Fragmentation_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','SinglePionECAL_JECSources','SinglePionHCAL_JECSources','SubTotalAbsolute_JECSources','SubTotalMC_JECSources','SubTotalPt_JECSources','SubTotalRelative_JECSources','SubTotalScale_JECSources','TimePtEta_JECSources','Total_JECSources','TotalNoFlavor_JECSources','TotalNoFlavorNoTime_JECSources','TotalNoTime_JECSources']:
# for var in ['AbsoluteStat_JECSources','FlavorPhotonJet_JECSources','FlavorPureBottom_JECSources','FlavorPureCharm_JECSources','FlavorPureGluon_JECSources','FlavorPureQuark_JECSources','FlavorQCD_JECSources','FlavorZJet_JECSources','Fragmentation_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','SinglePionECAL_JECSources','SinglePionHCAL_JECSources','SubTotalAbsolute_JECSources','SubTotalMC_JECSources','SubTotalPt_JECSources','SubTotalRelative_JECSources','TimePtEta_JECSources','TotalNoFlavor_JECSources','TotalNoFlavorNoTime_JECSources','TotalNoTime_JECSources']:

# for var in ['AbsoluteMPFBias_JECSources','AbsoluteScale_JECSources','AbsoluteStat_JECSources','FlavorPhotonJet_JECSources','FlavorPureBottom_JECSources','FlavorPureCharm_JECSources','FlavorPureGluon_JECSources','FlavorPureQuark_JECSources','FlavorQCD_JECSources','FlavorZJet_JECSources','Fragmentation_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','SinglePionECAL_JECSources','SinglePionHCAL_JECSources','TimePtEta_JECSources']:
# for var in ['AbsoluteMPFBias_JECSources','AbsoluteStat_JECSources','FlavorPhotonJet_JECSources','FlavorPureBottom_JECSources','FlavorPureCharm_JECSources','FlavorPureGluon_JECSources','FlavorPureQuark_JECSources','FlavorQCD_JECSources','FlavorZJet_JECSources','Fragmentation_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','SinglePionECAL_JECSources','SinglePionHCAL_JECSources','TimePtEta_JECSources']:
# for var in ['AbsoluteStat_JECSources','FlavorQCD_JECSources','Fragmentation_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','SinglePionECAL_JECSources','SinglePionHCAL_JECSources','TimePtEta_JECSources']:


# ,'SinglePionECAL_JECSources','SinglePionHCAL_JECSources' fastsim only?

for var in ['AbsoluteMPFBias_JECSources','AbsoluteScale_JECSources','AbsoluteStat_JECSources','FlavorQCD_JECSources','Fragmentation_JECSources','PileUpDataMC_JECSources','PileUpPtBB_JECSources','PileUpPtEC1_JECSources','PileUpPtEC2_JECSources','PileUpPtHF_JECSources','PileUpPtRef_JECSources','RelativeBal_JECSources','RelativeFSR_JECSources','RelativeJEREC1_JECSources','RelativeJEREC2_JECSources','RelativeJERHF_JECSources','RelativePtBB_JECSources','RelativePtEC1_JECSources','RelativePtEC2_JECSources','RelativePtHF_JECSources','RelativeSample_JECSources','RelativeStatEC_JECSources','RelativeStatFSR_JECSources','RelativeStatHF_JECSources','TimePtEta_JECSources']:
  varHistUp = dic[plot+var+'Up'][proc]
  varHistUp.Add(nom, -1.)
  varHistDown = dic[plot+var+'Down'][proc]
  varHistDown.Add(nom, -1.)
  for i in range(0, varHistUp.GetXaxis().GetNbins()+1):
    # print varHistUp.GetBinContent(i)
    varHistUp.SetBinContent(i, varHistUp.GetBinContent(i)**2.)
    varHistDown.SetBinContent(i, varHistDown.GetBinContent(i)**2.)
  srcUp.Add(varHistUp)
  srcDown.Add(varHistDown)

for i in range(0, srcUp.GetXaxis().GetNbins()+1):
  srcUp.SetBinContent(i, srcUp.GetBinContent(i)**0.5)
  srcDown.SetBinContent(i, srcDown.GetBinContent(i)**0.5)


# raise SystemExit(0)

up = nom.Clone()
up.Add(devUp)
down = nom.Clone()
down.Add(devDown, -1)


srcup = nom.Clone()
srcup.Add(srcUp)
srcdown = nom.Clone()
srcdown.Add(srcDown, -1)

c1 = ROOT.TCanvas('c', 'c', 1300, 800)
nom.SetTitle('')
nom.SetLineColor(ROOT.kBlack)
jecUp.SetLineColor(ROOT.kBlue)
jecDown.SetLineColor(ROOT.kBlue)
up.SetLineColor(ROOT.kGreen)
down.SetLineColor(ROOT.kGreen)
srcup.SetLineColor(ROOT.kRed)
srcdown.SetLineColor(ROOT.kRed)

# offZ.SetLineWidth(2)
# onZ.SetLineWidth(2)
# offZ.GetXaxis().SetRangeUser(0.005, 0.020)
# offZ.GetYaxis().SetRangeUser(0., 0.15)
# offZ.GetXaxis().SetTitle("#sigma_{i#etai#eta}(#gamma)")  
# offZ.GetYaxis().SetTitle("(1/N) dN")  
legend = ROOT.TLegend(0.3,0.82,0.7,0.89)
legend.AddEntry(jecUp,"total JEC","L")
legend.AddEntry(up,"grouped JEC summed","L")
legend.AddEntry(srcup,"sources JEC summed","L")
legend.SetBorderSize(0)
legend.SetNColumns(3)
jecUp.Divide(nom)
jecDown.Divide(nom)
up.Divide(nom)
down.Divide(nom)
srcup.Divide(nom)
srcdown.Divide(nom)
nom.Divide(nom)
nom.GetYaxis().SetRangeUser(0.8, 1.2)
nom.GetYaxis().SetTitle("variation / nominal")  
nom.GetXaxis().SetTitle(plot)  


nom.Draw('HIST')
jecUp.Draw('HIST same')
jecDown.Draw('HIST same')
up.Draw('HIST same')
down.Draw('HIST same')
srcup.Draw('HIST same')
srcdown.Draw('HIST same')
legend.Draw()
c1.SaveAs('JECcheck.png')

