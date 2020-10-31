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
from ttg.tools.style import drawLumi, setDefault, drawTex
from ttg.tools.helpers import plotDir, getObjFromFile
import copy
import pickle
import numpy
import uuid

lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
lumiScalesRounded = {'2016':35.9, '2017':41.5, '2018':59.7}

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

def getPad(canvas, number):
  pad = canvas.cd(number)
  pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())
  pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
  pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
  pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
  return pad

def getRatioCanvas(name):
  xWidth, yWidth, yRatioWidth = 1000, 950, 200
  yWidth           += yRatioWidth
  bottomMargin      = yWidth/float(yRatioWidth)*ROOT.gStyle.GetPadBottomMargin()
  yBorder           = yRatioWidth/float(yWidth)

  canvas = ROOT.TCanvas(str(uuid.uuid4()), name, xWidth, yWidth)
  canvas.Divide(1, 2, 0, 0)
  canvas.topPad = getPad(canvas, 1)
  canvas.topPad.SetBottomMargin(0)
  canvas.topPad.SetPad(canvas.topPad.GetX1(), yBorder, canvas.topPad.GetX2(), canvas.topPad.GetY2())
  canvas.bottomPad = getPad(canvas, 2)
  canvas.bottomPad.SetTopMargin(0)
  canvas.bottomPad.SetBottomMargin(bottomMargin)
  canvas.bottomPad.SetPad(canvas.bottomPad.GetX1(), canvas.bottomPad.GetY1(), canvas.bottomPad.GetX2(), yBorder)
  return canvas


def removeOut(inHist, rec, out):
  inHist = inHist.Clone()
  out = out.Clone()
  out.Divide(rec)
  for i in range(0, out.GetXaxis().GetNbins()+1):
    inHist.SetBinContent(i, inHist.GetBinContent(i)*(1.-out.GetBinContent(i)))
    inHist.SetBinError(i, inHist.GetBinError(i)*(1.-out.GetBinContent(i)))
  return inHist

ROOT.gStyle.SetOptStat(0)

labels = {
          'unfReco_phPt' :            ('reco p_{T}(#gamma) (GeV)', 'gen p_{T}(#gamma) (GeV)'),
          'unfReco_phLepDeltaR' :     ('reco #DeltaR(#gamma, l)',  'gen #DeltaR(#gamma, l)'),
          'unfReco_ll_deltaPhi' :     ('reco #Delta#phi(ll)',      'gen #Delta#phi(ll)'),
          'unfReco_jetLepDeltaR' :    ('reco #DeltaR(#gamma, j)',  'gen #DeltaR(#gamma, j)'),
          'unfReco_jetPt' :           ('reco p_{T}(j1) (GeV)',     'gen p_{T}(j1) (GeV)'),
          'unfReco_ll_absDeltaEta' :  ('reco |#Delta#eta(ll)|',    'gen |#Delta#eta(ll)|'),
          'unfReco_phBJetDeltaR' :    ('reco #DeltaR(#gamma, b)',  'gen #DeltaR(#gamma, b)'),
          'unfReco_phAbsEta' :        ('reco |#eta|(#gamma)',      'gen |#eta|(#gamma)')
          }
# setDefault()


distList = [('data/otra16AsrFit_fitDiagnostics_exp.root', 'unfReco_jetLepDeltaR'),
('data/otra16AsrFit_fitDiagnostics_exp.root', 'unfReco_jetPt'),
('data/otra16AsrFit_fitDiagnostics_exp.root', 'unfReco_ll_absDeltaEta'),
# ('data/otra16BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_cosTheta'),
('data/otra16BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_deltaPhi'),
('data/otra16BsrFit_fitDiagnostics_exp.root', 'unfReco_phAbsEta'),
('data/otra16CsrFit_fitDiagnostics_exp.root', 'unfReco_phBJetDeltaR'),
('data/otra16CsrFit_fitDiagnostics_exp.root', 'unfReco_phLepDeltaR'),
('data/otra16CsrFit_fitDiagnostics_exp.root', 'unfReco_phPt')]


