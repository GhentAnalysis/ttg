#! /usr/bin/env python

#
# Script as have been used to do the combine fit for AN-17-197 
#
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.plots.plot         import getHistFromPkl, normalizeBinWidth
from ttg.plots.combineTools import writeCard, runFitDiagnostics, runSignificance, runImpacts, goodnessOfFit, doLinearityCheck
from ttg.plots.systematics  import systematics, linearSystematics, showSysList, q2Sys, pdfSys, rateParameters

import os, ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt


####################
# Helper functions #
####################

# Sets dummy bin contents for completely empty histograms (probably experienced some crash during tests in the past)
# I assume this is probably needed anymore
def protectHist(hist):
  if hist.Integral() < 0.00001:
    for i in range(1, hist.GetNbinsX()+1):
      if hist.GetBinContent(i) <= 0.00001: hist.SetBinContent(i, 0.00001)
  return hist

# Applies a scalefactor, given as a list of tuples (SF, upError, downError) to a histogram
# When sys==Up/Down, returns the upper/down estimate respectively
# (originally the SF was derived separately per bin, now simply one general SF is being used)
def applyNonPromptSF(histTemp, nonPromptSF, sys=None):
  if not nonPromptSF: 
    return histTemp
  hist = histTemp.Clone()
# srMap = {1:'njet1-deepbtag1p', 2:'njet2p-deepbtag0', 3:'njet2p-deepbtag1', 4:'njet2p-deepbtag2p'}
  srMap = {1:'all', 2:'all', 3:'all', 4:'all'}
  for i, sr in srMap.iteritems():
    err = max(abs(nonPromptSF[sr][1]), abs(nonPromptSF[sr][2])) # fix for failed fits
    if sys and sys == "Up":     sf = nonPromptSF[sr][0] + err
    elif sys and sys == "Down": sf = nonPromptSF[sr][0] - err
    else:                       sf = nonPromptSF[sr][0]
    hist.SetBinContent(i, hist.GetBinContent(i)*sf)
  return hist

# Write a histrogram to the rootfile, for "name" of the distribution and "template"
# Optionaly the bin width could be noralized, specific bins could be set to 0,
# the shape could be replaced by another one or all the bins could be merged into one
from ttg.plots.replaceShape import replaceShape
def writeHist(rootFile, name, template, histTemp, norm=None, removeBins = None, shape=None, mergeBins=False):  # pylint: disable=R0913
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

###########################################
# Create directory to store combine stuff #
###########################################
try:    os.makedirs('combine')
except: pass


#############################################################################################################################################

################################################################
# Function to write ROOT File for a charged isolation only fit #
################################################################
# the chgIso fit is complicated, better study first the simple signal regions fit to get familiar with the code

tag             = 'eleSusyLoose-phoCBnoChgIso-match'                # Here we use the plots where no charged iso cut is applied, and we have the contributions separated by photon type
templatesChgIso = ['TTGamma', 'TTJets', 'ZG', 'DY', 'other']        # Stacks for chgIso fit have single-t merged into other

