#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
import pickle
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.045)
ROOT.gStyle.SetPadLeftMargin(0.14)
import pdb

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


labels = {
          'unfReco_phPt' :            ('p_{T}(#gamma) [GeV]',  'p_{T}(#gamma) [GeV]'            , 'd#sigma / d p_{T}(#gamma) [fb/GeV]'),
          'unfReco_phLepDeltaR' :     ('#DeltaR(#gamma, l)',   '#DeltaR(#gamma, l)'             , 'd#sigma / d #DeltaR(#gamma, l) [fb]'),
          'unfReco_ll_deltaPhi' :     ('#Delta#phi(ll)',       '#Delta#phi(ll)'                 , 'd#sigma / d #Delta#phi(ll) [fb]'),
          'unfReco_jetLepDeltaR' :    ('#DeltaR(l, j)',        '#DeltaR(l, j)'                  , 'd#sigma / d #DeltaR(l, j) [fb]'),
          'unfReco_jetPt' :           ('p_{T}(j1) [GeV]',      'p_{T}(j1) [GeV]'                , 'd#sigma / d p_{T}(j1) [fb/GeV]'),
          'unfReco_ll_absDeltaEta' :  ('|#Delta#eta(ll)|',     '|#Delta#eta(ll)|'               , 'd#sigma / d |#Delta#eta(ll)| [fb]'),
          'unfReco_phBJetDeltaR' :    ('#DeltaR(#gamma, b)',   '#DeltaR(#gamma, b)'             , 'd#sigma / d #DeltaR(#gamma, b) [fb]'),
          'unfReco_phAbsEta' :        ('|#eta|(#gamma)',       '|#eta|(#gamma)'                 , 'd#sigma / d |#eta|(#gamma) [fb]'),
          'unfReco_phLep1DeltaR' :    ('#DeltaR(#gamma, l1)',       '#DeltaR(#gamma, l1)'       , 'd#sigma / d #DeltaR(#gamma, l1) [fb]'),
          'unfReco_phLep2DeltaR' :    ('#DeltaR(#gamma, l2)',       '#DeltaR(#gamma, l2)'       , 'd#sigma / d #DeltaR(#gamma, l2) [fb]'),
          'unfReco_Z_pt' :            ('p_{T}(ll) [GeV]',           'p_{T}(ll) [GeV]'           , 'd#sigma / d p_{T}(ll) [fb/GeV]'),
          'unfReco_l1l2_ptsum' :      ('p_{T}(l1)+p_{T}(l2) [GeV]', 'p_{T}(l1)+p_{T}(l2) [GeV]' , 'd#sigma / d p_{T}(l1)+p_{T}(l2) [fb/GeV]')
          }

colors = 50*[ROOT.kRed , ROOT.kBlue, ROOT.kGreen+2, ROOT.kMagenta, ROOT.kCyan, ROOT.kOrange-3, ROOT.kBlack, ROOT.kGray]


plots = [
  'unfReco_phPt',
  'unfReco_phLepDeltaR',
  'unfReco_jetLepDeltaR',
  'unfReco_jetPt',
  'unfReco_ll_absDeltaEta',
  'unfReco_ll_deltaPhi',
  'unfReco_phAbsEta',
  'unfReco_phBJetDeltaR',
  'unfReco_phLep1DeltaR',
  'unfReco_phLep2DeltaR',
  'unfReco_Z_pt',
  'unfReco_l1l2_ptsum'
  ]

# rd, ru = 0.98, 1.02
rd, ru = -.05, 0.05


# plots = ['unfReco_phLepDeltaR']
# plots = ['unfReco_phLepDeltaR', 'unfReco_phPt']
# systs = ['pdf', 'q2']

# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'NPFlat', 'pu', 'pvSFDown16', 'other_Other+#gamma (genuine)Other+#gamma (genuine)']
# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'NPFlat', 'pu', 'other_Other+#gamma (genuine)Other+#gamma (genuine)']
# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'NPFlat', 'pu']
systs = [ 'lumi', 'q2', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'NPFlat', 'pu']
# systs = ['singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'other_Other+#gamma (genuine)Other+#gamma (genuine)', 'lumi']

naming = {'q2':'scale', 'fsr':'fsr', 'bTagbCO':'btag b corr.', 'lSFElSyst':'lep. SF el Syst.', 'phSF': 'ph SF', 'NPFlat': 'NP flat', 'pu': 'pu', 'lumi':'lumi'}

for plot in plots:
  hists = pickle.load(open('/storage_mnt/storage/user/gmestdac/TTG/CMSSW_10_2_10/src/ttg/unfolding/unfoldedHists/dict' + plot + 'RunII.pkl', 'r'))
  # pdb.set_trace()
  nom = hists['']

  c1 = ROOT.TCanvas('c', 'c', 1400, 1500)
  legend = ROOT.TLegend(0.15,0.91,0.95,0.99)
  for s, sys in enumerate(systs):
    # hists[sys + 'Up'].Add(nom, -1)
    # hists[sys + 'Down'].Add(nom, -1)
    # hists[sys + 'Up'].Divide(nom)
    # hists[sys + 'Down'].Divide(nom)

    hists[sys + 'Up'].Add(nom, -1)
    hists[sys + 'Down'].Add(nom, -1)
    hists[sys + 'Up'].Divide(nom)
    hists[sys + 'Down'].Divide(nom)

    hists[sys + 'Up'].SetLineStyle(1)
    hists[sys + 'Up'].SetLineColor(colors[s])
    hists[sys + 'Down'].SetLineStyle(9)
    hists[sys + 'Down'].SetLineColor(colors[s])
    hists[sys + 'Up'].SetLineWidth(4)
    hists[sys + 'Down'].SetLineWidth(4)
    if s == 0:
      hists[sys + 'Up'].GetYaxis().SetRangeUser(rd, ru)
      hists[sys + 'Up'].SetTitle('')
      hists[sys + 'Up'].GetYaxis().SetTitle('impact [%]')
      hists[sys + 'Up'].GetXaxis().SetTitle(labels[plot][0])
    hists[sys + 'Up'].Draw('SAME hist')
    hists[sys + 'Down'].Draw('SAME hist')
    # else:
    legend.AddEntry(hists[sys+ 'Up'], naming[sys] , 'L')

  legend.SetNColumns(4)
  legend.SetColumnSeparation(0.1)
  legend.SetFillStyle(0)
  legend.SetLineStyle(0)
  legend.SetBorderSize(0)
  legend.Draw()



  l1 = ROOT.TLine(hists[systs[0]+ 'Up'].GetBinLowEdge(1),0., hists[systs[0]+ 'Up'].GetBinLowEdge(hists[systs[0]+ 'Up'].GetXaxis().GetLast()+1),0.)
  l1.SetLineStyle(3)  
  l1.SetLineWidth(2)
  l1.Draw()

  c1.SaveAs('arcSystPlots/' + plot + '.png')


