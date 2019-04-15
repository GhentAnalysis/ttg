#! /usr/bin/env python

#
# Argument parser and logging
#
import os, argparse, copy
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--year',           action='store',      default=None,        help='year for which to plot, of not specified run for all 3', choices=['16', '17', '18','all'])
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--channel',        action='store',      default=None)
argParser.add_argument('--tag',            action='store',      default='phoCBfull')
argParser.add_argument('--sys',            action='store',      default=None)
argParser.add_argument('--filterPlot',     action='store',      default=None)
argParser.add_argument('--runSys',         action='store_true', default=False)
argParser.add_argument('--showSys',        action='store_true', default=False)
argParser.add_argument('--post',           action='store_true', default=False)
argParser.add_argument('--editInfo',       action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
argParser.add_argument('--overwrite',      action='store_true', default=False, help='do not load a plot/histogram if it already exists')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Check git and edit the info file
#
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi
if args.editInfo:
  try:    os.makedirs(os.path.join(plotDir, args.tag))
  except: pass
  editInfo(os.path.join(plotDir, args.tag))

#
# Systematics
#
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList

#
# Submit subjobs
#
if not args.isChild:
  updateGitInfo()
  from ttg.tools.jobSubmitter import submitJobs
  from ttg.plots.variations   import getVariations

  if args.showSys and args.runSys: sysList = showSysList + ['stat']
  elif args.sys:                   sysList = [args.sys]
  else:                            sysList = [None] + (systematics.keys() if args.runSys else [])

  subJobArgs, subJobList = getVariations(args, sysList)

  submitJobs(__file__, subJobArgs, subJobList, argParser, subLog=args.tag)
  exit(0)

#
# Initializing
#
import ROOT
from ttg.plots.plot           import Plot, xAxisLabels, fillPlots, addPlots
from ttg.plots.plot2D         import Plot2D, add2DPlots
from ttg.plots.cutInterpreter import cutStringAndFunctions
from ttg.samples.Sample       import createStack
from ttg.plots.photonCategories import photonCategoryNumber
from math import pi

ROOT.gROOT.SetBatch(True)

# reduce string comparisons in loop --> store as booleans
phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
forward     = args.tag.count('forward')
prefire     = args.tag.count('prefireCheck')
noWeight    = args.tag.count('noWeight')
normalize   = any(args.tag.count(x) for x in ['sigmaIetaIeta', 'randomConeCheck', 'splitOverlay', 'compareWithTT', 'compareTTSys', 'compareTTGammaSys'])


#
# Create stack
#
#
import glob
stackFile = 'default_' + args.year
for f in sorted(glob.glob("../samples/data/*.stack")):
  stackName = os.path.basename(f).split('.')[0]
  if not stackName[-3:] in ['_16', '_17', '_18']:
    log.warning('stack file without year label found (' + stackName + '), please remove or label properly')
    exit(0)
  if stackName not in stackFile and args.tag.count(stackName[:-3]) and stackName[-2:] in ['16', '17', '18']:
    stackFile = stackName[:-3]

years = ['16', '17', '18'] if args.year == 'all' else [args.year]

if args.year == 'all':
  for year in years:
    if not os.path.isfile('../samples/data/' + stackFile + '_' + year + '.stack'):
      log.warning('stackfile ' + stackFile + '_' + year + '.stack is missing, exiting')
      exit(0)


# FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME 
# !!!!!!!!!!!!!! temporarily using 16 tuplesfile for everything 
# tupleFiles = {y : os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_' + y + '.conf') for y in ['16', '17', '18']}

tupleFiles = {y : os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_' + '16' + '.conf') for y in ['16', '17', '18']}


#FIXME maybe check somewhere that all 3 tuples contain the same samples (or mitigate by separate stack files or some year-specifier within the stack)
# when running over all years, just initialise the plots with the stack for 16
stack = createStack(tuplesFile   = os.path.expandvars(tupleFiles['16' if args.year == 'all' else args.year]),
                    styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '_' + ('16' if args.year == 'all' else args.year) + '.stack'),
                    channel      = args.channel,
                    replacements = getReplacementsForStack(args.sys))

#
# Define plots
#
Plot.setDefaults(stack=stack, texY = ('(1/N) dN/dx' if normalize else 'Events'))
Plot2D.setDefaults(stack=stack)

def channelNumbering(t):
  return (1 if t.isMuMu else (2 if t.isEMu else 3))

def createSignalRegions(t):
  if t.njets == 1:
    if t.ndbjets == 0: return 0
    else:              return 1
  elif t.njets >= 2:
    if t.ndbjets == 0: return 2
    if t.ndbjets == 1: return 3
    else:              return 4
  return -1

def createSignalRegionsSmall(t):
  if t.njets == 1:
    if t.ndbjets > 0:  return 0
  elif t.njets >= 2:
    if t.ndbjets == 0: return 1
    if t.ndbjets == 1: return 2
    else:              return 3
  return -1

def createSignalRegionsLarge(t):
  if t.njets == 1:
    if t.ndbjets == 0: return 0
    else:              return 1
  elif t.njets == 2:
    if t.ndbjets == 0: return 2
    if t.ndbjets == 1: return 3
    else:              return 4
  elif t.njets >= 3:
    if t.ndbjets == 0: return 5
    if t.ndbjets == 1: return 6
    if t.ndbjets == 2: return 7
    else:              return 8
  return -1

# Plot definitions (allow long lines, and switch off unneeded lambda warning, because lambdas are needed)
# pylint: disable=C0301,W0108
def makePlotList():
  plotList = []
  if args.tag.count('randomConeCheck'):
    plotList.append(Plot('photon_chargedIso',          'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (20, 0, 20)))
    plotList.append(Plot('photon_chargedIso_small',    'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (80, 0, 20)))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)', lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c._phPt[c.ph], (20, 0, 2)))
  else:
    plotList.append(Plot('yield',                      'yield',                                 lambda c : channelNumbering(c),                                (3,  0.5, 3.5), histModifications=xAxisLabels(['#mu#mu', 'e#mu', 'ee'])))
    plotList.append(Plot('nVertex',                    'vertex multiplicity',                   lambda c : c._nVertex,                                         (50, 0, 50)))
    plotList.append(Plot('nTrueInt',                   'nTrueInt',                              lambda c : c._nTrueInt,                                        (50, 0, 50)))
    plotList.append(Plot('nphoton',                    'number of photons',                     lambda c : c.nphotons,                                         (4,  -0.5, 3.5)))
    plotList.append(Plot('photon_pt',                  'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            (20, 15, 115)))
    plotList.append(Plot('photon_eta',                 '|#eta|(#gamma)',                        lambda c : abs(c._phEta[c.ph]),                                (15, 0, 2.5)))
    plotList.append(Plot('photon_phi',                 '#phi(#gamma)',                          lambda c : c._phPhi[c.ph],                                     (10, -pi, pi)))
    plotList.append(Plot('photon_mva',                 '#gamma-MVA',                            lambda c : c._phMva[c.ph],                                     (20, -1, 1)))
    plotList.append(Plot('photon_chargedIso',          'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_NO',       'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins',     'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 1, 2, 3, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins_NO',  'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 1, 2, 3, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_small',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (80, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_small_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (80, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_wide',     'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 2, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_wide_NO',  'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 2, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins2',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 1, 2, 3, 5, 10], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins2_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441, 1, 2, 3, 5, 10], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins3',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.1] + range(1, 21), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins3_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.1] + range(1, 21), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)',      lambda c : c._phChargedIsolation[c.ph]/c.ph_pt,                (20, 0, 2)))
    plotList.append(Plot('photon_neutralIso',          'neutralIso(#gamma) (GeV)',              lambda c : c._phNeutralHadronIsolation[c.ph],                  (25, 0, 5)))
    plotList.append(Plot('photon_photonIso',           'photonIso(#gamma) (GeV)',               lambda c : c._phPhotonIsolation[c.ph],                         (32, 0, 8)))
    plotList.append(Plot('photon_SigmaIetaIeta',       '#sigma_{i#etai#eta}(#gamma)',           lambda c : c._phSigmaIetaIeta[c.ph],                           (20, 0, 0.04)))
    plotList.append(Plot('photon_hadOverEm',           'hadronicOverEm(#gamma)',                lambda c : c._phHadronicOverEm[c.ph],                          (20, 0, .025)))
    plotList.append(Plot('phJetDeltaR',                '#DeltaR(#gamma, j)',                    lambda c : c.phJetDeltaR,                                      [0, 0.1, 0.6, 1.1, 1.6, 2.1, 2.6, 3.1, 3.6, 4.1, 4.6]))
    plotList.append(Plot('phBJetDeltaR',               '#DeltaR(#gamma, b)',                    lambda c : c.phBJetDeltaR,                                     [0, 0.1, 0.6, 1.1, 1.6, 2.1, 2.6, 3.1, 3.6, 4.1, 4.6]))
    plotList.append(Plot('l1_pt',                      'p_{T}(l_{1}) (GeV)',                    lambda c : c.l1_pt,                                            (20, 25, 225)))
    plotList.append(Plot('l1_eta',                     '|#eta|(l_{1})',                         lambda c : abs(c._lEta[c.l1]),                                 (15, 0, 2.4)))
    plotList.append(Plot('l1_eta_small',               '|#eta|(l_{1})',                         lambda c : abs(c._lEta[c.l1]),                                 (50, 0, 2.4)))
    plotList.append(Plot('l1_phi',                     '#phi(l_{1})',                           lambda c : c._lPhi[c.l1],                                      (10, -pi, pi)))
    plotList.append(Plot('l1_relIso',                  'relIso(l_{1})',                         lambda c : c._relIso[c.l1],                                    (10, 0, 0.12)))
    plotList.append(Plot('l1_jetDeltaR',               '#DeltaR(l_{1}, j)',                     lambda c : c.l1JetDeltaR,                                      (20, 0, 5)))
    plotList.append(Plot('l2_pt',                      'p_{T}(l_{2}) (GeV)',                    lambda c : c.l2_pt,                                            (20, 15, 215)))
    plotList.append(Plot('l2_eta',                     '|#eta|(l_{2})',                         lambda c : abs(c._lEta[c.l2]),                                 (15, 0, 2.4)))
    plotList.append(Plot('l2_eta_small',               '|#eta|(l_{2})',                         lambda c : abs(c._lEta[c.l2]),                                 (50, 0, 2.4)))
    plotList.append(Plot('l2_phi',                     '#phi(l_{2})',                           lambda c : c._lPhi[c.l2],                                      (10, -pi, pi)))
    plotList.append(Plot('l2_relIso',                  'relIso(l_{2})',                         lambda c : c._relIso[c.l2],                                    (10, 0, 0.12)))
    plotList.append(Plot('l2_jetDeltaR',               '#DeltaR(l_{2}, j)',                     lambda c : c.l2JetDeltaR,                                      (20, 0, 5)))
    plotList.append(Plot('dl_mass',                    'm(ll) (GeV)',                           lambda c : c.mll,                                              (20, 0, 200)))
    plotList.append(Plot('dl_mass_small',              'm(ll) (GeV)',                           lambda c : c.mll,                                              (40, 0, 200)))
    plotList.append(Plot('ll_deltaPhi',                '#Delta#phi(ll)',                        lambda c : deltaPhi(c._lPhi[c.l1], c._lPhi[c.l2]),             (10, 0, pi)))
    plotList.append(Plot('photon_randomConeIso',       'random cone chargedIso(#gamma) (Gev)',  lambda c : c._phRandomConeChargedIsolation[c.ph],              (20, 0, 20)))
    plotList.append(Plot('l1g_mass',                   'm(l_{1}#gamma) (GeV)',                  lambda c : c.ml1g,                                             (20, 0, 200)))
    plotList.append(Plot('l1g_mass_small',             'm(l_{1}#gamma) (GeV)',                  lambda c : c.ml1g,                                             (40, 0, 200)))
    plotList.append(Plot('phL1DeltaR',                 '#DeltaR(#gamma, l_{1})',                lambda c : c.phL1DeltaR,                                       (20, 0, 5)))
    plotList.append(Plot('l2g_mass',                   'm(l_{2}#gamma) (GeV)',                  lambda c : c.ml2g,                                             (20, 0, 200)))
    plotList.append(Plot('l2g_mass_small',             'm(l_{2}#gamma) (GeV)',                  lambda c : c.ml2g,                                             (40, 0, 200)))
    plotList.append(Plot('phL2DeltaR',                 '#DeltaR(#gamma, l_{2})',                lambda c : c.phL2DeltaR,                                       (20, 0, 5)))
    plotList.append(Plot('phoPt_over_dlg_mass',        'p_{T}(#gamma)/m(ll#gamma)',             lambda c : c.ph_pt/c.mllg,                                     (40, 0, 2)))
    plotList.append(Plot('dlg_mass',                   'm(ll#gamma) (GeV)',                     lambda c : c.mllg,                                             (40, 0, 500)))
    plotList.append(Plot('dlg_mass_zoom',              'm(ll#gamma) (GeV)',                     lambda c : c.mllg,                                             (40, 50, 200)))
    plotList.append(Plot('phLepDeltaR',                '#DeltaR(#gamma, l)',                    lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                    (20, 0, 5)))
    plotList.append(Plot('njets',                      'number of jets',                        lambda c : c.njets,                                            (8, -.5, 7.5)))
    plotList.append(Plot('nbtag',                      'number of medium b-tags (deepCSV)',     lambda c : c.ndbjets,                                          (4, -.5, 3.5)))
    plotList.append(Plot('j1_pt',                      'p_{T}(j_{1}) (GeV)',                    lambda c : c._jetSmearedPt[c.j1],                              (30, 30, 330)))
    plotList.append(Plot('j1_eta',                     '|#eta|(j_{1})',                         lambda c : abs(c._jetEta[c.j1]),                               (15, 0, 2.4)))
    plotList.append(Plot('j1_phi',                     '#phi(j_{1})',                           lambda c : c._jetPhi[c.j1],                                    (10, -pi, pi)))
    plotList.append(Plot('j1_deepCSV',                 'deepCSV(j_{1})',                        lambda c : c._jetDeepCsv_b[c.j1] + c._jetDeepCsv_bb[c.j1],     (20, 0, 1)))
    plotList.append(Plot('j2_pt',                      'p_{T}(j_{2}) (GeV)',                    lambda c : c._jetSmearedPt[c.j2],                                     (30, 30, 330)))
    plotList.append(Plot('j2_eta',                     '|#eta|(j_{2})',                         lambda c : abs(c._jetEta[c.j2]),                               (15, 0, 2.4)))
    plotList.append(Plot('j2_phi',                     '#phi(j_{2})',                           lambda c : c._jetPhi[c.j2],                                    (10, -pi, pi)))
    plotList.append(Plot('j2_deepCSV',                 'deepCSV(j_{2})',                        lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2],     (20, 0, 1)))
    plotList.append(Plot('dbj1_pt',                    'p_{T}(bj_{1}) (GeV)',                   lambda c : c._jetSmearedPt[c.dbj1],                            (30, 30, 330)))
    plotList.append(Plot('dbj2_pt',                    'p_{T}(bj_{2}) (GeV)',                   lambda c : c._jetSmearedPt[c.dbj2],                            (30, 30, 330)))
    plotList.append(Plot('dbj1_deepCSV',               'deepCSV(dbj_{1})',                      lambda c : c._jetDeepCsv_b[c.dbj1] + c._jetDeepCsv_bb[c.dbj1], (20, 0, 1)))
    plotList.append(Plot('dbj2_deepCSV',               'deepCSV(dbj_{2})',                      lambda c : c._jetDeepCsv_b[c.dbj2] + c._jetDeepCsv_bb[c.dbj2], (20, 0, 1)))
    plotList.append(Plot('signalRegions',              'signal region',                         lambda c : createSignalRegions(c),                             (5, 0, 5), histModifications=xAxisLabels(['1j,0b', '1j,1b', '#geq2j,0b', '#geq2j,1b', '#geq2j,#geq2b'])))
    plotList.append(Plot('signalRegionsSmall',         'signal region',                         lambda c : createSignalRegionsSmall(c),                        (4, 0, 4), histModifications=xAxisLabels(['1j,1b', '#geq2j,0b', '#geq2j,1b', '#geq2j,#geq2b'])))
    plotList.append(Plot('signalRegionsLarge',         'signal region',                         lambda c : createSignalRegionsLarge(c),                        (9, 0, 9), histModifications=xAxisLabels(['1j,0b', '1j,1b', '2j,0b', '2j,1b', '2j,2b', '#geq3j,0b', '#geq3j,1b', '#geq3j,2b', '#geq3j,3b'])))
    plotList.append(Plot('eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))
    plotList.append(Plot('genPhoton_pt',               'p_{T}(gen #gamma) (GeV)',               lambda c : c.genPhPt,                                          (10, 10, 110)))
    plotList.append(Plot('genPhoton_eta',              '|#eta|(gen #gamma)',                    lambda c : abs(c.genPhEta),                                    (15, 0, 2.5), overflowBin=None))
    plotList.append(Plot('genPhoton_minDeltaR',        'min #DeltaR(gen #gamma, other)',        lambda c : c.genPhMinDeltaR,                                   (15, 0, 1.5)))
    plotList.append(Plot('genPhoton_DeltaR',           '#DeltaR(gen #gamma, #gamma)',           lambda c : c.genPhDeltaR,                                      (15, 0, 0.3)))
    plotList.append(Plot('genPhoton_relPt',            'rel p_{T}',                             lambda c : c.genPhRelPt,                                       (20, -0.2, 0.2)))
    plotList.append(Plot('photonCategory',             'photonCategory',                        lambda c : photonCategoryNumber(c),                            (4, 0.5, 4.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake'])))
  # pylint: enable=C0301

  if args.filterPlot:
    plotList[:] = [p for p in plots if args.filterPlot in p.name]
  return plotList

years = ['16', '17', '18'] if args.year == 'all' else [args.year]
lumiScales = {'16':35.863818448,
              '17':41.529548819,
              '18':59.688059536}

totalPlots = []

from ttg.tools.style import drawLumi

for year in years:
  plots = makePlotList()
  stack = createStack(tuplesFile   = os.path.expandvars(tupleFiles[year]),
                    styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '_' + year + '.stack'),
                    channel      = args.channel,
                    replacements = getReplacementsForStack(args.sys))

  # link the newly loaded samples to their respective existing histograms in the plots
  for plot in plots:
    plot.stack = stack
    for sample in plot.histos.keys():
      for newSample in sum(stack, []):
        if sample.name == newSample.name: plot.histos[newSample] = plot.histos.pop(sample)
  

  log.info('Using stackFile ' + stackFile)
  loadedPlots = []
  if not args.overwrite:
    # FIXME fix and reenable
    # for plot in plots:
    #   loaded = plot.loadFromCache(os.path.join(plotDir, year, args.tag, args.channel, args.selection), args.sys)
    #   if loaded: loadedPlots.append(plot)
    plotsToFill = list(set(plots).symmetric_difference(set(loadedPlots)))
    loadedPlots = list(set(plots) & set(loadedPlots))
    for loadedPlot in loadedPlots:
      log.info('Loaded plot from cache: ' + loadedPlot.name)

  lumiScale = lumiScales[year]
  #
  # Loop over events (except in case of showSys when the histograms are taken from the results.pkl file)
  #
  if not args.showSys:
    if   args.tag.count('eleCBTight') and not args.tag.count('eleCBTight-phoCB'): reduceType = 'eleCBTight'
    elif args.tag.count('noPixelSeedVeto'):                                           reduceType = 'eleCBTight-phoCB-noPixelSeedVeto'
    else:                                                                             reduceType = 'eleCBTight-phoCB'
    if args.tag.count('test'):                                           reduceType = 'phoCB'
    reduceType = applySysToReduceType(reduceType, args.sys)

    from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
    for sample in sum(stack, []):
      cutString, passingFunctions = cutStringAndFunctions(args.selection, args.channel)
      cutString = applySysToString(sample.name, args.sys, cutString)
      if args.sys and 'Scale' not in args.sys and sample.isData: continue
      c = sample.initTree(reducedType = reduceType, year=year)

      c.data = sample.isData

      # Filter booleans
      c.genuine           = sample.texName.count('genuine')
      c.misIdEle          = sample.texName.count('misidentified') or sample.texName.count('misIdEle')
      c.hadronicPhoton    = sample.texName.count('nonprompt') or sample.texName.count('hadronic photons') or sample.texName.count('hadronicPhoton')
      c.hadronicFake      = sample.texName.count('nonprompt') or sample.texName.count('hadronic fakes') or sample.texName.count('hadronicFake')
      c.checkMatch        = any([c.hadronicPhoton, c.misIdEle, c.hadronicFake, c.genuine])
      c.failSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} fail')     or args.tag.count("failSigmaIetaIeta")
      c.sideSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} sideband') or args.tag.count("sidebandSigmaIetaIeta")
      c.passSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} pass') or args.tag.count("passSigmaIetaIeta") or args.tag.count("noChgIso")
      c.sigmaIetaIeta1    = sample.texName.count('sideband1')
      c.sigmaIetaIeta2    = sample.texName.count('sideband2')
      c.failChgIso        = args.tag.count("failChgIso") or sample.texName.count('chgIso fail')
      c.passChgIso        = args.tag.count("passChgIso") or sample.texName.count('chgIso pass')

      if forward:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.03001 < #sigma_{i#etai#eta} < 0.032')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.032 < #sigma_{i#etai#eta}')
      else:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.01022 < #sigma_{i#etai#eta} < 0.012')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.012 < #sigma_{i#etai#eta}')

      selectPhoton        = args.selection.count('llg') or args.selection.count('lg')

      for i in sample.eventLoop(cutString):
        c.GetEntry(i)
        if not sample.isData and args.sys:
          applySysToTree(sample.name, args.sys, c)

        if not passingFunctions(c): continue

        if selectPhoton:
          if phoCBfull and not c._phCutBasedMedium[c.ph]:  continue
          if forward and abs(c._phEta[c.ph]) < 1.566:      continue
          if not forward and abs(c._phEta[c.ph]) > 1.4442: continue

          if not checkSigmaIetaIeta(c): continue  # filter for sigmaIetaIeta sideband based on filter booleans (pass or fail)
          if not checkChgIso(c):        continue  # filter for chargedIso sideband based on filter booleans (pass or fail)
          if not checkMatch(c):         continue  # filter using AN15-165 definitions based on filter booleans (genuine, hadronicPhoton, misIdEle or hadronicFake)

        if not (selectPhoton and c._phPt[c.ph] > 20): c.phWeight  = 1.                             # Note: photon SF is 0 when pt < 20 GeV

        if sample.isData: eventWeight = 1.
        elif noWeight:    eventWeight = 1.
        else:             eventWeight = c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*c._prefireWeight*lumiScale

        fillPlots(plotsToFill, c, sample, eventWeight)

  plots = plotsToFill + loadedPlots

  if args.year == 'all':
    sortedPlots = sorted(plots, key=lambda x: x.name)
    if totalPlots:
      for i, totalPlot in enumerate(sorted(totalPlots, key=lambda x: x.name)):
        if isinstance(totalPlot, Plot2D):
          totalPlot = add2DPlots(totalPlot, sortedPlots[i])
        else:
          totalPlot = addPlots(totalPlot, sortedPlots[i])
    else:
      totalPlots = copy.deepcopy(plots)

  # In case of plots: could consider to treat the rateParameters similar as the linearSystematics
  # from ttg.plots.systematics import rateParameters
  # linearSystematics.update({(i+'_norm') : (i, j) for i,j in rateParameters.iteritems()})

  #
  # set some extra arguments for the plots
  #
  if not args.sys or args.showSys:
    extraArgs = {}
    normalizeToMC = [False, True] if args.channel != 'noData' else [False]
    if args.tag.count('onlydata'):
      extraArgs['resultsDir']  = os.path.join(plotDir, year, args.tag, args.channel, args.selection)
      extraArgs['systematics'] = ['sideBandUnc']
    elif args.showSys:
      extraArgs['addMCStat']   = True
      if args.sys:
        extraArgs['addMCStat'] = (args.sys == 'stat')
        showSysList            = [args.sys] if args.sys != 'stat' else []
        linearSystematics      = {i: j for i, j in linearSystematics.iteritems() if i.count(args.sys)}
      extraArgs['systematics']       = showSysList
      extraArgs['linearSystematics'] = linearSystematics
      extraArgs['resultsDir']        = os.path.join(plotDir, year, args.tag, args.channel, args.selection)
      extraArgs['postFitInfo']       = ('chgIsoFit_dd_all' if args.tag.count('matchCombined') else 'srFit') if args.post else None


    if args.channel != 'noData':
      extraArgs['ratio']   = {'yRange' : (0.4, 1.6), 'texY': 'data/MC'}

    if(normalize or args.tag.count('compareChannels')):
      extraArgs['scaling'] = 'unity'
      extraArgs['ratio']   = {'yRange' : (0.1, 1.9), 'texY':'ratio'}
      normalizeToMC        = [False]

    if args.tag.count('compareTTSys'):
      extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}'}

    if args.tag.count('compareTTGammaSys'):
      extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}#gamma'}

  #
  # Drawing the plots
  #
  noWarnings = True
  for plot in plots: # 1D plots
    if isinstance(plot, Plot2D): continue
    if not args.showSys:
      plot.saveToCache(os.path.join(plotDir, year, args.tag, args.channel, args.selection), args.sys)
      if plot.name == "yield":
        log.info("Yields: ")
        for s, y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))

      for norm in normalizeToMC:
        if norm: extraArgs['scaling'] = {0:1}
        for logY in [False, True]:
          if not logY and args.tag.count('sigmaIetaIeta') and plot.name.count('photon_chargedIso_bins_NO'): yRange = (0.0001, 0.75)
          else:                                                                                             yRange = None
          extraTag  = '-log'    if logY else ''
          extraTag += '-sys'    if args.showSys else ''
          extraTag += '-normMC' if norm else ''
          extraTag += '-post'   if args.post else ''
          err = plot.draw(
                    plot_directory    = os.path.join(plotDir, year, args.tag, args.channel + extraTag, args.selection, (args.sys if args.sys else '')),
                    logX              = False,
                    logY              = logY,
                    sorting           = True,
                    yRange            = yRange if yRange else (0.003 if logY else 0.0001, "auto"),
                    drawObjects       = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData')),
                    fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
                    **extraArgs
          )
          extraArgs['saveGitInfo'] = False
          if err: noWarnings = False

  if not args.sys:
    for plot in plots: # 2D plots
      if not hasattr(plot, 'varY'): continue
      for logY in [False, True]:
        for option in ['SCAT', 'COLZ']:
          plot.draw(plot_directory = os.path.join(plotDir, year, args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                    logZ           = False,
                    drawOption     = option,
                    drawObjects    = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData')))
  if noWarnings: 
    log.info('Plots made for 20' + year)
    if not args.year == 'all': log.info('Finished')
  else:          
    log.info('Could not produce all plots for 20' + year)


#
# Drawing the full RunII plots if requested
#

if not args.year == 'all': exit(0)

# NOTE doing this in a sepatate code block seems like the better option for now 
lumiScale = sum(lumiScales.values())

noWarnings = True
for plot in totalPlots: # 1D plots
  if isinstance(plot, Plot2D): continue
  if not args.showSys:
    plot.saveToCache(os.path.join(plotDir, 'all', args.tag, args.channel, args.selection), args.sys)
    if plot.name == "yield":
      log.info("Yields: ")
      for s, y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))

    for norm in normalizeToMC:
      if norm: extraArgs['scaling'] = {0:1}
      for logY in [False, True]:
        if not logY and args.tag.count('sigmaIetaIeta') and plot.name.count('photon_chargedIso_bins_NO'): yRange = (0.0001, 0.75)
        else:                                                                                             yRange = None
        extraTag  = '-log'    if logY else ''
        extraTag += '-sys'    if args.showSys else ''
        extraTag += '-normMC' if norm else ''
        extraTag += '-post'   if args.post else ''
        err = plot.draw(
                  plot_directory    = os.path.join(plotDir, 'all', args.tag, args.channel + extraTag, args.selection, (args.sys if args.sys else '')),
                  logX              = False,
                  logY              = logY,
                  sorting           = True,
                  yRange            = yRange if yRange else (0.003 if logY else 0.0001, "auto"),
                  drawObjects       = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData')),
                  fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
                  **extraArgs
        )
        extraArgs['saveGitInfo'] = False
        if err: noWarnings = False

if not args.sys:
  for plot in totalPlots: # 2D plots
    if not hasattr(plot, 'varY'): continue
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ']:
        plot.draw(plot_directory = os.path.join(plotDir, 'all', args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData')))
if noWarnings: log.info('Finished')
else:          log.info('Could not produce all plots - finished')