def writeRootFileForChgIso(name, selection):
  plot = 'photon_chargedIso_bins_NO'

  if selection == 'all': selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'
  else:                  selection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-' + selection + '-photonPt20'

  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  dataHist = getHistFromPkl(('eleSusyLoose-phoCBnoChgIso', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])  # Get data histogram, with ee, emu and mumu merged
  writeHist(f, 'chgIso', 'data_obs', dataHist, norm=1)                                                                             # For the chgIso we normalized the bin width (i.e. contents become events/GeV)

  from ttg.plots.plot import applySidebandUnc
  for splitType in ['_g', '_f', '_h']: # histograms are written per photon type
    if   splitType == '_g': selectors = [[t, '(genuine,misIdEle)'] for t in templatesChgIso]
    elif splitType == '_f': selectors = [[t, '(hadronicFake)']     for t in templatesChgIso]
    elif splitType == '_h': selectors = [[t, '(hadronicPhoton)']   for t in templatesChgIso]

    if name.count('dd') and splitType=='_f':
      # In case of data-driven fake estimation, we take data shape from the sideband
      sideBandShape = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
      normalizeBinWidth(sideBandShape, 1)
      sideBandShapeUp   = applySidebandUnc(sideBandShape, plot, selection, True)  # up and down error based on tt closure (but this part might be broken by now)
      sideBandShapeDown = applySidebandUnc(sideBandShape, plot, selection, False)
      
      chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, '', *selectors)
      writeHist(f, 'chgIso',                'all_f', chgIsoHist, norm=1, shape=sideBandShape)         # the shapes fakes are replaced by sideband (but normalization is kept)
      writeHist(f, 'chgIsoSideBandUncUp',   'all_f', chgIsoHist, norm=1, shape=sideBandShapeUp)
      writeHist(f, 'chgIsoSideBandUncDown', 'all_f', chgIsoHist, norm=1, shape=sideBandShapeDown)
    else:
      # Default case
      chgIsoHist = getHistFromPkl((tag, 'all', selection), plot, '', *selectors)
      writeHist(f, 'chgIso',  'all' + splitType, chgIsoHist, norm=1)

  # Add also sigmaIetaIeta sideband itself for fake normalization [assume that it is similar in sideband as in nominal region] 
  # In this way, the charged isolation fit can focus on the hadronic normalization
  plot = 'photon_SigmaIetaIeta'
  dataHist = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-matchCombined', 'all', selection), plot, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
  writeHist(f, 'sigEtaEta', 'data_obs', dataHist)
  for splitType in ['_g', '_f', '_h']:
    if   splitType == '_g': selectors = [[sample, '(genuine photons)'] for sample in ['TTGamma', 'TTJets', 'DY']] + [[sample, '(misidentified electrons)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    if   splitType == '_h': selectors = [[sample, '(hadronic photons)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    if   splitType == '_f': selectors = [[sample, '(hadronic fakes)'] for sample in ['TTGamma', 'TTJets', 'DY']]
    hist = getHistFromPkl(('eleSusyLoose-phoCB-sidebandSigmaIetaIeta-matchCombined', 'all', selection), plot, '', *selectors)
    writeHist(f, 'sigEtaEta',  'all' + splitType, hist)
  f.Close()

#############################################################
# Function to make Post-fit plots for charged isolation fit #
#############################################################
from ttg.plots.plot import Plot
from ttg.tools.style import drawLumi
import ttg.tools.style as styles
# Simply get the histograms back out of the shapes file and applies the fit results
def plotPostFit(filename, name, name2, res):
  f = ROOT.TFile('combine/' + filename + '_shapes.root')
  all_f      = f.Get(name + '/all_f')
  all_g      = f.Get(name + '/all_g')
  all_h      = f.Get(name + '/all_h')
  data       = f.Get(name + '/data_obs')

  if res:
    all_g.Scale(res['r'][0])
    all_f.Scale(res['fake_norm'][0])
    all_h.Scale(res['hadronic_norm'][0])

  data.style  = styles.errorStyle(ROOT.kBlack)
  all_g.style = styles.fillStyle(ROOT.kYellow) 
  all_h.style = styles.fillStyle(ROOT.kRed) 
  all_f.style = styles.fillStyle(ROOT.kGreen)

  data.texName  = 'data (dilepton)'
  all_g.texName = 'genuine'
  all_h.texName = 'hadronic photons'
  all_f.texName = 'hadronic fakes (from sideband)' if name == 'chgIso' else 'hadronic fakes'

  plot       = Plot(name + name2, 'Photon Ch. Had. Isolation (GeV)' if name=='chgIso' else '#sigma_{i#eta i#eta}', None, None, overflowBin=None, stack=[[]], texY='Events / GeV')
  plot.stack = [[all_g, all_h, all_f], [data]]
  plot.histos = {i:i for i in sum(plot.stack, [])}

  from ttg.tools.helpers import plotDir
  plot.draw(plot_directory = os.path.join(plotDir, 'combinePlots'),
    ratio   = {'yRange':(0.1,1.9),'texY': 'data/MC'},
    logX    = False, logY = False, sorting = False,
    yRange  = (0.0001, "auto"),
    drawObjects = drawLumi(None, 35.9),
  )

#########################
# Charged isolation fit #
#########################
fakeSF, hadronicSF = {}, {}
def doChgIsoFit():
  log.info(' --- Charged isolation fit --- ')
  templatesPh = ['all_g', 'all_f', 'all_h']
  extraLines  = ['fake_norm     rateParam * all_f 1']
  extraLines += ['hadronic_norm rateParam * all_h 1']#, 'hadronic_norm param 1.0 0.3']
  extraLines += ['* autoMCStats 0 1 1']

  #for sel in ['njet1-deepbtag1p', 'njet2p-deepbtag0', 'njet2p-deepbtag1', 'njet2p-deepbtag2p','njet2p-deepbtag1p','all']:
  for sel in ['all']:
    for dataDriven in [True]:
      cardName = 'chgIsoFit_' + ('dd_' if dataDriven else '') + sel
      writeRootFileForChgIso(cardName, sel)
      # Write the combine card for shapes "chgIso" and "sigEtaEta", using templates split by photon type, and write out the above mentioned extra lines
      # Only systematic here is the SideBandUnc applying for the chgIso shape for the fakes
      # [templatesNoSys]=None in this case
      # [linearSystematics] are empty in this case
      writeCard(cardName, ['chgIso', 'sigEtaEta'], templatesPh, None, extraLines, ['all_f:chgIso:SideBandUnc'], {})
      # Run the combine fit diagnostics using the above card and accompanying root file, track the hadronic and fake normalizations (i.e. the needed SF)
      results = runFitDiagnostics(cardName, toys=False, statOnly=False, trackParameters = ['hadronic_norm','fake_norm'])
      fakeSF[sel]     = results['fake_norm']
      hadronicSF[sel] = results['hadronic_norm']
      # Post pre- and postfit
      plotPostFit(cardName, 'chgIso', '_prefit',  None)
      plotPostFit(cardName, 'chgIso', '_postfit', results)
      plotPostFit(cardName, 'sigEtaEta', '_prefit',  None)
      plotPostFit(cardName, 'sigEtaEta', '_postfit', results)
      # Make impact parameter plot with the cards
      runImpacts(cardName)

  for j, k in fakeSF.iteritems():
    log.info('Charged isolation fit for ' + j + ' results in fakes: %.2f (+%.2f, %.2f)' % k)
  for j, k in hadronicSF.iteritems():
    log.info('Charged isolation fit for ' + j + ' results in hadronics: %.2f (+%.2f, %.2f)' % k)

doChgIsoFit()




#############################################################################################################################################

########################################################
# Function to write ROOT file for a signal regions fit #
########################################################

templates = ['TTGamma', 'TTJets', 'ZG', 'DY', 'other', 'single-t']
def writeRootFile(name, systematicVariations):
  f = ROOT.TFile('combine/' + name + '_shapes.root', 'RECREATE')

  baseSelection = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20'                 # Selection for standard signal regions
  onZSelection  = 'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20'         # Selection for on-Z ZGamma CR
  ttSelection   = 'll-looseLeptonVeto-mll40-offZ-signalRegion-nphoton0'              # Selection for 0-photon ttbar CR
  tag           = 'eleSusyLoose-phoCBfull-matchNew'
  tagTT         = 'eleSusyLoose'

  # Write the data histograms to the combine shapes file: SR (separate for ee, emu, mumu, SF), ZGamma CR and ttbar CR
  writeHist(f, 'sr_OF', 'data_obs', getHistFromPkl((tag,   'emu',  baseSelection), 'signalRegionsSmall', '', ['MuonEG']),                               mergeBins=False)
  writeHist(f, 'sr_SF', 'data_obs', getHistFromPkl((tag,   'SF',   baseSelection), 'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon']),             mergeBins=False)
  writeHist(f, 'sr_ee', 'data_obs', getHistFromPkl((tag,   'ee',   baseSelection), 'signalRegionsSmall', '', ['DoubleEG']),                             mergeBins=False)
  writeHist(f, 'sr_mm', 'data_obs', getHistFromPkl((tag,   'mumu', baseSelection), 'signalRegionsSmall', '', ['DoubleMuon']),                           mergeBins=False)
  writeHist(f, 'zg_SF', 'data_obs', getHistFromPkl((tag,   'SF',   onZSelection),  'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon']),             mergeBins=True)   # always merge regions: use simply one CR
  writeHist(f, 'tt',    'data_obs', getHistFromPkl((tagTT, 'all',  ttSelection),   'signalRegionsSmall', '', ['DoubleEG'], ['DoubleMuon'], ['MuonEG']), mergeBins=True)   # always mergs regions: use simply one CR

  for t in templates:
    promptSelectors   = [[t, '(genuine,misIdEle)']]
    fakeSelectors     = [[t, '(hadronicFake)']]
    hadronicSelectors = [[t, '(hadronicPhoton)']]

    # Write SR and ZGamma CR
    for shape, channel in [('sr_OF', 'emu'), ('sr_SF', 'SF'), ('sr_ee', 'ee'), ('sr_mm', 'mumu'), ('zg_SF', 'SF')]:
      q2Variations = []
      pdfVariations = []
      for sys in [''] + systematicVariations:
        prompt   = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *promptSelectors)
        fake     = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *fakeSelectors)
        hadronic = getHistFromPkl((tag, channel, baseSelection if not 'zg' in shape else onZSelection), 'signalRegionsSmall', sys, *hadronicSelectors)

        # In case of fakes and hadronics, apply their SF (and calculate up and down variations)
        if sys == '':
          fakeUp, fakeDown         = applyNonPromptSF(fake, fakeSF, 'Up'),         applyNonPromptSF(fake, fakeSF, 'Down')
          hadronicUp, hadronicDown = applyNonPromptSF(hadronic, hadronicSF, 'Up'), applyNonPromptSF(hadronic, hadronicSF, 'Down')
        fake     = applyNonPromptSF(fake, fakeSF)
        hadronic = applyNonPromptSF(hadronic, hadronicSF)

        # Add up the contributions of genuine, fake and hadronic photons
        if sys == '':
          totalUp   = prompt.Clone()
          totalDown = prompt.Clone()
          totalUp.Add(fakeUp)
          totalDown.Add(fakeDown)
          totalUp.Add(hadronicUp)
          totalDown.Add(hadronicDown)
          writeHist(f, shape+'nonPromptUp',   t, totalUp, mergeBins = ('zg' in shape))
          writeHist(f, shape+'nonPromptDown', t, totalDown, mergeBins = ('zg' in shape))
        total = prompt.Clone()
        total.Add(hadronic)
        total.Add(fake)

        if sys == '':     nominal = total                                                   # Save nominal case to be used for q2/pdf calculations
        if 'pdf' in sys:  pdfVariations += [total]                                          # Save all pdfVariations in list
        elif 'q2' in sys: q2Variations += [total]                                           # Save all q2Variations in list
        else:             writeHist(f, shape+sys, t, total, mergeBins = ('zg' in shape))    # Write nominal and other systematics

      # Calculation of up and down envelope pdf variations
      if len(pdfVariations) > 0:
        up, down = pdfSys(pdfVariations, nominal)
        writeHist(f, shape+'pdfUp',   t, up,   mergeBins = ('zg' in shape))
        writeHist(f, shape+'pdfDown', t, down, mergeBins = ('zg' in shape))

      # Calcualtion of up and down envelope q2 variations
      if len(q2Variations) > 0:
        up, down = q2Sys(q2Variations)
        writeHist(f, shape+'q2Up',   t, up,   mergeBins = ('zg' in shape))
        writeHist(f, shape+'q2Down', t, down, mergeBins = ('zg' in shape))

    # Similar for tt CR, only here we do not have to sum the photon types
    for shape, channel in [('tt', 'all')]:
      q2Variations = []
      pdfVariations = []
      selector = [[t,]]
      for sys in [''] + systematicVariations:
        total = getHistFromPkl((tagTT, channel, ttSelection), 'signalRegionsSmall', sys, *selector)

        if sys == '':     nominal = total
        if 'pdf' in sys:  pdfVariations += [total]
        elif 'q2' in sys: q2Variations += [total]
        else:             writeHist(f, shape+sys, t, total, mergeBins = True)

      if len(pdfVariations) > 0:
        up, down = pdfSys(pdfVariations, nominal)
        writeHist(f, shape+'pdfUp',   t, up,   mergeBins=True)
        writeHist(f, shape+'pdfDown', t, down, mergeBins=True)

      if len(q2Variations) > 0:
        up, down = q2Sys(q2Variations)
        writeHist(f, shape+'q2Up',   t, up,   mergeBins=True)
        writeHist(f, shape+'q2Down', t, down, mergeBins=True)


  f.Close()

