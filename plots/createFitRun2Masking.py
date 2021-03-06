#! /usr/bin/env python

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store', default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--ratio', action='store_true', help="fit xsec ratio")
argParser.add_argument('--blind', action='store_true', help="do not use data")
argParser.add_argument('--run', action='store', default='combine', help="custom run name")
argParser.add_argument('--chan', action='store', default='ee', help="dilepton channel name", choices=['ee', 'mumu', 'emu', 'll'])
argParser.add_argument('--year', action='store', default='2016', help="year of data taking", choices=['2016', '2017', '2018', 'All'])
argParser.add_argument('--tab', action='store_true', help="produce tables")
argParser.add_argument('--noPartial', action='store_true', help="don't apply partial correlations")
argParser.add_argument('--masked', action='store_true', default=None, help="add masked distributions")
argParser.add_argument('--maskSet', action='store', default='A', help="which set of distributions to add")
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import initCombineTools, writeCard, runFitDiagnostics, runSignificance, runImpacts, runCompatibility, goodnessOfFit, doLinearityCheck, plotNLLScan, plotSys, plotCC
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, rateParameters

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

# return a histogram with any change w.r.t. the nominal inverted
# NOTE assuming we want not nom - a, nom + a. up , not up = a * nom, down = 1/a * nom
# up = nom + dev. down = nom - dev = nom - (up -nom) = 2* nom - up
def invertVar(nomHist, varHist):
    inverseHist = nomHist.Clone()
    for i in range(1, nomHist.GetNbinsX()+1):
      inverseHist.SetBinContent(i, max(2. * nomHist.GetBinContent(i) - varHist.GetBinContent(i), 0.))
    return inverseHist

def applyNonPromptSF(histTemp, nonPromptSF, sys=None):
  if not nonPromptSF: 
    return histTemp
  hist = histTemp.Clone()
  srMap = {1:'all', 2:'all', 3:'all', 4:'all'}
  for i, sr in srMap.iteritems():
    err = max(abs(nonPromptSF[sr][1]), abs(nonPromptSF[sr][2])) # fix for failed fits
    if sys and sys == "Up":     sf = nonPromptSF[sr][0] + err
    elif sys and sys == "Down": sf = nonPromptSF[sr][0] - err
    else:                       sf = nonPromptSF[sr][0]
    hist.SetBinContent(i, hist.GetBinContent(i)*sf)
  return hist

from ttg.plots.replaceShape import replaceShape
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
    protectHist(hist).Write(template)

try: os.makedirs(args.run + args.chan)
except: pass
# VVTo2L2Nu = other
#  if a template is added for some reason, keep TTGamma first and nonprompt last
# templates = ['TTGamma', 'TT_Dil', 'ZG', 'DY', 'VVTo2L2Nu', 'singleTop', 'nonprompt']
templates = ['TTGamma', 'ZG', 'VVTo2L2Nu', 'singleTop', 'nonprompt']
# maskedDist = ['unfReco_phPt','unfReco_phLepDeltaR','unfReco_phEta', 'unfReco_ll_deltaPhi']

# maskedDist = ['unfReco_jetLepDeltaR','unfReco_jetPt','unfReco_ll_absDeltaEta','unfReco_ll_cosTheta','unfReco_ll_deltaPhi','unfReco_phAbsEta','unfReco_phBJetDeltaR','unfReco_phLepDeltaR','unfReco_phPt']

if args.maskSet == 'A':
  maskedDist = ['unfReco_jetLepDeltaR','unfReco_jetPt','unfReco_ll_absDeltaEta']
if args.maskSet == 'B':
  maskedDist = ['unfReco_ll_cosTheta','unfReco_ll_deltaPhi','unfReco_phAbsEta']
if args.maskSet == 'C':
  maskedDist = ['unfReco_phBJetDeltaR','unfReco_phLepDeltaR','unfReco_phPt']


from ttg.plots.systematics import correlations

