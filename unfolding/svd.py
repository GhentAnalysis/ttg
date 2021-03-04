#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018', 'RunII'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
argParser.add_argument('--unblind',   action='store_true', default=False,  help='unblind 2017 and 2018')
args = argParser.parse_args()


if args.year == '2016': args.unblind = True

import ROOT
import pdb

# ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gStyle.SetOptStat(0)

# from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
# from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
# from ttg.tools.style import drawLumi, setDefault, drawTex
# from ttg.tools.helpers import plotDir, getObjFromFile
import copy
import pickle
# import numpy
# import uuid


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)



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
  'unfReco_l1l2_ptsum'
  ]


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


#################### main code ####################

for dist in distList:
  print('--------------------------------------------------------------------------------------------------------------------------------------------------')
  log.info('running for '+ dist)
  responseDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfcadB/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']


  # raise SystemExit(0)
  # data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  # data.SetBinContent(0, 0.)

  # unfold.SetInput(data)

  # response = unfold.GetProbabilityMatrix( 'ProbMatrix')

  # raise SystemExit(0)
  # m = ROOT.TMatrixD( response.GetXaxis().GetNbins(), response.GetYaxis().GetNbins())
  # for xbin in range(1, response.GetNbinsX()+1):
  #     for ybin in range(1,response.GetNbinsY()+1):
  #         m[xbin-1, ybin-1] = response.GetBinContent( xbin, ybin)


  regMode = ROOT.TUnfold.kRegModeCurvature

  constraintMode = ROOT.TUnfold.kEConstraintArea
  mapping = ROOT.TUnfold.kHistMapOutputVert 
  densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
  sysMode = ROOT.TUnfoldDensity.kSysErrModeMatrix

  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )

  response = unfold.GetProbabilityMatrix( 'ProbMatrix')
  # raise SystemExit(0)
  m = ROOT.TMatrixD( response.GetYaxis().GetNbins(), response.GetXaxis().GetNbins())
  for xbin in range(1, response.GetNbinsY() +1):
      for ybin in range(1,response.GetNbinsX() +1):
          m[xbin-1, ybin-1] = response.GetBinContent(ybin, xbin)
  # m.Print()

  svd = ROOT.TDecompSVD( m )
  svd.Decompose()
  # svd.Print()

  sig = svd.GetSig()
  # sig.Print()
  nSig = len(sig)
  sigmaMax = sig[0]
  sigmaMin = sig[nSig-1]
  condition = sigmaMax / max(0,sigmaMin)
  log.info(labels[dist] + '  ' + str(condition))
  # log.info("Condition value : " + str(condition))

  