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


def getRatioCanvas(name):
  xWidth, yWidth, yRatioWidth = 1000, 850, 300
  yWidth           += yRatioWidth
  bottomMargin      = yWidth/float(yRatioWidth)*ROOT.gStyle.GetPadBottomMargin()
  yBorder           = yRatioWidth/float(yWidth)

  canvas = ROOT.TCanvas(name, name, xWidth, yWidth)
  canvas.Divide(1, 2, 0, 0)
  canvas.topPad = getPad(canvas, 1)
  canvas.topPad.SetBottomMargin(0)
  canvas.topPad.SetPad(canvas.topPad.GetX1(), yBorder, canvas.topPad.GetX2(), canvas.topPad.GetY2())
  canvas.bottomPad = getPad(canvas, 2)
  canvas.bottomPad.SetTopMargin(0)
  canvas.bottomPad.SetBottomMargin(bottomMargin)
  canvas.bottomPad.SetPad(canvas.bottomPad.GetX1(), canvas.bottomPad.GetY1(), canvas.bottomPad.GetX2(), yBorder)
  return canvas



offZuncorHists ={'2016': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgestCheck-noZgCorr/all/llg-mll20-offZ-llgNoZ-photonPt20/',
                 '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgestCheck-noZgCorr/all/llg-mll20-offZ-llgNoZ-photonPt20/',
                 '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgestCheck-noZgCorr/all/llg-mll20-offZ-llgNoZ-photonPt20/'
}

offZcorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgNoZ-photonPt20/',
               '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgNoZ-photonPt20/',
               '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgNoZ-photonPt20/'
}



onZuncorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest-noZgCorr/all/llg-mll20-offZ-llgOnZ-photonPt20/',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest-noZgCorr/all/llg-mll20-offZ-llgOnZ-photonPt20/',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest-noZgCorr/all/llg-mll20-offZ-llgOnZ-photonPt20/'
}

onZcorHists ={'2016':  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgOnZ-photonPt20/',
            '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgOnZ-photonPt20/',
            '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgestCheck/all/llg-mll20-offZ-llgOnZ-photonPt20/'
}



def getPad(canvas, number):
  pad = canvas.cd(number)
  pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin()+0.05)
  pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin()-0.05)
  pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
  pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
  return pad


def sumHists(picklePath, plot = 'signalRegions'):
  hists = pickle.load(open(picklePath))[plot]
  ZHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not ZHist:ZHist = hist
      else: ZHist.Add(hist)
  return ZHist

labels = {
          'unfReco_phPt' :          'p_{T}(#gamma) (GeV)',     
          'unfReco_phLepDeltaR' :   '#DeltaR(#gamma, l)',  
          'unfReco_ll_deltaPhi' :   '#Delta#phi(ll)',            
          'unfReco_jetLepDeltaR' :  '#DeltaR(l, j)',             
          'unfReco_jetPt' :         'p_{T}(j1) (GeV)',          
          'unfReco_ll_absDeltaEta' :'|#Delta#eta(ll)|',      
          'unfReco_phBJetDeltaR' :  '#DeltaR(#gamma, b)',     
          'unfReco_phAbsEta' :      '|#eta|(#gamma)',       
          'unfReco_phLep1DeltaR' :  '#DeltaR(#gamma, l1)',     
          'unfReco_phLep2DeltaR' :  '#DeltaR(#gamma, l2)',     
          'unfReco_Z_pt' :          'p_{T}(ll) (GeV)', 
          'unfReco_l1l2_ptsum' :    'p_{T}(l1)+p_{T}(l2) (GeV)',
          'signalRegionsZoom' :     'N_j / N_b',
          'signalRegions'     :     'N_j / N_b',
          'photon_pt' :          'p_{T}(#gamma) (GeV)'
          }

distList = [
  'unfReco_jetLepDeltaR',
  'unfReco_jetPt',
  'unfReco_ll_absDeltaEta',
  'unfReco_ll_deltaPhi',
  'unfReco_phAbsEta',
  'unfReco_phBJetDeltaR',
  'unfReco_phLepDeltaR',
  'unfReco_phPt',
  'unfReco_phLep1DeltaR',
  'unfReco_phLep2DeltaR',
  'unfReco_Z_pt',
  'unfReco_l1l2_ptsum',
  'signalRegionsZoom',
  'signalRegions',
  'photon_pt'
  ]

