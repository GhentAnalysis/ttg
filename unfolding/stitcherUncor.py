#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
# argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
args = argParser.parse_args()

import ROOT
import pdb

ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(95)

ROOT.gStyle.SetPaintTextFormat("3.2f")
ROOT.gStyle.SetPadBottomMargin(0.13)
ROOT.gStyle.SetPadTopMargin(0.05)
ROOT.gStyle.SetPadLeftMargin(0.06)

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

lumiunc = {'2016':0.012, '2017':0.023, '2018':0.025}


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


# noYearCor = ['pvSF','lSFEl','lSFMu','trigger']
noYearCor = ['lSFElStat' ,'lSFMuStat' ,'pvSF' ,'trigStatEE','trigStatEM','trigStatMM','trigSyst' ,'HFUC' ,'AbsoluteUC' ,'BBEC1UC' ,'EC2UC' ,'RelativeSampleUC']

def stitch1D(h6, h7, h8):
  binning = []
  start = h6.GetXaxis().GetBinLowEdge(1)
  end = h6.GetXaxis().GetBinUpEdge(h6.GetXaxis().GetNbins())
  for y in [0., 1. , 2.]:
    for i in range(1, h6.GetXaxis().GetNbins()+1):
      binning.append(y*(end-start) + h6.GetXaxis().GetBinLowEdge(i))
  binning.append(3.*end - 2.*start)
  stitched = ROOT.TH1D(h6.GetName() + "RunII" + 'c' + str(uuid.uuid4()).replace('-',''), h6.GetName() + "RunII", len(binning)-1, numpy.array(binning))

  # log.info(binning)
  for y, h in enumerate([h6, h7, h8]):
    nbins = h.GetXaxis().GetNbins()
    for i in range (1, nbins+1):
      stitched.SetBinContent(y*nbins + i, h.GetBinContent(i))
      stitched.SetBinError(y*nbins + i, h.GetBinError(i))
  stitched.SetBinContent(nbins   , h6.GetBinContent(nbins  ) + h6.GetBinContent(nbins+1))
  stitched.SetBinContent(2*nbins , h7.GetBinContent(nbins) + h7.GetBinContent(nbins+1))
  stitched.SetBinContent(3*nbins , h8.GetBinContent(nbins) + h8.GetBinContent(nbins+1))
  stitched.SetBinError(nbins   ,   (h6.GetBinError(nbins)**2. + h6.GetBinError(nbins+1)**2.)**0.5)
  stitched.SetBinError(2*nbins ,   (h7.GetBinError(nbins)**2. + h7.GetBinError(nbins+1)**2.)**0.5)
  stitched.SetBinError(3*nbins ,   (h8.GetBinError(nbins)**2. + h8.GetBinError(nbins+1)**2.)**0.5)
  # pdb.set_trace()
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
  stitched = ROOT.TH2D(h6.GetName() + "RunII" + 'c' + str(uuid.uuid4()).replace('-',''), h6.GetName() + "RunII", len(binning)-1, numpy.array(binning), len(ybinning)-1, numpy.array(ybinning))

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



#################### main code ####################

if not os.path.exists('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/'):
    os.makedirs('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/')

if not os.path.exists('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA/noData/placeholderSelection/'):
    os.makedirs('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA/noData/placeholderSelection/')

if not os.path.exists('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA_NLO/noData/placeholderSelection/'):
    os.makedirs('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA_NLO/noData/placeholderSelection/')