# for dist in ['unfReco_phPt','unfReco_phLepDeltaR','unfReco_phEta', 'unfReco_ll_deltaPhi']:
# for dist in ['unfReco_phPt']:
# for dist in ['unfReco_phEta']:
for fitFile, dist in distList:
  log.info('running for '+ dist)
  ########## loading ##########
  # fitFile = 'data/srFit_fitDiagnostics_obs.root'
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

  outMig = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + args.year + '/unfSep3/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  rec = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + args.year + '/unfSep3/noData/placeholderSelection/' + dist.replace('unfReco','rec_unfReco') + '.pkl','r'))[dist.replace('unfReco','rec_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  data = copyBinning(data, outMig)
  mcTot = copyBinning(mcTot, outMig)
  mcBkg = copyBinning(mcBkg, outMig)


  mcBkgNoUnc = mcBkg.Clone('MCBkgNoUnc')
  for i in range(0, mcBkgNoUnc.GetXaxis().GetNbins()+1):
    mcBkgNoUnc.SetBinError(i, 0.)

  response = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + args.year + '/unfSep3/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  ########## UNFOLDING ##########
  ##### setup ##### 
  # regMode = ROOT.TUnfold.kRegModeCurvature
  # NOTE no regularization
  regMode = ROOT.TUnfold.kRegModeNone
  constraintMode = ROOT.TUnfold.kEConstraintArea
  # mapping = ROOT.TUnfold.kHistMapOutputHoriz 
  mapping = ROOT.TUnfold.kHistMapOutputVert 
  densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )
  logTauX = ROOT.TSpline3()
  logTauY = ROOT.TSpline3()
  lCurve  = ROOT.TGraph()
  logTauCurvature = ROOT.TSpline3()


  ##### unfold data #####
  dataStatOnly = data.Clone('dataStatOnly')

  data.Add(mcBkg, -1.)
  mcTot.Add(mcBkgNoUnc,-1.)
  # data.Add(outMig, -1.)
  # mcTot.Add(outMig,-1.)
  data = removeOut(data, rec, outMig)
  mcTot = removeOut(mcTot, rec, outMig)


  data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)
  mcTot.SetBinContent(mcTot.GetXaxis().GetNbins()+1, 0.)
  mcTot.SetBinContent(0, 0.)



  dataStatOnly.Add(mcBkgNoUnc, -1.)
  # dataStatOnly.Add(outMig, -1.)
  dataStatOnly = removeOut(dataStatOnly, rec, outMig)


  unfold.SetInput(data)
  spl = ROOT.TSpline3()
  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData_' + dist)

  unfold.SetInput(mcTot)
  unfold.DoUnfold(0.)
  unfoldedMC = unfold.GetOutput('unfoldedMC_' + dist)

  unfoldedMC.Scale(1./lumiScales[args.year])
  # plMC.Scale(1./lumiScales[args.year])
  unfMC2 = unfoldedMC.Clone()
  unfolded.Scale(1./lumiScales[args.year])
  log.info(dist + ' integral: ' + str(unfolded.Integral()))

  cunf = getRatioCanvas(dist)
  cunf.topPad.cd()

  unfoldedMC.SetLineWidth(3)
  unfoldedMC.SetLineColor(ROOT.kBlue)
  unfoldedMC.SetFillStyle(3244)
  unfoldedMC.SetFillColor(ROOT.kBlue)
  # unfoldedMC.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*0.2)
  unfoldedMC.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*1.3)
  unfoldedMC.GetXaxis().SetTitle(labels[dist][1])
  unfoldedMC.GetYaxis().SetTitle('Fiducial cross section (fb)')
  unfoldedMC.SetTitle('')
  unfoldedMC.Draw('E2')
  unfMC2 = unfoldedMC.Clone()
  unfMC2.Draw('HIST same')
  unfMC2.SetFillColor(ROOT.kWhite)
  unfoldedMC.SetMinimum(0.)
  unfolded.SetLineColor(ROOT.kBlack)
  unfolded.SetLineWidth(2)
  unfolded.SetMarkerStyle(8)
  unfolded.SetMarkerSize(1)
  # plMC = response.ProjectionY("PLMC")
  plMC = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + args.year + '/unfSep3/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  plMC.Scale(1./lumiScales[args.year])
  plMC.SetLineColor(ROOT.kRed)
  plMC.SetLineWidth(2)
  plMC.Draw('same')
  unfolded.Draw('same E1 X0')
  # legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
  legend = ROOT.TLegend(0.28,0.83,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(unfoldedMC,"Simulation","l")
  legend.AddEntry(unfolded,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"pe")
  # legend.AddEntry(plMC,"PL truth","l")
  legend.Draw()
  # raise SystemExit(0)

  cunf.bottomPad.cd()

  unfold.SetInput(dataStatOnly)
  unfold.DoUnfold(0.)
  unfdataStatOnly = unfold.GetOutput('unfoldedDataStatOnly_' + dist)

  unfdataStatOnly.Scale(1./lumiScales[args.year])

  unfoldedRat = unfdataStatOnly.Clone('ratio')
  unfoldedMCnoUnc = unfoldedMC.Clone('')
  for i in range(0, unfoldedMCnoUnc.GetXaxis().GetNbins()+1):
    unfoldedMCnoUnc.SetBinError(i, 0)
  

  systband = unfoldedMC.Clone('systBand')
  for i in range(0, systband.GetXaxis().GetNbins()+1):
    if systband.GetBinContent(i) == 0: 
      systband.SetBinError(i, 0.)
    else:
      systband.SetBinError(i, systband.GetBinError(i)/systband.GetBinContent(i))
    systband.SetBinContent(i, 1.)

  unfoldedRat.Divide(unfoldedMCnoUnc)

  unfoldedRat.SetLineColor(ROOT.kBlack)
  unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)
  # unfoldedRat.SetTitle('')
  # unfoldedRat.GetXaxis().SetTitle(labels[dist][1])
  # unfoldedRat.GetXaxis().SetLabelSize(0.14)
  # unfoldedRat.GetXaxis().SetTitleSize(0.14)
  # unfoldedRat.GetXaxis().SetTitleOffset(1.2)
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  # unfoldedRat.GetYaxis().SetNdivisions(3,5,0)
  # unfoldedRat.GetYaxis().SetLabelSize(0.1)
  # unfoldedRat.Draw('E1 X0')


  systband.SetTitle('')
  systband.GetXaxis().SetTitle(labels[dist][1])
  systband.GetYaxis().SetTitle('Ratio')
  systband.GetXaxis().SetLabelSize(0.14)
  systband.GetXaxis().SetTitleSize(0.14)
  systband.GetYaxis().SetTitleSize(0.14)
  systband.GetXaxis().SetTitleOffset(1.2)
  systband.GetYaxis().SetRangeUser(0.4, 1.6)
  systband.GetYaxis().SetNdivisions(3,5,0)
  systband.GetYaxis().SetLabelSize(0.1)

  systband.SetLineWidth(3)
  systband.SetLineColor(ROOT.kBlue)
  systband.SetFillStyle(3244)
  systband.SetFillColor(ROOT.kBlue)
  systband.Draw('E2')
  unfoldedRat.Draw('E1 same X0')




  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cunf.SaveAs('unfolded/'+ dist +'.pdf')
  cunf.SaveAs('unfolded/'+ dist +'.png')



  cpreunf = getRatioCanvas(dist)
  cpreunf.topPad.cd()


  mcTot.SetLineWidth(3)
  mcTot.SetLineColor(ROOT.kBlue)
  mcTot.SetFillStyle(3244)
  mcTot.SetFillColor(ROOT.kBlue)
  mcTot.GetYaxis().SetRangeUser(0., data.GetMaximum()*1.3)
  mcTot.GetXaxis().SetTitle(labels[dist][0])
  mcTot.GetYaxis().SetTitle('Events')
  mcTot.SetTitle('')
  mcTot.Draw('E2')
  mcTot2 = mcTot.Clone()
  mcTot2.Draw('HIST same')
  mcTot2.SetFillColor(ROOT.kWhite)
  mcTot.SetMinimum(0.)
  data.SetLineColor(ROOT.kBlack)
  data.SetLineWidth(2)
  data.SetMarkerStyle(8)
  data.SetMarkerSize(1)
  data.Draw('same E1 X0')
  # legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
  legend = ROOT.TLegend(0.28,0.825,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(mcTot,"Simulation","l")
  legend.AddEntry(data,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"pe")
  legend.Draw()



  cpreunf.bottomPad.cd()



  preunfRat = dataStatOnly.Clone('ratio')
  MCnoUnc = mcTot.Clone('')
  for i in range(0, MCnoUnc.GetXaxis().GetNbins()+1):
    MCnoUnc.SetBinError(i, 0)
  
  systband = mcTot.Clone('systBand')
  for i in range(0, systband.GetXaxis().GetNbins()+1):
    if systband.GetBinContent(i) == 0: 
      systband.SetBinError(i, 0.)
    else:
      systband.SetBinError(i, systband.GetBinError(i)/systband.GetBinContent(i))
    systband.SetBinContent(i, 1.)

  preunfRat.Divide(MCnoUnc)

  preunfRat.SetLineColor(ROOT.kBlack)
  preunfRat.SetMarkerStyle(ROOT.kFullCircle)
  systband.SetTitle('')
  systband.GetXaxis().SetTitle(labels[dist][0])
  systband.GetYaxis().SetTitle('Ratio')
  systband.GetXaxis().SetLabelSize(0.14)
  systband.GetXaxis().SetTitleSize(0.14)
  systband.GetYaxis().SetTitleSize(0.14)
  systband.GetXaxis().SetTitleOffset(1.2)
  systband.GetYaxis().SetRangeUser(0.4, 1.6)
  preunfRat.GetYaxis().SetRangeUser(0.4, 1.6)
  systband.GetYaxis().SetNdivisions(3,5,0)
  systband.GetYaxis().SetLabelSize(0.1)

  systband.SetLineWidth(3)
  systband.SetLineColor(ROOT.kBlue)
  systband.SetFillStyle(3244)
  systband.SetFillColor(ROOT.kBlue)
  systband.Draw('E2')
  preunfRat.Draw('E1 same X0')

  cpreunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.pdf')
  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.png')