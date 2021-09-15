#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--year',      action='store',      default=None,                 help='Only run for a specific year', choices=['2016', '2017', '2018', 'RunII'])
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
ROOT.gStyle.SetPaintTextFormat("3.2f")
# ROOT.gStyle.SetPalette(ROOT.kRedBlue)


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
log.info("WARNING  all system messages lower than Errors are not being shown to prevent hunderds of RuntimeWarnings from being printed, be aware of this when debugging")
log.info("WARNING  --------------------------------------------------------------------------------------------------------------------------------------------------")

def getPad(canvas, number):
  pad = canvas.cd(number)
  pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin()+0.05)
  pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin()-0.05)
  pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
  pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
  return pad

def getRatioCanvas(name):
  xWidth, yWidth, yRatioWidth = 1000, 720, 220
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
  'unfReco_phPt',
  'unfReco_phLepDeltaR',
  'unfReco_jetLepDeltaR',
  'unfReco_jetPt',
  'unfReco_ll_absDeltaEta',
  'unfReco_ll_deltaPhi',
  'unfReco_phAbsEta',
  'unfReco_phBJetDeltaR',
  'unfReco_phLep1DeltaR',
  'unfReco_phLep2DeltaR',
  'unfReco_Z_pt',
  'unfReco_l1l2_ptsum'
  ]

varList = ['']


sysVaryData = ['bFrag', 'ephScale','ephRes','pu','pf','phSF','pvSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuStat','lSFElStat','lSFMuSyst','lSFElSyst','trigStatMM','trigStatEE','trigStatEM','trigSyst', 'lTracking', 'zgcorrstat5', 'zgcorrstat6', 'zgcorrstat7', 'zgcorrstat8', 'zgcorrstat9']

if args.year == 'RunII': sysList = ['bFrag', 'isr','fsr','ephScale','ephRes','pu','pf','phSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuSyst','lSFElSyst', 'lTracking', 'zgcorrstat5', 'zgcorrstat6', 'zgcorrstat7', 'zgcorrstat8', 'zgcorrstat9']
else: sysList = ['bFrag', 'isr','fsr','ephScale','ephRes','pu','pf','phSF','pvSF','bTagl','bTagbUC','bTagbCO','JER','NPFlat','NPHigh','lSFMuStat','lSFElStat','lSFMuSyst','lSFElSyst','trigStatMM','trigStatEE','trigStatEM','trigSyst', 'lTracking', 'zgcorrstat5', 'zgcorrstat6', 'zgcorrstat7', 'zgcorrstat8', 'zgcorrstat9']

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
    else:backgrounds[process] = hist.Clone()
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
    # statistical uncertainties backgrounds
    EMatSum = unfold.GetEmatrixSysBackgroundUncorr('outMig','outMigE'+'c' + str(uuid.uuid4()).replace('-',''))
    for bkg in backgrounds.keys():
      EMatSum.Add(unfold.GetEmatrixSysBackgroundUncorr(bkg, bkg+'E'+'c' + str(uuid.uuid4()).replace('-','')))

    # statistical uncertainty on response matrix
    EMatSum.Add(unfold.GetEmatrixSysUncorr('respoMatStat'))

    EDat = unfold.GetEmatrixInput('dataE'+'c' + str(uuid.uuid4()).replace('-',''))
    bkgStat = data.Clone()
    bkgStat.Reset('ICES')
    dataStat = bkgStat.Clone()
    for i in range(1, bkgStat.GetXaxis().GetNbins()+1):
      bkgStat.SetBinContent(i, EMatSum.GetBinContent(i, i)**0.5)
      dataStat.SetBinContent(i, EDat.GetBinContent(i, i)**0.5)
    # pdb.set_trace()
    return (unfolded, dataStat, bkgStat, EDat, EMatSum)

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


def calcChi2(data, pred):
  diff = data.Clone()
  diff.Add(pred, -1.)
  chi2 = 0.
  for i in range( 1, diff.GetXaxis().GetNbins() + 1 ): 
    chi2 += diff.GetBinContent(i)**2. / pred.GetBinContent(i)
  return chi2