for dist in distList:
  log.info('running for '+ dist)
  response16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  reco16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  out16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))
  fid16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))

  response17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  reco17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  out17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))
  fid17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))

  response18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl','r'))
  reco18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
  out18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl','r'))
  fid18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))


  responseRunII = copy.deepcopy(response16)
  recoRunII = copy.deepcopy(reco16)
  recoSumRunII = copy.deepcopy(reco16)
  outRunII = copy.deepcopy(out16)
  fidRunII = copy.deepcopy(fid16)

  distResp = dist.replace('unfReco','response_unfReco')
  distOut = dist.replace('unfReco','out_unfReco')
  distFid = dist.replace('unfReco','fid_unfReco')

  for var in recoRunII.keys():
    if any(var.count(uncorVar) for uncorVar in noYearCor):
      log.info(var + ' treated as uncorrelated')
      recoRunII[var + '16'] = {}
      recoRunII[var + '17'] = {}
      recoRunII[var + '18'] = {}
      recoSumRunII[var + '16'] = {}
      recoSumRunII[var + '17'] = {}
      recoSumRunII[var + '18'] = {}

      for proc in recoRunII[var].keys():
        recoRunII[var][proc] = None #so you can't accidentally use both
        recoRunII[var + '16'][proc] = stitch1D(reco16[var][proc], reco17[dist][proc], reco18[dist][proc])
        recoRunII[var + '17'][proc] = stitch1D(reco16[dist][proc], reco17[var][proc], reco18[dist][proc])
        recoRunII[var + '18'][proc] = stitch1D(reco16[dist][proc], reco17[dist][proc], reco18[var][proc])

        recoSumRunII[var][proc] = None
        recoSumRunII[var + '16'][proc] = reco16[var][proc].Clone()
        recoSumRunII[var + '16'][proc].Add(reco17[dist][proc])
        recoSumRunII[var + '16'][proc].Add(reco18[dist][proc])

        recoSumRunII[var + '17'][proc] = reco16[dist][proc].Clone()
        recoSumRunII[var + '17'][proc].Add(reco17[var][proc])
        recoSumRunII[var + '17'][proc].Add(reco18[dist][proc])

        recoSumRunII[var + '18'][proc] = reco16[dist][proc].Clone()
        recoSumRunII[var + '18'][proc].Add(reco17[dist][proc])
        recoSumRunII[var + '18'][proc].Add(reco18[var][proc])
    else:
      for proc in recoRunII[var].keys():
        recoRunII[var][proc] = stitch1D(reco16[var][proc], reco17[var][proc], reco18[var][proc])
        recoSumRunII[var][proc].Add(reco17[var][proc])
        recoSumRunII[var][proc].Add(reco18[var][proc])

  for var in outRunII.keys():
    if any(var.count(uncorVar) for uncorVar in noYearCor):
      outRunII[var + '16'] = {}
      outRunII[var + '17'] = {}
      outRunII[var + '18'] = {}
      for proc in outRunII[var].keys():
        outRunII[var][proc] = None
        outRunII[var + '16'][proc] = stitch1D(out16[var][proc], out17[distOut][proc], out18[distOut][proc])
        outRunII[var + '17'][proc] = stitch1D(out16[distOut][proc], out17[var][proc], out18[distOut][proc])
        outRunII[var + '18'][proc] = stitch1D(out16[distOut][proc], out17[distOut][proc], out18[var][proc])
    else:
      for proc in outRunII[var].keys():
        outRunII[var][proc] = stitch1D(out16[var][proc], out17[var][proc], out18[var][proc])


  for var in responseRunII.keys():
    if any(var.count(uncorVar) for uncorVar in noYearCor):
      responseRunII[var + '16'] = {}
      responseRunII[var + '17'] = {}
      responseRunII[var + '18'] = {}
      for proc in responseRunII[var].keys():
        responseRunII[var][proc] = None
        responseRunII[var + '16'][proc] = stitch2D(response16[var][proc], response17[distResp][proc], response18[distResp][proc])
        responseRunII[var + '17'][proc] = stitch2D(response16[distResp][proc], response17[var][proc], response18[distResp][proc])
        responseRunII[var + '18'][proc] = stitch2D(response16[distResp][proc], response17[distResp][proc], response18[var][proc])
    else:
      for proc in responseRunII[var].keys():
        responseRunII[var][proc] = stitch2D(response16[var][proc], response17[var][proc], response18[var][proc])

  for var in fidRunII.keys():
    if any(var.count(uncorVar) for uncorVar in noYearCor):
      fidRunII[var + '16'] = {}
      fidRunII[var + '17'] = {}
      fidRunII[var + '18'] = {}
      for proc in fidRunII[var].keys():
        fidRunII[var][proc] = None
        fidRunII[var + '16'][proc] = fid16[var][proc].Clone()
        fidRunII[var + '16'][proc].Add(fid17[distFid][proc])
        fidRunII[var + '16'][proc].Add(fid18[distFid][proc])

        fidRunII[var + '17'][proc] = fid16[distFid][proc].Clone()
        fidRunII[var + '17'][proc].Add(fid17[var][proc])
        fidRunII[var + '17'][proc].Add(fid18[distFid][proc])

        fidRunII[var + '18'][proc] = fid16[distFid][proc].Clone()
        fidRunII[var + '18'][proc].Add(fid17[distFid][proc])
        fidRunII[var + '18'][proc].Add(fid18[var][proc])

    else:
      for proc in fidRunII[var].keys():
        fidRunII[var][proc].Add(fid17[var][proc])
        fidRunII[var][proc].Add(fid18[var][proc])


  pickle.dump(recoRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl', 'w'))
  pickle.dump(responseRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','response_unfReco') + '.pkl', 'w'))
  pickle.dump(outRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','out_unfReco') + '.pkl', 'w'))
  pickle.dump(fidRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl', 'w'))
  pickle.dump(recoSumRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist.replace('unfReco','sum_unfReco') + '.pkl', 'w'))


  respStichCanv = ROOT.TCanvas('stitchedResp' + dist,'stitchedResp' + dist, 1900, 700)
  respStichCanv.SetLogz(True)
  # respStichCanv.SetLeftMargin(0.1)
  respR2 = responseRunII[dist.replace('unfReco','response_unfReco')]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  respR2.SetTitle('')
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
  respR2.GetZaxis().SetRangeUser(respR2.GetMaximum()*0.0004, respR2.GetMaximum()*1.03)
  respR2.Draw('COLZ')
  respStichCanv.SaveAs('unfolded/' + dist + 'stitchedResp.png')
  respStichCanv.SaveAs('unfolded/' + dist + 'stitchedResp.pdf')





  fidNLO16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))
  fidNLO17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))
  fidNLO18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))

  fidNLORunII = copy.deepcopy(fidNLO16)
  distFid = dist.replace('unfReco','fid_unfReco')

  for var in fidNLORunII.keys():
    for proc in fidNLORunII[var].keys():
      fidNLORunII[var][proc].Add(fidNLO17[var][proc])
      fidNLORunII[var][proc].Add(fidNLO18[var][proc])


