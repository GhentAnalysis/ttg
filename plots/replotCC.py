#! /usr/bin/env python

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store', default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--ratio', action='store_true', help="fit xsec ratio")
argParser.add_argument('--blind', action='store_true', help="do not use data")
argParser.add_argument('--run', action='store', default='combine', help="custom run name")
argParser.add_argument('--chan', action='store', default='ee', help="dilepton channel name", choices=['ee', 'mumu', 'emu', 'll'])
argParser.add_argument('--year', action='store', default='2016', help="year of data taking", choices=['2016', '2017', '2018', 'All'])
argParser.add_argument('--distName', action='store', default='unfReco_phPt', help="input file name")
argParser.add_argument('--tab', action='store_true', help="produce tables")
argParser.add_argument('--noPartial', action='store_true', help="don't apply partial correlations")
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import initCombineTools, writeCard, runFitDiagnostics, runSignificance, runImpacts, runCompatibility, goodnessOfFit, doLinearityCheck, plotNLLScan, plotSys, plotCC, plotCCR2split, plotCCRIINice, plotCCRIINiceXsec
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, CRSys, rateParameters

import os, sys, subprocess, ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt
from termcolor import colored




######################
# Signal regions fit #
######################
def doSignalRegionFit(cardName, shapes, perPage=30, doRatio=False, year='2016', run='combine', blind=False, distName='None, crash'):

    years = [year]
    if year == 'All': 
        years = ['2016','2017','2018']
    

    outDir = run+args.chan
    initCombineTools(year, doCleaning=False, run=outDir)
    


    if blind == False:
      print colored('##### Run channel compatibility (obs)', 'red')
      # runCompatibility(cardName, year, perPage, doRatio=doRatio, run=outDir)
      if year == 'All':
        # runCompatibility(cardName, year, perPage, doRatio=doRatio, run=outDir, group=True)
        plotCCR2split(cardName, year, poi='r', run=outDir, mode='obs', addNominal=True)
        plotCCRIINice(cardName, year, poi='r', run=outDir, mode='grouped_obs', addNominal=True)
        plotCCRIINiceXsec(cardName, year, poi='r', run=outDir, mode='grouped_obs', addNominal=True)
      else:
          plotCC(cardName, year, poi='r', rMin=0.7, rMax=1.5, run=outDir, mode='obs', addNominal=True)
      # TODO adjust plotter so it can plot the grouped ones

    print colored('##### Run channel compatibility (exp)', 'red')
    # runCompatibility(cardName, year, perPage, toys=True, doRatio=doRatio, run=outDir)
    if year == 'All':
      # runCompatibility(cardName, year, perPage, toys=True, doRatio=doRatio, run=outDir, group=True)
      plotCCR2split(cardName, year, poi='r', run=outDir, mode='exp', addNominal=True)
      plotCCRIINice(cardName, year, poi='r', run=outDir, mode='grouped_exp', addNominal=True)
      plotCCRIINiceXsec(cardName, year, poi='r', run=outDir, mode='grouped_exp', addNominal=True)
    else:
      plotCC(cardName, year, poi='r', rMin=0.7, rMax=1.5, run=outDir, mode='exp', addNominal=True)


doRatio = args.ratio
fitName = 'srFit'
if doRatio: fitName = 'ratioFit'

shapes = []

if args.chan == 'll':
  for reg in ('sr_ee','sr_mumu', 'sr_emu'):
    shapes.append(reg)
else: 
  shapes.append('sr_'+args.chan)

doSignalRegionFit(fitName, shapes, 35, doRatio=doRatio, year=args.year, blind=args.blind, run=args.run, distName = args.distName)
