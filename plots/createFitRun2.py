#! /usr/bin/env python

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store', default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--ratio', action='store_true', help="fit xsec ratio")
argParser.add_argument('--blind', action='store_true', help="do not use data")
argParser.add_argument('--run', action='store', default='combine', help="custom run name")
argParser.add_argument('--chan', action='store', default='ee', help="dilepton channel name", choices=['ee', 'mumu', 'emu', 'll'])
argParser.add_argument('--tab', action='store_true', help="produce tables")
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import initCombineTools, writeCard, runFitDiagnostics, runSignificance, runImpacts, runCompatibility, goodnessOfFit, doLinearityCheck, plotNLLScan, plotSys, plotCC
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, rateParameters

import os, ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt
from termcolor import colored

def protectHist(hist):    
    if hist.Integral() < 0.00001:
        for i in range(1, hist.GetNbinsX()+1):
            if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
    return hist

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
def writeHist(rootFile, name, template, histTemp, norm=None, removeBins = None, shape=None, mergeBins=False):
    hist = histTemp.Clone()
    if norm:  normalizeBinWidth(hist, norm)
    if shape: hist = replaceShape(hist, shape)
    if removeBins:
        for i in removeBins:
            hist.SetBinContent(i, 0)
            hist.SetBinError(i, 0)
    if mergeBins:
        hist.Rebin(hist.GetNbinsX())
    if not rootFile.GetDirectory(name): rootFile.mkdir(name)
    rootFile.cd(name)
    protectHist(hist).Write(template)

try: os.makedirs(args.run + args.chan)
except: pass

templates = ['TTGamma', 'TT_Dil', 'ZG', 'DY', 'other', 'single-t']

def writeRootFile(name, systematicVariations, year):

    fname = args.run + args.chan + '/' + name + '_shapes.root'
    print fname
    f = ROOT.TFile(fname, 'RECREATE')

    baseSelection = 'llg-mll40-offZ-llgNoZ-signalRegion-photonPt20'
    tag           = 'phoCBfull_compos_ALL'

    # Write the data histograms to the combine shapes file: SR (separate for ee, emu, mumu, SF), ZGamma CR and ttbar CR
    dataHistName = {'ee':'DoubleEG', 'mumu':'DoubleMuon', 'emu':'MuonEG'}
    channels = []
    if args.chan == 'll':
        for ch in ['ee', 'mumu', 'emu']:
            writeHist(f, 'sr_' + ch, 'data_obs', getHistFromPkl((year, tag, ch, baseSelection), 'signalRegions', '', [dataHistName[ch]]), mergeBins=False)
            channels.append(('sr_' + ch, ch))
    else: 
        writeHist(f, 'sr_' + args.chan, 'data_obs', getHistFromPkl((year, tag, args.chan, baseSelection), 'signalRegions', '', [dataHistName[args.chan]]), mergeBins=False)
        channels.append(('sr_' + args.chan, args.chan))            

    for t in templates:
        
        promptSelectors   = [[t, '(genuine)']]
        fakeSelectors     = [[t, '(hadronicFake)']]
        hadronicSelectors = [[t, '(hadronicPhoton)']]
      
        for shape, channel in channels:
