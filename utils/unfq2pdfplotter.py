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


# plots = ['unfReco_phLepDeltaR']
# plots = ['unfReco_phLepDeltaR', 'unfReco_phPt']
# systs = ['pdf', 'q2']

# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'NPFlat', 'pu', 'pvSFDown16', 'other_Other+#gamma (genuine)Other+#gamma (genuine)']
# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'NPFlat', 'pu', 'other_Other+#gamma (genuine)Other+#gamma (genuine)']
# systs = ['q2', 'lumi', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'NPFlat', 'pu']
# systs = [ 'lumi', 'q2', 'fsr', 'bTagbCO', 'lSFElSyst', 'phSF', 'NPFlat', 'pu']
# systs = ['singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 'other_Other+#gamma (genuine)Other+#gamma (genuine)', 'lumi']

# naming = {'q2':'scale', 'fsr':'fsr', 'bTagbCO':'btag b corr.', 'lSFElSyst':'lep. SF el Syst.', 'phSF': 'ph SF', 'NPFlat': 'NP flat', 'pu': 'pu', 'lumi':'lumi'}


# histos = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA_NLO/noData/placeholderSelection/' + 'unfReco_phPt'.replace('unfReco','fid_unfReco') + '_norm.pkl','r'))


# norm = True
norm = False


syskey = 'q2'
if norm:
  rd, ru = -.07, 0.07
else:
  rd, ru = -.18, 0.18


# syskey = 'pdfSc_1'
# if norm:
#   rd, ru = -.04, 0.04
# else:
#   rd, ru = -.12, 0.12

for plot in plots:  
  histos = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA_NLO/noData/placeholderSelection/' + plot.replace('unfReco','fid_unfReco') + '.pkl','r'))
  # pdb.set_trace()
  hists = {k: histos[k].values()[0] for k in histos.keys() if k.count(syskey)}

  hists[''] = histos['fid_' + plot].values()[0].Clone()


  nom = hists[''].Clone()
  for i in range(nom.GetXaxis().GetNbins()+2):
    nom.SetBinError(i, 0)

  if norm:
    nom.Scale(1/nom.Integral())

  nomnorm = nom.Clone()
  nomnorm.Scale(1/nomnorm.Integral())

  nb = nom.GetXaxis().GetNbins()
  nom.SetBinContent(nb, nom.GetBinContent(nb)+nom.GetBinContent(nb+1))

  c1 = ROOT.TCanvas('c', 'c', 1400, 1500)
  legend = ROOT.TLegend(0.20,0.8,0.9,0.9)
  for i, s in enumerate(hists.keys()):
    if s == '': continue

    hists[s].SetBinContent(nb, hists[s].GetBinContent(nb)+hists[s].GetBinContent(nb+1))
    hists[s].SetBinError(nb, (hists[s].GetBinError(nb)**2.+hists[s].GetBinError(nb+1)**2.))
    hists[s].SetBinContent(nb+1, 0.)
    hists[s].SetBinError(nb+1, 0.)
    if norm:
      hists[s].Scale(1/hists[s].Integral())


    hists[s+'norm'] = hists[s].Clone()
    hists[s+'norm'].Scale(1/hists[s+'norm'].Integral())

    hists[s+'norm'].Add(nomnorm, -1)
    hists[s+'norm'].Divide(nomnorm)

    hists[s].Add(nom, -1)
    hists[s].Divide(nom)
    hists[s].SetLineStyle(1)
    hists[s].SetLineColor(colors[i])
    hists[s].SetLineWidth(4)
    hists[s].GetYaxis().SetRangeUser(rd, ru)
    hists[s].SetTitle('')

    hists[s].GetYaxis().SetTitle('impact [%]')
    hists[s].GetXaxis().SetTitle(labels[plot][0])
    hists[s].Draw('SAME hist')
    
    legend.AddEntry(hists[s], s.replace('fid_' + plot + 'q2Sc_' , '').replace('fid_' + plot + 'pdfSc_' , 'pdf') , 'L')

  legend.SetNColumns(6)
  legend.SetColumnSeparation(0.1)
  legend.SetFillStyle(0)
  legend.SetLineStyle(0)
  legend.SetBorderSize(0)
  legend.Draw()



  l1 = ROOT.TLine(hists[s].GetBinLowEdge(1),0., hists[s].GetBinLowEdge(hists[s].GetXaxis().GetLast()+1),0.)
  l1.SetLineStyle(3)  
  l1.SetLineWidth(2)
  l1.Draw()

  c1.SaveAs('unfpdfq2plots/'+ plot.replace('unfReco_', '') + ('norm' if norm else '') + '_' + syskey + '.png')


