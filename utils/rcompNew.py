#
# nonprompt photon background estimation weights
#

import numpy
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
# ROOT.gStyle.SetPadRightMargin(0.055)
# ROOT.gStyle.SetPadLeftMargin(0.065)
ROOT.gStyle.SetPadBottomMargin(0.12)
ROOT.gStyle.SetPadTopMargin(0.03)
ROOT.gStyle.SetEndErrorSize(5)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


sstr = [
('N_{j}, N_{b}'      , 0.983, 0.068, 0.027),
('p_{T}(#gamma)'     , 0.992, 0.066, 0.027),
('|#eta(#gamma)|'    , 1.044, 0.072, 0.027),
('#Delta(#gamma,l)'  , 0.960, 0.070, 0.027),
('|#Delta#eta(ll)|'  , 1.022, 0.071, 0.029),
('#Delta#phi(ll)'    , 1.031, 0.078, 0.027),
]

nfits = len(sstr)
# avg = sum([item[1] for item in sstr])/nfits

hist = ROOT.TH1F('stat', 'stat', nfits, 0, nfits)
histstat = ROOT.TH1F('stat', 'stat', nfits, 0, nfits)

labels = []
for i, ss in enumerate(sstr):
  hist.GetXaxis().SetBinLabel(i+1, ss[0])
  hist.SetBinContent(i+1, ss[1])
  histstat.SetBinContent(i+1, ss[1])
  hist.SetBinError(i+1,   ss[2])
  histstat.SetBinError(i+1,   ss[3])
  texl = ROOT.TLatex(i+0.3,0.75,'r=' + str(ss[1]))
  texl.SetTextSize(0.03)
  labels.append(texl)

c = ROOT.TCanvas("c", "c", 1000, 750)

hist.GetYaxis().SetRangeUser(0, 1.2)
hist.GetYaxis().SetTitle('Signal strength r')
hist.GetXaxis().SetTitle('Fitted distribution')
hist.GetXaxis().SetLabelSize(0.05)
hist.GetXaxis().SetTitleOffset(1.45)
hist.SetTitle('')
hist.SetLineWidth(2)
# hist.Draw('E1 X0')
hist.SetMarkerStyle(21)
hist.Draw('P E1 X0')
histstat.Draw('same E1 X0')
band = ROOT.TBox(0., sstr[0][1]-(sstr[0][2]**2.+sstr[0][3]**2.)**0.5, nfits, sstr[0][1]+(sstr[0][2]**2.+sstr[0][3]**2.)**0.5)
band.SetFillColorAlpha(ROOT.kBlue, 0.25)
bandstat = ROOT.TBox(0., sstr[0][1]-sstr[0][3], nfits, sstr[0][1]+sstr[0][3])
bandstat.SetFillColorAlpha(ROOT.kRed, 0.25)
band.Draw()
bandstat.Draw()
texStat = ROOT.TLatex(nfits+0.12,sstr[0][1]-.02,"Stat.")
texStat.SetTextSize(0.03)
texStat.SetTextColor(ROOT.kRed)
texStat.Draw()
texTot = ROOT.TLatex(nfits+0.12,sstr[0][1]+sstr[0][2]-.035,"Total")
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

#   stat = ROOT.TH1F('stat', 'stat', 12, 0, 12)
#   hists = {}
#   for sys in systs:
#     hists[sys] = ROOT.TH1F(sys, sys, 12, 0, 12)
#     hists[sys + 'B'] = ROOT.TH1F(sys, sys, 12, 0, 12)

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
