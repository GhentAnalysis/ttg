#
# compare Zg corrections between years
#
# NOTE currently both Zg genuine and nonprompt will be scaled/corrected, shouldn't matter much but this seems most correct

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle
import time
import ROOT
ROOT.TH1.SetDefaultSumw2()
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

uncorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/',
             '2017':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/',
             '2018':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/'
}

corHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-ZgestCheck/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/',
           '2017':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-ZgestCheck/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/',
           '2018':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-ZgestCheck/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/'
}


def sumHists(picklePath, plot, chan):
  hists = pickle.load(open(picklePath.replace('CHAN', chan)))[plot]
  ZHist = None
  dataHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not ZHist:ZHist = hist
      else: ZHist.Add(hist)
    elif 'data' in name:
      if not dataHist:dataHist = hist
      else: dataHist.Add(hist)
  return (ZHist, dataHist)



for plot in ['signalRegions', 'signalRegionsZoom', 'njets', 'nbtag']:
  for year in ['2016', '2017', '2018']:
    eecor, eedata = sumHists(corHists[year] + plot + '.pkl', plot, 'ee')
    eecor.Divide(sumHists(uncorHists[year] + plot + '.pkl', plot, 'ee')[0])
    if plot == 'signalRegions':
      labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
      for i, l in enumerate(labels):
        eecor.GetXaxis().SetBinLabel(i+1, l)
        eedata.GetXaxis().SetBinLabel(i+1, l)
    if plot == 'signalRegionsZoom':
      labels = ['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
      for i, l in enumerate(labels):
        eecor.GetXaxis().SetBinLabel(i+1, l)
        eedata.GetXaxis().SetBinLabel(i+1, l)

    mmcor, mmdata = sumHists(corHists[year] + plot + '.pkl', plot, 'mumu')
    mmcor.Divide(sumHists(uncorHists[year] + plot + '.pkl', plot, 'mumu')[0])
    if plot == 'signalRegions':
      labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
      for i, l in enumerate(labels):
        mmcor.GetXaxis().SetBinLabel(i+1, l)
        mmdata.GetXaxis().SetBinLabel(i+1, l)
    if plot == 'signalRegionsZoom':
      labels = ['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
      for i, l in enumerate(labels):
        mmcor.GetXaxis().SetBinLabel(i+1, l)
        mmdata.GetXaxis().SetBinLabel(i+1, l)

    c1 = ROOT.TCanvas("c1", "c1", 1200, 800)
    eecor.SetLineColor(ROOT.kBlue)
    mmcor.SetLineColor(ROOT.kRed)
    eecor.Draw()
    mmcor.Draw('same')
    eecor.SetTitle(" ")
    eecor.GetYaxis().SetTitle("corrected / uncorrected")
    eecor.GetXaxis().SetTitle(plot)
    eecor.GetYaxis().SetRangeUser(0., 2.5)
    legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
    legend.AddEntry(eecor,"ee correction","E")
    legend.AddEntry(mmcor,"mu mu correction","E")
    legend.Draw()
    c1.SaveAs('ZGcorreevsmumu/' + year + plot + '.pdf')
    c1.SaveAs('ZGcorreevsmumu/' + year + plot + '.png')

    c1 = ROOT.TCanvas("c1", "c1", 1200, 800)
    eedata.SetLineColor(ROOT.kBlue)
    mmdata.SetLineColor(ROOT.kRed)
    eedata.Scale(1./eedata.Integral())
    mmdata.Scale(1./mmdata.Integral())
    eedata.Draw()
    mmdata.Draw('same')
    eedata.SetTitle(" ")
    eedata.GetYaxis().SetTitle("(1/N) dN/dx'")
    eedata.GetXaxis().SetTitle(plot)
    eedata.GetYaxis().SetRangeUser(0., 0.2)
    legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
    legend.AddEntry(eedata,"ee data","E")
    legend.AddEntry(mmdata,"mu mu data","E")
    legend.Draw()
    c1.SaveAs('ZGcorreevsmumu/data' + year + plot + '.pdf')
    c1.SaveAs('ZGcorreevsmumu/data' + year + plot + '.png')