def calcNewChi2(data, pred, covars, normalized = False):
  # as described here: https://arxiv.org/abs/1904.05237
  cov = covars[0].Clone()
  for i in covars[1:]:
    cov.Add(i)

  res = data.Clone()
  res.Add(pred, -1)

  # make matrices
  nxy = cov.GetXaxis().GetNbins()
  mat = ROOT.TMatrixD(nxy+2, nxy+2, cov.GetArray())
  rhor = ROOT.TMatrixD(1, nxy+2, res.GetArray())
  rvert = ROOT.TMatrixD(nxy+2, 1, res.GetArray())

  # chop off under and overflows 
  # mat = mat.GetSub(1,nxy,1,nxy)
  # rhor = rhor.GetSub(0,0,1,nxy)
  # rvert = rvert.GetSub(1,nxy,0,0)

  if normalized:
    # chop off under and overflows  + 1 extra bin
    mat = mat.GetSub(1,nxy-1,1,nxy-1)
    rhor = rhor.GetSub(0,0,1,nxy-1)
    rvert = rvert.GetSub(1,nxy-1,0,0)
    mat.Invert()
    mul1 = ROOT.TMatrixD(1, nxy-1)
  else:
    # chop off under and overflows
    mat = mat.GetSub(1,nxy,1,nxy)
    rhor = rhor.GetSub(0,0,1,nxy)
    rvert = rvert.GetSub(1,nxy,0,0)
    mat.Invert()
    mul1 = ROOT.TMatrixD(1, nxy)

  mul1.Mult(rhor, mat)
  mul2 = ROOT.TMatrixD(1, 1)
  mul2.Mult(mul1, rvert)

  chi = mul2(0,0)
  return chi


def invertVar(nomHist, varHist):
    inverseHist = nomHist.Clone()
    for i in range(1, nomHist.GetNbinsX()+1):
      inverseHist.SetBinContent(i, max(2. * nomHist.GetBinContent(i) - varHist.GetBinContent(i), 0.))
    return inverseHist


def getTotalDeviations(inputHists):
# ensures histograms are not modified here, keep them correct for later use
  histDict  = {key: inputHists[key].Clone() for key in inputHists.keys()}

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


def getTotalDeviationsAvg(inputHists):
# ensures histograms are not modified here, keep them correct for later use
  histDict  = {key: inputHists[key].Clone() for key in inputHists.keys()}

  nominal = histDict[''].Clone()
  totSys = nominal.Clone()
  totSys.Reset('ICES')

  ups = [name for name in histDict.keys() if name.count('Up')]
  for sys in ups:
    histDict[sys].Add(nominal, -1.)
    histDict[sys].Multiply(histDict[sys])
    dsys = sys.replace('Up','Down')
    histDict[dsys].Add(nominal, -1.)
    histDict[dsys].Multiply(histDict[dsys])
    histDict[sys].Add(histDict[dsys])
    histDict[sys].Scale(0.5)
    totSys.Add(histDict[sys])

  for i in range(0, totSys.GetXaxis().GetNbins()+1):
    totSys.SetBinContent(i, totSys.GetBinContent(i)**0.5)
  return totSys

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
    if var == '': continue
    histDict[var].Add(nominal, -1.)

  for i in range(0, nominal.GetNbinsX()+1):
    maxUp.SetBinContent(  i, max([histDict[key].GetBinContent(i) for key in histDict.keys() if not key=='']))
    maxDown.SetBinContent(i, min([histDict[key].GetBinContent(i) for key in histDict.keys() if not key=='']))

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


tabulated = {}

def tabulate(name, dist, dtStat, mcStat, systUp, systDown):
  tabulated[name] = ([],[],[],[],[]) 
  for i in range(1, dist.GetXaxis().GetNbins()+1):
    # if name.count('sum'):
      # pdb.set_trace()
    if dist.GetXaxis().GetBinLowEdge(i).is_integer() and dist.GetXaxis().GetBinLowEdge(i+1).is_integer():
      tabulated[name][0].append( '$' + str( int(dist.GetXaxis().GetBinLowEdge(i))) + ' - ' + str(int(dist.GetXaxis().GetBinLowEdge(i+1))) + '$')
    else:
      tabulated[name][0].append( '$' + str( dist.GetXaxis().GetBinLowEdge(i)) + ' - ' + str(dist.GetXaxis().GetBinLowEdge(i+1)) + '$')
    tabulated[name][1].append( '$' + str( round( dist.GetBinContent(i), 2)) + '$')
    tabulated[name][2].append( '$' + str( round( dtStat.GetBinContent(i), 2)) + '$')
    tabulated[name][3].append( '$' + str( round( mcStat.GetBinContent(i), 2)) + '$')
    # tabulated[name][4].append( '$' + str( round( max(abs(systUp.GetBinContent(i)),abs(systDown.GetBinContent(i))) , 2)) + '$')
    tabulated[name][4].append( '$' + str( round(systUp.GetBinContent(i)  ,2)) + '$')

