#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018', 'RunII'])
# argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
argParser.add_argument('--unblind',   action='store_true', default=False,  help='unblind 2017 and 2018')
argParser.add_argument('--LOtheory',  action='store_true', default=False,  help='use LO sample for pdf and q2 uncertainty on the theory prediction')
argParser.add_argument('--norm',      action='store_true', default=False,  help='produce normalized output')
argParser.add_argument('--check',     action='store_true', default=False,  help='plot other python8 sample as crosscheck')
argParser.add_argument('--overview',  action='store_true', default=False,  help='print the average absolute impact of the systematics')
args = argParser.parse_args()


if args.year == '2016': args.unblind = True
args.unblind = True

import ROOT
import pdb
import pprint

ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gStyle.SetOptStat(0)

ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)

ROOT.gStyle.SetHatchesLineWidth(4)


from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
from ttg.tools.style import drawLumi, setDefault, drawTex
from ttg.tools.helpers import plotDir, getObjFromFile, lumiScales, lumiScalesRounded
import copy
import pickle
import numpy
import uuid


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


ROOT.gErrorIgnoreLevel = ROOT.kError
log.info("WARNING  --------------------------------------------------------------------------------------------------------------------------------------------------")
log.info("WARNING  all system messages lower than Errors are not being shown to prevent hunderds of RuntimeWarnings from being print, be aware of this when debugging")
log.info("WARNING  --------------------------------------------------------------------------------------------------------------------------------------------------")

def getPad(canvas, number):
  pad = canvas.cd(number)
  pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin()+0.05)
  pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin()-0.05)
  pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
  pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
  return pad

def getRatioCanvas(name):
  xWidth, yWidth, yRatioWidth = 1000, 950, 300
  yWidth           += yRatioWidth
  bottomMargin      = yWidth/float(yRatioWidth)*ROOT.gStyle.GetPadBottomMargin()
  yBorder           = yRatioWidth/float(yWidth)

  canvas = ROOT.TCanvas('c' + str(uuid.uuid4()).replace('-',''), name, xWidth, yWidth)
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

lumiunc = {'2016':0.012, '2017':0.023, '2018':0.025}
lumiunc['RunII'] = 0.016 

labels = {
          'unfReco_phPt' :            ('p_{T}(#gamma) [GeV]',  'p_{T}(#gamma) [GeV]'            , 'd#sigma / d p_{T}(#gamma) [fb/GeV]'),
          'unfReco_phLepDeltaR' :     ('#DeltaR(#gamma, l)',   '#DeltaR(#gamma, l)'             , 'd#sigma / d #DeltaR(#gamma, l) [fb]'),
          'unfReco_ll_deltaPhi' :     ('#Delta#phi(ll)',       '#Delta#phi(ll)'                 , 'd#sigma / d #Delta#phi(ll) [fb]'),
          'unfReco_jetLepDeltaR' :    ('#DeltaR(l, j)',        '#DeltaR(l, j)'                  , 'd#sigma / d #DeltaR(l, j) [fb]'),
          'unfReco_jetPt' :           ('p_{T}(j1) [GeV]',      'p_{T}(j1) [GeV]'                , 'd#sigma / d p_{T}(j1) [fb/GeV]'),
          'unfReco_ll_absDeltaEta' :  ('|#Delta#eta(ll)|',     '|#Delta#eta(ll)|'               , 'd#sigma / d |#Delta#eta(ll)| [fb]'),
          'unfReco_phBJetDeltaR' :    ('#DeltaR(#gamma, b)',   '#DeltaR(#gamma, b)'             , 'd#sigma / d #DeltaR(#gamma, b) [fb]'),
          'unfReco_phAbsEta' :        ('|#eta|(#gamma)',       '|#eta|(#gamma)'                 , 'd#sigma / d |#eta|(#gamma) [fb]'),
          'unfReco_phLep1DeltaR' :    ('#DeltaR(#gamma, l1)',       '#DeltaR(#gamma, l1)'       , 'd#sigma / d #DeltaR(#gamma, l1) [fb]'),
          'unfReco_phLep2DeltaR' :    ('#DeltaR(#gamma, l2)',       '#DeltaR(#gamma, l2)'       , 'd#sigma / d #DeltaR(#gamma, l2) [fb]'),
          'unfReco_Z_pt' :            ('p_{T}(ll) [GeV]',           'p_{T}(ll) [GeV]'           , 'd#sigma / d p_{T}(ll) [fb/GeV]'),
          'unfReco_l1l2_ptsum' :      ('p_{T}(l1)+p_{T}(l2) [GeV]', 'p_{T}(l1)+p_{T}(l2) [GeV]' , 'd#sigma / d p_{T}(l1)+p_{T}(l2) [fb/GeV]')
          }

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

