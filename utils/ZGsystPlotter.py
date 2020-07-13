#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
from ttg.plots.ZgWeight import ZgWeight
import pickle
import time
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.055)
ROOT.gStyle.SetPadLeftMargin(0.065)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  ZGHist = None
  dataHist = None
  for name, hist in hists.iteritems():
    if 'data' in name:
      if not dataHist: dataHist = hist
      else: dataHist.Add(hist)
    elif 'ZG' in name:
      if not ZGHist: ZGHist = hist
      else: ZGHist.Add(hist)
    else: continue
  return (ZGHist, dataHist)


rd, ru = 0.5, 1.55
# rd, ru = 0.8, 1.25


labels = 3*['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b']
channels = ['ee', 'mumu', 'emu']


# systs = ['NPUp','NPDown','bTaglUp','bTaglDown','bTagbUp','bTagbDown']
# sysSets =  [['phSF','NP','lSFEl'],['trigger','ephScale','pu'],['ephRes','JEC','pf'],['fsr','lSFMu','pvSF'],['bTagb','isr','JER']]
# sysSets =  [['phSF','NP'],['lSFEl','trigger'],['ephScale','pu'],['ephRes','JEC'],['pf','fsr'],['lSFMu','pvSF'],['bTagb','isr'],['JER','bTagl']]
sysSets =  [['phSF'],['NP'],['lSFEl'],['trigger'],['ephScale'],['pu'],['ephRes'],['JEC'],['pf'],['fsr'],['lSFMu'],['pvSF'],['bTagb'],['isr'],['JER'],['bTagl']]

for sysSet in sysSets:
  systs = []
  for sys in sysSet:
    systs.append(sys + 'Down')
    systs.append(sys + 'Up')

  colors = [ROOT.kRed + 2, ROOT.kRed-4, ROOT.kBlue + 2, ROOT.kBlue-4, ROOT.kGreen + 2, ROOT.kGreen-3]
  path = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-defaultEstimDD-AP-MA/CHAN/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegionsZoomAlt.pkl'

  stat = ROOT.TH1F('stat', 'stat', 21, 0, 21)
  hists = {}
  for sys in systs:
    hists[sys] = ROOT.TH1F(sys, sys, 21, 0, 21)
    hists[sys + 'corr'] = ROOT.TH1F(sys, sys, 21, 0, 21)

  for c, chan in enumerate (channels):
    nominal, data = sumHists(path.replace('CHAN', chan), 'signalRegionsZoomAlt')
    zgweightnom = ZgWeight('2017', '')
    for i in range(1, 8):
      try:
        stat.SetBinError(7*c + i, nominal.GetBinError(i)/nominal.GetBinContent(i))
        stat.SetBinContent(7*c + i, 1.)
      except:
        stat.SetBinError(7*c + i, 0.)
        stat.SetBinContent(7*c + i, 1.)
    for sys in systs:
      sysHist, _ = sumHists(path.replace('CHAN', chan), 'signalRegionsZoomAlt' + sys)
      sysHist.Divide(nominal)
      zgweight = ZgWeight('2017', sys)
      for i in range(1, 8):
        if sysHist.GetBinContent(i) == 0:
          hists[sys].SetBinContent(7*c + i, 1.)        
        else:
          hists[sys].SetBinContent(7*c + i, sysHist.GetBinContent(i))
        # TODO deal with last 2 bins being merged   ignore for now
        hists[sys + 'corr'].SetBinContent(7*c + i, zgweight.getWeightTest(i, c)/max((zgweightnom.getWeightTest(i, c)), 0.00000001))

  c1 = ROOT.TCanvas('c', 'c', 1600, 700)
  for i, l in enumerate(labels):
    stat.GetXaxis().SetBinLabel(i+1, l)
  stat.GetYaxis().SetRangeUser(rd, ru)
  stat.GetYaxis().SetTickLength(0.007)
  stat.SetLineColor(ROOT.kBlack)
  stat.SetTitle('')
  stat.Draw('E1')


  for i, l in enumerate(labels):
    hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)

  # hists[systs[0]].GetYaxis().SetRangeUser(0.9, 1.1)


  legend = ROOT.TLegend(0.15,0.91,0.85,0.96)
  for s, sys in enumerate(systs):
    hists[sys].SetLineColor(colors[s])
    hists[sys].SetLineWidth(3)
    hists[sys].Draw('SAME')
    legend.AddEntry(hists[sys], sys + '    ', 'L')
    hists[sys + 'corr'].SetLineColor(colors[s])
    hists[sys + 'corr'].SetLineWidth(3)
    hists[sys + 'corr'].SetLineStyle(2)
    hists[sys + 'corr'].Draw('SAME')
    legend.AddEntry(hists[sys + 'corr'], sys + ' Zg corr change   ', 'L')

  legend.SetNColumns(6)
  legend.SetFillStyle(0)
  legend.SetLineStyle(0)
  legend.SetBorderSize(0)
  legend.Draw()


  latex = ROOT.TLatex()
  latex.SetTextSize(0.055);
  latex.DrawLatex(0.25 ,rd+0.02,"#bf{ee}")
  latex.DrawLatex(7.25 ,rd+0.02,"#bf{#mu#mu}")
  latex.DrawLatex(14.25,rd+0.02,"#bf{e#mu}")

  l1 = ROOT.TLine(7.,rd,7.,ru*0.9)
  l1.SetLineStyle(3)  
  l1.SetLineWidth(2)
  l1.Draw()
  l2 = ROOT.TLine(14.,rd,14.,ru*0.9)
  l2.SetLineStyle(3)  
  l2.SetLineWidth(2)
  l2.Draw()
  c1.SaveAs('systPlotsZG/' + sysSet[0] + '.png')
