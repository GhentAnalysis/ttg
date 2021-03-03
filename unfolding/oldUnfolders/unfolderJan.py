#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018'])
argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
argParser.add_argument('--blind',   action='store_true', default=False,  help='blind the data, data will be replaced by total MC')
args = argParser.parse_args()

import ROOT
import pdb

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

lumiunc = {'2016':0.025, '2017':0.023, '2018':0.025}

labels = {
          'unfReco_phPt' :            ('reco p_{T}(#gamma) (GeV)',  'gen p_{T}(#gamma) (GeV)'),
          'unfReco_phLepDeltaR' :     ('reco #DeltaR(#gamma, l)',   'gen #DeltaR(#gamma, l)'),
          'unfReco_ll_deltaPhi' :     ('reco #Delta#phi(ll)',       'gen #Delta#phi(ll)'),
          'unfReco_jetLepDeltaR' :    ('reco #DeltaR(l, j)',        'gen #DeltaR(l, j)'),
          'unfReco_jetPt' :           ('reco p_{T}(j1) (GeV)',      'gen p_{T}(j1) (GeV)'),
          'unfReco_ll_absDeltaEta' :  ('reco |#Delta#eta(ll)|',     'gen |#Delta#eta(ll)|'),
          'unfReco_phBJetDeltaR' :    ('reco #DeltaR(#gamma, b)',   'gen #DeltaR(#gamma, b)'),
          'unfReco_phAbsEta' :        ('reco |#eta|(#gamma)',       'gen |#eta|(#gamma)'),
          'unfReco_phLep1DeltaR' :    ('#DeltaR(#gamma, l1)',       'gen #DeltaR(#gamma, l1)'),
          'unfReco_phLep2DeltaR' :    ('#DeltaR(#gamma, l2)',       'gen #DeltaR(#gamma, l2)'),
          'unfReco_Z_pt' :            ('p_{T}(ll) (GeV)',           'gen p_{T}(ll) (GeV)'),
          'unfReco_l1l2_ptsum' :      ('p_{T}(l1)+p_{T}(l2) (GeV)', 'gen p_{T}(l1)+p_{T}(l2) (GeV)')
          }

distList = [
  # 'unfReco_jetLepDeltaR',
  # 'unfReco_jetPt',
  # 'unfReco_ll_absDeltaEta',
  # 'unfReco_ll_cosTheta',
  # 'unfReco_ll_deltaPhi',
  # 'unfReco_phAbsEta',
  # 'unfReco_phBJetDeltaR',
  'unfReco_phLepDeltaR',
  'unfReco_phPt',
  # 'unfReco_phLep1DeltaR',
  # 'unfReco_phLep2DeltaR',
  # 'unfReco_Z_pt',
  # 'unfReco_l1l2_ptsum'
  ]

sysList = ['isr','fsr','ue','erd','ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','JEC','JER','NP']
sysVaryData = ['ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','JEC','JER','NP']
# sysList = ['isr','fsr','ue','erd','ephScale','ephRes','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb','NP']
# TODO no response matrix for ue, erd, ephScale,'ephRes','NP' use nominal there automatically. some just missing  guess
# sysList = ['isr','fsr','pu','pf','phSF','pvSF','lSFSy','lSFEl','lSFMu','trigger','bTagl','bTagb']
varList = ['']
varList += [sys + direc for sys in sysList for direc in ['Down', 'Up']]