def getCovarHists(inputHists, template):
  template = template.Clone()
  template.Reset('ICES')
  # pass eMat to this funtion to easily get the correct binning
  nominal = inputHists[''].Clone()
  covarMat = {}
  for name, hist in inputHists.iteritems():
    covarMat[name] = template.Clone(str(uuid.uuid4()).replace('-',''))
    for i in range(1, hist.GetXaxis().GetNbins()+1):
      for j in range(1, hist.GetXaxis().GetNbins()+1):
        covarMat[name].SetBinContent(i, j, (hist.GetBinContent(i)-nominal.GetBinContent(i))*(hist.GetBinContent(j)-nominal.GetBinContent(j)))
  # pdb.set_trace()
  return covarMat



def getCovarHistsFromDev(inputHists, template):
  template = template.Clone()
  template.Reset('ICES')
  # pass eMat to this funtion to easily get the correct binning
  covarMat = {}
  for name, hist in inputHists.iteritems():
    covarMat[name] = template.Clone(str(uuid.uuid4()).replace('-',''))
    for i in range(1, hist.GetXaxis().GetNbins()+1):
      for j in range(1, hist.GetXaxis().GetNbins()+1):
        covarMat[name].SetBinContent(i, j, hist.GetBinContent(i)*hist.GetBinContent(j))
  return covarMat
#################### main code ####################

log.info('for these systematics data is varied instead of the response matrix:')
log.info(str(sysVaryData))