######################
# Signal regions fit #
######################
def doSignalRegionFit(cardName, shapes, perPage=30, doRatio=False):
  log.info(' --- Signal regions fit (' + cardName + ') --- ')
  extraLines  = [(t + '_norm rateParam * ' + t + '* 1')                 for t in templates[1:]]
  extraLines += [(t + '_norm param 1.0 ' + str(rateParameters[t]/100.)) for t in templates[1:]]
  extraLines += ['* autoMCStats 0 1 1']

  if doRatio: # Special case in order to fit the ratio of ttGamma to ttbar [hardcoded numbers as discussed with 1l group]
    log.info(' --- Ratio ttGamma/ttBar fit (' + cardName + ') --- ')
    extraLines += ['renormTTGamma rateParam * TTGamma* 0.338117493', 'nuisance edit freeze renormTTGamma ifexists']
    extraLines += ['renormTTbar rateParam * TTJets* 1.202269886',    'nuisance edit freeze renormTTbar ifexists']
    extraLines += ['TTbar_norm rateParam * TT* 0.83176 [0.,2.]']
  else: # default measurement
    log.info(' --- Signal regions fit (' + cardName + ') --- ')

  # Write shapes file and combine card using
  # * systematic.keys() --> all the up/down, pdf and q2 variations histograms as imported from ttg.plots.systematics, being used to write the shape file
  # * the list of shapes to be used in the fit (SR for specific channels, CR's)
  # * the templates defined above
  # * [templatesNoSys] not use (would simply add a template without systematics)
  # * the extraLines at the bottom of the combine card defined above
  # * the showSysList are the names of all the nuisance parameters + extra nuisance parameter for the non prompt SF uncertainty
  # * no linear systematics (originally there was lumi here, but we were requested to take it out)
  # * the up/down variations of FSR were scaled back with 1/sqrt(2) according to TOP recommendations
  writeRootFile(cardName, systematics.keys())
  writeCard(cardName, shapes, templates, None, extraLines, showSysList + ['nonPrompt'], {}, scaleShape={'fsr': 1/sqrt(2)})

  # Run the fit diagnostics, giving results (both for stat+sys as for stat-only)
  runFitDiagnostics(cardName, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=False)
  runFitDiagnostics(cardName, trackParameters = [(t+'_norm') for t in templates[1:]]+['r'], toys=False, statOnly=True)
  # Run impacts (and also with toys), perPage defines how much nuisances per page on the impact plot
  runImpacts(cardName, perPage)
  runImpacts(cardName, perPage, toys=True)
  # Calculate the significance
  runSignificance(cardName)
  runSignificance(cardName, expected=True)


doSignalRegionFit('srFit_SF', ['sr_SF', 'zg_SF'], 35)
doSignalRegionFit('srFit_OF', ['sr_OF', 'zg_SF'], 35)
doSignalRegionFit('srFit', ['sr_OF', 'sr_SF', 'zg_SF'], 35)
doSignalRegionFit('srFit_ee', ['sr_ee', 'zg_SF'], 35)
doSignalRegionFit('srFit_mm', ['sr_mm', 'zg_SF'], 35)

doSignalRegionFit('ratioFit', ['sr_OF', 'sr_SF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_SF', ['sr_SF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_OF', ['sr_OF', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_ee', ['sr_ee', 'zg_SF'], 35, doRatio=True)
doSignalRegionFit('ratioFit_mm', ['sr_mm', 'zg_SF'], 35, doRatio=True)
#goodnessOfFit('srFit')
#doLinearityCheck('srFit')