varList += ['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]

varList += ['pdf_' + str(i) for i in range(0, 100)]

# theoSysList = ['isr','fsr','ue','erd']

theoSysList = ['isr','fsr']
theoVarList = ['']
theoVarList += [sys + direc for sys in theoSysList for direc in ['Down', 'Up']]
# theoVarList += ['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
theoVarList += ['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
theoVarList += ['pdf_' + str(i) for i in range(0, 100)]


bkgNorms = [('other_Other+#gamma (genuine)Other+#gamma (genuine)', 0.3),
            ('VVTo2L2NuMultiboson+#gamma (genuine)', 0.3),
            ('ZG_Z#gamma (genuine)Z#gamma (genuine)', 0.03),
            ('singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 0.1)]


# unfolding settings
regMode = ROOT.TUnfold.kRegModeNone
constraintMode = ROOT.TUnfold.kEConstraintArea
mapping = ROOT.TUnfold.kHistMapOutputVert 
densityFlags = ROOT.TUnfoldDensity.kDensityModeUser
sysMode = ROOT.TUnfoldDensity.kSysErrModeMatrix


#################### functions ####################
def getHistos(histDict, dist, variation, blind=False):
  data, signal, backgrounds = None, None, {}
  for process, hist in histDict[dist+variation].items():
    nbins = hist.GetXaxis().GetNbins()
    hist.SetBinContent(nbins, hist.GetBinContent(nbins) + hist.GetBinContent(nbins+1))
    hist.SetBinError(nbins, (hist.GetBinError(nbins)**2. + hist.GetBinError(nbins+1)**2.)**0.5)
    hist.SetBinContent(nbins + 1, 0.)
    hist.SetBinError(nbins + 1, 0.)
    if process.count('data'):
      # for data always take nominal
      if not data: data = histDict[dist][process].Clone()
      else: data.Add(histDict[dist][process])
    elif process.count('TTGamma'): signal = hist.Clone()
    else:backgrounds[process] = hist
  assert data
  assert signal
  assert backgrounds
  if blind:
    tot = sumDict(backgrounds)
    for i in range(0, tot.GetXaxis().GetNbins()+1):
      tot.SetBinError(i, 0.)
    tot.Add(signal)
    return (tot, signal, backgrounds)
  else:
    return (data, signal, backgrounds)


def getUnfolded(response, data, backgrounds, outMig, splitStats = False):
  unfold = ROOT.TUnfoldDensity( response, mapping, regMode, constraintMode, densityFlags )

  data.SetBinContent(data.GetXaxis().GetNbins()+1, 0.)
  data.SetBinContent(0, 0.)
  unfold.SetInput(data)
  for process, hist in backgrounds.items():
    hist.SetBinContent(hist.GetXaxis().GetNbins()+1, 0.)
    hist.SetBinContent(0, 0.)
    unfold.SubtractBackground(hist, process)
  outMig.SetBinContent(outMig.GetXaxis().GetNbins()+1, 0.)
  outMig.SetBinContent(0, 0.)
  unfold.SubtractBackground(outMig, 'outMig')

  unfold.DoUnfold(0.)
  unfolded = unfold.GetOutput('unfoldedData' + str(uuid.uuid4()))

  if not splitStats: 
    return unfolded
  else:
    EMatSum = unfold.GetEmatrixSysBackgroundUncorr('outMig','outMigE'+str(uuid.uuid4()))
    for bkg in backgrounds.keys():
      EMatSum.Add(unfold.GetEmatrixSysBackgroundUncorr(bkg, bkg+'E'+str(uuid.uuid4())))

    EDat = unfold.GetEmatrixInput('dataE'+str(uuid.uuid4()))
    bkgStat = data.Clone()
    bkgStat.Reset('ICES')
    dataStat = bkgStat.Clone()
    for i in range(1, bkgStat.GetXaxis().GetNbins()):
      bkgStat.SetBinContent(i, EMatSum.GetBinContent(i, i)**0.5)
      dataStat.SetBinContent(i, EDat.GetBinContent(i, i)**0.5)

    return (unfolded, dataStat, bkgStat)

def getTotalDeviations(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict[''].Clone()
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
  nominal = histDict[''].Clone()
  rms = nominal.Clone()
  rms.Reset('ICES')

  for var in histDict.keys():
    histDict[var].Add(nominal, -1.)
    histDict[var].Multiply(histDict[var])
    rms.Add(histDict[var])

  nvars = len(histDict)-1

  for i in range(0, totalUp.GetXaxis().GetNbins()+1):
    rms.SetBinContent(i, (rms.GetBinContent(i)/nvars)**0.5)
  return rms

def getEnv(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict[''].Clone()
  maxUp = nominal.Clone()
  maxUp.Reset('ICES')
  maxDown = maxUp.Clone()

  for var in histDict.keys(): 
    histDict[var].Add(nominal, -1.)

  for i in range(0, nominal.GetNbinsX()+1):
    maxUp.SetBinContent(  i, max([hist.GetBinContent(i) for hist in histDict.values()]))
    maxDown.SetBinContent(i, min([hist.GetBinContent(i) for hist in histDict.values()]))

  return maxUp, maxDown

def sumDict(dictionary):
  histos = dictionary.values()
  dictSum = histos[0].Clone()
  for hist in histos[1:]:
    dictSum.Add(hist)
  return dictSum

def varyData(data, signalNom, signal):
  sig = signal.Clone()
  sig.Add(signalNom, -1.)
  sig.Divide(signalNom)
  data = data.Clone()
  for i in range(0, data.GetXaxis().GetNbins()+1):
    data.SetBinContent(i, data.GetBinContent(i)*(1.+ sig.GetBinContent(i)) )
    data.SetBinError(i, data.GetBinError(i)*(1.+ sig.GetBinContent(i)) )
  return data


#################### main code ####################

for dist in distList:
  log.info('running for '+ dist)

  histDict = pickle.load(open('/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-niceEstimDD-Ya/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  responseDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfcadB/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  outMigDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfcadB/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))

  # get nominal unfolded, with the statistics split into data and MC backgrounds
  response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  data, signalNom, backgroundsNom = getHistos(histDict, dist, '', blind = args.blind)
  totalNom = sumDict(backgroundsNom)
  totalNom.Add(signalNom)

  unfoldedNom, dataStat, bkgStat = getUnfolded(response, data, backgroundsNom, outMig, splitStats = True)
  unfoldedNom.Scale(1./lumiScales[args.year])
  dataStat.Scale(1./lumiScales[args.year])
  bkgStat.Scale(1./lumiScales[args.year])


  # get unfolded results for all systematic variations
  unfoldedDict, pdfDict, q2Dict = {}, {}, {}
  
  log.info('for these systematics data is varied instead of the response matrix: ' + str(sysVaryData))
  for var in varList:
    data, signal, backgrounds = getHistos(histDict, dist, var)
    if any([var.count(entry) for entry in sysVaryData]):
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      totalVar = sumDict(backgrounds)
      totalVar.Add(signal)
      data = varyData(data, totalNom, totalVar)
    else:
      try: 
        response = responseDict[dist.replace('unfReco','response_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      except:
        log.warning('no response matrix or outside migration histogram for ' +var + ' , check if there should be')
        response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

    # if any([var.count(entry) for entry in sysVaryData]):
      
    unfolded = getUnfolded(response, data, backgrounds, outMig)
    unfolded.Scale(1./lumiScales[args.year])
    if var.count('pdf'): pdfDict[var] = unfolded
    elif var.count('q2'): q2Dict[var] = unfolded
    else: unfoldedDict[var] = unfolded

  for direc in [('Down', -1.), ('Up', 1.)]:
    for bkgNorm in bkgNorms:
      data, signal, backgrounds = getHistos(histDict, dist, '', blind = args.blind)
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

      backgrounds[bkgNorm[0]].Scale(1. + bkgNorm[1]*direc[1])
      unfolded = getUnfolded(response, data, backgrounds, outMig)
      unfolded.Scale(1./lumiScales[args.year])

      unfoldedDict[bkgNorm[0]+direc[0]] = unfolded

    # Lumi uncertainty
    data, signal, backgrounds = getHistos(histDict, dist, '', blind = args.blind)
    response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']

    for bkg in backgrounds.values():
      bkg.Scale(1. + lumiunc[args.year] * direc[1])
    outMig.Scale(1. + lumiunc[args.year] * direc[1])
    unfolded = getUnfolded(response, data, backgrounds, outMig)
    unfolded.Scale(1./lumiScales[args.year])

    unfoldedDict['lumi'+direc[0]] = unfolded



  totalUp, totalDown = getTotalDeviations(unfoldedDict)

  pdfDict[''] = unfoldedNom.Clone()
  q2Dict[''] = unfoldedNom.Clone()
  q2Up, q2Down = getEnv(q2Dict)
  pdfrms = getRMS(pdfDict)
  # add q2 and pdf to totalUp and totalDown
  for i in range(1, totalUp.GetXaxis().GetNbins()):
    totalUp.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Up.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)
    totalDown.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Down.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)

  unfoldedMC = getUnfolded(response, signal, {}, outMig)
  unfoldedMC.Scale(1./lumiScales[args.year])


  # stick just data statistics onto unfoldedNom
  for i in range(1, unfoldedNom.GetXaxis().GetNbins()):
    unfoldedNom.SetBinError(i, dataStat.GetBinContent(i))

  # data stats, MC stats, and systematics onto this one
  unfoldedTotUnc = unfoldedNom.Clone()
  for i in range(1, unfoldedTotUnc.GetXaxis().GetNbins()):
    totalErr = (dataStat.GetBinContent(i)**2+ bkgStat.GetBinContent(i)**2+ max(abs(totalUp.GetBinContent(i)),abs(totalDown.GetBinContent(i)))**2)**0.5
    unfoldedTotUnc.SetBinError(i, totalErr)



# NOTE THIS BLOCK LOADS THE SYSTEMATICS BAND FOR THE THEORY, VERY SIMILAR TO PREUNF CODE

  # plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfcadB/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  # plMC = response.ProjectionY("PLMC")


  plMCDict, plMCpdfDict, plMCq2Dict = {}, {}, {}

  for var in theoVarList:
    plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfcadB/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    plMC.Scale(1./lumiScales[args.year])
    if var.count('pdf'): plMCpdfDict[var] = plMC
    elif var.count('q2'): plMCq2Dict[var] = plMC
    else: plMCDict[var] = plMC

  plMCpdfDict[''] = plMCDict[''].Clone()
  plMCq2Dict[''] = plMCDict[''].Clone()

  pltotalUp, pltotalDown = getTotalDeviations(plMCDict)
  plpdfrms = getRMS(plMCpdfDict)
  plq2Up, plq2Down = getEnv(plMCq2Dict)

  raise SystemExit(0)

  # add q2 and pdf to pltotalUp and pltotalDown
  for i in range(1, pltotalUp.GetXaxis().GetNbins()):
    pltotalUp.SetBinContent(i, (pltotalUp.GetBinContent(i)**2 + plq2Up.GetBinContent(i)**2 + plpdfrms.GetBinContent(i)**2)**0.5)
    pltotalDown.SetBinContent(i, (pltotalUp.GetBinContent(i)**2 + plq2Down.GetBinContent(i)**2 + plpdfrms.GetBinContent(i)**2)**0.5)

  plMCTot = plMCDict[''].Clone()

  pickle.dump(plMCTot, file('unfoldedHists/theo' + dist + args.year + '.pkl', 'w'))

  # raise SystemExit(0)

  for i in range(1, plMCTot.GetXaxis().GetNbins()):
    totalErr = (plMCTot.GetBinError(i)**2+ max(pltotalUp.GetBinContent(i),pltotalDown.GetBinContent(i))**2)**0.5
    plMCTot.SetBinError(i, totalErr)



  cunf = getRatioCanvas(dist)
# TOP PAD
  cunf.topPad.cd()


  unfoldedTotUnc.SetLineWidth(1)
  unfoldedTotUnc.SetLineColor(ROOT.kBlack)
  # unfoldedTotUnc.SetFillStyle(3244)
  # unfoldedTotUnc.SetFillColor(ROOT.kOrange)
  # unfoldedTotUnc.GetYaxis().SetRangeUser(0., unfoldedNom.GetMaximum()*0.2)
  unfoldedTotUnc.SetMinimum(0.)
  unfoldedTotUnc.GetYaxis().SetRangeUser(0., unfoldedNom.GetMaximum()*1.3)
  unfoldedTotUnc.GetXaxis().SetTitle(labels[dist][1])
  unfoldedTotUnc.GetYaxis().SetTitle('Fiducial cross section (fb)')
  unfoldedTotUnc.SetTitle('')
  unfoldedTotUnc.Draw('E X0')

  pickle.dump(unfoldedTotUnc, file('unfoldedHists/data' +  dist + args.year + '.pkl', 'w'))


  plMCTot2 = plMCTot.Clone()
  plMCTot2.SetLineWidth(1)
  plMCTot2.SetLineColor(ROOT.kRed)
  plMCTot2.Draw('same HIST')

  # stats on this are normally very small, ttgamma samples have great statistics (so not drawing it)
  # plMCTot.SetFillColor(ROOT.kRed)
  plMCTot.SetFillColorAlpha(ROOT.kRed, 0.4)
  # plMCTot.SetLineWidth(3)

  plMCTot.SetFillStyle(1001)
  plMCTot.Draw('same E2')
  unfoldedMC.Draw('same')

  # DRAW DATA
  unfoldedNom.SetLineColor(ROOT.kBlack)
  ROOT.gStyle.SetEndErrorSize(9)
  unfoldedNom.SetLineWidth(1)
  unfoldedNom.SetMarkerStyle(8)
  unfoldedNom.SetMarkerSize(1)
  unfoldedNom.Draw('same E1 X0')
  # unfoldedNom.Draw('same')

  legend = ROOT.TLegend(0.28,0.8,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(plMCTot,"Theory","l")
  legend.AddEntry(unfoldedMC,"Unfolded MC Signal","l")
  legend.AddEntry(unfolded,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"e")
  legend.Draw()

# RATIO PAD
  cunf.bottomPad.cd()


# TODO prediction might need some kind of scaling

  unfoldedRat = unfoldedNom.Clone('ratio')

  for i in range(1, unfoldedRat.GetXaxis().GetNbins()+1):
    unfoldedRat.SetBinError(i, unfoldedRat.GetBinError(i)/unfoldedRat.GetBinContent(i))
    unfoldedRat.SetBinContent(i, 1.)


  unfoldedRat.SetLineColor(ROOT.kBlack)
  unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  unfoldedRat.GetXaxis().SetTitle(labels[dist][1])
  unfoldedRat.GetYaxis().SetTitle('Pred. / Data')
  unfoldedRat.SetTitle('')
  unfoldedRat.GetXaxis().SetLabelSize(0.14)
  unfoldedRat.GetXaxis().SetTitleSize(0.14)
  unfoldedRat.GetXaxis().SetTitleOffset(1.2)
  unfoldedRat.GetYaxis().SetTitleSize(0.11)
  unfoldedRat.GetYaxis().SetTitleOffset(0.4)
  unfoldedRat.GetYaxis().SetRangeUser(0.4, 1.6)
  unfoldedRat.GetYaxis().SetNdivisions(3,5,0)
  unfoldedRat.GetYaxis().SetLabelSize(0.1)

  unfoldedRat.Draw('E1 X0')
  l1 = ROOT.TLine(unfoldedRat.GetXaxis().GetXmin(),1,unfoldedRat.GetXaxis().GetXmax(),1)
  l1.Draw()
  # unfoldedRat = unfoldedNom.Clone('ratio')
  # unfsystBand = unfoldedRat.Clone()
  
  # totalUp.Divide(unfsystBand)
  # totalDown.Divide(unfsystBand)

  # for i in range(0, unfsystBand.GetXaxis().GetNbins()+1):
  #   unfsystBand.SetBinError(i, max(totalUp.GetBinContent(i), totalDown.GetBinContent(i)))
  #   unfsystBand.SetBinContent(i, 1.)

  # unfsystBand.SetLineColor(ROOT.kBlack)
  # unfsystBand.SetFillColor(ROOT.kBlack)
  # unfsystBand.SetLineWidth(3)
  # unfsystBand.SetFillStyle(3244)
  # unfsystBand.SetMarkerSize(0)


  # unfsystBand.GetYaxis().SetRangeUser(0.4, 1.6)
  # unfsystBand.GetXaxis().SetTitle(labels[dist][1])
  # unfsystBand.GetYaxis().SetTitle('Data / Theory')
  # unfsystBand.SetTitle('')
  # unfsystBand.GetXaxis().SetLabelSize(0.14)
  # unfsystBand.GetXaxis().SetTitleSize(0.14)
  # unfsystBand.GetXaxis().SetTitleOffset(1.2)
  # unfsystBand.GetYaxis().SetTitleSize(0.11)
  # unfsystBand.GetYaxis().SetTitleOffset(0.4)
  # unfsystBand.GetYaxis().SetRangeUser(0.4, 1.6)
  # unfsystBand.GetYaxis().SetNdivisions(3,5,0)
  # unfsystBand.GetYaxis().SetLabelSize(0.1)
  # unfsystBand.Draw('E2')


  # unfoldedRat.Divide(plMCDict[''])
  # unfoldedRat.SetLineColor(ROOT.kBlack)
  # unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)

  # unfoldedRat.Draw('same E1 X0')


  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cunf.SaveAs('unfolded/'+ dist +'.pdf')
  cunf.SaveAs('unfolded/'+ dist +'.png')





#  pre-unfolding plots:

  dataNom, signalNom, backgroundsDict = getHistos(histDict, dist, '', blind = args.blind)
  backgroundsNom = sumDict(backgroundsDict)
  backgroundsNoUnc = backgroundsNom.Clone('')
  for i in range(0, backgroundsNoUnc.GetXaxis().GetNbins()+1):
    backgroundsNoUnc.SetBinError(i, 0.)

  dataTotStat = dataNom.Clone('')

  dataNom.Add(backgroundsNoUnc, -1.) 
  # dataNom is now data signal with data only stat uncertainties

  dataTotStat.Add(backgroundsNom, -1.)


  preUnfDict, preUnfpdfDict, preUnfq2Dict = {}, {}, {}
  
  preUnfDict[''] = dataNom.Clone()

  for var in varList:
    data, signal, backgroundsDict = getHistos(histDict, dist, var, blind = args.blind)
    backgrounds = sumDict(backgroundsDict)
    data.Add(backgrounds, -1.)
    data = varyData(data, signalNom, signal)
    if var.count('pdf'): preUnfpdfDict[var] = data
    elif var.count('q2'): preUnfq2Dict[var] = data
    else: preUnfDict[var] = data



  for direc in [('Down', -1.), ('Up', 1.)]:
    for bkgNorm in bkgNorms:
      data, signal, backgroundsDict = getHistos(histDict, dist, '', blind = args.blind)
      backgroundsDict[bkgNorm[0]].Scale(1. + bkgNorm[1]*direc[1])
      backgrounds = sumDict(backgroundsDict)
      data.Add(backgrounds, -1.)
      data = varyData(data, signalNom, signal)
      preUnfDict[bkgNorm[0]+direc[0]] = data
    
    # Lumi uncertainty

    data, signal, backgroundsDict = getHistos(histDict, dist, '', blind = args.blind)
    backgroundsDict[bkgNorm[0]].Scale(1. + bkgNorm[1]*direc[1])
    backgrounds = sumDict(backgroundsDict)
    backgrounds.Scale(1. + lumiunc[args.year] * direc[1])
    data.Add(backgrounds, -1.)
    data = varyData(data, signalNom, signal)
    preUnfDict['lumi'+direc[0]] = data

  totalUp, totalDown = getTotalDeviations(preUnfDict)

  preUnfpdfDict[''] = dataNom.Clone()
  preUnfq2Dict[''] = dataNom.Clone()
  q2Up, q2Down = getEnv(preUnfq2Dict)
  pdfrms = getRMS(preUnfpdfDict)
  # add q2 and pdf to totalUp and totalDown
  for i in range(1, totalUp.GetXaxis().GetNbins()):
    totalUp.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Up.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)
    totalDown.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Down.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)


  dataTotUnc = dataTotStat.Clone()
  for i in range(1, dataTotUnc.GetXaxis().GetNbins()):
    totalErr = (dataTotStat.GetBinError(i)**2+ max(totalUp.GetBinContent(i),totalDown.GetBinContent(i))**2)**0.5
    dataTotUnc.SetBinError(i, totalErr)



  cpreunf = getRatioCanvas(dist)
  cpreunf.topPad.cd()


  dataTotUnc.SetLineWidth(1)
  dataTotUnc.SetLineColor(ROOT.kBlack)
  dataTotUnc.SetMinimum(0.)
  dataTotUnc.GetYaxis().SetRangeUser(0., dataTotUnc.GetMaximum()*1.3)
  dataTotUnc.GetXaxis().SetTitle(labels[dist][1])
  dataTotUnc.GetYaxis().SetTitle('Events')
  dataTotUnc.SetTitle('')
  


  dataNom.SetLineColor(ROOT.kBlack)
  ROOT.gStyle.SetEndErrorSize(9)
  dataNom.SetLineWidth(1)
  dataNom.SetMarkerStyle(8)
  dataNom.SetMarkerSize(1)
  # dataNom.Draw('same E1 X0')

  signalNom.Draw('')

  dataNom.Draw('E1 X0 same')

  dataTotUnc.Draw('E same')

  legend = ROOT.TLegend(0.28,0.84,0.85,0.88)
  legend.SetBorderSize(0)
  legend.SetNColumns(2)
  legend.AddEntry(signalNom, "Theory","l")
  legend.AddEntry(dataNom,'data (' + str(lumiScalesRounded[args.year]) + '/fb)',"e")
  legend.Draw()




  cpreunf.bottomPad.cd()

  preUnfRat = dataNom.Clone()
  preunfsystBand = preUnfRat.Clone()
  
  totalUp.Divide(preUnfRat)
  totalDown.Divide(preUnfRat)
  preUnfRat.Divide(signalNom)
  # preUnfRat.SetLineColor(ROOT.kBlack)
  # preUnfRat.SetMarkerStyle(ROOT.kFullCircle)
  # preUnfRat.GetYaxis().SetRangeUser(0.4, 1.6)

  # preUnfRat.SetTitle('')
  # preUnfRat.GetXaxis().SetTitle(labels[dist][1])
  # preUnfRat.GetYaxis().SetTitle('Data / Theory')
  # preUnfRat.GetXaxis().SetLabelSize(0.14)

  # preUnfRat.GetXaxis().SetTitleSize(0.14)
  # preUnfRat.GetXaxis().SetTitleOffset(1.2)
  # preUnfRat.GetYaxis().SetTitleSize(0.11)
  # preUnfRat.GetYaxis().SetTitleOffset(0.4)
  # preUnfRat.GetYaxis().SetRangeUser(0.4, 1.6)
  # preUnfRat.GetYaxis().SetNdivisions(3,5,0)
  # preUnfRat.GetYaxis().SetLabelSize(0.1)


  for i in range(0, preunfsystBand.GetXaxis().GetNbins()+1):
    preunfsystBand.SetBinError(i, max(totalUp.GetBinContent(i), totalDown.GetBinContent(i)))
    preunfsystBand.SetBinContent(i, 1.)

  preunfsystBand.SetLineColor(ROOT.kBlack)
  preunfsystBand.SetFillColor(ROOT.kBlack)
  preunfsystBand.SetLineWidth(3)
  preunfsystBand.SetFillStyle(3244)
  preunfsystBand.SetMarkerSize(0)


  preunfsystBand.GetYaxis().SetRangeUser(0.4, 1.6)
  preunfsystBand.GetXaxis().SetTitle(labels[dist][0])
  preunfsystBand.GetYaxis().SetTitle('Data / Theory')
  preunfsystBand.SetTitle('')
  preunfsystBand.GetXaxis().SetLabelSize(0.14)
  preunfsystBand.GetXaxis().SetTitleSize(0.14)
  preunfsystBand.GetXaxis().SetTitleOffset(1.2)
  preunfsystBand.GetYaxis().SetTitleSize(0.11)
  preunfsystBand.GetYaxis().SetTitleOffset(0.4)
  preunfsystBand.GetYaxis().SetRangeUser(0.4, 1.6)
  preunfsystBand.GetYaxis().SetNdivisions(3,5,0)
  preunfsystBand.GetYaxis().SetLabelSize(0.1)
  preunfsystBand.Draw('E2')

  preUnfRat.Draw('E1 X0 same')

  # unfoldedRat.SetLineColor(ROOT.kBlack)
  # unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)

  # unfoldedRat.Draw('same E1 X0')


  cpreunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS Preliminary'), 11)
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.65,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'(13 TeV)'), 11)


  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.pdf')
  cpreunf.SaveAs('unfolded/preUnf_'+ dist +'.png')