for dist in distList:
  print('--------------------------------------------------------------------------------------------------------------------------------------------------')
  log.info('running for '+ dist)


  if args.year == 'RunII':
    histDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/phoCBfull-niceEstimDD-RE/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  else:
    histDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/phoCBfull-niceEstimDD-RE/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))

  responseDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  outMigDict = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/' + args.year + '/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))

  # get nominal unfolded, with the statistics split into data and MC backgrounds
  response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  data, signalNom, backgroundsNom = getHistos(histDict, dist, '', blind = not args.unblind)
  totalNom = sumDict(backgroundsNom)
  outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
  totalNom.Add(signalNom)

  unfoldedNom, dataStat, bkgStat, eMat, eMatBkg = getUnfolded(response, data, backgroundsNom, outMig, splitStats = True)

  # pdb.set_trace()

  # returns correlation matrix as well. It's the data statistics only one
  # pdb.set_trace()
  eMat.Scale((1./lumiScales[args.year])**2.)
  eMatBkg.Scale((1./lumiScales[args.year])**2.)
  unfoldedNom.Scale(1./lumiScales[args.year])
  dataStat.Scale(1./lumiScales[args.year])
  bkgStat.Scale(1./lumiScales[args.year])




  # draw tau scan  (no, we're not regularizing)
  drawTauScan(response, data, backgroundsNom, outMig, outName = 'tauScan'+dist+args.year, title = labels[dist][0].replace('reco ', '').replace('[GeV]', ''))

  # get unfolded results for all systematic variations
  unfoldedDict, pdfDict, q2Dict = {}, {}, {}
  

  for var in varList:
    data, signal, backgrounds = getHistos(histDict, dist, var, blind = not args.unblind)
    if any([var.count(entry) for entry in sysVaryData]):
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
      totalVar = sumDict(backgrounds)
      totalVar.Add(signal)
      data = varyData(data, totalNom, totalVar)
    else:
      try: 
        response = responseDict[dist.replace('unfReco','response_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')+var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
        outMig = fracSigData(outMig, signalNom, backgroundsNom, data)
      except:
        log.warning('no response matrix or outside migration histogram for ' +var + ' , check if there should be')
        response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
        outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
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
      response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      outMig = fracSigData(outMig, signalNom, backgroundsNom, data)


      backgrounds[bkgNorm[0]].Scale(1. + bkgNorm[1]*direc[1])
      unfolded = getUnfolded(response, data, backgrounds, outMig)
      unfolded.Scale(1./lumiScales[args.year])

      unfoldedDict[bkgNorm[0]+direc[0]] = unfolded

    # ZG corr flat uncertainty
    data, signal, backgrounds = getHistos(histDict, dist, '', blind = not args.unblind)
    response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    outMig = fracSigData(outMig, signalNom, backgroundsNom, data)

    backgrounds['ZG_Z#gamma (genuine)Z#gamma (genuine)'].Scale(1. + 0.018*direc[1])
    unfolded = getUnfolded(response, data, backgrounds, outMig)
    unfolded.Scale(1./lumiScales[args.year])

    unfoldedDict['ZG_sigcr'+direc[0]] = unfolded

    # Lumi uncertainty
    data, signal, backgrounds = getHistos(histDict, dist, '', blind = not args.unblind)
    response = responseDict[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    outMig = outMigDict[dist.replace('unfReco','out_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    outMig = fracSigData(outMig, signalNom, backgroundsNom, data)


    # NOTE can just scale data right? needs to be applied to signal too, but not NP, hence the 0.91
    dtScale = data.Clone()
    # pdb.set_trace()
    dtScale.Scale(1. + (lumiunc[args.year] * direc[1] * 0.91))
    outMig.Scale(1. + (lumiunc[args.year] * direc[1] * 0.91))

    unfolded = getUnfolded(response, dtScale, backgrounds, outMig)
    
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
  # totalUp, totalDown = getTotalDeviations(unfoldedDict)
  totalSys = getTotalDeviationsAvg(unfoldedDict)

  q2Up, q2Down = getEnv(q2Dict)
  pdfrms = getRMS(pdfDict)
  

  # produce covariance matrices to draw later
  covarInput = {}
  covarInput['q2Up']    = unfoldedDict[''].Clone()
  covarInput['q2Up'].Add(q2Up)
  covarInput['q2Down']  = unfoldedDict[''].Clone()
  covarInput['q2Down'].Add(q2Down)
  covarInput['pdfUp']   = unfoldedDict[''].Clone()
  covarInput['pdfUp'].Add(pdfrms)
  covarInput['pdfDown'] = unfoldedDict[''].Clone()
  covarInput['pdfDown'].Add(pdfrms, -1)
  covarInput.update(unfoldedDict)

  pickle.dump(covarInput, file('unfoldedHists/dict' +  dist + args.year + ('_norm' if args.norm else '')  +'.pkl', 'w'))

  covars = getCovarHists(covarInput, eMat)

  pickle.dump(covars, file('unfoldedHists/covMat' +  dist + args.year + ('_norm' if args.norm else '')  +'.pkl', 'w'))

  covTot = covars[''].Clone()
  covTot.Reset('ICES') # just to be sure
  for key in [i for i in covars.keys() if i.count('Up')]:
    covh = covars[key].Clone()
    covh.Add(covars[key.replace('Up','Down')])
    covh.Scale(0.5)
    covTot.Add(covh)

  if args.norm:
    dtStatCovs = getCovarHists(dtStatDict, eMat)
    bkgStatCovs = getCovarHists(mcStatDict, eMat)
    dtStatTot = dtStatCovs[''].Clone()
    bkgStatTot = bkgStatCovs[''].Clone()
    dtStatTot.Reset('ICES') # just to be sure
    bkgStatTot.Reset('ICES') # just to be sure
    for key in [i for i in dtStatCovs.keys() if i.count('Up')]:
      dtStatTot.Add(dtStatCovs[key])
      bkgStatTot.Add(bkgStatCovs[key])
    eMat = dtStatTot.Clone()
    eMatBkg = bkgStatTot.Clone()

  # pdb.set_trace()
  # add background stats (+resp matrix stats) to syst covar matrix
  covTot.Add(eMatBkg)

  # add q2 and pdf to totalUp and totalDown
  # for i in range(1, totalUp.GetXaxis().GetNbins()+1):
  #   totalUp.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Up.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)
  #   totalDown.SetBinContent(i, (totalUp.GetBinContent(i)**2 + q2Down.GetBinContent(i)**2 + pdfrms.GetBinContent(i)**2)**0.5)

  for i in range(1, totalSys.GetXaxis().GetNbins()+1):
    totalSys.SetBinContent(i, (totalSys.GetBinContent(i)**2 + (q2Up.GetBinContent(i)**2 + q2Down.GetBinContent(i)**2)/2. + pdfrms.GetBinContent(i)**2)**0.5)

  # stick just data statistics onto unfoldedNom
  # NOTE actually uncertainty on unfoldedNom/unfolding output might already be data statistics only
  for i in range(1, unfoldedNom.GetXaxis().GetNbins()+1):
    unfoldedNom.SetBinError(i, dataStat.GetBinContent(i))

  # data stats, MC stats, and systematics onto this one
  # pdb.set_trace()
  unfoldedTotUnc = unfoldedNom.Clone()
  for i in range(1, unfoldedTotUnc.GetXaxis().GetNbins()+1):
    # totalErr = (dataStat.GetBinContent(i)**2+ bkgStat.GetBinContent(i)**2+ max(abs(totalUp.GetBinContent(i)),abs(totalDown.GetBinContent(i)))**2)**0.5
    totalErr = (dataStat.GetBinContent(i)**2+ bkgStat.GetBinContent(i)**2+ totalSys.GetBinContent(i)**2)**0.5

    unfoldedTotUnc.SetBinError(i, totalErr)

  # tabulate(dist, unfoldedTotUnc, dataStat, bkgStat, totalUp, totalDown)
  tabulate(dist, unfoldedTotUnc, dataStat, bkgStat, totalSys, totalSys)


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

  # pickle.dump(plNLOq2Dict,  file('unfoldedHists/theQ2dict' +  dist + args.year + ('_norm' if args.norm else '')  +'.pkl', 'w'))
  # pickle.dump(plNLOpdfDict, file('unfoldedHists/thePDFdict' +  dist + args.year + ('_norm' if args.norm else '')  +'.pkl', 'w'))
  # pdb.set_trace()


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

  # pdb.set_trace()

  theoCovs = getCovarHistsFromDev({'plq2i': plq2Up, 'plpdfi': plpdfrms}, eMat)


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
    unfoldedTotUnc.GetYaxis().SetRangeUser(0.001, max(unfoldedTotUnc.GetMaximum()*1.44, plMCTot.GetMaximum()*1.44))
  elif dist in ['unfReco_phBJetDeltaR']:
    unfoldedTotUnc.GetYaxis().SetRangeUser(0.001, max(unfoldedTotUnc.GetMaximum()*1.44, plMCTot.GetMaximum()*1.44))
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

  # plHWpp.Draw('hist same')
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


  log.info(labels[dist][0] + 'simplistic Chi^2: ' + str(calcChi2(unfoldedNom, plMCTot)))

  chi2 = calcNewChi2(unfoldedNom, plMCTot, [covTot, eMat, theoCovs['plpdfi'], theoCovs['plq2i']], normalized = args.norm)
  ndof = unfoldedNom.GetXaxis().GetNbins() - (1 if args.norm else 0)
  log.info(labels[dist][0] + 'Chi^2: ' + str(chi2))
  log.info('nbins / dof ' + str(ndof))


  if dist in ['unfReco_phBJetDeltaR', 'unfReco_ll_deltaPhi', 'unfReco_phLep1DeltaR']: #legend on the left
    legend = ROOT.TLegend(1.1-0.92,0.60,1.1-0.61,0.87)
    # texchi = ROOT.TLatex(1.1-0.92+0.01,0.59,'#chi^{2} / ndof = ' + str(round(chi2, 2)) + ' / ' + str(ndof))
  elif dist in ['unfReco_phLep2DeltaR']: #legend in the middle
    legend = ROOT.TLegend(0.61-0.2,0.60,0.92-0.2,0.87)
    # texchi = ROOT.TLatex(0.62-0.2+0.01,0.59,'#chi^{2} / ndof = ' + str(round(chi2, 2)) + ' / ' + str(ndof))
  else:
    legend = ROOT.TLegend(0.61,0.60,0.92,0.87)
    # texchi = ROOT.TLatex(0.63,0.59,'#chi^{2} / ndof = ' + str(round(chi2, 2)) + ' / ' + str(ndof))
    
  # texchi.SetTextFont(42)
  # texchi.SetNDC()
  # texchi.SetTextSize(0.038)
  # texchi.Draw()
  
  legend.SetBorderSize(0)
  legend.SetNColumns(1)
  legend.AddEntry(unfoldedNom,'Data',"PE")
  legend.AddEntry(plMCTot2,"MG5+Pythia8","l")
  legend.AddEntry(plMCTot,"Theory unc.","f")
  legend.AddEntry(plMCTot,'#chi^{2} / dof = ' + str(round(chi2, 2)) + ' / ' + str(ndof),"")
  # legend.AddEntry(unfoldedMC,"Unfolded MC Signal","l")
  # legend.AddEntry(plHWpp,'MG5+Herwig++',"l")
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

  if args.norm and not dist in ['unfReco_jetPt', 'unfReco_Z_pt', 'unfReco_l1l2_ptsum']:
    theRatBand.GetYaxis().SetRangeUser(0.7, 1.3)
  else:
    theRatBand.GetYaxis().SetRangeUser(0.38, 1.62)
  theRatBand.GetYaxis().SetNdivisions(3,5,0)
  theRatBand.GetYaxis().SetLabelSize(0.15)

  theRatBand.Draw('E2')


  unfoldedRat.Draw('E X0 same')

  # plHWppRat.Draw('same hist')
  plHW7Rat.Draw('same hist')
  if args.check:
    plPy8Rat.Draw('same hist')

  theoRat.Draw('same HIST')


  l1 = ROOT.TLine(unfoldedRat.GetXaxis().GetXmin(),1,unfoldedRat.GetXaxis().GetXmax(),1)
  l1.Draw()

  cunf.cd()
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.04,"#bf{CMS} #it{Preliminary}"), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()+0.04,  1-ROOT.gStyle.GetPadTopMargin()+0.04, ('%3.0f fb^{#minus 1} (13 TeV)'%lumiScalesRounded[args.year])), 31)

  if args.norm:
    drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  1-ROOT.gStyle.GetPadTopMargin(),  labels[dist][2] ), 31, size=0.042, angle=90)
  else:
    drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  1-ROOT.gStyle.GetPadTopMargin(), 'Fiducial cross section [fb]'), 31, size=0.042, angle=90)
  drawTex((ROOT.gStyle.GetPadLeftMargin()- (0.055 if args.norm else 0.04),  0.07,'Pred. / data'), 11, size=0.042, angle=90)


  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.pdf') 
  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.png')
  cunf.SaveAs('unfolded/'+ args.year + dist + ('_Norm' if args.norm else '') + '.root')


  # Cloning here prevents strange root plotting headaches
  correlStat = eMat.Clone()
  correlSyst = covTot.Clone()

  # Draw covariance matrices
  statCovCanv = ROOT.TCanvas('statCov' + dist,'statCov' + dist, 1200, 1100)
  # statCovCanv.SetLogz(True)
  statCovCanv.SetRightMargin(0.17)
  statCovCanv.SetLeftMargin(0.12)
  statCovCanv.SetTopMargin(0.07)
  statCovCanv.SetBottomMargin(0.11)
  eMat.SetTitle('')
  eMat.GetXaxis().SetTitle(labels[dist][1])
  eMat.GetYaxis().SetTitle(labels[dist][1])
  eMat.GetZaxis().SetTitle("Covariance [fb^{2}]")
  eMat.GetYaxis().SetTitleOffset(1.3)
  eMat.GetXaxis().SetTitleOffset(1.1)
  eMat.GetZaxis().SetTitleOffset(1.1)
  eMat.GetXaxis().SetTitleSize(0.045)
  eMat.GetYaxis().SetTitleSize(0.045)
  eMat.GetZaxis().SetTitleSize(0.045)
  eMat.GetXaxis().SetLabelSize(0.04)
  eMat.GetYaxis().SetLabelSize(0.04)
  eMat.GetXaxis().SetTickLength(0)
  eMat.GetYaxis().SetTickLength(0)
  eMat.LabelsOption('v','x')
  
  # pdb.set_trace()
  
  eMat.Draw('COLZ text')
  # ROOT.gPad.Update()
  # ROOT.gPad.RedrawAxis()
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.045,'#bf{CMS} #it{Supplementary}'), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()-0.03,  1-ROOT.gStyle.GetPadTopMargin()+0.045, ('%3.0f fb^{#minus 1} (13 TeV)'%lumiScalesRounded[args.year])), 31)
  if args.year == 'RunII':
    statCovCanv.SaveAs('unfolded/' + dist + 'statCov' + ('_norm' if args.norm else '') + '.png')
    statCovCanv.SaveAs('unfolded/' + dist + 'statCov' + ('_norm' if args.norm else '') + '.pdf')


  systCovCanv = ROOT.TCanvas('systCov' + dist,'systCov' + dist, 1200, 1100)
  # systCovCanv.SetLogz(True)
  systCovCanv.SetRightMargin(0.17)
  systCovCanv.SetLeftMargin(0.12)
  systCovCanv.SetTopMargin(0.07)
  systCovCanv.SetBottomMargin(0.11)
  covTot.SetTitle('')

  covTot.GetXaxis().SetTitle(labels[dist][1])
  covTot.GetYaxis().SetTitle(labels[dist][1])
  covTot.GetZaxis().SetTitle("Covariance [fb^{2}]")
  covTot.GetYaxis().SetTitleOffset(1.3)
  covTot.GetXaxis().SetTitleOffset(1.1)
  covTot.GetZaxis().SetTitleOffset(1.1)
  covTot.GetXaxis().SetTitleSize(0.045)
  covTot.GetYaxis().SetTitleSize(0.045)
  covTot.GetZaxis().SetTitleSize(0.045)
  covTot.GetXaxis().SetLabelSize(0.04)
  covTot.GetYaxis().SetLabelSize(0.04)

  covTot.GetXaxis().SetTickLength(0)
  covTot.GetYaxis().SetTickLength(0)
  covTot.LabelsOption('v','x')
  ROOT.gPad.Update()
  ROOT.gPad.RedrawAxis()
  covTot.Draw('COLZ text')
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.045,'#bf{CMS} #it{Supplementary}'), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()-0.03,  1-ROOT.gStyle.GetPadTopMargin()+0.045, ('%3.0f fb^{#minus 1} (13 TeV)'%lumiScalesRounded[args.year])), 31)
  if args.year == 'RunII':
    systCovCanv.SaveAs('unfolded/' + dist + 'systCov' + ('_norm' if args.norm else '')+  '.png')
    systCovCanv.SaveAs('unfolded/' + dist + 'systCov' + ('_norm' if args.norm else '')+  '.pdf')

  for i in range(1, correlStat.GetXaxis().GetNbins()+1):
    for j in range(1, correlStat.GetXaxis().GetNbins()+1):
      correlStat.SetBinContent(i, j, correlStat.GetBinContent(i,j)/((eMat.GetBinContent(i,i)*eMat.GetBinContent(j,j))**0.5))
  correlStatCovCanv = ROOT.TCanvas('correlStatCov' + dist,'correlStatCov' + dist, 1200, 1100)
  # correlStatCovCanv.SetLogz(True)
  correlStatCovCanv.SetRightMargin(0.17)
  correlStatCovCanv.SetLeftMargin(0.12)
  correlStatCovCanv.SetTopMargin(0.07)
  correlStatCovCanv.SetBottomMargin(0.11)
  correlStat.SetTitle('')

  correlStat.GetXaxis().SetTitle(labels[dist][1])
  correlStat.GetYaxis().SetTitle(labels[dist][1])
  correlStat.GetZaxis().SetTitle("Correlation")
  correlStat.GetYaxis().SetTitleOffset(1.3)
  correlStat.GetXaxis().SetTitleOffset(1.1)
  correlStat.GetZaxis().SetTitleOffset(1.1)
  correlStat.GetXaxis().SetTitleSize(0.045)
  correlStat.GetYaxis().SetTitleSize(0.045)
  correlStat.GetZaxis().SetTitleSize(0.045)
  correlStat.GetXaxis().SetLabelSize(0.04)
  correlStat.GetYaxis().SetLabelSize(0.04)

  correlStat.GetXaxis().SetTickLength(0)
  correlStat.GetYaxis().SetTickLength(0)
  correlStat.LabelsOption('v','x')
  correlStat.Draw('COLZ text')

  ROOT.gPad.Update()
  ROOT.gPad.RedrawAxis()
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.045,'#bf{CMS} #it{Supplementary}'), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()-0.03,  1-ROOT.gStyle.GetPadTopMargin()+0.045, ('%3.0f fb^{#minus 1} (13 TeV)'%lumiScalesRounded[args.year])), 31)
  if args.year == 'RunII':
    correlStatCovCanv.SaveAs('unfolded/' + dist + 'correlStatCov' + ('_norm' if args.norm else '') + '.png')
    correlStatCovCanv.SaveAs('unfolded/' + dist + 'correlStatCov' + ('_norm' if args.norm else '') + '.pdf')


  for i in range(1, correlSyst.GetXaxis().GetNbins()+1):
    for j in range(1, correlSyst.GetXaxis().GetNbins()+1):
      correlSyst.SetBinContent(i, j, correlSyst.GetBinContent(i,j)/((covTot.GetBinContent(i,i)*covTot.GetBinContent(j,j))**0.5))
  correlSystCovCanv = ROOT.TCanvas('correlSystCov' + dist,'correlSystCov' + dist, 1200, 1100)
  # correlSystCovCanv.SetLogz(True)
  correlSystCovCanv.SetRightMargin(0.17)
  correlSystCovCanv.SetLeftMargin(0.12)
  correlSystCovCanv.SetTopMargin(0.07)
  correlSystCovCanv.SetBottomMargin(0.11)
  correlSyst.SetTitle('')

  correlSyst.GetXaxis().SetTitle(labels[dist][1])
  correlSyst.GetYaxis().SetTitle(labels[dist][1])
  correlSyst.GetZaxis().SetTitle("Correlation")
  correlSyst.GetYaxis().SetTitleOffset(1.3)
  correlSyst.GetXaxis().SetTitleOffset(1.1)
  correlSyst.GetZaxis().SetTitleOffset(1.1)
  correlSyst.GetXaxis().SetTitleSize(0.045)
  correlSyst.GetYaxis().SetTitleSize(0.045)
  correlSyst.GetZaxis().SetTitleSize(0.045)
  correlSyst.GetXaxis().SetLabelSize(0.04)
  correlSyst.GetYaxis().SetLabelSize(0.04)

  correlSyst.GetXaxis().SetTickLength(0)
  correlSyst.GetYaxis().SetTickLength(0)
  correlSyst.LabelsOption('v','x')
  correlSyst.Draw('COLZ text')
  ROOT.gPad.Update()
  ROOT.gPad.RedrawAxis()
  drawTex((ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.045,'#bf{CMS} #it{Supplementary}'), 11)
  drawTex((1-ROOT.gStyle.GetPadRightMargin()-0.03,  1-ROOT.gStyle.GetPadTopMargin()+0.045, ('%3.0f fb^{#minus 1} (13 TeV)'%lumiScalesRounded[args.year])), 31)
  if args.year == 'RunII':
    correlSystCovCanv.SaveAs('unfolded/' + dist + 'correlSystCov' + ('_norm' if args.norm else '') + '.png')
    correlSystCovCanv.SaveAs('unfolded/' + dist + 'correlSystCov' + ('_norm' if args.norm else '') + '.pdf')