# for plot in ['photon_pt_large', 'photon_pt', 'photon_eta_large', 'photon_eta_large', 'signalRegionsZoom']:

for year in ['2016', '2017', '2018']:
  for plot in distList:
    if plot == 'unfReco_jetPt':
    # if True:
      onZcor    = sumHists(onZcorHists[year].replace('mll20', 'mll20-njet1p') + plot + '.pkl', plot)
      onZuncor  = sumHists(onZuncorHists[year].replace('mll20', 'mll20-njet1p') + plot + '.pkl', plot)
      offZcor   = sumHists(offZcorHists[year].replace('mll20', 'mll20-njet1p') + plot + '.pkl', plot)
      offZuncor = sumHists(offZuncorHists[year].replace('mll20', 'mll20-njet1p') + plot + '.pkl', plot)
    else:
      onZcor    = sumHists(onZcorHists[year] + plot + '.pkl', plot)
      onZuncor  = sumHists(onZuncorHists[year] + plot + '.pkl', plot)
      offZcor   = sumHists(offZcorHists[year] + plot + '.pkl', plot)
      offZuncor = sumHists(offZuncorHists[year] + plot + '.pkl', plot)
    onZcor.Scale(1./onZcor.Integral())
    onZuncor.Scale(1./onZuncor.Integral())
    offZcor.Scale(1./offZcor.Integral())
    offZuncor.Scale(1./offZuncor.Integral())
    # if plot == 'signalRegions':
    #   labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
    #   for i, l in enumerate(labels):
    #     cor16.GetXaxis().SetBinLabel(i+1, l)

    c1 = getRatioCanvas(year+plot)
  # TOP PAD
    c1.topPad.cd()



    # c1 = ROOT.TCanvas("c1")
    onZuncor.SetLineColor(861)
    onZcor.SetLineColor(602)   
    onZcor.SetMarkerStyle(8)
    offZuncor.SetLineColor(632)
    offZcor.SetLineColor(633)    
    offZcor.SetMarkerStyle(8)

    onZuncor.SetLineWidth(2)
    onZcor.SetLineWidth(2)
    offZuncor.SetLineWidth(2)
    offZcor.SetLineWidth(2)

    onZuncor.Draw()
    onZcor.Draw('same')
    offZuncor.Draw('same')
    offZcor.Draw('same')
    onZuncor.SetTitle(" ")
    onZuncor.GetYaxis().SetTitle("(1/N) dN")
    # cor16.GetYaxis().SetRangeUser(0., 2.5)
    legend = ROOT.TLegend(0.3,0.78,0.8,0.89)
    legend.SetNColumns(2)
    legend.AddEntry(onZuncor, "on-Z uncorrected", 'E')
    legend.AddEntry(onZcor, "on-Z corrected", 'E')
    legend.AddEntry(offZuncor, "off-Z uncorrected", 'E')
    legend.AddEntry(offZcor, "off-Z corrected", 'E')
    legend.SetBorderSize(0)
    legend.Draw()

  # RATIO PAD
    c1.bottomPad.cd()

    offRat = offZcor.Clone()
    onRat = onZcor.Clone()
    offRat.Divide(offZuncor)
    onRat.Divide(onZuncor)
    offRat.GetYaxis().SetRangeUser(0.5, 1.5)

    offRat.GetXaxis().SetTitle(plot)
    offRat.GetYaxis().SetTitle('corr. / uncorr.')
    offRat.SetTitle('')
    offRat.GetXaxis().SetLabelSize(0.14)
    offRat.GetXaxis().SetTitleSize(0.14)
    offRat.GetXaxis().SetTitleOffset(1.2)
    offRat.GetYaxis().SetTitleSize(0.11)
    offRat.GetYaxis().SetTitleOffset(0.4)
    offRat.GetYaxis().SetNdivisions(3,5,0)
    offRat.GetYaxis().SetLabelSize(0.1)

    offRat.GetXaxis().SetTitle(labels[plot])
    offRat.Draw('hist')
    onRat.Draw('hist same')

    l1 = ROOT.TLine(offRat.GetXaxis().GetXmin(),1,offRat.GetXaxis().GetXmax(),1)
    l1.Draw()

    c1.SaveAs('ZgCorrPlots/onOff-' + year + '-' + plot + '.pdf')
    c1.SaveAs('ZgCorrPlots/onOff-' + year + '-' + plot + '.png')