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


offZuncorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-offZ-llgNoZ-photonPt20/',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest/all/llg-mll40-offZ-llgNoZ-photonPt20/',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/all/llg-mll40-offZ-llgNoZ-photonPt20/'
}

offZcorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgNoZ-photonPt20/',
            '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgNoZ-photonPt20/',
            '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgNoZ-photonPt20/'
}

onZuncorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/'
}

onZcorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgOnZ-photonPt20/',
            '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgOnZ-photonPt20/',
            '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-ZgestCheck/all/llg-mll40-offZ-llgOnZ-photonPt20/'
}


def sumHists(picklePath, plot = 'signalRegions'):
  hists = pickle.load(open(picklePath))[plot]
  ZHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not ZHist:ZHist = hist
      else: ZHist.Add(hist)
  return ZHist


for year in ['2016', '2017', '2018']:
  for plot in ['photon_pt_large', 'photon_pt', 'photon_eta_large', 'photon_eta_large']:
    onZcor    = sumHists(onZcorHists[year] + plot + '.pkl', plot)
    onZuncor  = sumHists(onZuncorHists[year] + plot + '.pkl', plot)
    offZcor   = sumHists(offZcorHists[year] + plot + '.pkl', plot)
    offZuncor = sumHists(offZuncorHists[year] + plot + '.pkl', plot)
    onZcor.Scale(1./onZcor.Integral())
    onZuncor.Scale(1./onZuncor.Integral())
    offZcor.Scale(1./offZcor.Integral())
    offZuncor.Scale(1./offZuncor.Integral())
    if plot == 'signalRegions':
      labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
      for i, l in enumerate(labels):
        cor16.GetXaxis().SetBinLabel(i+1, l)
    c1 = ROOT.TCanvas("c1")
    onZuncor.SetLineColor(861)
    onZcor.SetLineColor(602)   
    onZcor.SetMarkerStyle(8)
    offZuncor.SetLineColor(632)
    offZcor.SetLineColor(633)    
    offZcor.SetMarkerStyle(8)

    onZuncor.Draw()
    onZcor.Draw('same')
    offZuncor.Draw('same')
    offZcor.Draw('same')
    onZuncor.SetTitle(" ")
    onZuncor.GetXaxis().SetTitle(plot)
    onZuncor.GetYaxis().SetTitle("(1/N) dN")
    # cor16.GetYaxis().SetRangeUser(0., 2.5)
    legend = ROOT.TLegend(0.8,0.75,0.9,0.9)
    legend.AddEntry(onZuncor, "onZuncor", 'E')
    legend.AddEntry(onZcor, "onZcor", 'E')
    legend.AddEntry(offZuncor, "offZuncor", 'E')
    legend.AddEntry(offZcor, "offZcor", 'E')
    legend.Draw()
    c1.SaveAs('ZgCorrPlots/onOff-' + year + '-' + plot + '.pdf')
    c1.SaveAs('ZgCorrPlots/onOff-' + year + '-' + plot + '.png')
