#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
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
from ttg.tools.style import drawLumi, commonStyle, setDefault, setDefault2D, drawTex
from ttg.tools.helpers import plotDir, getObjFromFile
import copy
import pickle
import numpy
import uuid

ROOT.gStyle.SetOptStat(0)

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

def removeOut(inHist, rec, out):
  inHist = inHist.Clone()
  out = out.Clone()
  out.Divide(rec)
  for i in range(0, out.GetXaxis().GetNbins()+1):
    inHist.SetBinContent(i, inHist.GetBinContent(i)*(1.-out.GetBinContent(i)))
    inHist.SetBinError(i, 0.00001 if inHist.GetBinError(i)==0 else inHist.GetBinError(i)*(1.-out.GetBinContent(i)))
  return inHist

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

def loadYear(fitFile, year, responseVersion):
  data = getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_ee/data')
  mcTot = getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_ee/total')
  mcBkg = getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_ee/total_background')
  data = graphToHist(data, mcTot)

  dataemu = getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_emu/data')
  mcTot.Add(getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_emu/total'))
  mcBkg.Add(getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_emu/total_background'))
  dataemu = graphToHist(dataemu, mcTot)
  data.Add(dataemu)

  datamumu = getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_mumu/data')
  mcTot.Add(getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_mumu/total'))
  mcBkg.Add(getObjFromFile(fitFile,'shapes_fit_s/y' + year + '_' + dist + '_sr_mumu/total_background'))
  datamumu = graphToHist(datamumu, mcTot)
  data.Add(datamumu)

  outMig = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + year + '/' + responseVersion + '/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  rec = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + year + '/' + responseVersion + '/noData/placeholderSelection/' + dist.replace('unfReco','rec_unfReco') + '.pkl','r'))[dist.replace('unfReco','rec_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  data = copyBinning(data, outMig)
  mcTot = copyBinning(mcTot, outMig)
  mcBkg = copyBinning(mcBkg, outMig)

  mcBkgNoUnc = mcBkg.Clone('MCBkgNoUnc' + year)
  for i in range(0, mcBkgNoUnc.GetXaxis().GetNbins()+1):
    mcBkgNoUnc.SetBinError(i, 0.)

  dataStatOnly = data.Clone('dataStatOnly' + year)

  data.Add(mcBkg, -1.)
  mcTot.Add(mcBkgNoUnc,-1.)
  # data.Add(outMig, -1.)
  # mcTot.Add(outMig,-1.)
  data = removeOut(data, rec, outMig)
  mcTot = removeOut(mcTot, rec, outMig)


  dataStatOnly.Add(mcBkgNoUnc, -1.)
  # dataStatOnly.Add(outMig, -1.)
  dataStatOnly = removeOut(dataStatOnly, rec, outMig)


  data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)
  mcTot.SetBinContent(mcTot.GetXaxis().GetNbins()+1, 0.)
  mcTot.SetBinContent(0, 0.)

  dataStatOnly.SetBinContent(mcTot.GetXaxis().GetNbins()+1, 0.)
  dataStatOnly.SetBinContent(0, 0.)

  return (data, mcTot, dataStatOnly)






def stitch1D(h6, h7, h8):
  binning = []
  start = h6.GetXaxis().GetBinLowEdge(1)
  end = h6.GetXaxis().GetBinUpEdge(h6.GetXaxis().GetNbins())
  for y in [0., 1. , 2.]:
    for i in range(1, h6.GetXaxis().GetNbins()+1):
      binning.append(y*(end-start) + h6.GetXaxis().GetBinLowEdge(i))
  binning.append(3.*end - 2.*start)
  stitched = ROOT.TH1F(h6.GetName() + "RunII", h6.GetName() + "RunII", len(binning)-1, numpy.array(binning))

  # log.info(binning)
  for y, h in enumerate([h6, h7, h8]):
    nbins = h.GetXaxis().GetNbins()
    for i in range (1, nbins+1):
      stitched.SetBinContent(y*nbins + i, h.GetBinContent(i))
      stitched.SetBinError(y*nbins + i, h.GetBinError(i))
  return stitched



def stitch2D(h6, h7, h8):
  binning = []
  start = h6.GetXaxis().GetBinLowEdge(1)
  end = h6.GetXaxis().GetBinUpEdge(h6.GetXaxis().GetNbins())
  for y in [0., 1. , 2.]:
    for i in range(1, h6.GetXaxis().GetNbins()+1):
      binning.append(y*(end-start) + h6.GetXaxis().GetBinLowEdge(i))
  binning.append(3.*end - 2.*start)
  ybinning = []
  start = h6.GetYaxis().GetBinLowEdge(1)
  end = h6.GetYaxis().GetBinUpEdge(h6.GetYaxis().GetNbins())
  # log.info(binning)
  for i in range(1, h6.GetYaxis().GetNbins()+1):
    ybinning.append(h6.GetYaxis().GetBinLowEdge(i))
  ybinning.append(end)
  stitched = ROOT.TH2F(h6.GetName() + "RunII", h6.GetName() + "RunII", len(binning)-1, numpy.array(binning), len(ybinning)-1, numpy.array(ybinning))

  for y, h in enumerate([h6, h7, h8]):
    nbins = h.GetXaxis().GetNbins()
    nybins = h.GetYaxis().GetNbins()
    for j in range(1, nybins+1):
      for i in range(1, nbins+1):
        stitched.SetBinContent(y*nbins + i, j, h.GetBinContent(i, j))
        stitched.SetBinError(y*nbins + i, j, h.GetBinError(i, j))
        stitched.GetXaxis().SetBinLabel(y*nbins + i, str(round(h.GetXaxis().GetBinLowEdge(i), 2)))
      stitched.GetYaxis().SetBinLabel(j, str(round(h.GetYaxis().GetBinLowEdge(j), 2)))
      uflowVal = h6.GetBinContent(0, j) + h7.GetBinContent(0, j) + h8.GetBinContent(0, j)
      uflowErr = (h6.GetBinError(0, j)**2. + h7.GetBinError(0, j)**2. + h8.GetBinError(0, j)**2.)**0.5
      stitched.SetBinContent(0, j, uflowVal)
      stitched.SetBinError(0, j, uflowErr)
  return stitched


def getPad(canvas, number):
  pad = canvas.cd(number)
  pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())
  pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
  pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
  pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
  return pad

def getRatioCanvas(name):
  xWidth, yWidth, yRatioWidth = 1000, 1050, 280
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


labels = {
          'unfReco_phPt' :            ('reco p_{T}(#gamma) (GeV)', 'gen p_{T}(#gamma) (GeV)'),
          'unfReco_phLepDeltaR' :     ('reco #DeltaR(#gamma, l)',  'gen #DeltaR(#gamma, l)'),
          'unfReco_ll_deltaPhi' :     ('reco #Delta#phi(ll)',      'gen #Delta#phi(ll)'),
          'unfReco_jetLepDeltaR' :    ('reco #DeltaR(l, j)',       'gen #DeltaR(l, j)'),
          'unfReco_jetPt' :           ('reco p_{T}(j1) (GeV)',     'gen p_{T}(j1) (GeV)'),
          'unfReco_ll_absDeltaEta' :  ('reco |#Delta#eta(ll)|',    'gen |#Delta#eta(ll)|'),
          'unfReco_phBJetDeltaR' :    ('reco #DeltaR(#gamma, b)',  'gen #DeltaR(#gamma, b)'),
          'unfReco_phAbsEta' :        ('reco |#eta|(#gamma)',      'gen |#eta|(#gamma)')
          }

distList = [('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_jetLepDeltaR'),
('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_jetPt'),
('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_ll_absDeltaEta'),
# ('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_cosTheta'),
('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_deltaPhi'),
('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_phAbsEta'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phBJetDeltaR'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phLepDeltaR'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phPt')]


ROOT.gStyle.SetPadRightMargin(0.06)
ROOT.gStyle.SetPadLeftMargin(0.12)


totalLumi = 35.863818448 + 41.529548819 + 59.688059536



for fitFile, dist in distList:
# for dist in ['unfReco_phPt']:
# for dist in ['unfReco_phEta']:
  log.info('running for '+ dist)
  ########## loading ##########
  responseVersion = 'unfSep3'

# TODO NOTE testing with resp matrix 16
  data16, mcTot16, dataStatOnly16 = loadYear(fitFile, '2016', responseVersion)
  data17, mcTot17, dataStatOnly17 = loadYear(fitFile, '2017', responseVersion)
  data18, mcTot18, dataStatOnly18 = loadYear(fitFile, '2018', responseVersion)

  response16 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  response17 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2017/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  response18 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2018/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  dataR2 = stitch1D(data16, data17, data18)
  mcTotR2 = stitch1D(mcTot16, mcTot17, mcTot18)
  respR2 = stitch2D(response16, response17, response18)

  dataR2StatOnly = stitch1D(dataStatOnly16, dataStatOnly17, dataStatOnly18)

  ########## UNFOLDING ##########
  ##### setup ##### 
  # regMode = ROOT.TUnfold.kRegModeCurvature
  # NOTE no regularization
  regMode = ROOT.TUnfold.kRegModeNone
  constraintMode = ROOT.TUnfold.kEConstraintArea
  # mapping = ROOT.TUnfold.kHistMapOutputHoriz 
  mapping = ROOT.TUnfold.kHistMapOutputVert 
  densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
  unfold = ROOT.TUnfoldDensity( respR2, mapping, regMode, constraintMode, densityFlags )
  logTauX = ROOT.TSpline3()
  logTauY = ROOT.TSpline3()
  lCurve  = ROOT.TGraph()
  logTauCurvature = ROOT.TSpline3()


  ##### unfold data #####


  unfold.SetInput(dataR2)
  spl = ROOT.TSpline3()
  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData_' + dist)

  plMC = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  plMC.Add(pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2017/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'])
  plMC.Add(pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2018/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'])
  plMC.SetLineColor(ROOT.kRed)


  # raise SystemExit(0)
  unfold.SetInput(mcTotR2)
  unfold.DoUnfold(0.)
  unfoldedMC = unfold.GetOutput('unfoldedMC_' + dist)

  unfoldedMC.Scale(1./totalLumi)
  plMC.Scale(1./totalLumi)
  unfMC2 = unfoldedMC.Clone()
  unfolded.Scale(1./totalLumi)

  cunf = getRatioCanvas(dist)
  cunf.topPad.cd()
  # cunf = ROOT.TCanvas(dist, dist, 1000,700)

  unfoldedMC.SetLineWidth(3)
  unfoldedMC.SetLineColor(ROOT.kBlue)
  unfoldedMC.SetFillStyle(3244)
  unfoldedMC.SetFillColor(ROOT.kBlue)
  # unfoldedMC.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*0.2)
  # unfoldedMC.GetXaxis().SetTitle(labels[dist][1])
  unfoldedMC.GetYaxis().SetRangeUser(0, unfolded.GetMaximum()*1.3)
  unfoldedMC.GetYaxis().SetTitle('Fiducial cross section (fb)')
  unfoldedMC.GetYaxis().SetTitleSize(0.05)
  unfoldedMC.SetTitle('')



  unfMC2.SetFillColor(ROOT.kWhite)
  unfoldedMC.SetMinimum(0.)
  unfolded.SetLineColor(ROOT.kBlack)
  unfolded.SetLineWidth(2)
  unfolded.SetMarkerStyle(8)
  unfolded.SetMarkerSize(1)
  plMC.SetLineColor(ROOT.kRed)
  plMC.SetLineWidth(3)
  legend = ROOT.TLegend(0.28,0.825,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  # legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
  legend.AddEntry(unfoldedMC,"Simulation","l")
  legend.AddEntry(unfolded,"Data (137/fb) ","pe")
  legend.AddEntry(plMC,"PL truth","l")




  unfoldedMC.Draw('E2')
  unfMC2.SetLineWidth(3)
  unfMC2.Draw('HIST same')
  plMC.Draw('same')
  unfolded.Draw('same E1 X0')
  log.info(dist + ' integral: ' + str(unfolded.Integral()))
  legend.Draw()

  difc = plMC.Clone()
  difc.Add(unfolded, -1.)
  l = [ difc.GetBinContent(i) for i in range(0, difc.GetXaxis().GetNbins()+1)]
  lr = [99 if unfolded.GetBinContent(i)==0 else difc.GetBinContent(i)/unfolded.GetBinContent(i) for i in range(0, difc.GetXaxis().GetNbins()+1)]
  log.info(l)
  log.info(lr)

  cunf.bottomPad.cd()
  
  unfold.SetInput(dataR2StatOnly)
  unfold.DoUnfold(0.)
  unfdataR2StatOnly = unfold.GetOutput('unfoldedDataStatOnly_' + dist)
  unfdataR2StatOnly.Scale(1./totalLumi)

  # unfoldedRat = unfdataR2StatOnly.Clone('ratio')
  # unfoldedMCnoUnc = unfoldedMC.Clone('')
  # for i in range(0, unfoldedMCnoUnc.GetXaxis().GetNbins()+1):
  #   unfoldedMCnoUnc.SetBinError(i, 0)
  # unfoldedRat.Divide(unfoldedMCnoUnc)

  # unfoldedRat.SetLineColor(ROOT.kBlack)
  # unfoldedRat.SetMarkerStyle(ROOT.kFullCircle);
  # unfoldedRat.SetTitle('')
  # unfoldedRat.GetXaxis().SetTitle(labels[dist][1])
  # unfoldedRat.GetXaxis().SetLabelSize(0.14);
  # unfoldedRat.GetXaxis().SetTitleSize(0.14);
  # unfoldedRat.GetXaxis().SetTitleOffset(1.2)
  # unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  # unfoldedRat.GetYaxis().SetNdivisions(3,5,0)
  # unfoldedRat.GetYaxis().SetLabelSize(0.1);
  # unfoldedRat.Draw('E1 X0')


# 
# 


  unfoldedRat = unfdataR2StatOnly.Clone('ratio')
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
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)


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
# 
# 

  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)

  cunf.SaveAs('unfoldedR2/'+ dist +'.pdf')
  cunf.SaveAs('unfoldedR2/'+ dist +'.png')




  data = data16.Clone()
  mcTot = mcTot16.Clone()
  data.Add(data17)
  mcTot.Add(mcTot17)
  data.Add(data18)
  mcTot.Add(mcTot18)

  dataStat = dataStatOnly16.Clone()
  dataStat.Add(dataStatOnly17)
  dataStat.Add(dataStatOnly18)

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

  legend = ROOT.TLegend(0.28,0.825,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(mcTot,"Simulation","l")
  legend.AddEntry(data,"Data (137/fb) ","pe")
  legend.Draw()



  cpreunf.bottomPad.cd()

  preunfRat = dataStat.Clone('ratio')
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

  cpreunf.SaveAs('unfoldedR2/preUnf_'+ dist +'.pdf')
  cpreunf.SaveAs('unfoldedR2/preUnf_'+ dist +'.png')




setDefault2D(isColZ=True)
ROOT.gStyle.SetLabelSize(0.055, "xy")
ROOT.gStyle.SetPadLeftMargin(0.08)
ROOT.gStyle.SetPadRightMargin(0.1)
ROOT.gStyle.SetPadBottomMargin(0.19)
ROOT.gStyle.SetTitleSize(0.05, "xy")


distList = [('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_jetLepDeltaR'),
('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_jetPt'),
('data/bolbiR2AsrFit_fitDiagnostics_exp.root', 'unfReco_ll_absDeltaEta'),
# ('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_cosTheta'),
('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_ll_deltaPhi'),
('data/bolbiR2BsrFit_fitDiagnostics_exp.root', 'unfReco_phAbsEta'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phBJetDeltaR'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phLepDeltaR'),
('data/bolbiR2CsrFit_fitDiagnostics_exp.root', 'unfReco_phPt')]


for fitFile, dist in distList:
  log.info('plotting response matrices for '+ dist)
  ########## loading ##########
  data16, mcTot16, dataStatOnly16 = loadYear(fitFile, '2016', responseVersion)
  data17, mcTot17, dataStatOnly17 = loadYear(fitFile, '2017', responseVersion)
  data18, mcTot18, dataStatOnly18 = loadYear(fitFile, '2018', responseVersion)

  response16 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  response17 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2017/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  response18 = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2018/'+ responseVersion +'/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  dataR2 = stitch1D(data16, data17, data18)
  mcTotR2 = stitch1D(mcTot16, mcTot17, mcTot18)
  respR2 = stitch2D(response16, response17, response18)
  
  respStichCanv = ROOT.TCanvas('stitchedResp' + dist,'stitchedResp' + dist, 1900, 700)
  respStichCanv.SetLogz(True)
  # respStichCanv.SetLeftMargin(0.1)
  # histo.SetTitle('')
  respR2.GetXaxis().SetTitle(labels[dist][0])
  respR2.GetYaxis().SetTitle(labels[dist][1])
  respR2.GetYaxis().SetTitleOffset(0.8)
  respR2.GetXaxis().SetTitleOffset(1.8)
  respR2.GetXaxis().SetTickLength(0)
  respR2.GetYaxis().SetTickLength(0)
  respR2.LabelsOption('v','x')
  ROOT.gPad.Update()
  ROOT.gPad.RedrawAxis()
  # ROOT.gStyle.SetPadRightMargin(0.05)
  # respR2.GetZaxis().SetRangeUser(respR2.GetMaximum()*0.0004, respR2.GetMaximum()*1.03)
  respR2.Draw('COLZ')
  respStichCanv.SaveAs(dist + 'stitchedResp.png')