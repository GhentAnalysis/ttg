#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
args = argParser.parse_args()

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gStyle.SetOptStat(0)

from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
from ttg.tools.style import drawLumi, setDefault, drawTex
from ttg.tools.helpers import plotDir, getObjFromFile
import copy
import pickle
import numpy
import uuid


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


#################### Settings and definitons ####################
lumiScales = {'2016':35.863818448, '2017':41.529548819, '2018':59.688059536}
lumiScalesRounded = {'2016':35.9, '2017':41.5, '2018':59.7}

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

varList = ['']
# sysList = ['isr','fsr','ue','erd','ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','JEC','JER','NP']
sysList = ['isr','fsr','ue','erd','ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','NP']
# TODO no response matrix for ue, erd, ephScale,'ephRes',,'JEC','JER','NP' use nominal there automatically. some just missing  guess
# sysList = ['isr','fsr','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb']
varList += [sys + direc for sys in sysList for direc in ['Down', 'Up']]

# TODO
# NOTE
# pdf and q2 needs separate implementation

# unfolding settings
regMode = ROOT.TUnfold.kRegModeNone
constraintMode = ROOT.TUnfold.kEConstraintArea
mapping = ROOT.TUnfold.kHistMapOutputVert 
densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
sysMode = ROOT.TUnfoldDensity.kSysErrModeMatrix


#################### functions ####################
def getHistos(histDict, dist, variation, rmBkgStats):
  data, signal, backgrounds = None, None, {}
  for process, hist in histDict[dist+variation].items():
    if process.count('data'):
      # for data always take nominal
      if not data: data = histDict[dist][process].Clone()
      else: data.Add(histDict[dist][process])
    elif process.count('TTGamma'): signal = hist.Clone()
    else:
      if rmBkgStats: 
        hist = hist.Clone()
        for i in range(0, hist.GetXaxis().GetNbins()+1):
          hist.SetBinError(i, 0)
      backgrounds[process] = hist
  assert data
  assert signal
  assert backgrounds
  return (data, signal, backgrounds)


def getUnfolded(response, data, backgrounds, outMig, signalVari = None):
  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )
  data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)
  # raise SystemExit(0)
  unfold.SetInput(data)
  for process, hist in backgrounds.items():
    hist.SetBinContent(hist.GetXaxis().GetNbins()+1, 0.)
    hist.SetBinContent(0, 0.)
    unfold.SubtractBackground(hist, process)
  outMig.SetBinContent(outMig.GetXaxis().GetNbins()+1, 0.)
  outMig.SetBinContent(0, 0.)
  unfold.SubtractBackground(outMig, 'outMig')
  logTauX = ROOT.TSpline3()
  logTauY = ROOT.TSpline3()
  lCurve  = ROOT.TGraph()
  logTauCurvature = ROOT.TSpline3()

  spl = ROOT.TSpline3()
  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData' + str(uuid.uuid4()))
  return unfolded


# def getTotalDeviations(histDict):
# # WARNING this modifies the systematics histograms, be aware if you look at them later in the code
#   nominal = histDict['']
#   totalUp = nominal.Clone()
#   totalUp.Reset('ICES')
#   totalDown = totalUp.Clone()
#   for sys in sysList:
#     histDict[sys+'Up'].Add(nominal, -1.)
#     histDict[sys+'Up'].Multiply(histDict[sys+'Up'])
#     totalUp.Add(histDict[sys+'Up'])
#     histDict[sys+'Down'].Add(nominal, -1.)
#     histDict[sys+'Down'].Multiply(histDict[sys+'Down'])
#     totalDown.Add(histDict[sys+'Down'])
#   for i in range(0, totalUp.GetXaxis().GetNbins()+1):
#     totalUp.SetBinContent(i, totalUp.GetBinContent(i)**0.5)
#     totalDown.SetBinContent(i, totalDown.GetBinContent(i)**0.5)
#   return totalUp, totalDown

