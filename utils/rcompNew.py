#
# nonprompt photon background estimation weights
#

import numpy
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.055)
ROOT.gStyle.SetPadLeftMargin(0.065)
ROOT.gStyle.SetPadBottomMargin(0.12)
ROOT.gStyle.SetPadTopMargin(0.03)
ROOT.gStyle.SetEndErrorSize(5)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

# OLD 2016 input
# sstr = [
# ('p_{T}(#gamma)'                         , 1.118, 0.049, 0.031),
# ('N_{j}, N_{b}'                          , 1.114, 0.051, 0.031),
# ('|#eta(#gamma)|'                        , 1.155, 0.059, 0.032),
# ('#Delta(#gamma,l)'                      , 1.085, 0.053, 0.030),
# ('|#Delta#eta(ll)|'                      , 1.063, 0.054, 0.031),
# ('#Delta#phi(ll)'                        , 1.129, 0.058, 0.031),
# ('p_{T}(ll)'                             , 1.139, 0.053, 0.031),
# ('#scale[0.8]{p_{T}(l1)+p_{T}(l2)}'      , 1.198, 0.059, 0.032),
# ('p_{T}(j1)'                             , 1.107, 0.053, 0.030),
# ('#DeltaR(l, j)'                         , 1.127, 0.054, 0.030),
# ('#DeltaR(#gamma, b)'                    , 1.134, 0.055, 0.031),
# ('#DeltaR(#gamma, l1)'                   , 1.095, 0.061, 0.030),
# ('#DeltaR(#gamma, l2)'                   , 1.103, 0.062, 0.030),
# ]

# RunII "END" input
sstr = [
('p_{T}(#gamma)'                         , 1.132, 0.041, 0.016),
('N_{j}, N_{b}'                          , 1.168, 0.042, 0.017),
('|#eta(#gamma)|'                        , 1.142, 0.040, 0.016),
('#Delta(#gamma,l)'                      , 1.089, 0.042, 0.016),
('|#Delta#eta(ll)|'                      , 1.122, 0.040, 0.016),
('#Delta#phi(ll)'                        , 1.105, 0.041, 0.016),
('p_{T}(ll)'                             , 1.181, 0.042, 0.017),
('#scale[0.8]{p_{T}(l1)+p_{T}(l2)}'      , 1.186, 0.042, 0.017),
('p_{T}(j1)'                             , 1.146, 0.039, 0.016),
('#DeltaR(l, j)'                         , 1.131, 0.040, 0.016),
('#DeltaR(#gamma, b)'                    , 1.156, 0.041, 0.017),
('#DeltaR(#gamma, l1)'                   , 1.114, 0.041, 0.016),
('#DeltaR(#gamma, l2)'                   , 1.134, 0.040, 0.016),
]

# phPtll                    1.118  49 31
# signalRegionsZoomCapll    1.114  51 31
# phAbsEtall                1.155  59 32
# phLepDeltaRll             1.085  53 30
# ll_absDeltaEtall          1.063  54 31
# ll_deltaPhill             1.129  58 31
# Z_ptll                    1.139  53 31
# l1l2_ptsumll              1.198  59 32
# jetPtll                   1.107  53 30
# jetLepDeltaRll            1.127  54 30
# phBJetDeltaRll            1.134  55 31
# phLep2DeltaRll            1.095  61 30
# phLep1DeltaRll            1.103  62 30

nfits = len(sstr)
# avg = sum([item[1] for item in sstr])/nfits

hist = ROOT.TH1D('stat', 'stat', nfits, 0, nfits)
histstat = ROOT.TH1D('stat', 'stat', nfits, 0, nfits)

labels = []
for i, ss in enumerate(sstr):
  hist.GetXaxis().SetBinLabel(i+1, ss[0])
  hist.SetBinContent(i+1, ss[1])
  histstat.SetBinContent(i+1, ss[1])
  hist.SetBinError(i+1,   (ss[2]**2+ss[3]**2)**0.5)
  histstat.SetBinError(i+1,   ss[3])
  texl = ROOT.TLatex(i+0.3,0.85,'r=' + str(ss[1]))
  texl.SetTextSize(0.03)
  labels.append(texl)

c = ROOT.TCanvas("c", "c", 1500, 750)

hist.GetYaxis().SetRangeUser(0.8, 1.35)
hist.GetYaxis().SetTitle('Signal strength r')
hist.GetXaxis().SetTitle('Fitted distribution')
hist.GetXaxis().SetLabelSize(0.05)
hist.GetXaxis().SetTitleOffset(1.45)
hist.SetTitle('')
hist.SetLineWidth(3)
histstat.SetLineWidth(3)
# hist.Draw('E1 X0')
hist.SetMarkerStyle(21)
hist.SetMarkerSize(2)
hist.Draw('P E1 X0')
histstat.Draw('same E1 X0')
band = ROOT.TBox(0., sstr[0][1]-(sstr[0][2]**2.+sstr[0][3]**2.)**0.5, nfits, sstr[0][1]+(sstr[0][2]**2.+sstr[0][3]**2.)**0.5)
band.SetFillColorAlpha(ROOT.kBlue, 0.25)
bandstat = ROOT.TBox(0., sstr[0][1]-sstr[0][3], nfits, sstr[0][1]+sstr[0][3])
bandstat.SetFillColorAlpha(ROOT.kRed, 0.25)
band.Draw()
bandstat.Draw()
texStat = ROOT.TLatex(nfits+0.12,sstr[0][1]-0.008,"Stat.")
texStat.SetTextSize(0.03)
texStat.SetTextColor(ROOT.kRed)
texStat.Draw()
texTot = ROOT.TLatex(nfits+0.12,sstr[0][1]+sstr[0][2]-.012,"Total")
texTot.SetTextSize(0.03)
texTot.SetTextColor(ROOT.kBlue)
texTot.Draw()
for l in labels: l.Draw()
c.SaveAs('rComparison.pdf')
c.SaveAs('rComparison.png')