varList = ['']




sysVaryData = ['bFrag', 'ephScale','ephRes','pu','pf','phSF','pvSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuStat','lSFElStat','lSFMuSyst','lSFElSyst','trigStatMM','trigStatEE','trigStatEM','trigSyst', 'lTracking']

if args.year == 'RunII': sysList = ['bFrag', 'isr','fsr','ephScale','ephRes','pu','pf','phSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuSyst','lSFElSyst', 'lTracking']
else: sysList = ['bFrag', 'isr','fsr','ephScale','ephRes','pu','pf','phSF','pvSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuStat','lSFElStat','lSFMuSyst','lSFElSyst','trigStatMM','trigStatEE','trigStatEM','trigSyst', 'lTracking']

varList += [sys + direc for sys in sysList for direc in ['Down', 'Up']]

if args.year == 'RunII':
  for var in ['lSFElStat', 'lSFMuStat', 'pvSF', 'trigStatEE', 'trigStatEM', 'trigStatMM', 'trigSyst', 'HFUC', 'AbsoluteUC', 'BBEC1UC', 'EC2UC', 'RelativeSampleUC']:
    for y in ['16', '17', '18']:
      for direc in ['Up', 'Down']:
        varList += [var + direc + y]

varList += ['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
varList += ['pdf_' + str(i) for i in range(0, 100)]
varList += ['colRec_' + str(i) for i in range(1, 4)]


theoSysList = []

theoVarList = ['']
theoVarList += [sys + direc for sys in theoSysList for direc in ['Down', 'Up']]

# theoVarList += ['colRec_' + str(i) for i in range(1, 4)]
# NOTE ColRec implemettation at PL was removed

NLOtheoVarList = []

if args.LOtheory:
  # theoVarList += ['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
  theoVarList += ['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
  # TODO switch!!!!!!!!!
  # theoVarList += ['pdf_' + str(i) for i in range(0, 100)]
  theoVarList += ['pdfSc_' + str(i) for i in range(0, 100)]
else:
  NLOtheoVarList = ['']
  if args.year == 'RunII':
    NLOtheoVarList += ['fdpUp', 'fdpDown', '2qUp', '2qDown']
  else:
    NLOtheoVarList += ['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
    NLOtheoVarList += ['pdfSc_' + str(i) for i in range(0, 100)]



bkgNorms = [('other_Other+#gamma (genuine)Other+#gamma (genuine)', 0.3),
            ('ZG_Z#gamma (genuine)Z#gamma (genuine)', 0.03),
            ('singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)', 0.1),
            ]


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

  # raise SystemExit(0)
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
  unfolded = unfold.GetOutput('unfoldedData' + 'c' + str(uuid.uuid4()).replace('-',''))

  if not splitStats: 
    return unfolded
  else:
    EMatSum = unfold.GetEmatrixSysBackgroundUncorr('outMig','outMigE'+'c' + str(uuid.uuid4()).replace('-',''))
    for bkg in backgrounds.keys():
      EMatSum.Add(unfold.GetEmatrixSysBackgroundUncorr(bkg, bkg+'E'+'c' + str(uuid.uuid4()).replace('-','')))

    EDat = unfold.GetEmatrixInput('dataE'+'c' + str(uuid.uuid4()).replace('-',''))
    bkgStat = data.Clone()
    bkgStat.Reset('ICES')
    dataStat = bkgStat.Clone()
    for i in range(1, bkgStat.GetXaxis().GetNbins()+1):
      bkgStat.SetBinContent(i, EMatSum.GetBinContent(i, i)**0.5)
      dataStat.SetBinContent(i, EDat.GetBinContent(i, i)**0.5)
    # pdb.set_trace()
    return (unfolded, dataStat, bkgStat, EDat)

def drawTauScan(response, data, backgrounds, outMig, outName, title):
  unfold = ROOT.TUnfoldDensity( response, mapping, ROOT.TUnfold.kRegModeCurvature, constraintMode, densityFlags )

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

  result = ROOT.TSpline3()
  iBest = unfold.ScanTau(200,0.000001,0.01, result, ROOT.TUnfoldDensity.kEScanTauRhoAvg)
  log.info("tau: " + str(unfold.GetTau()))

  tauCanvas = ROOT.TCanvas('c' + str(uuid.uuid4()).replace('-',''), outName, 700, 700)
  h= tauCanvas.DrawFrame(-6,0.15,-2,0.9)
  h.SetXTitle("log(#tau)")
  h.SetYTitle("average correlation coefficient")
  h.SetTitle(title)
  result.Draw('LP same')
  texl = ROOT.TLatex(-5.5,0.8,'#tau = ' + str(round(unfold.GetTau(), 8)))
  texl.SetTextSize(0.035)
  texl.Draw()
  # tauCanvas.SaveAs('tauScans/' + outName + '.pdf') #creates 2 page pdf for some reason
  tauCanvas.SaveAs('tauScans/' + outName + '.png',"EmbedFonts") 


def calcChi2(data, models):
  data = data.Clone()
  diff = data.Clone()
  for model in models:
    diff.Add(model, -1.)
  chi2 = 0
  for i in range( 1, diff.GetXaxis().GetNbins() + 1 ): 
    # chi2 += (diff.GetBinContent(i)**2.) / (data.GetBinError(i)**2.)
    chi2 += diff.GetBinContent(i)**2. / diff.GetBinContent(i)
  # chi2 = chi2 / data.GetXaxis().GetNbins()
  return chi2

def invertVar(nomHist, varHist):
    inverseHist = nomHist.Clone()
    for i in range(1, nomHist.GetNbinsX()+1):
      inverseHist.SetBinContent(i, max(2. * nomHist.GetBinContent(i) - varHist.GetBinContent(i), 0.))
    return inverseHist


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

def getDeviationOverview(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict['']
  sysImpacts = []
  for name in histDict.keys():
    vari = histDict[name].Clone()
    vari.Add(nominal, -1.)
    vari.Divide(nominal)
    sysImpacts.append((name, round( sum([abs(vari.GetBinContent(i)) for i in range(1,vari.GetXaxis().GetNbins()+1)])/vari.GetXaxis().GetNbins() * 100., 3)  ))
    # sysImpacts.append((name, round((histDict[name].Integral()-nominal)/nominal * 100., 3) )) 
  sysImpacts = sorted(sysImpacts, key=lambda tup: abs(tup[1]), reverse=True)
  pprint.pprint(sysImpacts)
  # pdb.set_trace()


def getRMS(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict[''].Clone()
  rms = nominal.Clone()
  rms.Reset('ICES')

  for var in histDict.keys():
    if var == '': continue
    histDict[var].Add(nominal, -1.)
    histDict[var].Multiply(histDict[var])
    rms.Add(histDict[var])

  nvars = len(histDict)-1

  for i in range(0, rms.GetXaxis().GetNbins()+1):
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
  for i in range(0, data.GetXaxis().GetNbins()+1):
    data.SetBinContent(i, data.GetBinContent(i)*(1.+ sig.GetBinContent(i)) )
    data.SetBinError(i, data.GetBinError(i)*(1.+ sig.GetBinContent(i)) )
  return data

def fracSigData(outMC, signal, bkgDict, data): # scale bins of data to (mc/signal) fraction, but with uncertainties of MC (keep rel unc the same). Used for outMig fraction
  # dataSig = data.Clone()
  # backgrounds = sumDict(bkgDict)
  # dataSig.Add(backgrounds, -1.)
  # outMC = outMC.Clone()
  # outMC.Scale(dataSig.Integral() / signal.Integral() )
  # # for i in range(1, dataSig.GetXaxis().GetNbins()+1):
  # #   if dataSig.GetBinContent(i) < 0:
  # #     # log.info(dist)
  # #     log.info(dataSig.GetBinContent(i) )
  # return outMC
  
  dataFrac = data.Clone()
  backgrounds = sumDict(bkgDict)
  dataFrac.Add(backgrounds, -1.)
  for i in range(1, dataFrac.GetXaxis().GetNbins()+1):
    if dataFrac.GetBinContent(i) < 0:   #in case data - backgrounds gets negative anywhere
      dataFrac.SetBinContent(i, outMC.GetBinContent(i))
      dataFrac.SetBinError(i,   outMC.GetBinError(i))
    else:
      dataFrac.SetBinContent(i, dataFrac.GetBinContent(i) * (outMC.GetBinContent(i) / signal.GetBinContent(i)) )
      dataFrac.SetBinError(i,   dataFrac.GetBinContent(i) * (outMC.GetBinError(i) / outMC.GetBinContent(i)) )
# NOTE if you take the bin by bin approach need to deal with cases where data-backgrounds < 0 ?
  return dataFrac

#################### main code ####################

log.info('for these systematics data is varied instead of the response matrix:')
log.info(str(sysVaryData))

for dist in distList:
  print('--------------------------------------------------------------------------------------------------------------------------------------------------')
  log.info('running for '+ dist)


  if args.year == 'RunII':
    histDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  else:
    histDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))

  responseDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  outMigDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))

  # get nominal unfolded, with the statistics split into data and MC backgrounds
  response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  data, signalNom, backgroundsNom = getHistos(histDict, dist, '', blind = not args.unblind)
  totalNom = sumDict(backgroundsNom)
  outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
  totalNom.Add(signalNom)

  unfoldedNom, dataStat, bkgStat, eMat = getUnfolded(response, data, backgroundsNom, outMig, splitStats = True)
  # returns correlation matrix as well. It's the data statistics only one
  # pdb.set_trace()
  unfoldedNom.Scale(1./lumiScales[args.year])
  dataStat.Scale(1./lumiScales[args.year])
  bkgStat.Scale(1./lumiScales[args.year])

  # log.info("chi2 before unfolding: " + str(calcChi2(data, backgroundsNom.values()+[signalNom]) / lumiScales[args.year] ))


  # draw tau scan  (no, we're not regularizing)
  drawTauScan(response, data, backgroundsNom, outMig, outName = 'tauScan'+dist+args.year, title = labels[dist][0].replace('reco ', '').replace('[GeV]', ''))

  # get unfolded results for all systematic variations
  unfoldedDict, pdfDict, q2Dict = {}, {}, {}
  

  for var in varList:
    data, signal, backgrounds = getHistos(histDict, dist, var, blind = not args.unblind)
    if any([var.count(entry) for entry in sysVaryData]):
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
      totalVar = sumDict(backgrounds)
      totalVar.Add(signal)
      data = varyData(data, totalNom, totalVar)
    else:
      try: 
        response = responseDict[dist.replace('unfReco','response_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
      except:
        log.warning('no response matrix or outside migration histogram for ' +var + ' , check if there should be')
        response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
        outMig = fracSigData(outMig, signalNom, backgroundsNom, data)

    # if any([var.count(entry) for entry in sysVaryData]):
      
    unfolded = getUnfolded(response, data, backgrounds, outMig)
    unfolded.Scale(1./lumiScales[args.year])
    if var.count('pdf'): pdfDict[var] = unfolded
    elif var.count('q2'): q2Dict[var] = unfolded
    elif var.count('colRec'): 
      unfoldedDict[var+'Up'] = unfolded
      unfoldedDict[var+'Down'] = invertVar(unfoldedNom, unfolded) 
    else: unfoldedDict[var] = unfolded

  for direc in [('Down', -1.), ('Up', 1.)]:
    for bkgNorm in bkgNorms:
      data, signal, backgrounds = getHistos(histDict, dist, '', blind = not args.unblind)
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
      outMig = fracSigData(outMig, signalNom, backgroundsNom, data)


      backgrounds[bkgNorm[0]].Scale(1. + bkgNorm[1]*direc[1])
      unfolded = getUnfolded(response, data, backgrounds, outMig)
      unfolded.Scale(1./lumiScales[args.year])

      unfoldedDict[bkgNorm[0]+direc[0]] = unfolded

    # Lumi uncertainty
    data, signal, backgrounds = getHistos(histDict, dist, '', blind = not args.unblind)
    response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    outMig = fracSigData(outMig, signalNom, backgroundsNom, data)


    # NOTE can just scale data right? needs to be applied to signal too, but not NP, hence the 0.91
    data.Scale(1. + (lumiunc[args.year] * direc[1] * 0.91))
    unfolded = getUnfolded(response, data, backgrounds, outMig)
    unfolded.Scale(1./lumiScales[args.year])

    unfoldedDict['lumi'+direc[0]] = unfolded

    # underlying event unc -> flat, signal only, can just scale unfolded
    unfoldedDict['UE'+direc[0]] = unfoldedNom.Clone()
    unfoldedDict['UE'+direc[0]].Scale(1. + 0.005 * direc[1])

  pdfDict[''] = unfoldedNom.Clone()
  q2Dict[''] = unfoldedNom.Clone()

  # pdb.set_trace()
  if args.norm:
    # replace data and MC statistics | do before unfoldedNom is normalized!
    dtStatDict = {"": unfoldedNom.Clone()}
    mcStatDict = {"": unfoldedNom.Clone()}
    dtStatDict[""].Scale(1./dtStatDict[""].Integral())
    mcStatDict[""].Scale(1./mcStatDict[""].Integral())
    for i in range(1, unfoldedNom.GetXaxis().GetNbins()+1):
      for direction in [(-1., 'Down'), (1.,'Up')]:
        dtStatVar = unfoldedNom.Clone()
        dtStatVar.SetBinContent(i, dtStatVar.GetBinContent(i) + direction[0]*dataStat.GetBinContent(i))
        dtStatVar.Scale(1./dtStatVar.Integral())
        dtStatDict['stat' + str(i) + direction[1]] = dtStatVar.Clone()
        mcStatVar = unfoldedNom.Clone()
        mcStatVar.SetBinContent(i, mcStatVar.GetBinContent(i) + direction[0]*bkgStat.GetBinContent(i))
        mcStatVar.Scale(1./mcStatVar.Integral())
        mcStatDict['stat' + str(i) + direction[1]] = mcStatVar.Clone()
    dataStat, dataStatDown = getTotalDeviations(dtStatDict)
    bkgStat, bkgStatDown = getTotalDeviations(mcStatDict)
    # could take the max of up and down, but they are practically the same
    # for i in range(1, unfoldedNom.GetXaxis().GetNbins()+1):
    #   dataStat.SetBinContent(max())
    #   bkgStat.SetBinContent(max())

    # normalize result and variations
    for his in unfoldedDict.values():
      his.Scale(1./his.Integral())
    for his in q2Dict.values():
      his.Scale(1./his.Integral())
    for his in pdfDict.values():
      his.Scale(1./his.Integral())
    unfoldedNom.Scale(1./unfoldedNom.Integral())

  if args.overview:
    getDeviationOverview(unfoldedDict)
  totalUp, totalDown = getTotalDeviations(unfoldedDict)
  q2Up, q2Down = getEnv(q2Dict)
  pdfrms = getRMS(pdfDict)

  # add q2 and pdf to totalUp and totalDown
  for i in range(1, totalUp.GetXaxis().GetNbins()+1):
    totalUp.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Up.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)
    totalDown.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Down.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)


  # stick just data statistics onto unfoldedNom
  # NOTE actually uncertainty on unfoldedNom/unfolding output might already be data statistics only
  for i in range(1, unfoldedNom.GetXaxis().GetNbins()+1):
    unfoldedNom.SetBinError(i, dataStat.GetBinContent(i))

  # data stats, MC stats, and systematics onto this one
  unfoldedTotUnc = unfoldedNom.Clone()
  for i in range(1, unfoldedTotUnc.GetXaxis().GetNbins()+1):
    totalErr = (dataStat.GetBinContent(i)**2+ bkgStat.GetBinContent(i)**2+ max(abs(totalUp.GetBinContent(i)),abs(totalDown.GetBinContent(i)))**2)**0.5
    unfoldedTotUnc.SetBinError(i, totalErr)

  # get the unfolded MC as well, for sanity checks
  unfoldedMC = getUnfolded(response, signal, {}, outMig)
  unfoldedMC.Scale(1./lumiScales[args.year])



# NOTE THIS BLOCK LOADS THE SYSTEMATICS BAND FOR THE THEORY
  plMCDict, plMCpdfDict, plMCq2Dict = {}, {}, {}

  plNLOpdfDict, plNLOq2Dict, plNLOMCDict = {}, {}, {}

  for var in theoVarList:
    plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    # plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + '2016' + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
    plMC.Scale(1./lumiScales[args.year])
    if var.count('pdf'): plMCpdfDict[var] = plMC.Clone()
    elif var.count('q2'): plMCq2Dict[var] = plMC.Clone()
    else: plMCDict[var] = plMC

  for var in NLOtheoVarList:
    plMC = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + ('_norm' if args.norm else '') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')+var]['ttgjetst#bar{t}#gamma NLO (genuine)']
    plMC.Scale(1./lumiScales[args.year])
    if var.count('pdf'): plNLOpdfDict[var] = plMC.Clone()
    elif var.count('q2'): plNLOq2Dict[var] = plMC.Clone()
    elif var == '': 
      plNLOpdfDict[''] = plMC.Clone()
      plNLOq2Dict[''] = plMC.Clone()
    else: plNLOMCDict[var] = plMC.Clone()
    # else: log.info(var + ' not supposed to be in NLO list')

  plMCpdfDict[''] = plMCDict[''].Clone()
  plMCq2Dict[''] = plMCDict[''].Clone()
  pltotalUp, pltotalDown = getTotalDeviations(plMCDict)


  if args.LOtheory:
    plpdfrms = getRMS(plMCpdfDict)
    plq2Up, plq2Down = getEnv(plMCq2Dict)
  else:
    if args.year == 'RunII':
      plpdfrms = plNLOMCDict['fdpUp'].Clone()
      plpdfrms.Add(plNLOq2Dict[''], -1)

      plq2Up = plNLOMCDict['2qUp'].Clone()
      plq2Down = plNLOMCDict['2qDown'].Clone()
      plq2Up.Add(plNLOq2Dict[''], -1)
      plq2Down.Add(plNLOq2Dict[''], -1)

      for i in range(1, pltotalUp.GetXaxis().GetNbins()+1):
        # pdb.set_trace()
        plpdfrms.SetBinContent(i, plpdfrms.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
        plq2Up.SetBinContent(i, plq2Up.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
        plq2Down.SetBinContent(i, plq2Down.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
      # TODO scale to LO sample yields
    else:
      plpdfrms = getRMS(plNLOpdfDict)
      plq2Up, plq2Down = getEnv(plNLOq2Dict)
      for i in range(1, pltotalUp.GetXaxis().GetNbins()+1):
        # pdb.set_trace()
        plpdfrms.SetBinContent(i, plpdfrms.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
        plq2Up.SetBinContent(i, plq2Up.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
        plq2Down.SetBinContent(i, plq2Down.GetBinContent(i) * plMCDict[''].GetBinContent(i) / plNLOpdfDict[''].GetBinContent(i))
    # TODO scale to LO sample yields
  
  # add q2 and pdf to pltotalUp and pltotalDown
  for i in range(1, pltotalUp.GetXaxis().GetNbins()+1):
    pltotalUp.SetBinContent(i, (pltotalUp.GetBinContent(i)**2 + plq2Up.GetBinContent(i)**2 + plpdfrms.GetBinContent(i)**2)**0.5)
    pltotalDown.SetBinContent(i, (pltotalUp.GetBinContent(i)**2 + plq2Down.GetBinContent(i)**2 + plpdfrms.GetBinContent(i)**2)**0.5)

  plMCTot = plMCDict[''].Clone()

  # raise SystemExit(0)

  for i in range(1, plMCTot.GetXaxis().GetNbins()+1):
    totalErr = (plMCTot.GetBinError(i)**2+ max(pltotalUp.GetBinContent(i),pltotalDown.GetBinContent(i))**2)**0.5
    plMCTot.SetBinError(i, totalErr)

  pickle.dump(plMCTot, file('unfoldedHists/theo' + dist + args.year + '.pkl', 'w'))


  cunf = getRatioCanvas(dist)
# TOP PAD
  cunf.topPad.cd()


  unfoldedTotUnc.SetLineWidth(3)
  unfoldedTotUnc.SetLineColor(ROOT.kBlack)
  unfoldedTotUnc.SetMinimum(0.)

  if args.norm:
    plMCTot.Scale(1/plMCTot.Integral())

  if dist in ['unfReco_phAbsEta']:
    unfoldedTotUnc.GetYaxis().SetRangeUser(0.001, max(unfoldedTotUnc.GetMaximum()*1.4, plMCTot.GetMaximum()*1.4))
  elif dist in ['unfReco_phBJetDeltaR']:
    unfoldedTotUnc.GetYaxis().SetRangeUser(0.001, max(unfoldedTotUnc.GetMaximum()*1.35, plMCTot.GetMaximum()*1.4))
  else:
    unfoldedTotUnc.GetYaxis().SetRangeUser(0.001, max(unfoldedTotUnc.GetMaximum()*1.2, plMCTot.GetMaximum()*1.2))
  unfoldedTotUnc.GetXaxis().SetTitle(labels[dist][1])
  unfoldedTotUnc.GetYaxis().SetTitle('')
  unfoldedTotUnc.GetYaxis().SetTitleOffset(1.55)

  unfoldedTotUnc.SetTitle('')
  unfoldedTotUnc.GetYaxis().SetTitleSize(0.24)
  unfoldedTotUnc.GetYaxis().SetTitleOffset(0.3)
  unfoldedTotUnc.GetYaxis().SetLabelSize(0.05)

  unfoldedTotUnc.Draw('E X0')

  pickle.dump(unfoldedTotUnc, file('unfoldedHists/data' +  dist + args.year + '.pkl', 'w'))

  plMCTot2 = plMCTot.Clone()


  # stats on this are normally very small, ttgamma samples have great statistics (so not drawing it)

  plMCTot.SetFillColorAlpha(ROOT.kBlack, 0.5)
  plMCTot.SetLineColor(ROOT.kBlack)

  plMCTot.SetFillStyle(3005)
  plMCTot.Draw('same E2')

  unfoldedMC.SetLineWidth(3)

  plMCTot2.SetLineWidth(3)
  plMCTot2.SetLineColor(ROOT.kBlack)
  plMCTot2.Draw('same HIST')



  plHWpp = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/herwigppfix/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilHWppt#bar{t}#gamma (genuine)']
  plHW7 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/herwig7fix/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilHW7t#bar{t}#gamma (genuine)']
  plPy8 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/pythia8fix/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))[dist.replace('unfReco','fid_unfReco')]['TTGamma_DilPy8t#bar{t}#gamma (genuine)']
  plHWpp.Scale(1./lumiScales['2016'])
  plHW7.Scale(1./lumiScales['2016'])
  plPy8.Scale(1./lumiScales['2016'])

  if args.norm:
    plHWpp.Scale(1/plHWpp.Integral())
    plHW7.Scale(1/plHW7.Integral())
    plPy8.Scale(1/plPy8.Integral())

  plHWpp.Draw('hist same')
  plHW7.Draw('hist same')
  if args.check:
    plPy8.Draw('hist same')

  plHWpp.SetLineWidth(3)
  plHW7.SetLineWidth(3)
  plPy8.SetLineWidth(3)

  plHWpp.SetLineColor(ROOT.kRed)
  plHW7.SetLineColor(ROOT.kBlue)
  plHWpp.SetLineStyle(7)
  plHW7.SetLineStyle(2)

  plPy8.SetLineColor(ROOT.kMagenta+2)

  # DRAW DATA
  unfoldedNom.SetLineColor(ROOT.kBlack)
  ROOT.gStyle.SetEndErrorSize(9)
  unfoldedNom.SetLineWidth(3)
  unfoldedNom.SetMarkerStyle(8)
  unfoldedNom.SetMarkerSize(2)
  unfoldedNom.Draw('same E1 X0')

  if dist in ['unfReco_phBJetDeltaR', 'unfReco_ll_deltaPhi', 'unfReco_phLep1DeltaR']: #legend on the left
    legend = ROOT.TLegend(1.1-0.92,0.61,1.1-0.62,0.87)
  else:
    legend = ROOT.TLegend(0.62,0.61,0.92,0.87)
  
  legend.SetBorderSize(0)
  legend.SetNColumns(1)
  legend.AddEntry(unfoldedNom,'Data',"PE")
  legend.AddEntry(plMCTot2,"MG5+Pythia8","l")
  legend.AddEntry(plMCTot,"Theory unc.","f")
  # legend.AddEntry(unfoldedMC,"Unfolded MC Signal","l")
  legend.AddEntry(plHWpp,'MG5+Herwig++',"l")
  legend.AddEntry(plHW7,'MG5+Herwig7',"l")
  if args.check:
    legend.AddEntry(plPy8,'PYTHIA8 ALT',"l")
  legend.Draw()


# RATIO PAD
  cunf.bottomPad.cd()


# TODO prediction might need some kind of scaling

  unfoldedRat = unfoldedTotUnc.Clone('ratio')

  for i in range(1, unfoldedRat.GetXaxis().GetNbins()+1):
    unfoldedRat.SetBinError(i, unfoldedRat.GetBinError(i)/unfoldedRat.GetBinContent(i))
    unfoldedRat.SetBinContent(i, 1.)

  theoRat = plMCTot2.Clone()
  theRatBand = plMCTot.Clone()
  plHWppRat = plHWpp.Clone()
  plHW7Rat = plHW7.Clone()
  plPy8Rat = plPy8.Clone()

  for i in range(1, theoRat.GetXaxis().GetNbins()+1):
    theoRat.SetBinError(i, theoRat.GetBinError(i)/unfoldedTotUnc.GetBinContent(i))
    theoRat.SetBinContent(i, theoRat.GetBinContent(i)/unfoldedTotUnc.GetBinContent(i))
    theRatBand.SetBinError(i, theRatBand.GetBinError(i)/unfoldedTotUnc.GetBinContent(i))
    theRatBand.SetBinContent(i, theRatBand.GetBinContent(i)/unfoldedTotUnc.GetBinContent(i))
    plHWppRat.SetBinContent(i, plHWppRat.GetBinContent(i)/unfoldedTotUnc.GetBinContent(i))
    plHW7Rat.SetBinContent(i, plHW7Rat.GetBinContent(i)/unfoldedTotUnc.GetBinContent(i))
    plPy8Rat.SetBinContent(i, plPy8Rat.GetBinContent(i)/unfoldedTotUnc.GetBinContent(i))

  unfoldedRat.SetLineColor(ROOT.kBlack)
  unfoldedRat.SetMarkerStyle(ROOT.kFullCircle)
  unfoldedRat.SetMarkerSize(2)
  theRatBand.GetYaxis().SetRangeUser(0.36, 1.64)
  theRatBand.GetXaxis().SetTitle(labels[dist][1])
  # theRatBand.GetYaxis().SetTitle('Pred. / data')
  theRatBand.GetYaxis().SetTitle('')
  theRatBand.SetTitle('')
  theRatBand.GetXaxis().SetLabelSize(0.15)
  theRatBand.GetXaxis().SetTitleSize(0.18)
  theRatBand.GetXaxis().SetTitleOffset(1)
  theRatBand.GetYaxis().SetTitleSize(0.21)
  theRatBand.GetYaxis().SetTitleOffset(0.3)
  theRatBand.GetYaxis().SetRangeUser(0.38, 1.62)
  theRatBand.GetYaxis().SetNdivisions(3,5,0)
  theRatBand.GetYaxis().SetLabelSize(0.15)

  theRatBand.Draw('E2')


  unfoldedRat.Draw('E X0 same')

  plHWppRat.Draw('same hist')
  plHW7Rat.Draw('same hist')
  if args.check:
    plPy8Rat.Draw('same hist')

  theoRat.Draw('same HIST')


  l1 = ROOT.TLine(unfoldedRat.GetXaxis().GetXmin(),1,unfoldedRat.GetXaxis().GetXmax(),1)
  l1.Draw()

  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.04,'CMS #bf{#it{Preliminary}}'), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()+0.04,  1-ROOT.gStyle.GetPadTopMargin()+0.04, ('#bf{%3.0f fb^{-1} (13 TeV)}'%lumiScalesRounded[args.year])), 31)

  if args.norm:
    drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  1-ROOT.gStyle.GetPadTopMargin(), '#bf{' + labels[dist][2] + '}'), 31, size=0.042, angle=90)
  else:
    drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  1-ROOT.gStyle.GetPadTopMargin(), '#bf{Fiducial cross section [fb]}'), 31, size=0.042, angle=90)
  drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  0.07,'#bf{Pred. / data}'), 11, size=0.042, angle=90)


  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.pdf') 
  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.png')
  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.root')