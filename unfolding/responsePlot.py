#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
# argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
args = argParser.parse_args()

import ROOT
import pdb
from ttg.tools.style import drawTex


from array import array



ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(95)

ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gStyle.SetPadTopMargin(0.07)
ROOT.gStyle.SetPadLeftMargin(0.15)
ROOT.gStyle.SetPadRightMargin(0.18)

# from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
# from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
# from ttg.tools.style import drawLumi, setDefault, drawTex
# from ttg.tools.helpers import plotDir, getObjFromFile, lumiScales, lumiScalesRounded
# import copy
import pickle
import numpy
# import uuid


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


red = array('d', [1.0,0.302])
green = array('d', [1.0,0.745])
blue = array('d', [1.0,0.933])
stops = array('d', [0.0,1.0])
ROOT.TColor.CreateGradientColorTable(2,stops,red,green,blue,25)

lumiunc = {'2016':0.012, '2017':0.023, '2018':0.025}

distList = [
  'unfReco_phLepDeltaR',
  'unfReco_jetLepDeltaR',
  'unfReco_jetPt',
  'unfReco_ll_absDeltaEta',
  'unfReco_ll_deltaPhi',
  'unfReco_phAbsEta',
  'unfReco_phBJetDeltaR',
  'unfReco_phPt',
  'unfReco_phLep1DeltaR',
  'unfReco_phLep2DeltaR',
  'unfReco_Z_pt',
  'unfReco_l1l2_ptsum'
  ]

  # 'unfReco_ll_cosTheta',

labels = {
          'unfReco_phPt' :            ('Reconstructed p_{T}(#gamma) [GeV]',       'Generated p_{T}(#gamma) [GeV]'        , 'd#sigma/dp_{T}(#gamma) [fb/GeV]'      , ' 1/#sigma d#sigma/dp_{T}(#gamma) [1/GeV]'         ),
          'unfReco_phLepDeltaR' :     ('Reconstructed min #DeltaR(#gamma, l)',    'Generated min #DeltaR(#gamma, l)'     , 'd#sigma/d#DeltaR(#gamma, l) [fb]'     , ' 1/#sigma d#sigma/d#DeltaR(#gamma, l)'            ),
          'unfReco_ll_deltaPhi' :     ('Reconstructed #Delta#phi(ll)',            'Generated #Delta#phi(ll)'             , 'd#sigma/d#Delta#phi(ll) [fb]'         , ' 1/#sigma d#sigma/d#Delta#phi(ll)'                ),
          'unfReco_jetLepDeltaR' :    ('Reconstructed min #DeltaR(l, j)',         'Generated min #DeltaR(l, j)'          , 'd#sigma/d#DeltaR(l, j) [fb]'          , ' 1/#sigma d#sigma/d#DeltaR(l, j)'                 ),
          'unfReco_jetPt' :           ('Reconstructed p_{T}(j1) [GeV]',           'Generated p_{T}(j1) [GeV]'            , 'd#sigma/dp_{T}(j1) [fb/GeV]'          , ' 1/#sigma d#sigma/dp_{T}(j1) [1/GeV]'             ),
          'unfReco_ll_absDeltaEta' :  ('Reconstructed |#Delta#eta(ll)|',          'Generated |#Delta#eta(ll)|'           , 'd#sigma/d|#Delta#eta(ll)| [fb]'       , ' 1/#sigma d#sigma/d|#Delta#eta(ll)|'              ),
          'unfReco_phBJetDeltaR' :    ('Reconstructed min #DeltaR(#gamma, b)',    'Generated min #DeltaR(#gamma, b)'     , 'd#sigma/d#DeltaR(#gamma, b) [fb]'     , ' 1/#sigma d#sigma/d#DeltaR(#gamma, b)'            ),
          'unfReco_phAbsEta' :        ('Reconstructed |#eta|(#gamma)',            'Generated |#eta|(#gamma)'             , 'd#sigma/d|#eta|(#gamma) [fb]'         , ' 1/#sigma d#sigma/d|#eta|(#gamma)'                ),
          'unfReco_phLep1DeltaR' :    ('Reconstructed #DeltaR(#gamma, l1)',       'Generated #DeltaR(#gamma, l1)'        , 'd#sigma/d#DeltaR(#gamma, l1) [fb]'    , ' 1/#sigma d#sigma/d#DeltaR(#gamma, l1)'           ),
          'unfReco_phLep2DeltaR' :    ('Reconstructed #DeltaR(#gamma, l2)',       'Generated #DeltaR(#gamma, l2)'        , 'd#sigma/d#DeltaR(#gamma, l2) [fb]'    , ' 1/#sigma d#sigma/d#DeltaR(#gamma, l2)'           ),
          'unfReco_Z_pt' :            ('Reconstructed p_{T}(ll) [GeV]',           'Generated p_{T}(ll) [GeV]'            , 'd#sigma/dp_{T}(ll) [fb/GeV]'          , ' 1/#sigma d#sigma/dp_{T}(ll) [1/GeV]'             ),
          'unfReco_l1l2_ptsum' :      ('Reconstructed p_{T}(l1)+p_{T}(l2) [GeV]', 'Generated p_{T}(l1)+p_{T}(l2) [GeV]'  , 'd#sigma/dp_{T}(l1)+p_{T}(l2) [fb/GeV]', ' 1/#sigma d#sigma/dp_{T}(l1)+p_{T}(l2) [1/GeV]'   )
          }


ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)


