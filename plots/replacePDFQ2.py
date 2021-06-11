#! /usr/bin/env python

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store', default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth, applySysToOtherHist
from ttg.plots.combineTools import initCombineTools, writeCard, runFitDiagnostics, runSignificance, runImpacts, runCompatibility, goodnessOfFit, doLinearityCheck, plotNLLScan, plotSys, plotCC
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, CRSys, rateParameters
from ttg.tools.helpers import getObjFromFile
import urllib2
import pickle

import os, sys, subprocess, ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt
from termcolor import colored

def protectHist(hist):    
    if hist.Integral() < 0.00001:
        for i in range(1, hist.GetNbinsX()+1):
            if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
    return hist

# limit the variation in every bin to +-100%, needed for systematics from sample variations with low statistics
def capVar(nomHist, varHist):    
    for i in range(1, nomHist.GetNbinsX()+1):
      varHist.SetBinContent(i, max(min(2.* nomHist.GetBinContent(i), varHist.GetBinContent(i)), 0))
    return varHist


def writeHist(rootFile, name, template, histTemp, norm=None, removeBins = [0], shape=None, mergeBins=False, addOverflow=True):

    hist = histTemp.Clone()
    if norm:  normalizeBinWidth(hist, norm)
    if shape: hist = replaceShape(hist, shape)
    if removeBins:
        for i in removeBins:
            hist.SetBinContent(i, 0)
            hist.SetBinError(i, 0)
    if mergeBins:
        hist.Rebin(hist.GetNbinsX())
    if addOverflow:
      nbins = hist.GetNbinsX()
      hist.SetBinContent(nbins, hist.GetBinContent(nbins) + hist.GetBinContent(nbins + 1))
      hist.SetBinError(nbins, sqrt(hist.GetBinError(nbins)**2 + hist.GetBinError(nbins + 1)**2))
      hist.SetBinContent(nbins+1, 0.)
      hist.SetBinError(nbins+1, 0.)
    
    
    if not rootFile.GetDirectory(name): rootFile.mkdir(name)
    rootFile.cd(name)
    protectHist(hist).Write(template, ROOT.TObject.kOverwrite)



# folder = 'R2ZatEllModified'
folder = '18ZatEllModified'
name = 'srFit'
nloName = 'unfBLS-r_NLO'

# years = ['2016','2017','2018']
years = ['2018']

for year in years:
  fname = folder + '/' + name + '_' + year + '_shapes.root'
  # f = ROOT.TFile(fname, 'RECREATE')
  f = ROOT.TFile(fname, 'UPDATE')

  # baseSelection = 'llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20'
  # tag           = 'phoCBfull-niceEstimDD'
  # dataHistName = {'ee':'DoubleEG', 'mumu':'DoubleMuon', 'emu':'MuonEG'}

  nloFile = urllib2.urlopen('https://homepage.iihe.ac.be/~gmestdac/ttG/' + year + '/' + nloName + '/noData/placeholderSelection/rec_unfReco_phPt.pkl')
  nloHist = pickle.load(nloFile)
  q2Variations = []
  pdfVariations = []

  nom = nloHist['rec_unfReco_phPt']['ttgjetst#bar{t}#gamma NLO (genuine)']

  for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd'):
    pdfVariations.append(nloHist['rec_unfReco_phPtq2Sc_'+i]['ttgjetst#bar{t}#gamma NLO (genuine)'])

  for i in range(0, 100):
    q2Variations.append(nloHist['rec_unfReco_phPtpdfSc_' + str(i)]['ttgjetst#bar{t}#gamma NLO (genuine)'])

# TODO check if there's no issues with objects that should actually be cloned etc

  for channel in ['ee', 'emu', 'mumu']:

    nominalLO = getObjFromFile(folder + '/' + name + '_' + year + '_shapes.root','sr_' + channel + '/TTGamma')

    pdfup, pdfdown = pdfSys(pdfVariations, nom)
    q2up, q2down = q2Sys(q2Variations)

    pdfup = applySysToOtherHist(nom, pdfup, nominalLO)
    pdfdown = applySysToOtherHist(nom, pdfdown, nominalLO)
    q2up = applySysToOtherHist(nom, q2up, nominalLO)
    q2down = applySysToOtherHist(nom, q2down, nominalLO)

    #  The names of the histrgrams aren't right, and the effect isn't as expected

    writeHist(f, 'sr_' + channel + 'pdfUp',   'TTGamma', pdfup,   mergeBins = False)
    writeHist(f, 'sr_' + channel + 'pdfDown', 'TTGamma', pdfdown, mergeBins = False)
    writeHist(f, 'sr_' + channel + 'q2Up',    'TTGamma', q2up,   mergeBins = False)
    writeHist(f, 'sr_' + channel + 'q2Down',  'TTGamma', q2down, mergeBins = False)

  f.Close()