# NOTE: code to print yield and unc table, don't delete!

if not args.norm:
  maxnbins  = max([len(tabulated[key][0]) for key in tabulated.keys()])
  print '\\begin{table}[]  \n  \\centering \n \scriptsize \n  \\begin{tabular}{c' + '|c'*maxnbins + '}'
  for key in tabulated.keys():
    lextra = maxnbins - len(tabulated[key][0])
    label = labels[key][0].replace('#', '\\').replace('DeltaR', 'Delta R')
    print '$' + label + '$ & '  + (' & ').join(tabulated[key][0] + [' '] * lextra ) + '\\\\ \\hline'
    print 'yield &                     ' + (' & ').join(tabulated[key][1] + [' '] * lextra ) + '\\\\'
    print 'data stat. unc. &           ' + (' & ').join(tabulated[key][2] + [' '] * lextra ) + '\\\\'
    print 'mc stat. unc. &             ' + (' & ').join(tabulated[key][3] + [' '] * lextra ) + '\\\\'
    print 'syst. unc. &                ' + (' & ').join(tabulated[key][4] + [' '] * lextra ) + '\\\\ \\hline'
  print '\\end{tabular} \n \\caption{Bin ranges, yields, and uncertainties per bin for the various full Run II differential results.} \n \\label{tab:unfTabulated} \n \\end{table}'
    