#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',     help='Specify type of reducedTuple')
argParser.add_argument('--var',       action='store',      default='phPt',               help='variable to unfold')
argParser.add_argument('--subJob',    action='store',      default=None,                 help='The xth subjob for a sample, number of subjobs is defined by split parameter in tuples.conf')
argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
# argParser.add_argument('--overwrite', action='store_true', default=False,                help='overwrite if valid output file already exists')
args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
from ttg.tools.style import drawLumi
from ttg.tools.helpers import plotDir, getObjFromFile
import copy
import pickle
import numpy

lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


def graphToHist(graph, template):
  hist = template.Clone(graph.GetName())
  hist.Reset("ICES")
  for i in range(1, hist.GetXaxis().GetNbins()+1):
    hist.SetBinContent(i, graph.Eval(i-0.5))
    hist.SetBinError(i, graph.GetErrorY(i-1))
  return hist

# TODO double check overflows here
def copyBinning(inputHist, template):
  hist = template.Clone(inputHist.GetName())
  hist.Reset("ICES")
  for i in range(1, inputHist.GetXaxis().GetNbins()+1):
    hist.SetBinContent(i, inputHist.GetBinContent(i))
    hist.SetBinError(i, inputHist.GetBinError(i))
  return hist



for dist in ['unfReco_phPt','unfReco_phLepDeltaR','unfReco_phEta', 'unfReco_ll_deltaPhi']:
# for dist in ['unfReco_phPt']:
# for dist in ['unfReco_phEta']:
# for dist in ['unfReco_phPt']:
  log.info('running for '+ dist)
  ########## loading ##########
  fitFile = 'data/srFit_fitDiagnostics_obs.root'
  data = getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_ee/data')
  mcTot = getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_ee/total')
  mcBkg = getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_ee/total_background')
  data = graphToHist(data, mcTot)

  dataemu = getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_emu/data')
  mcTot.Add(getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_emu/total'))
  mcBkg.Add(getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_emu/total_background'))
  dataemu = graphToHist(dataemu, mcTot)
  data.Add(dataemu)

  datamumu = getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_mumu/data')
  mcTot.Add(getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_mumu/total'))
  mcBkg.Add(getObjFromFile(fitFile,'shapes_fit_s/' + dist + '_sr_mumu/total_background'))
  datamumu = graphToHist(datamumu, mcTot)
  data.Add(datamumu)

  outMig = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/unflmva4/noData/placeholderSelection/' + dist.replace('unfReco','out') + '.pkl','r'))[dist.replace('unfReco','out')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  data = copyBinning(data, outMig)
  mcTot = copyBinning(mcTot, outMig)
  mcBkg = copyBinning(mcBkg, outMig)


  mcBkgNoUnc = mcBkg.Clone('MCBkgNoUnc')
  for i in range(0, mcBkgNoUnc.GetXaxis().GetNbins()+1):
    mcBkgNoUnc.SetBinError(i, 0.)

  response = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/unflmva4/noData/placeholderSelection/' + dist.replace('unfReco','response') + '.pkl','r'))[dist.replace('unfReco','response')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  ########## UNFOLDING ##########
  ##### setup ##### 
  regMode = ROOT.TUnfold.kRegModeCurvature
  constraintMode = ROOT.TUnfold.kEConstraintArea
  mapping = ROOT.TUnfold.kHistMapOutputHoriz 
  densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )
  logTauX = ROOT.TSpline3()
  logTauY = ROOT.TSpline3()
  lCurve  = ROOT.TGraph()

  ##### unfold data #####
  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD-JUN/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt.pkl'
  data.Add(mcBkg, -1.)
  mcTot.Add(mcBkgNoUnc,-1.)
  data.Add(outMig, -1.)
  mcTot.Add(outMig,-1.)

  data.SetBinContent(mcTot.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)

  unfold.SetInput(data)
  # iBest   = unfold.ScanLcurve(30,1e-04,1e-03,lCurve,logTauX,logTauY)
  # log.info(iBest)
  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData_' + dist)
  cunf = ROOT.TCanvas(dist)
  unfolded.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*1.3)
  unfolded.Draw()
  plMC = response.ProjectionX("PLMC")
  plMC.SetLineColor(ROOT.kRed)
  plMC.Draw('same')

  mcTot.SetBinContent(mcTot.GetXaxis().GetNbins()+1, 0.)
  mcTot.SetBinContent(0, 0.)

  unfold.SetInput(mcTot)
  unfold.DoUnfold(0.)
  unfoldedMC = unfold.GetOutput('unfoldedMC_' + dist)
  unfoldedMC.SetLineColor(ROOT.kGreen)
  unfoldedMC.Draw('same')
  unfoldedMC.SetMinimum(0.)
  cunf.SaveAs('unfolded/'+ dist +'.pdf')

