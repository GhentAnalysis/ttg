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
ROOT.gStyle.SetPadRightMargin(0.055)
ROOT.gStyle.SetPadLeftMargin(0.065)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  mcHist = None
  dataHist = None
  for name, hist in hists.iteritems():
    if 'data' in name:
      if not dataHist: dataHist = hist
      else: dataHist.Add(hist)
    else:
      if not mcHist: mcHist = hist
      else: mcHist.Add(hist)
  return (mcHist, dataHist)


# TODO switch to alternative plot where last two bins are merged
# labels = 3*['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b']
channels = ['ee', 'mumu', 'emu']



# systs = ['NPUp','NPDown','bTaglUp','bTaglDown','bTagbUp','bTagbDown']
sysSets =  [['lSFSy']]
# sysSets =  [['phSF','NP','lSFEl'],['trigger','ephScale','pu'],['ephRes','JEC','pf'],['fsr','lSFMu','pvSF'],['bTagb','isr','JER']]

for sysSet in sysSets:
  systs = []
  for sys in sysSet:
    systs.append(sys + 'Down')
    systs.append(sys + 'Up')

  colors = [ROOT.kRed + 2, ROOT.kRed-4, ROOT.kBlue + 2, ROOT.kBlue-4, ROOT.kGreen + 2, ROOT.kGreen-3]
  path = '/storage_mnt/storage/user/gmestdac/public_html/ttG//2016/phoCBfull-niceEstimDD/all-sys/llg-mll20-signalRegion-offZ-llgNoZ-photonPt20/l2_pt.pkl'

  stat = ROOT.TH1F('stat', 'stat', 20, 15, 215)
  hists = {}
  for sys in systs:
    hists[sys] = ROOT.TH1F(sys, sys,20, 15, 215)

  # for c, chan in enumerate (channels):
  #   nominal, data = sumHists(path.replace('CHAN', chan), 'signalRegionsZoomAlt')
  #   for i in range(1, 8):
  #     stat.SetBinError(7*c + i, data.GetBinError(i)/data.GetBinContent(i))
  #     stat.SetBinContent(7*c + i, 1.)
  #   for sys in systs:
  #     sysHist, _ = sumHists(path.replace('CHAN', chan), 'signalRegionsZoomAlt' + sys)
  #     sysHist.Divide(nominal)
  #     for i in range(1, 8):
  #       hists[sys].SetBinContent(7*c + i, sysHist.GetBinContent(i))

  c1 = ROOT.TCanvas('c', 'c', 1600, 700)
  # for i, l in enumerate(labels):
  #   stat.GetXaxis().SetBinLabel(i+1, l)
  stat.GetYaxis().SetRangeUser(0.8, 1.25)
  stat.GetYaxis().SetTickLength(0.007)
  stat.SetLineColor(ROOT.kBlack)
  stat.SetTitle('')
  stat.Draw('E1')


  # for i, l in enumerate(labels):
  #   hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)

  # hists[systs[0]].GetYaxis().SetRangeUser(0.9, 1.1)


  legend = ROOT.TLegend(0.15,0.82,0.85,0.9)
  for s, sys in enumerate(systs):
    hists[sys].SetLineColor(colors[s])
    hists[sys].SetLineWidth(3)
    hists[sys].Draw('SAME')
    legend.AddEntry(hists[sys], sys, 'L')
  legend.SetNColumns(6)
  legend.SetFillStyle(0)
  legend.SetLineStyle(0)
  legend.SetBorderSize(0)
  legend.Draw()


  latex = ROOT.TLatex()
  latex.SetTextSize(0.055);
  latex.DrawLatex(0.25 ,0.82,"#bf{ee}")
  latex.DrawLatex(7.25 ,0.82,"#bf{#mu#mu}")
  latex.DrawLatex(14.25,0.82,"#bf{e#mu}")

  l1 = ROOT.TLine(7.,0.8,7.,1.2)
  l1.SetLineStyle(3)
  l1.Draw()
  l2 = ROOT.TLine(14.,0.8,14.,1.2)
  l2.SetLineStyle(3)
  l2.Draw()
  # c1.SaveAs('sysPlotter/' + sysSet[0] + '.pdf')
  c1.SaveAs('sysPlotternew/' + sysSet[0] + '.png')
