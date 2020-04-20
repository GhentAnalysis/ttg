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

hists ={
            # '1j0b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet1-deepbtag0-offZ-llgOnZ-photonPt20/',
            '1j1b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet1-deepbtag1-offZ-llgOnZ-photonPt20/',
            '2j0b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet2-deepbtag0-offZ-llgOnZ-photonPt20/',
            '3j0b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet3-deepbtag0-offZ-llgOnZ-photonPt20/',
            '2j1b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet2-deepbtag1-offZ-llgOnZ-photonPt20/',
            # '2j2b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet2-deepbtag2-offZ-llgOnZ-photonPt20/',
            # '3j1b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet3-deepbtag1-offZ-llgOnZ-photonPt20/',
            # '3j2b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet3-deepbtag2-offZ-llgOnZ-photonPt20/',
            # '3j3b':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-njet3-deepbtag3-offZ-llgOnZ-photonPt20/',
}

def sumHists(picklePath, plot = 'signalRegions'):
  hists = pickle.load(open(picklePath))[plot]
  ZHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not ZHist:ZHist = hist
      else: ZHist.Add(hist)
  return ZHist


# for plot in ['photon_pt', 'photon_pt_large']:
for plot in ['photon_pt']:
  c1 = ROOT.TCanvas("c1", '', 1200, 800)
  legend = ROOT.TLegend(0.8,0.7,0.9,0.9)
  zghists = {}
  for i, sel in enumerate(hists.keys()):
    zghists[sel] = sumHists(hists[sel] + plot + '.pkl', plot)
    zghists[sel].Scale(1./zghists[sel].Integral())
    zghists[sel].GetYaxis().SetRangeUser(0., 0.4)
    zghists[sel].Draw('same')
    legend.AddEntry(zghists[sel],sel,"E")
    zghists[sel].SetLineColor(i+1)
    zghists[sel].SetLineWidth(2)
  zghists['1j1b'].SetTitle(" ")
  zghists['1j1b'].GetYaxis().SetTitle("(1/N) dN")
  zghists['1j1b'].GetXaxis().SetTitle(plot)
  legend.Draw()
  c1.SaveAs('zgnjet/' + plot + '.pdf')
  c1.SaveAs('zgnjet/' + plot + '.png')

canv1 = ROOT.TCanvas("c1", '' , 1200, 800)
legend = ROOT.TLegend(0.7,0.7,0.9,0.9)
sel1 = '2j0b'
sel2 = '1j1b'
u1= sumHists(hists[sel1] + 'photon_pt' + '.pkl', 'photon_pt')
u2= sumHists(hists[sel2] + 'photon_pt' + '.pkl', 'photon_pt')
c1 = u1.Clone()
u1.GetYaxis().SetRangeUser(0., 0.05)
u1.Add(u2)
u1.Scale(1./u1.Integral())
u1.SetLineColor(ROOT.kRed)
u1.SetLineWidth(2)
u1.Draw('')
c1.Add(u2, 0.8)
c1.Scale(1./c1.Integral())
c1.SetLineColor(ROOT.kBlue)
c1.SetLineWidth(2)
c1.GetYaxis().SetTitle("(1/N) dN")
c1.GetXaxis().SetTitle('photon_pt')
u1.SetTitle(" ")
c1.Draw('same')
legend.AddEntry(u1, sel1 + ' + ' + sel2,"E")
legend.AddEntry(c1, sel1 + ' + 0.8 * ' + sel2,"E")
legend.Draw()
canv1.SaveAs('zgnjet/scaleone.png')
