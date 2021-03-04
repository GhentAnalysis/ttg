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
          'unfReco_phPt' :            ('reco p_{T}(#gamma) (GeV)',       'gen p_{T}(#gamma) (GeV)'),
          'unfReco_phLepDeltaR' :     ('reco #DeltaR(#gamma, l)',        'gen #DeltaR(#gamma, l)'),
          'unfReco_ll_deltaPhi' :     ('reco #Delta#phi(ll)',            'gen #Delta#phi(ll)'),
          'unfReco_jetLepDeltaR' :    ('reco #DeltaR(l, j)',             'gen #DeltaR(l, j)'),
          'unfReco_jetPt' :           ('reco p_{T}(j1) (GeV)',           'gen p_{T}(j1) (GeV)'),
          'unfReco_ll_absDeltaEta' :  ('reco |#Delta#eta(ll)|',          'gen |#Delta#eta(ll)|'),
          'unfReco_phBJetDeltaR' :    ('reco #DeltaR(#gamma, b)',        'gen #DeltaR(#gamma, b)'),
          'unfReco_phAbsEta' :        ('reco |#eta|(#gamma)',            'gen |#eta|(#gamma)'),
          'unfReco_phLep1DeltaR' :    ('reco #DeltaR(#gamma, l1)',       'gen #DeltaR(#gamma, l1)'),
          'unfReco_phLep2DeltaR' :    ('reco #DeltaR(#gamma, l2)',       'gen #DeltaR(#gamma, l2)'),
          'unfReco_Z_pt' :            ('reco p_{T}(ll) (GeV)',           'gen p_{T}(ll) (GeV)'),
          'unfReco_l1l2_ptsum' :      ('reco p_{T}(l1)+p_{T}(l2) (GeV)', 'gen p_{T}(l1)+p_{T}(l2) (GeV)')
          }

plotList = [
  'perf_unfReco_jetLepDeltaR',
  'perf_unfReco_jetPt',
  'perf_unfReco_ll_absDeltaEta',
  # 'perf_unfReco_ll_cosTheta',
  'perf_unfReco_ll_deltaPhi',
  'perf_unfReco_phAbsEta',
  'perf_unfReco_phBJetDeltaR',
  'perf_unfReco_phLepDeltaR',
  'perf_unfReco_phPt',
  'perf_unfReco_phLep1DeltaR',
  'perf_unfReco_phLep2DeltaR',
  'perf_unfReco_Z_pt',
  'perf_unfReco_l1l2_ptsum'
  ]


def getBinning(a):
  return numpy.linspace(a[1],a[2],a[0]-1)

for plot in plotList:
  perf = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfJanNew/noData/placeholderSelection/' + plot + '.pkl'))[plot]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  outMig = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfJanNew/noData/placeholderSelection/' + plot.replace('perf', 'out') + '.pkl'))[plot.replace('perf', 'out')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  totRec = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfJanNew/noData/placeholderSelection/' + plot.replace('perf', 'rec') + '.pkl'))[plot.replace('perf', 'rec')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  reco   = perf.ProjectionX("reco",1, perf.GetXaxis().GetNbins()) # pl not including over/underflows, but they should be empty anyway
  pl = perf.ProjectionY("pl",0, perf.GetXaxis().GetNbins())                                       # reco underflow bins = events failing reco. Included in this sum
  pl.SetBinContent(0, 0.)
  pl.SetBinError(0, 0.)
  diag = pl.Clone( "efficiency")
  diag.Reset("ICES")
  for i in range(0, pl.GetXaxis().GetNbins()+1):
    diag.SetBinContent(i, perf.GetBinContent(i,i))
    diag.SetBinError(i, perf.GetBinError(i,i))


  # NOTE do not change the order
  # purity     = ROOT.TEfficiency(diag, reco)
  purity = diag.Clone()
  purity.Divide(reco)
  reco.SetBinContent(0,0.)
  # efficiency = ROOT.TEfficiency(reco, pl)
  efficiency = diag.Clone()
  efficiency.Divide(pl)


  canv = ROOT.TCanvas()
  efficiency.GetYaxis().SetRangeUser(0.,1.2)
  efficiency.SetLineColor(ROOT.kBlue)
  efficiency.GetXaxis().SetTitle(labels[plot.replace('perf_','')][0])
  efficiency.GetYaxis().SetTitle('ratio')
  efficiency.SetTitle('')

  efficiency.Draw('')
  purity.SetLineColor(ROOT.kRed)
  purity.Draw('same')
  outMig.Divide(totRec)
  outMig.SetLineColor(418)
  outMig.Draw('same')

  legend = ROOT.TLegend(0.15,0.83,0.89,0.89)
  legend.SetNColumns(3)
  legend.AddEntry(efficiency,"efficiency","l")
  legend.AddEntry(purity,"purity","l")
  legend.AddEntry(outMig,"f_out","l")
  legend.SetBorderSize(0)
  legend.Draw()

  canv.SaveAs('performance/'+ plot + '_' + args.year +'.pdf')

  fid = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfJanNew/noData/placeholderSelection/' + plot.replace('perf', 'fid') + '.pkl'))[plot.replace('perf', 'fid')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  log.info(plot + ' efficiency: ' + str(diag.Integral()/fid.Integral()))

  # for histo, plotName, ymax in [(efficiency, 'eff',0.5), (purity, 'pur',1.0)]:
  # for histo, plotName, ymax in [(stability, 'stab',0.5), (purity, 'pur',1.0)]:

    # ROOT.gPad.Update(); 
    # graph = efficiency.GetPaintedGraph(); 
    # graph.SetMinimum(0);
    # graph.SetMaximum(1); 
    # ROOT.gPad.Update(); 

  # Outside migration plots
  # TODO make clones
  # TODO update to naming based on loop
  # out = [i for i in plotListOut if i.name==binning[0].replace('response','out')][0].histos.values()[0].Clone()
  # rec = [i for i in plotListRec if i.name==binning[0].replace('response','rec')][0].histos.values()[0].Clone()
  # out.Divide(rec)
  # for i in range(0, out.GetXaxis().GetNbins()+1):
  #   out.SetBinContent(i, 1. - out.GetBinContent(i))
  # canv = ROOT.TCanvas()
  # out.GetYaxis().SetRangeUser(0., 1.0)
  # out.Draw('E1')
  # canv.SaveAs('performance/out'+ binning[0].replace('response_','') +'.pdf')