def writeRootFile(name, shapes, systematicVariations, year, distribution='signalRegions'):
    name = name if distribution == 'signalRegions' else (name + '_' + distribution)
    fname = args.run + args.chan + '/' + name + '_' + year + '_shapes.root'
    print fname
    f = ROOT.TFile(fname, 'RECREATE')

    baseSelection = 'llg-mll20-signalRegionAB-offZ-llgNoZ-photonPt20'
    tag           = 'phoCBfull-niceEstimDD-otravez'
    dataHistName = {'ee':'DoubleEG', 'mumu':'DoubleMuon', 'emu':'MuonEG'}

    for shape in shapes:
      # Write the data histograms to the combine shapes file, separate for ee, emu, mumu
      writeHist(f, shape, 'data_obs', getHistFromPkl((year, tag, shape[3:], baseSelection), distribution, '', [dataHistName[shape[3:]]]), mergeBins=False)
      # write the MC histograms to the shapes file
      for t in templates:
        q2Variations = []
        pdfVariations = []
        for sys in [''] + systematicVariations:
          if t == 'nonprompt':
            Selectors     = [['NP', 'nonprompt']]
          else:
            Selectors     = [[t, '(genuine)']]
          
          prompt    = getHistFromPkl((year, tag, shape[3:], baseSelection), distribution, sys, *Selectors)
          if sys == '':     nominal = prompt                                                   # Save nominal case to be used for q2/pdf calculations
          if 'pdf' in sys:  pdfVariations += [prompt]                                          # Save all pdfVariations in list
          elif 'q2' in sys: q2Variations += [prompt]                                           # Save all q2Variations in list
          else:
            if 'erdDown' in sys:
              sel = [['NP', 'nonprompt']] if t == 'nonprompt' else [[t, '(genuine)']]
              ErdUpprompt    = getHistFromPkl((year, tag, shape[3:], baseSelection), distribution, 'erdUp', *sel)
              prompt = invertVar(nominal, ErdUpprompt)
            prompt = capVar(nominal, prompt)
            writeHist(f, shape+sys, t, prompt, mergeBins = False)    # Write nominal and other systematics   
            sysUncor = sys.replace('Up', '_' + year +'Up').replace('Down', '_' + year +'Down')
            sysCor1617 = sys.replace('Up', '_1617Up').replace('Down', '_1617Down')
            sysCor1618 = sys.replace('Up', '_1618Up').replace('Down', '_1618Down')
            sysCor1718 = sys.replace('Up', '_1718Up').replace('Down', '_1718Down')
            writeHist(f, shape+sysUncor, t, prompt, mergeBins = False)    # Write same variation with a year suffix, potentially needed for partial correlations
            writeHist(f, shape+sysCor1617, t, prompt, mergeBins = False)    # Write same variation with a year suffix, potentially needed for partial correlations
            writeHist(f, shape+sysCor1618, t, prompt, mergeBins = False)    # Write same variation with a year suffix, potentially needed for partial correlations
            writeHist(f, shape+sysCor1718, t, prompt, mergeBins = False)    # Write same variation with a year suffix, potentially needed for partial correlations
        # Calculation of up and down envelope pdf variations
        if len(pdfVariations) > 0:
          up, down = pdfSys(pdfVariations, nominal)
          writeHist(f, shape+'pdfUp',   t, up,   mergeBins = False)
          writeHist(f, shape+'pdfDown', t, down, mergeBins = False)
          writeHist(f, shape+'pdf_' + year + 'Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'pdf_' + year + 'Down', t, down, mergeBins = False)
          writeHist(f, shape+'pdf_1617Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'pdf_1617Down', t, down, mergeBins = False)
          writeHist(f, shape+'pdf_1618Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'pdf_1618Down', t, down, mergeBins = False)
          writeHist(f, shape+'pdf_1718Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'pdf_1718Down', t, down, mergeBins = False)
        # Calcualtion of up and down envelope q2 variations
        if len(q2Variations) > 0:
          up, down = q2Sys(q2Variations)
          writeHist(f, shape+'q2Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'q2Down', t, down, mergeBins = False)
          writeHist(f, shape+'q2_' + year + 'Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'q2_' + year + 'Down', t, down, mergeBins = False)
          writeHist(f, shape+'q2_1617Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'q2_1617Down', t, down, mergeBins = False)
          writeHist(f, shape+'q2_1618Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'q2_1618Down', t, down, mergeBins = False)
          writeHist(f, shape+'q2_1718Up',   t, up,   mergeBins = False)
          writeHist(f, shape+'q2_1718Down', t, down, mergeBins = False)
    f.Close()

######################
# Signal regions fit #
######################
def doSignalRegionFit(cardName, shapes, perPage=30, doRatio=False, year='2016', run='combine', blind=False, masked=None):

    years = [year]
    if year == 'All': 
        years = ['2016','2017','2018']
    
    log.info(' --- Signal regions fit (' + cardName + ') --- ')
    extraLines  = [(t + '_norm rateParam * ' + t + '* 1')                 for t in templates[1:-1]]
    extraLines += [(t + '_norm param 1.0 ' + str(rateParameters[t]/100.)) for t in templates[1:-1]]
    extraLines += ['* autoMCStats 0 1 1']
    
    if doRatio == True: # Special case in order to fit the ratio of ttGamma to ttbar [hardcoded numbers as discussed with 1l group]
      log.info(' --- Ratio ttGamma/ttBar fit --- ')
      extraLines += ['renormTTGamma rateParam * TTGamma* 0.338117493', 'nuisance edit freeze renormTTGamma ifexists']
      extraLines += ['renormTTbar rateParam * TT_Dil* 1.202269886',    'nuisance edit freeze renormTTbar ifexists']
      #extraLines += ['TT_Dil_norm rateParam * TT* 0.83176 [0.,2.]'] # fit ttbar xsec (TT_Dil_norm) and the ttg/ttbar ratio (r)
      extraLines += ['TT_Dil_norm rateParam * TT* 0.83176 [0.,2.]']
      #extraLines += ['TT_Dil_norm rateParam * TT_Dil* 0.83176 [0.,2.]'] # fit to ttg (r) and ttbar (TT_Dil_norm) xsecs

    # Write shapes file and combine card using
    # * systematic.keys() --> all the up/down, pdf and q2 variations histograms as imported from ttg.plots.systematics, being used to write the shape file
    # * the list of shapes to be used in the fit (SR for specific channels, CR's)
    # * the templates defined above
    # * [templatesNoSys] not use (would simply add a template without systematics)
    # * the extraLines at the bottom of the combine card defined above
    # * the showSysList are the names of all the nuisance parameters + extra nuisance parameter for the non prompt SF uncertainty
    # * no linear systematics (originally there was lumi here, but we were requested to take it out)
    # * the up/down variations of FSR were scaled back with 1/sqrt(2) according to TOP recommendations

    outDir = run+args.chan
    initCombineTools(year, doCleaning=False, run=outDir)
    
    listSys = {}
    shapeSys = {}
    nameSys = {}
    for y in years:
      shapeSys[y] = []
      nameSys[y] = []
      listSys[y] = showSysList[:]
      if y == '2018': listSys[y].remove('pf')
      for i in systematics.keys():
        if ('pf' in i) and (y == '2018'): continue
        nameSys[y].append(i)
        if 'Up' in i:
          shapeSys[y].append(i.replace('Up',''))            

    normSys = [(t+'_norm') for t in templates[1:-1]]
    
    print colored('##### Prepare ROOT file with histograms', 'red')
    for y in years:
      writeRootFile(cardName, shapes, nameSys[y], y)
      if masked:
        for distr in maskedDist:
          writeRootFile(cardName, shapes, nameSys[y], y, distribution=distr)
    
    print colored('##### Prepare data card', 'red')
    cards = []
    for y in years:
      writeCard(cardName, shapes, templates, None, extraLines, listSys[y], {}, {}, run=outDir, year=y, correlations=correlations if args.year == 'All' else {})
      cards.append(cardName+'_'+y+'.txt')
      if masked:
        for distr in maskedDist:
          writeCard(cardName + '_' + distr , shapes, templates, None, extraLines, listSys[y], {}, {}, run=outDir, year=y, correlations=correlations if args.year == 'All' else {})
    if len(years) == 1:
      if masked:
        combArgs= ['main=' + cards[0]] + [distr + '=' +cardName + '_' + distr +'_'+y+'.txt' for distr in maskedDist]
        log.info('combineCards.py '+ ' '.join(combArgs))
        p = subprocess.Popen(['combineCards.py']+combArgs, cwd=outDir, stdout=open(outDir+'/'+cardName+'.txt','wb')); p.wait()
      else:
        os.system('cp '+ outDir +'/' + cards[0]+' '+outDir+'/'+cardName+'.txt')
    else:
      if masked:
        combArgs = ['y' + y + '_main=' +cardName + '_'+y+'.txt' for y in ['2016','2017','2018']]
        combArgs += ['y' + y + '_' + distr + '=' +cardName + '_' + distr +'_'+y+'.txt' for distr in maskedDist for y in ['2016','2017','2018']]
        log.info('combineCards.py '+ ' '.join(combArgs))
        p = subprocess.Popen(['combineCards.py']+combArgs, cwd=outDir, stdout=open(outDir+'/'+cardName+'.txt','wb')); p.wait()
      else:
        p = subprocess.Popen(['combineCards.py','y2016='+cards[0],'y2017='+cards[1],'y2018='+cards[2]], cwd=outDir, stdout=open(outDir+'/'+cardName+'.txt','wb')); p.wait()

    # else:
    #   for i, y in enumerate(years): 
    #     cards[i] = cardName+'_'+y
    #   p = subprocess.Popen(['combineCards.py','y2016='+cards[0] + '.txt','y2017='+cards[1] + '.txt','y2018='+cards[2] + '.txt'], cwd=outDir, stdout=open(outDir+'/'+cardName+'.txt','wb')); p.wait()
    #       # TODO implement channel masking with multiple years


    print colored('##### Run fit diagnostics for exp (stat)', 'red')
    runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:-1]]+['r'], toys=True, statOnly=True, mode='exp', run=outDir, maskedDist=maskedDist)
    print colored('##### Run fit diagnostics for exp (stat+sys)', 'red')
    runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:-1]]+['r'], toys=True, statOnly=False, mode='exp', run=outDir, maskedDist=maskedDist)

    if blind == False:
      print colored('##### Run fit diagnostics for obs (stat)', 'red')
      runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:-1]]+['r'], toys=False, statOnly=True, mode='obs', run=outDir, maskedDist=maskedDist)
      print colored('##### Run fit diagnostics for obs (stat+sys)', 'red')
      runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:-1]]+['r'], toys=False, statOnly=False, mode='obs', run=outDir, maskedDist=maskedDist)
doRatio = args.ratio
fitName = 'srFit'
if doRatio: fitName = 'ratioFit'

shapes = []

if args.chan == 'll':
  for reg in ('sr_ee','sr_mumu', 'sr_emu'):
    shapes.append(reg)
else: 
  shapes.append('sr_'+args.chan)

doSignalRegionFit(fitName, shapes, 35, doRatio=doRatio, year=args.year, blind=args.blind, run=args.run, masked=args.masked)

#goodnessOfFit('srFit', run=args.run+args.chan)
#doLinearityCheck('srFit', run=args.run+args.chan)
