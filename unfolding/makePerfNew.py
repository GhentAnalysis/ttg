#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse, numpy
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong, equalBinning
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.tools.style import drawLumi
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR
from ttg.samples.Sample import createSampleList, getSampleFromList
import copy
import pickle
from math import pi

ROOT.gStyle.SetOptStat(0)



from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


from ttg.plots.plotHelpers  import *




# labels = {
#           'unfReco_phPt' :            ('reco p_{T}(#gamma) (GeV)', 'gen p_{T}(#gamma) (GeV)'),
#           'unfReco_phLepDeltaR' :     ('reco #DeltaR(#gamma, l)',  'gen #DeltaR(#gamma, l)'),
#           'unfReco_ll_deltaPhi' :     ('reco #Delta#phi(ll)',      'gen #Delta#phi(ll)'),
#           'unfReco_jetLepDeltaR' :    ('reco #DeltaR(#gamma, j)',  'gen #DeltaR(#gamma, j)'),
#           'unfReco_jetPt' :           ('reco p_{T}(j1) (GeV)',     'gen p_{T}(j1) (GeV)'),
#           'unfReco_ll_absDeltaEta' :  ('reco |#Delta#eta(ll)|',    'gen |#Delta#eta(ll)|'),
#           'unfReco_phBJetDeltaR' :    ('reco #DeltaR(#gamma, b)',  'gen #DeltaR(#gamma, b)'),
#           'unfReco_phAbsEta' :        ('reco |#eta|(#gamma)',      'gen |#eta|(#gamma)')
#           }

# plotList = ['perf_unfReco_phPt',
# 'perf_unfReco_jetPt',
# 'perf_unfReco_jetLepDeltaR',
# 'perf_unfReco_phLepDeltaR',
# 'perf_unfReco_phBJetDeltaR',
# 'perf_unfReco_ll_absDeltaEta',
# 'perf_unfReco_ll_deltaPhi',
# 'perf_unfReco_phAbsEta']

labels = {
          'unfReco_phPt' :            'p_{T}(#gamma) (GeV)',
          'unfReco_phLepDeltaR' :     '#DeltaR(#gamma, l)',
          'unfReco_ll_deltaPhi' :     '#Delta#phi(ll)',
          'unfReco_jetLepDeltaR' :    '#DeltaR(l, j)',
          'unfReco_jetPt' :           'p_{T}(j1) (GeV)',
          'unfReco_ll_absDeltaEta' :  '|#Delta#eta(ll)|',
          'unfReco_phBJetDeltaR' :    '#DeltaR(#gamma, b)',
          'unfReco_phAbsEta' :        '|#eta|(#gamma)',
          'unfReco_phLep1DeltaR' :    '#DeltaR(#gamma, l1)',
          'unfReco_phLep2DeltaR' :    '#DeltaR(#gamma, l2)',
          'unfReco_Z_pt' :            'p_{T}(ll) (GeV)',
          'unfReco_l1l2_ptsum' :      'p_{T}(l1)+p_{T}(l2) (GeV)'
          }

plotList = [
  'response_unfReco_jetLepDeltaR',
  'response_unfReco_jetPt',
  'response_unfReco_ll_absDeltaEta',
  'response_unfReco_ll_deltaPhi',
  'response_unfReco_phAbsEta',
  'response_unfReco_phBJetDeltaR',
  'response_unfReco_phLepDeltaR',
  'response_unfReco_phPt',
  'response_unfReco_phLep1DeltaR',
  'response_unfReco_phLep2DeltaR',
  'response_unfReco_Z_pt',
  'response_unfReco_l1l2_ptsum'
  ]

  # 'response_unfReco_ll_cosTheta',

def getBinning(a):
  return numpy.linspace(a[1],a[2],a[0]-1)

for plot in plotList:
  response = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot + '.pkl'))[plot]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  perf = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot.replace('response', 'perf') + '.pkl'))[plot.replace('response', 'perf')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  fid = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot.replace('response', 'fid') + '.pkl'))[plot.replace('response', 'fid')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  recFid = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot.replace('response', 'recFid') + '.pkl'))[plot.replace('response', 'recFid')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  rec = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot.replace('response', 'rec') + '.pkl'))[plot.replace('response', 'rec')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  out = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfBMAR/noData/placeholderSelection/' + plot.replace('response', 'out') + '.pkl'))[plot.replace('response', 'out')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']



  gen = response.ProjectionY("pl")                                       # reco underflow bins = events failing reco. Included in this sum
  reco = response.ProjectionX("reco")  
  eff = gen.Clone('eff')
  eff.Reset("ICES")
  pur = reco.Clone('pur')
  pur.Reset("ICES")

  for i in range( gen.GetXaxis().GetNbins()+1 ):
      genVal  = gen.GetBinContent(i)
      effVal  = (perf.GetBinContent(i, i ) / genVal) if genVal else 0.
      eff.SetBinContent( i, effVal )

  for i in range( reco.GetXaxis().GetNbins()+1 ):
      recoPt  = reco.GetBinCenter(i)
      genBin  = gen.FindBin( recoPt )
      recoVal = reco.GetBinContent(i)
      purVal  = response.GetBinContent(i, genBin) / recoVal if recoVal else 0.
      pur.SetBinContent( i, purVal )

  canv = ROOT.TCanvas()

  out.GetYaxis().SetRangeUser(0.,1.2)
  out.GetXaxis().SetTitle(labels[plot.replace('response_','')])
  out.GetYaxis().SetTitle('ratio')
  out.SetTitle('')

  out.Divide(rec)
  out.SetLineColor(418)
  out.Draw('HIST')

  eff.SetLineColor(ROOT.kBlue)
  eff.Draw('same')
  pur.SetLineColor(ROOT.kRed)
  pur.Draw('same')

  legend = ROOT.TLegend(0.15,0.83,0.89,0.89)
  legend.SetNColumns(3)
  legend.AddEntry(eff,"efficiency","l")
  legend.AddEntry(pur,"purity","l")
  legend.AddEntry(out,"f_out","l")
  legend.SetBorderSize(0)
  legend.Draw()

  canv.SaveAs('performance/'+ plot.replace('response', 'performance') + '_' + args.year +'.pdf')

  log.info(plot + ' efficiency: ' + str(recFid.Integral()/fid.Integral()))
