#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
# argParser.add_argument('--sample',    action='store',      default=None,                 help='Sample for which to produce reducedTuple, as listed in samples/data/tuples*.conf')
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
# argParser.add_argument('--runLocal',  action='store_true', default=False,                help='use local resources instead of Cream02')
# argParser.add_argument('--debug',     action='store_true', default=False,                help='only run over first three files for debugging')
# argParser.add_argument('--isChild',   action='store_true', default=False,                help='mark as subjob, will never submit subjobs by itself')
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

def sumBackgrounds(histDict, sysList, dist):
  nominal = None
  for process, hist in histDict[dist].items():
    # log.info(process)
    if process.count('data') or process.count('TTGamma'): continue
    if not nominal: nominal = hist
    else: nominal.Add(hist)

  deviations = {'Up':{}, 'Down':{}}
  for sys in sysList:
    for direc in ['Up', 'Down']:
      histo = None
      for process, hist in histDict[dist+sys+direc].items():
        if process.count('data') or process.count('TTGamma'): continue
        if not histo: histo = hist
        else: histo.Add(hist)
      histo.Add(nominal, -1.)
      deviations[direc][sys] = histo

  totalUp = nominal.Clone()
  total = totalUp.Clone()
  totalUp.Reset("ICES")
  totalDown = totalUp.Clone()

  for sys in sysList:
    for direc in ['Up', 'Down']:
      for i in range(0, deviations[direc][sys].GetXaxis().GetNbins()+1):
        deviations[direc][sys].SetBinContent(i, deviations[direc][sys].GetBinContent(i)**2.)
    totalUp.Add(deviations['Up'][sys])
    totalDown.Add(deviations['Down'][sys])

  for i in range(0, total.GetXaxis().GetNbins()+1):
    # log.info('------------------------------')
    # log.info(total.GetBinError(i))
    # log.info(totalUp.GetBinContent(i))
    total.SetBinError(i, (total.GetBinError(i)**2. + totalUp.GetBinContent(i))**0.5 )
  return total
      

def sumData(histDict, dist):
  summedData = None
  for process, hist in histDict[dist].items():
    if not process.count('data'): continue
    log.info(process)
    if not summedData: summedData = hist
    else: summedData.Add(hist)
  return summedData

# def sumHists(picklePath, plot):
#   hists = pickle.load(open(picklePath))[plot]
#   sumHist = None
#   for name, hist in hists.iteritems():
#     if not 'data' in name:
#       if not sumHist: sumHist = hist
#       else: sumHist.Add(hist)
#     else: continue
#   return sumHist

ROOT.gStyle.SetOptStat(0)

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
# setDefault()


distList = [
'unfReco_jetLepDeltaR',
'unfReco_jetPt',
'unfReco_ll_absDeltaEta',
# 'unfReco_ll_cosTheta',
'unfReco_ll_deltaPhi',
'unfReco_phAbsEta',
'unfReco_phBJetDeltaR',
'unfReco_phLepDeltaR',
'unfReco_phPt']


# TODO
# NOTE
# pdf and q2 needs separate implementation



for dist in distList:
  log.info('running for '+ dist)
  # TODO generalize

  histDict = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016Nov/phoCBfull-niceEstimDD-otravez/all/llg-mll20-signalRegionAB-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  outMig = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + '2016Nov' + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  rec = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + '2016Nov' + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','rec_unfReco') + '.pkl','r'))[dist.replace('unfReco','rec_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  # sysList = ['isrUp','fsrUp','puUp','puDown','pfUp','phSFUp','pvSFUp','lSFSyUp','lSFElUp','lSFMuUp','triggerUp','bTaglUp','bTagbUp']
  # sysList = ['isr','fsr','pu','phSF']


  sysList = ['isr','fsr','ue','erd','ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','JEC','JER','NP']

  # for jecSys in ['Absolute','BBEC1'

  background = sumBackgrounds(histDict, sysList, dist)
  data = sumData(histDict, dist)

  # raise SystemExit(0)

  data.Add(background, -1.)
  # NOTE in this order!
  data = removeOut(data, rec, outMig)

  data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)

  response = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + '2016Nov' + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']


  # plMC = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + '2016Nov' + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  # # plMC = response.ProjectionY("PLMC")
  # plMC.Scale(1./lumiScales[args.year])

  ########## UNFOLDING ##########
  ##### setup ##### 
  # regMode = ROOT.TUnfold.kRegModeCurvature
  # NOTE no regularization
  regMode = ROOT.TUnfold.kRegModeNone
  constraintMode = ROOT.TUnfold.kEConstraintArea
  mapping = ROOT.TUnfold.kHistMapOutputVert 
  densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )
  # sysList = ['isrUp','isrDown','fsrUp','fsrDown','puUp','puDown','pfUp','pfDown','phSFUp','phSFDown','pvSFUp','pvSFDown','lSFSyUp','lSFSyDown','lSFElUp','lSFElDown','lSFMuUp','lSFMuDown','triggerUp','triggerDown','bTaglUp','bTaglDown','bTagbUp','bTagbDown']

  sysMode = ROOT.TUnfoldDensity.kSysErrModeMatrix
  sysList = ['isrUp','fsrUp','puUp','puDown','pfUp','phSFUp','pvSFUp','lSFSyUp','lSFElUp','lSFMuUp','triggerUp','bTaglUp','bTagbUp']
  # sysList = []
  unfold.SetInput(data)
  # for sys in sysList:
  #   varHist = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + args.year + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))[dist.replace('unfReco','response_unfReco')+sys]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  #   unfold.AddSysError(varHist, sys, mapping, sysMode)

  logTauX = ROOT.TSpline3()
  logTauY = ROOT.TSpline3()
  lCurve  = ROOT.TGraph()
  logTauCurvature = ROOT.TSpline3()


  ##### unfolding #####

  spl = ROOT.TSpline3()
  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData_' + dist)