####            q2Variations = []
####            pdfVariations = []
            for sys in [''] + systematicVariations:
                prompt   = getHistFromPkl((year, tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegions', sys, *promptSelectors)
                fake     = getHistFromPkl((year, tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegions', sys, *fakeSelectors)
                hadronic = getHistFromPkl((year, tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegions', sys, *hadronicSelectors)
                
                # Write SR and ZGamma CR
                ##    for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF'), ('sr_ee', 'ee'), ('sr_mm', 'mumu'), ('zg_SF', 'SF')]:
                ##      q2Variations = []
                ##      pdfVariations = []
                ##      for sys in [''] + systematicVariations:
                ##        prompt   = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *promptSelectors)
                ##        fake     = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *fakeSelectors)
                ##        hadronic = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *hadronicSelectors)
                
                # In case of fakes and hadronics, apply their SF (and calculate up and down variations)
                ##      if sys == '':
                ##          fakeUp, fakeDown         = applyNonPromptSF(fake, fakeSF, 'Up'),         applyNonPromptSF(fake, fakeSF, 'Down')
                ##          hadronicUp, hadronicDown = applyNonPromptSF(hadronic, hadronicSF, 'Up'), applyNonPromptSF(hadronic, hadronicSF, 'Down')
                ##        fake     = applyNonPromptSF(fake, fakeSF)
                ##        hadronic = applyNonPromptSF(hadronic, hadronicSF)

                # Add up the contributions of genuine, fake and hadronic photons
####                if sys == '':
####                    totalUp   = prompt.Clone()
####                    totalDown = prompt.Clone()
                    ##          totalUp.Add(fakeUp)
                    ##          totalDown.Add(fakeDown)
                    ##          totalUp.Add(hadronicUp)
                    ##          totalDown.Add(hadronicDown)
#                    writeHist(f, shape+'nonPromptUp',   t, totalUp, mergeBins = ('zg' in shape))
#                    writeHist(f, shape+'nonPromptDown', t, totalDown, mergeBins = ('zg' in shape))
                total = prompt.Clone()
                total.Add(hadronic)
                total.Add(fake)

                if sys == '':     nominal = total                                                   # Save nominal case to be used for q2/pdf calculations
                writeHist(f, shape+sys, t, total, mergeBins = ('zg' in shape))
        ##        if 'pdf' in sys:  pdfVariations += [total]                                          # Save all pdfVariations in list
        ##        elif 'q2' in sys: q2Variations += [total]                                           # Save all q2Variations in list
        ##        else:             writeHist(f, shape+sys, t, total, mergeBins = ('zg' in shape))    # Write nominal and other systematics   

        # Calculation of up and down envelope pdf variations
        ##      if len(pdfVariations) > 0:
        ##        up, down = pdfSys(pdfVariations, nominal)
        ##        writeHist(f, shape+'pdfUp',   t, up,   mergeBins = ('zg' in shape))
        ##        writeHist(f, shape+'pdfDown', t, down, mergeBins = ('zg' in shape))

        # Calcualtion of up and down envelope q2 variations
        ##      if len(q2Variations) > 0:
        ##        up, down = q2Sys(q2Variations)
        ##        writeHist(f, shape+'q2Up',   t, up,   mergeBins = ('zg' in shape))
        ##        writeHist(f, shape+'q2Down', t, down, mergeBins = ('zg' in shape))

        # Similar for tt CR, only here we do not have to sum the photon types
        ##    for shape, channel in [('tt', 'all')]:
        ##      q2Variations = []
        ##      pdfVariations = []
        ##      selector = [[t,]]
        ##      for sys in [''] + systematicVariations:
        ##        total = getHistFromPkl((tagTT, channel, ttSelection), 'signalRegionsSmall', sys, *selector)

        ##        if sys == '':     nominal = total
        ##        if 'pdf' in sys:  pdfVariations += [total]
        ##        elif 'q2' in sys: q2Variations += [total]
        ##        else:             writeHist(f, shape+sys, t, total, mergeBins = True)

        ##      if len(pdfVariations) > 0:
        ##        up, down = pdfSys(pdfVariations, nominal)
        ##        writeHist(f, shape+'pdfUp',   t, up,   mergeBins=True)
        ##        writeHist(f, shape+'pdfDown', t, down, mergeBins=True)

        ##      if len(q2Variations) > 0:
        ##        up, down = q2Sys(q2Variations)
        ##        writeHist(f, shape+'q2Up',   t, up,   mergeBins=True)
        ##        writeHist(f, shape+'q2Down', t, down, mergeBins=True)

    f.Close()

######################
# Signal regions fit #
######################
def doSignalRegionFit(cardName, shapes, perPage=30, doRatio=False, year='2016', run='combine', blind=False):
    
    log.info(' --- Signal regions fit (' + cardName + ') --- ')
    extraLines  = [(t + '_norm rateParam * ' + t + '* 1')                 for t in templates[1:]]
    extraLines += [(t + '_norm param 1.0 ' + str(rateParameters[t]/100.)) for t in templates[1:]]
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
    
    shapeSys = []
    for i in systematics.keys():
        if 'Up' in i:
            shapeSys.append(i.replace('Up',''))
    
    normSys = [(t+'_norm') for t in templates[1:]]
    
    allSys = shapeSys + normSys
    
    print colored('##### Prepare ROOT file with histograms', 'red')
    writeRootFile(cardName, systematics.keys(), year)
    
    print colored('##### Plot shape systematic variations', 'red')
    if args.chan == 'll':
        for ch in ['ee', 'mumu', 'emu']:
            fileName = args.run + args.chan + '/' + cardName + '_shapes.root'
            plotSys(fileName, 'sr', ch, templates, systematics.keys(), year, args.run, comb=True)
    else:
        fileName = args.run + args.chan + '/' + cardName + '_shapes.root'
        plotSys(fileName, 'sr', args.chan, templates, systematics.keys(), year, args.run)
    
    print colored('##### Prepare data card', 'red')
    writeCard(cardName, shapes, templates, None, extraLines, showSysList, {}, {}, run=outDir)
    ##writeCard(cardName, shapes, templates, None, extraLines, showSysList, {}, scaleShape={'fsr': 1/sqrt(2)})
    ##writeCard(cardName, shapes, templates, None, extraLines, showSysList + ['nonPrompt'], {}, scaleShape={'fsr': 1/sqrt(2)})

    if blind == False:
        print colored('##### Run fit diagnostics for obs (stat+sys)', 'red')
        runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=False, mode='obs', run=outDir)
        print colored('##### Run fit diagnostics for obs (stat)', 'red')
        runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=True, mode='obs', run=outDir)
        
    print colored('##### Run fit diagnostics for exp (stat+sys)', 'red')
    runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=True, statOnly=False, mode='exp', run=outDir)
    print colored('##### Run fit diagnostics for exp (stat)', 'red')
    runFitDiagnostics(cardName, year, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=True, statOnly=True, mode='exp', run=outDir)
    
    print colored('##### Run NLL scan', 'red')
    rMin = 0.5
    rMax = 1.5
    plotNLLScan(cardName, year, 'exp', trackParameters = [(t+'_norm') for t in templates[1:]], freezeParameters = allSys, doRatio=doRatio, rMin=rMin, rMax=rMax, run=outDir)
    
    if blind == False:
        if doRatio == True:
            rMin = 0.5
            rMax = 1.5
        plotNLLScan(cardName, year, 'obs', trackParameters = [(t+'_norm') for t in templates[1:]], freezeParameters = allSys, doRatio=doRatio, rMin=rMin, rMax=rMax, run=outDir)
        
    poi = ['r']
    if blind == False:
        print colored('##### Run impacts (obs)', 'red')        
        runImpacts(cardName, year, perPage, poi=poi, doRatio=doRatio, run=outDir)
        
    print colored('##### Run impacts (exp)', 'red')
    runImpacts(cardName, year, perPage, toys=True, poi=poi, doRatio=doRatio, run=outDir)

    if blind == False:
        print colored('##### Run channel compatibility (obs)', 'red')
        runCompatibility(cardName, year, perPage, doRatio=doRatio, run=outDir)
        plotCC(cardName, year, poi='r', rMin=0.7, rMax=1.3, run=outDir, mode='obs', addNominal=True)
        
    print colored('##### Run channel compatibility (exp)', 'red')
    runCompatibility(cardName, year, perPage, toys=True, doRatio=doRatio, run=outDir)
    plotCC(cardName, year, poi='r', rMin=0.7, rMax=1.3, run=outDir, mode='exp', addNominal=True)
    
    if doRatio == False:
        
        if blind == False:
            print colored('##### Calculate the significance (obs)', 'red')
            runSignificance(cardName, run=outDir)
            
        print colored('##### Calculate the significance (exp)', 'red')
        runSignificance(cardName, expected=True, run=outDir)
        
    if args.tab == True:
        print colored('##### Create tables', 'red')
        if blind == False: 
            os.system('./makeTable.py --mode=impacts_r --template=./data/impacts_r.tex --chan=' + args.chan + ' --run=' + args.run + ' --card=' + cardName)
        os.system('./makeTable.py --mode=impacts_r --template=./data/impacts_r.tex --chan=' + args.chan + ' --run=' + args.run + ' --card=' + cardName + ' --asimov')

doRatio = args.ratio
fitName = 'srFit'
if doRatio: fitName = 'ratioFit'

channels = []
if args.chan == 'll':
    for ch in ['ee', 'mumu', 'emu']:
        channels.append('sr_'+ch)
else: channels.append('sr_'+args.chan)
        
doSignalRegionFit(fitName, channels, 35, doRatio=doRatio, year='2016', blind=args.blind)

#goodnessOfFit('srFit', run=args.run+args.chan)
#doLinearityCheck('srFit', run=args.run+args.chan)
