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

uncorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016PreMar30/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreMar30/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018PreMar30/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/'
}

corHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016PreMar30/phoCBfull-ZgEstCheckNew/all/llg-mll40-offZ-llgOnZ-photonPt20/',
            '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreMar30/phoCBfull-ZgEstCheckNew/all/llg-mll40-offZ-llgOnZ-photonPt20/',
            '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018PreMar30/phoCBfull-ZgEstCheckNew/all/llg-mll40-offZ-llgOnZ-photonPt20/'
}


def sumHists(picklePath, plot = 'signalRegions'):
  hists = pickle.load(open(picklePath))[plot]
  ZHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not ZHist:ZHist = hist
      else: ZHist.Add(hist)
  return ZHist



for plot in ['signalRegions', 'njets', 'nbtag']:
  cor16 = sumHists(corHists['2016'] + plot + '.pkl', plot)
  cor17 = sumHists(corHists['2017'] + plot + '.pkl', plot)
  cor18 = sumHists(corHists['2018'] + plot + '.pkl', plot)
  cor16.Divide(sumHists(uncorHists['2016'] + plot + '.pkl', plot))
  cor17.Divide(sumHists(uncorHists['2017'] + plot + '.pkl', plot))
  cor18.Divide(sumHists(uncorHists['2018'] + plot + '.pkl', plot))
  if plot == 'signalRegions':
    labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
    for i, l in enumerate(labels):
      cor16.GetXaxis().SetBinLabel(i+1, l)
  c1 = ROOT.TCanvas("c1")
  cor16.SetLineColor(861)
  cor17.SetLineColor(602)
  cor18.SetLineColor(632)
  cor16.Draw()
  cor17.Draw('same')
  cor18.Draw('same')
  cor16.SetTitle(" ")
  cor16.GetYaxis().SetTitle("corrected / uncorrected")
  cor16.GetXaxis().SetTitle(plot)
  cor16.GetYaxis().SetRangeUser(0., 2.5)
  legend = ROOT.TLegend(0.8,0.75,0.9,0.9)
  legend.AddEntry(cor16,"2016","E")
  legend.AddEntry(cor17,"2017","E")
  legend.AddEntry(cor18,"2018","E")
  legend.Draw()
  c1.SaveAs('ZgCorrPlots/' + plot + '.pdf')
  c1.SaveAs('ZgCorrPlots/' + plot + '.png')