#  TODO sum sys uncertainties etc
# https://github.com/rappoccio/TUnfoldExamples/blob/c1a477890fa4afac933d6a8306a44957d9eb65ec/tunfoldsys_example.ipynb
# https://github.com/FNALLPC/unfolding-hats/blob/95af575f90b1f5e5ef1455315fc96a283654f7a8/tunfold/2-systematics.ipynb
  # test = unfold.GetDeltaSysSource('isrUp','isrUp')
# 
  # unfold.GetDeltaSysSource(s,'s').GetBinContent(3)/unfolded.GetBinContent(3)

  # raise SystemExit(0)
  unfolded.Scale(1./lumiScales[args.year])

  cunf = getRatioCanvas(dist)
# TOP PAD
  cunf.topPad.cd()


# # draw the yellow total unc band
#   unfoldedMC.SetLineWidth(3)
#   unfoldedMC.SetLineColor(ROOT.kOrange)
#   unfoldedMC.SetFillStyle(3244)
#   unfoldedMC.SetFillColor(ROOT.kOrange)
#   # unfoldedMC.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*0.2)
#   unfoldedMC.SetMinimum(0.)
#   unfoldedMC.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*1.3)
#   unfoldedMC.GetXaxis().SetTitle(labels[dist][1])
#   unfoldedMC.GetYaxis().SetTitle('Fiducial cross section (fb)')
#   unfoldedMC.SetTitle('')
#   unfoldedMC.Draw('E2')

# Draw the blue stat unc only band
  # histsum = sumHists('/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-niceEstimDD-otravez/all/llg-mll20-signalRegionAB-offZ-llgNoZ-photonPt20/' + dist + '.pkl', dist)




  # # Draw the blue line
  # unfMC2 = unfoldedMC.Clone()
  # unfMC2.SetLineColor(ROOT.kBlue)
  # unfMC2.Draw('HIST same')
  # unfMC2.SetFillColor(ROOT.kWhite)

  # DRAW DATA
  unfolded.SetLineColor(ROOT.kBlack)
  unfolded.SetLineWidth(2)
  unfolded.SetMarkerStyle(8)
  unfolded.SetMarkerSize(1)
  unfolded.Draw('same E1 X0')

  # legend = ROOT.TLegend(0.28,0.83,0.85,0.88)
  # legend.SetBorderSize(0)
  # legend.SetNColumns(2)
  # legend.AddEntry(unfoldedMC,"Simulation","l")
  # legend.AddEntry(unfolded,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"pe")
  # legend.Draw()