# rd, ru = 0.9, 1.1


# labels = 2*['1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b', '#geq3j,#geq3b']
# channels = ['ee', 'mumu']


# # systs = ['NPUp','NPDown','bTaglUp','bTaglDown','bTagbUp','bTagbDown']
# # sysSets =  [['phSF','NP','lSFEl'],['trigger','ephScale','pu'],['ephRes','JEC','pf'],['fsr','lSFMu','pvSF'],['bTagb','isr','JER']]
# # sysSets =  [['phSF','NP'],['lSFEl','trigger'],['ephScale','pu'],['ephRes','JEC'],['pf','fsr'],['lSFMu','pvSF'],['bTagb','isr'],['JER','bTagl']]
# sysSets =  [['phSF'],['NP'],['lSFEl'],['trigger'],['ephScale'],['pu'],['ephRes'],['JEC'],['pf'],['fsr'],['lSFMu'],['pvSF'],['bTagb'],['isr'],['JER'],['bTagl'],['lSFSy']]

# for sysSet in sysSets:
#   systs = []
#   for sys in sysSet:
#     systs.append(sys + 'Down')
#     systs.append(sys + 'Up')

#   colors = [ROOT.kRed + 2, ROOT.kRed-4, ROOT.kBlue + 2, ROOT.kBlue-4, ROOT.kGreen + 2, ROOT.kGreen-3]
#   path = '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-niceEstimDD-otravez-methoda/all/llg-mll20-signalRegionAB-offZ-llgNoZ-photonPt20/signalRegionsZoom.pkl'
#   pathB = '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-niceEstimDD-otravez/all/llg-mll20-signalRegionAB-offZ-llgNoZ-photonPt20/signalRegionsZoom.pkl'

#   stat = ROOT.TH1D('stat', 'stat', 12, 0, 12)
#   hists = {}
#   for sys in systs:
#     hists[sys] = ROOT.TH1D(sys, sys, 12, 0, 12)
#     hists[sys + 'B'] = ROOT.TH1D(sys, sys, 12, 0, 12)

#   for c, chan in enumerate (channels):
#     nominal, data = sumHists(path.replace('CHAN', chan), 'signalRegionsZoom')
#     nominalB, dataB = sumHists(path.replace('CHAN', chan), 'signalRegionsZoom')
#     for sys in systs:
#       sysHist, _ = sumHists(path.replace('CHAN', chan), 'signalRegionsZoom' + sys)
#       sysHistB, _ = sumHists(pathB.replace('CHAN', chan), 'signalRegionsZoom' + sys)
#       sysHist.Divide(nominal)
#       sysHistB.Divide(nominal)
#       for i in range(3, 10):
#         if sysHist.GetBinContent(i - 2) == 0:
#           hists[sys].SetBinContent(6*c + i - 2, 1.)        
#           hists[sys + 'B'].SetBinContent(6*c + i, 1.)        
#         else:
#           hists[sys].SetBinContent(6*c + i - 2, sysHist.GetBinContent(i))
#           hists[sys + 'B'].SetBinContent(6*c + i - 2, sysHistB.GetBinContent(i))

#   c1 = ROOT.TCanvas('c', 'c', 1600, 700)
#   for i, l in enumerate(labels):
#     stat.GetXaxis().SetBinLabel(i+1, l)
#   stat.GetYaxis().SetRangeUser(rd, ru)
#   stat.GetYaxis().SetTickLength(0.007)
#   stat.SetLineColor(ROOT.kBlack)
#   stat.SetTitle('')
#   # stat.Draw('E1')


#   for i, l in enumerate(labels):
#     hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)

#   # hists[systs[0]].GetYaxis().SetRangeUser(0.9, 1.1)


#   for s, sys in enumerate(systs):
#     hists[sys].SetLineColor(colors[s])
#     hists[sys].SetLineWidth(3)
#     hists[sys].GetYaxis().SetRangeUser(rd, ru)
#     hists[sys].SetTitle('')
#     hists[sys].Draw('SAME')
#     hists[sys + 'B'].SetLineColor(colors[s])
#     hists[sys + 'B'].SetLineWidth(3)
#     hists[sys + 'B'].SetLineStyle(2)
#     hists[sys + 'B'].Draw('SAME')



#   latex = ROOT.TLatex()
#   latex.SetTextSize(0.055);
#   latex.DrawLatex(0.25 ,rd+0.02,"#bf{ee}")
#   latex.DrawLatex(6.25 ,rd+0.02,"#bf{#mu#mu}")
#   # latex.DrawLatex(14.25,rd+0.02,"#bf{e#mu}")

#   l1 = ROOT.TLine(6.,rd,6.,ru*0.9)
#   l1.SetLineStyle(3)  
#   l1.SetLineWidth(2)
#   l1.Draw()
#   c1.SaveAs('systPlotsZGAB/' + sysSet[0] + 'zoom.png')