#################### main code ####################

for dist in distList:
  log.info('running for '+ dist)
  respR2 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  resp17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  resp18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  # pdb.set_trace()

  respR2.Add(resp17)
  respR2.Add(resp18)

  nxbins = respR2.GetXaxis().GetNbins()
  nybins = respR2.GetYaxis().GetNbins()

  respR2eq = ROOT.TH2D(dist + 'respSummed', dist + 'respSummed', nxbins, numpy.array(range(nxbins+1)).astype(float), nybins, numpy.array(range(nybins+1)).astype(float))

  respCanv = ROOT.TCanvas('respSummed' + dist,'respSummed' + dist, 810, 700)
  respCanv.SetLogz(True)
  # respStichCanv.SetLeftMargin(0.1)
  respR2eq.SetTitle('')
  respR2eq.GetXaxis().SetTitle(labels[dist][0])
  respR2eq.GetYaxis().SetTitle(labels[dist][1])
  # respR2eq.GetZaxis().SetTitle('Arbitrary units')
  respR2eq.GetZaxis().SetTitle('')
  respR2eq.GetYaxis().SetTitleOffset(1.5)
  respR2eq.GetXaxis().SetTitleOffset(1.5)
  respR2eq.GetZaxis().SetTitleOffset(1.3)
  respR2eq.GetXaxis().SetLabelSize(0.062)
  respR2eq.GetYaxis().SetLabelSize(0.062)
  respR2eq.GetZaxis().SetLabelSize(0.05)
  respR2eq.GetYaxis().SetTitleSize(0.048)
  respR2eq.GetXaxis().SetTitleSize(0.048)
  respR2eq.GetZaxis().SetTitleSize(0.048)
  # respR2eq.GetXaxis().SetTickLength(0)
  # respR2eq.GetYaxis().SetTickLength(0)


  print dist

  for i in range(1, nxbins+1):
    respR2eq.GetXaxis().SetBinLabel(i, ( str(int(respR2.GetXaxis().GetBinLowEdge(i))) if dist in ['unfReco_phPt', 'unfReco_jetPt', 'unfReco_Z_pt', 'unfReco_l1l2_ptsum'] else str(round(respR2.GetXaxis().GetBinLowEdge(i), 2)) ))

  for j in range(1, nybins+1):
    respR2eq.GetYaxis().SetBinLabel(j, ( str(int(respR2.GetYaxis().GetBinLowEdge(j))) if dist in ['unfReco_phPt', 'unfReco_jetPt', 'unfReco_Z_pt', 'unfReco_l1l2_ptsum'] else str(round(respR2.GetYaxis().GetBinLowEdge(j), 2)) ))

  # for i in range(1, nxbins+1):
  #   for j in range(1, nybins+1):
  #     respR2eq.SetBinContent(i, j, respR2.GetBinContent(i, j))

  projY = respR2.ProjectionY('proj')

  for i in range(1, nxbins+1):
    for j in range(1, nybins+1):
      respR2eq.SetBinContent(i, j, respR2.GetBinContent(i, j) / projY.GetBinContent(j))


  respR2eq.LabelsOption('v','x')
  # ROOT.gStyle.SetPadRightMargin(0.05)
  respR2eq.GetZaxis().SetRangeUser(respR2eq.GetMaximum()*0.0004, respR2eq.GetMaximum()*1.03)
  respR2eq.Draw('COLZ')
  # respR2eq.Draw('COLZ TEXT')
  ROOT.gPad.Update()
  ROOT.gPad.RedrawAxis()

  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.03,  1-ROOT.gStyle.GetPadTopMargin()+0.02,"#bf{CMS} #it{Supplementary}"), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()-0.02,  1-ROOT.gStyle.GetPadTopMargin()+0.02, ('(13 TeV)')), 31)

  respCanv.SaveAs('summedResponses/' + dist + 'repSummed.png')
  respCanv.SaveAs('summedResponses/' + dist + 'repSummed.pdf')