# RATIO PAD
  cunf.bottomPad.cd()

  # unfoldedRat = unfolded.Clone('ratio')
  # unfoldedMCnoUnc = unfoldedMC.Clone('')
  # for i in range(0, unfoldedMCnoUnc.GetXaxis().GetNbins()+1):
  #   unfoldedMCnoUnc.SetBinError(i, 0)
  

  # systband = unfoldedMC.Clone('systBand')
  # for i in range(0, systband.GetXaxis().GetNbins()+1):
  #   if systband.GetBinContent(i) == 0: 
  #     systband.SetBinError(i, 0.)
  #   else:
  #     systband.SetBinError(i, systband.GetBinError(i)/systband.GetBinContent(i))
  #   systband.SetBinContent(i, 1.)

  # unfoldedRat.Divide(unfoldedMCnoUnc)

  # unfoldedRat.SetLineColor(ROOT.kBlack)
  # unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)
  # unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)

  # systband.SetTitle('')
  # systband.GetXaxis().SetTitle(labels[dist][1])
  # systband.GetYaxis().SetTitle('Ratio')
  # systband.GetXaxis().SetLabelSize(0.14)
  # systband.GetXaxis().SetTitleSize(0.14)
  # systband.GetYaxis().SetTitleSize(0.14)
  # systband.GetXaxis().SetTitleOffset(1.2)
  # systband.GetYaxis().SetRangeUser(0.4, 1.6)
  # systband.GetYaxis().SetNdivisions(3,5,0)
  # systband.GetYaxis().SetLabelSize(0.1)

  # systband.SetLineWidth(3)
  # systband.SetLineColor(ROOT.kBlue)
  # systband.SetFillStyle(3244)
  # systband.SetFillColor(ROOT.kOrange)
  # systband.Draw('E2')
  # unfoldedRat.Draw('E1 same X0')




  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cunf.SaveAs('unfolded/'+ dist +'.pdf')
  cunf.SaveAs('unfolded/'+ dist +'.png')








  cpreunf = getRatioCanvas(dist)
  cpreunf.topPad.cd()


  # mcTot.SetLineWidth(3)
  # mcTot.SetLineColor(ROOT.kBlue)
  # mcTot.SetFillStyle(3244)
  # mcTot.SetFillColor(ROOT.kBlue)
  # mcTot.GetYaxis().SetRangeUser(0., data.GetMaximum()*1.3)
  # mcTot.GetXaxis().SetTitle(labels[dist][0])
  # mcTot.GetYaxis().SetTitle('Events')
  # mcTot.SetTitle('')
  # mcTot.Draw('E2')
  # mcTot2 = mcTot.Clone()
  # mcTot2.Draw('HIST same')
  # mcTot2.SetFillColor(ROOT.kWhite)
  # mcTot.SetMinimum(0.)
  data.SetLineColor(ROOT.kBlack)
  data.SetLineWidth(2)
  data.SetMarkerStyle(8)
  data.SetMarkerSize(1)
  data.Draw('same E1 X0')
  # # legend = ROOT.TLegend(0.7,0.75,0.9,0.9)
  # legend = ROOT.TLegend(0.28,0.825,0.85,0.88)
  # legend.SetBorderSize(0)
  # legend.SetNColumns(2)
  # legend.AddEntry(mcTot,"Simulation","l")
  # legend.AddEntry(data,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"pe")
  # legend.Draw()



  cpreunf.bottomPad.cd()



  # preunfRat = data.Clone('ratio')
  # MCnoUnc = mcTot.Clone('')
  # for i in range(0, MCnoUnc.GetXaxis().GetNbins()+1):
  #   MCnoUnc.SetBinError(i, 0)
  
  # systband = mcTot.Clone('systBand')
  # for i in range(0, systband.GetXaxis().GetNbins()+1):
  #   if systband.GetBinContent(i) == 0: 
  #     systband.SetBinError(i, 0.)
  #   else:
  #     systband.SetBinError(i, systband.GetBinError(i)/systband.GetBinContent(i))
  #   systband.SetBinContent(i, 1.)

  # preunfRat.Divide(MCnoUnc)

  # preunfRat.SetLineColor(ROOT.kBlack)
  # preunfRat.SetMarkerStyle(ROOT.kFullCircle)
  # systband.SetTitle('')
  # systband.GetXaxis().SetTitle(labels[dist][0])
  # systband.GetYaxis().SetTitle('Ratio')
  # systband.GetXaxis().SetLabelSize(0.14)
  # systband.GetXaxis().SetTitleSize(0.14)
  # systband.GetYaxis().SetTitleSize(0.14)
  # systband.GetXaxis().SetTitleOffset(1.2)
  # systband.GetYaxis().SetRangeUser(0.4, 1.6)
  # preunfRat.GetYaxis().SetRangeUser(0.4, 1.6)
  # systband.GetYaxis().SetNdivisions(3,5,0)
  # systband.GetYaxis().SetLabelSize(0.1)

  # systband.SetLineWidth(3)
  # systband.SetLineColor(ROOT.kBlue)
  # systband.SetFillStyle(3244)
  # systband.SetFillColor(ROOT.kBlue)
  # systband.Draw('E2')
  # preunfRat.Draw('E1 same X0')

  cpreunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.pdf')
  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.png')