#  absolutely barbaric implementation, I know
  # we sum the envelopes / rms variations, not the the indiviual variations
  procName = fidNLORunII[var].keys()[0]
  q2dict16 =  dict((var, fidNLO16[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict16 = dict((var, fidNLO16[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])
  q2dict17 =  dict((var, fidNLO17[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict17 = dict((var, fidNLO17[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])
  q2dict18 =  dict((var, fidNLO18[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict18 = dict((var, fidNLO18[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])

  plq2Up16, plq2Down16 =  getEnv(q2dict16)
  rmspdf16 = getRMS(pdfdict16)

  plq2Up17, plq2Down17 =  getEnv(q2dict17)
  rmspdf17 = getRMS(pdfdict17)

  plq2Up18, plq2Down18 =  getEnv(q2dict18)
  rmspdf18 = getRMS(pdfdict18)

  fidNLORunII[distFid + 'fdpUp'] = {}
  fidNLORunII[distFid + 'fdpDown'] = {}
  fidNLORunII[distFid + '2qUp'] = {}
  fidNLORunII[distFid + '2qDown'] = {}


  fidNLORunII[distFid + 'fdpUp'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + 'fdpDown'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + '2qUp'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + '2qDown'][procName] = fidNLORunII[distFid][procName].Clone()

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up16)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down16)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf16)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf16, -1)

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up17)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down17)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf17)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf17, -1)

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up18)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down18)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf18)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf18, -1)

  pickle.dump(fidNLORunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl', 'w'))



  # exact same thing, but normalizing the variations the the same integral as nominal 

  fidNLO16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))
  fidNLO17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))
  fidNLO18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '.pkl','r'))

  fidNLORunII = copy.deepcopy(fidNLO16)
  distFid = dist.replace('unfReco','fid_unfReco')

  for var in fidNLORunII.keys():
    for proc in fidNLORunII[var].keys():
      fidNLORunII[var][proc].Add(fidNLO17[var][proc])
      fidNLORunII[var][proc].Add(fidNLO18[var][proc])


#  absolutely barbaric implementation, I know
  # we sum the envelopes / rms variations, not the the indiviual variations
  procName = fidNLORunII[var].keys()[0]
  q2dict16 =  dict((var, fidNLO16[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict16 = dict((var, fidNLO16[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])
  q2dict17 =  dict((var, fidNLO17[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict17 = dict((var, fidNLO17[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])
  q2dict18 =  dict((var, fidNLO18[distFid + var][procName].Clone()) for var in ['']+['q2Sc_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
  pdfdict18 = dict((var, fidNLO18[distFid + var][procName].Clone()) for var in ['']+['pdfSc_' + str(i) for i in range(0, 100)])

  for dicti in [q2dict16, pdfdict16, q2dict17, pdfdict17, q2dict18, pdfdict18]:
    for h in dicti.values():
      h.Scale(dicti[''].Integral() / h.Integral())

  plq2Up16, plq2Down16 =  getEnv(q2dict16)
  rmspdf16 = getRMS(pdfdict16)

  plq2Up17, plq2Down17 =  getEnv(q2dict17)
  rmspdf17 = getRMS(pdfdict17)

  plq2Up18, plq2Down18 =  getEnv(q2dict18)
  rmspdf18 = getRMS(pdfdict18)

  fidNLORunII[distFid + 'fdpUp'] = {}
  fidNLORunII[distFid + 'fdpDown'] = {}
  fidNLORunII[distFid + '2qUp'] = {}
  fidNLORunII[distFid + '2qDown'] = {}


  fidNLORunII[distFid + 'fdpUp'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + 'fdpDown'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + '2qUp'][procName] = fidNLORunII[distFid][procName].Clone()
  fidNLORunII[distFid + '2qDown'][procName] = fidNLORunII[distFid][procName].Clone()

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up16)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down16)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf16)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf16, -1)

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up17)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down17)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf17)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf17, -1)

  fidNLORunII[distFid + '2qUp'][procName].Add(plq2Up18)
  fidNLORunII[distFid + '2qDown'][procName].Add(plq2Down18)
  fidNLORunII[distFid + 'fdpUp'][procName].Add(rmspdf18)
  fidNLORunII[distFid + 'fdpDown'][procName].Add(rmspdf18, -1)

  pickle.dump(fidNLORunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/RunII/unfENDA_NLO/noData/placeholderSelection/' + dist.replace('unfReco','fid_unfReco') + '_norm.pkl', 'w'))