def getTotalDeviations(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict['']
  totalUp = nominal.Clone()
  totalUp.Reset('ICES')
  totalDown = totalUp.Clone()

  ups = [name for name in histDict.keys() if name.count('Up')]
  downs = [name for name in histDict.keys() if name.count('Down')]
  for sys in ups:
    histDict[sys].Add(nominal, -1.)
    histDict[sys].Multiply(histDict[sys])
    totalUp.Add(histDict[sys])
  for sys in downs:
    histDict[sys].Add(nominal, -1.)
    histDict[sys].Multiply(histDict[sys])
    totalDown.Add(histDict[sys])

  for i in range(0, totalUp.GetXaxis().GetNbins()+1):
    totalUp.SetBinContent(i, totalUp.GetBinContent(i)**0.5)
    totalDown.SetBinContent(i, totalDown.GetBinContent(i)**0.5)
  return totalUp, totalDown


def getRMS(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict['']
  rms = nominal.Clone()
  rms.Reset('ICES')

  for hist in histDict.values():
    hist.Add(nominal, -1.)
    hist.Multiply(hist)
    rms.Add(hist)

  nvars = len(histDict)-1

  for i in range(0, totalUp.GetXaxis().GetNbins()+1):
    rms.SetBinContent(i, (rms.GetBinContent(i)/nvars)**0.5)
  return rms

def getEnv(histDict):
# TODO test
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict['']
  maxUp = nominal.Clone()
  maxUp.Reset('ICES')
  maxDown = maxUp.Clone()

  for hist in histDict.values(): 
    hist.Add(nominal, -1.)

  for i in range(0, hist.GetNbinsX()+1):
    upHist.SetBinContent(  i, max([hist.GetBinContent(i) for hist in histDict.values()]))
    downHist.SetBinContent(i, min([hist.GetBinContent(i) for hist in histDict.values()]))

  return maxUp, maxDown



#################### main code ####################
# rmBkgStats = False
rmBkgStats = True

for dist in distList:
  log.info('running for '+ dist)

    # TODO generalize
  histDict = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-niceEstimDD-Dec/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  responseDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfJan/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  outMigDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfJan/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))
  # rec = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/' + '2016Nov' + '/unfNovSys/noData/placeholderSelection/' + dist.replace('unfReco','rec_unfReco') + '.pkl','r'))[dist.replace('unfReco','rec_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

  
  # get unfolded results for all systematic variations
  unfoldedDict = {}
  for var in varList:
    log.info(var)
    #TODO need to generate variations for outside migration histos before trying to vary them
    outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    try:
      response = responseDict[dist.replace('unfReco','response_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    except:
      log.warning('no repsonse matrix for ' +var + ' , check if there should be')
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    if rmBkgStats:
      for i in range(0, outMig.GetXaxis().GetNbins()+1):
        outMig.SetBinError(i, 0)

    data, signal, backgrounds = getHistos(histDict, dist, var, rmBkgStats = rmBkgStats)
    unfolded = getUnfolded(response, data, backgrounds, outMig, signalVari = None)
    unfolded.Scale(1./lumiScales[args.year])
    unfoldedDict[var] = unfolded


  # TODO get unfolded results for varied bin stats

  unfolded = unfoldedDict['']

  # log.info('uncertainties bins')
  # log.info( [unfolded.GetBinError(i) for i in range(0, unfolded.GetXaxis().GetNbins()+1)]) 

  totalUp, totalDown = getTotalDeviations(unfoldedDict)


  unfoldedMC = getUnfolded(response, signal, {}, outMig, signalVari = None)
  unfoldedMC.Scale(1./lumiScales[args.year])

  plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfJan/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  # plMC = response.ProjectionY("PLMC")
  plMC.Scale(1./lumiScales[args.year])

  # raise SystemExit(0)


  unfoldedStatDict = {}

  outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  if rmBkgStats:
    for i in range(0, outMig.GetXaxis().GetNbins()+1):
      outMig.SetBinError(i, 0)

  
# NEED TO KEEP BACKGROUND STATS HERE, but then set them to zero manually
  if rmBkgStats:
    _, _, bkgStat = getHistos(histDict, dist, '', rmBkgStats = False)
    data, signal, backgrounds = getHistos(histDict, dist, '', rmBkgStats = True)
    for process in backgrounds.keys():
      backgrounds[process].SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
      backgrounds[process].SetBinContent(0, 0.)
      # the N+1 bin is overflow, which is not empty?
      for i in range(0, backgrounds[process].GetXaxis().GetNbins()+1):
        # log.info(bkgStat[process].GetBinError(i))
        backgrounds[process].SetBinContent(i, bkgStat[process].GetBinContent(i) + bkgStat[process].GetBinError(i))

        unfoldedStat = getUnfolded(response, data, backgrounds, outMig, signalVari = None)
        unfoldedStat.Scale(1./lumiScales[args.year])
        unfoldedStatDict[process[:10]+str(i)+'Up'] = unfoldedStat

        backgrounds[process].SetBinContent(i, bkgStat[process].GetBinContent(i) - bkgStat[process].GetBinError(i))
        unfoldedStat = getUnfolded(response, data, backgrounds, outMig, signalVari = None)
        unfoldedStat.Scale(1./lumiScales[args.year])
        unfoldedStatDict[process[:10]+str(i)+'Down'] = unfoldedStat

        # don't forget to reset
        backgrounds[process].SetBinContent(i, bkgStat[process].GetBinContent(i))

    unfoldedStatDict[''] = unfolded
    totalStatUp, totalStatDown = getTotalDeviations(unfoldedStatDict)

    # log.info('uncertainties bkg stat up')
    # log.info( [totalStatUp.GetBinContent(i) for i in range(0, totalStatUp.GetXaxis().GetNbins()+1)]) 

    # log.info('uncertainties bkg stat down')
    # log.info( [totalStatDown.GetBinContent(i) for i in range(0, totalStatDown.GetXaxis().GetNbins()+1)]) 


  unfoldedTotUnc = unfolded.Clone()
  for i in range(1, unfoldedTotUnc.GetXaxis().GetNbins()):
    unfoldedTotUnc.SetBinError(i, (unfolded.GetBinError(i)**2.+ max(totalUp.GetBinContent(i),totalDown.GetBinContent(i))**2.+ max(totalStatUp.GetBinContent(i),totalStatDown.GetBinContent(i))**2.)**0.5)


  # raise SystemExit(0)


  cunf = getRatioCanvas(dist)
# TOP PAD
  cunf.topPad.cd()


# draw the yellow total unc band
  unfoldedTotUnc.SetLineWidth(3)
  unfoldedTotUnc.SetLineColor(ROOT.kOrange)
  unfoldedTotUnc.SetFillStyle(3244)
  unfoldedTotUnc.SetFillColor(ROOT.kOrange)
  # unfoldedTotUnc.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*0.2)
  unfoldedTotUnc.SetMinimum(0.)
  unfoldedTotUnc.GetYaxis().SetRangeUser(0., unfolded.GetMaximum()*1.3)
  unfoldedTotUnc.GetXaxis().SetTitle(labels[dist][1])
  unfoldedTotUnc.GetYaxis().SetTitle('Fiducial cross section (fb)')
  unfoldedTotUnc.SetTitle('')
  unfoldedTotUnc.Draw('E2')

  plMC.SetLineColor(ROOT.kRed)
  # stats on this are normally very small, ttgamma samples have great statistics (so not drawing it)
  plMC.Draw('same')
  unfoldedMC.Draw('same')

  # DRAW DATA
  unfolded.SetLineColor(ROOT.kBlack)
  unfolded.SetLineWidth(2)
  unfolded.SetMarkerStyle(8)
  unfolded.SetMarkerSize(1)
  # unfolded.Draw('same E1 X0')
  unfolded.Draw('same')

  legend = ROOT.TLegend(0.28,0.8,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(plMC,"PL MC","l")
  legend.AddEntry(unfoldedMC,"Unfolded MC","l")
  legend.AddEntry(unfolded,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"pe")
  legend.Draw()

# RATIO PAD
  cunf.bottomPad.cd()

  unfoldedRat = unfolded.Clone('ratio')
  unfoldedRat.Divide(plMC)
  unfoldedRat.SetLineColor(ROOT.kBlack)
  unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  unfoldedRat.Draw('E1 X0')

  unfoldedRat.SetTitle('')
  unfoldedRat.GetXaxis().SetTitle(labels[dist][1])
  unfoldedRat.GetYaxis().SetTitle('Ratio')
  unfoldedRat.GetXaxis().SetLabelSize(0.14)
  unfoldedRat.GetXaxis().SetTitleSize(0.14)
  unfoldedRat.GetYaxis().SetTitleSize(0.14)
  unfoldedRat.GetXaxis().SetTitleOffset(1.2)
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  unfoldedRat.GetYaxis().SetNdivisions(3,5,0)
  unfoldedRat.GetYaxis().SetLabelSize(0.1)


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


  cpreunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.pdf')
  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.png')