#! /usr/bin/env python

#
# Argument parser and logging
#
import os, argparse, copy, pickle
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--year',           action='store',      default=None,        help='year for which to plot, of not specified run for all 3', choices=['2016', '2017', '2018', 'all', 'comb'])
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
argParser.add_argument('--noOverwrite',    action='store_true', default=False,       help='load a plot from cache if it already exists')
argParser.add_argument('--dumpArrays',     action='store_true', default=False)
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Check git and edit the info file
#
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR
if args.editInfo:
  editInfo(os.path.join(plotDir, args.tag))

#
# Systematics
#
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList

#
# Submit subjobs
#

import glob
for f in sorted(glob.glob("../samples/data/*.stack")):
  stackName = os.path.basename(f).split('.')[0]
  if not stackName[-5:] in ['_2016', '_2017', '_2018','_comb']:
    log.warning('stack file without year label found (' + stackName + '), please remove or label properly')
    exit(0)

if not args.isChild:
  updateGitInfo()
  from ttg.tools.jobSubmitter import submitJobs
  from ttg.plots.variations   import getVariations

  if args.showSys and args.runSys: sysList = showSysList + ['stat']
  elif args.sys:                   sysList = [args.sys]
  else:                            sysList = [None] + (systematics.keys() if args.runSys else [])

  subJobArgs, subJobList = getVariations(args, sysList)
  submitJobs(__file__, subJobArgs, subJobList, argParser, subLog= args.tag + '/' + args.year, jobLabel = "PL", wallTime= '30' if args.tag.count("base") else "15")
  exit(0)

#
# Initializing
#
import ROOT
from ttg.plots.plot                   import Plot, xAxisLabels, fillPlots, addPlots, customLabelSize, copySystPlots
from ttg.plots.plot2D                 import Plot2D, add2DPlots
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.plots.photonCategories       import photonCategoryNumber, chgIsoCat
from math import pi
from ttg.reduceTuple.objectSelection  import closestRawJet, rawJetDeltaR

ROOT.gROOT.SetBatch(True)

# reduce string comparisons in loop --> store as booleans
phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
forward     = args.tag.count('forward')
prefire     = args.tag.count('prefireCheck')
noWeight    = args.tag.count('noWeight')
normalize   = any(args.tag.count(x) for x in ['sigmaIetaIeta', 'randomConeCheck', 'splitOverlay', 'compareWithTT', 'compareTTSys', 'compareTTGammaSys', 'normalize'])

selectPhoton        = args.selection.count('llg') or args.selection.count('lg')


#
# Create stack
#
stackFile = 'default' 
for f in sorted(glob.glob("../samples/data/*.stack")):
  stackName = os.path.basename(f).split('.')[0][:-5]
  if stackName in args.tag and (len(stackName) > len(stackFile) or stackFile == 'default'):
    stackFile = stackName 

years = ['2016', '2017', '2018'] if args.year == 'all' else [args.year]
if args.year == 'all':
  for year in years:
    if not os.path.isfile('../samples/data/' + stackFile + '_' + year + '.stack'):
      log.warning('stackfile ' + stackFile + '_' + year + '.stack is missing, exiting')
      exit(0)

tupleFiles = {y : os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_' + y + '.conf') for y in ['2016', '2017', '2018','comb']}

#FIXME maybe check somewhere that all 3 tuples contain the same samples (or mitigate by separate stack files or some year-specifier within the stack)
# when running over all years, just initialise the plots with the stack for 16
stack = createStack(tuplesFile   = os.path.expandvars(tupleFiles['2016' if args.year == 'all' else args.year]),
                    styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '_' + ('2016' if args.year == 'all' else args.year) + '.stack'),
                    channel      = args.channel,
                    replacements = getReplacementsForStack(args.sys, args.year)
                    )

#
# Define plots
#
Plot.setDefaults(stack=stack, texY = ('(1/N) dN/dx' if normalize else 'Events'))
Plot2D.setDefaults(stack=stack)

def rawLep1JetDeltaR(tree):
  return min(deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) for j in range(tree._nJets))

def rawLep2JetDeltaR(tree):
  return min(deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) for j in range(tree._nJets))

def rawLepJetDeltaR(tree):
  return min([rawLep1JetDeltaR(tree), rawLep2JetDeltaR(tree)])

def closestRawJetLep1(tree):
  dist = [deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) for j in range(tree._nJets)]
  return dist.index(min(dist))

def closestRawJetLep2(tree):
  dist = [deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) for j in range(tree._nJets)]
  return dist.index(min(dist))

def genLep1RawJetDeltaR(tree):
  j = closestRawJetLep1(tree)
  if tree._lIsPrompt[tree.l1]: return deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1])
  else: return -1.

def genLep2RawJetDeltaR(tree):
  j = closestRawJetLep2(tree)
  if tree._lIsPrompt[tree.l2]: return deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2])
  else: return -1.

def genLepRawJetDeltaR(tree):
  # NOTE this means both leptons are required to be prompt
  return min([genLep1RawJetDeltaR(tree), genLep2RawJetDeltaR(tree)])

def genLepRawJetNearPhDeltaR(tree):
  j = closestRawJet(tree) #jet closest to photon
  distl1 = deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) if tree._lIsPrompt[tree.l1] else -1.
  distl2 = deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) if tree._lIsPrompt[tree.l2] else -1.
  return min([distl1, distl1])

def lepCutCB(tree):
  if not (tree._relIso[tree.l1] < 0.12 and tree._relIso[tree.l2] < 0.12): return False
  if tree._lFlavor[tree.l1] == 0 and not tree._lPOGTight[tree.l1]: return False
  if tree._lFlavor[tree.l1] == 1 and not tree._lPOGMedium[tree.l1]: return False
  if tree._lFlavor[tree.l2] == 0 and not tree._lPOGTight[tree.l2]: return False
  if tree._lFlavor[tree.l2] == 1 and not tree._lPOGMedium[tree.l2]: return False
  else: return True

def channelNumbering(t):
  return (1 if t.isMuMu else (2 if t.isEMu else 3))

def createSignalRegions(t):
  if t.ndbjets == 0:
    if t.njets == 0: return 0
    if t.njets == 1: return 1
    if t.njets == 2: return 2
    if t.njets >= 3: return 3
  elif t.ndbjets == 1:
    if t.njets == 1: return 4
    if t.njets == 2: return 5
    if t.njets >= 3: return 6
  elif t.ndbjets == 2:
    if t.njets == 2: return 7
    if t.njets >= 3: return 8
  elif t.ndbjets >= 3 and t.njets >= 3: return 9
  return -1

def createSignalRegionsZoom(t):
  if t.ndbjets == 0:
    if t.njets == 2: return 0
    if t.njets >= 3: return 1
  elif t.ndbjets == 1:
    if t.njets == 1: return 2
    if t.njets == 2: return 3
    if t.njets >= 3: return 4
  elif t.ndbjets == 2:
    if t.njets == 2: return 5
    if t.njets >= 3: return 6
  elif t.ndbjets >= 3 and t.njets >= 3: return 7
  return -1

# you can remove items from momList, but keep momRef 
momRef = {1: 'd', 2: 'u', 3: 's', 4: 'c', 5: 'b', 6: 't', 11: 'e', 13: '#mu', 15: '#tau', 21: 'g', 24: 'W', 111: '#pi^{0}', 221: '#pi^{+/-}', 223: '#rho^{+}', 331: '#rho `', 333: '#phi', 413: 'D^{*+}', 423: 'D^{*0}', 433: 'D_{s}^{*+}', 445: '445', 513: 'B^{*0}', 523: 'B^{*+}', 533: 'B_{s}^{*0}', 543: 'B_{c}^{*+}', 2212: 'p', 4312:'4312', 4314: '4314', 4322: '4322', 4324: '4324', 4334: '4334', 5324: '5324', 20443: '20443', 100443: '#psi'}
# momList = [1, 2, 3, 4, 5, 6, 11, 13, 15, 21, 24, 111, 221, 223, 331, 333, 413, 423, 433, 445, 513, 523, 533, 543, 2212, 4312, 4314, 4322, 4324, 4334, 5324, 20443, 100443]
momList = [1, 2, 3, 4, 5, 6, 11, 13, 15, 21, 24, 111, 221, 223, 331, 333, 413, 423, 433, 513, 523, 533, 543, 2212, 100443]
nameList = [momRef[mom] for mom in momList] + ['other']
momDict = {entry: num for num, entry in enumerate(momList)}

def momDictFunc(t):
  try: momId = abs(t._gen_phMomPdg[t.ph])
  except: momId= -1
  try: return momDict[momId]
  except: return len(momList)

# Plot definitions (allow long lines, and switch off unneeded lambda warning, because lambdas are needed)
def makePlotList():
  # pylint: disable=C0301,W0108
  plotList = []
  if args.tag.count('randomConeCheck'):
    plotList.append(Plot('photon_chargedIso',          'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (20, 0, 20)))
    plotList.append(Plot('photon_chargedIso_small',    'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (80, 0, 20)))
    plotList.append(Plot('photon_chargedIso_tiny',     'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (50, 0, 5)))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)', lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c._phPtCorr[c.ph], (20, 0, 2)))
  else:
    plotList.append(Plot('yield',                      'yield',                                 lambda c : channelNumbering(c),                                (3,  0.5, 3.5), histModifications=xAxisLabels(['#mu#mu', 'e#mu', 'ee'])))
    plotList.append(Plot('nVertex',                    'vertex multiplicity',                   lambda c : c._nVertex,                                         (50, 0, 50)))
    plotList.append(Plot('nTrueInt',                   'nTrueInt',                              lambda c : c._nTrueInt,                                        (50, 0, 50)))
    plotList.append(Plot('nphoton',                    'number of photons',                     lambda c : c.nphotons,                                         (4,  -0.5, 3.5)))
    plotList.append(Plot('photon_pt',                  'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            (24, 15, 135)))
    plotList.append(Plot('photon_pt_large',            'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            [15., 30., 45., 60., 80., 100., 120.]))
    plotList.append(Plot('photon_eta',                 '|#eta|(#gamma)',                        lambda c : abs(c._phEta[c.ph]),                                (15, 0, 2.5)))
    plotList.append(Plot('photon_eta_large',           '|#eta|(#gamma)',                        lambda c : abs(c._phEta[c.ph]),                                [0, 0.15, 0.3, 0.45, 0.60, 0.75, 0.9, 1.05, 1.2, 1.5, 1.8, 2.1, 2.5]))
    plotList.append(Plot('photon_phi',                 '#phi(#gamma)',                          lambda c : c._phPhi[c.ph],                                     (10, -pi, pi)))
    plotList.append(Plot('photon_mva',                 '#gamma-MVA',                            lambda c : c._phMva[c.ph],                                     (20, -1, 1)))
    plotList.append(Plot('photon_chargedIso_FP',       'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_FP_new',   'Photon charged-hadron Iso cut (GeV)',   lambda c : chgIsoCat(c),                                       [0, 1 , 2], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), histModifications=xAxisLabels(['fail', 'pass']) ))    
    plotList.append(Plot('photon_chargedIso',          'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_NO',       'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins',     'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 3, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins_NO',  'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 3, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_small',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (80, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_small_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        (80, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_wide',     'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_wide_NO',  'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 5, 10, 20], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins2',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 3, 5, 10], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins2_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 1.141 , 2, 3, 5, 10], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_chargedIso_bins3',    'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.1] + range(1, 21), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('photon_chargedIso_bins3_NO', 'Photon charged-hadron isolation (GeV)', lambda c : c._phChargedIsolation[c.ph],                        [0, 0.1] + range(1, 21), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin = None))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)',      lambda c : c._phChargedIsolation[c.ph]/c.ph_pt,                (20, 0, 2)))
    plotList.append(Plot('photon_neutralIso',          'neutralIso(#gamma) (GeV)',              lambda c : c._phNeutralHadronIsolation[c.ph],                  (25, 0, 5)))
    plotList.append(Plot('photon_photonIso',           'photonIso(#gamma) (GeV)',               lambda c : c._phPhotonIsolation[c.ph],                         (32, 0, 8)))
    plotList.append(Plot('photon_SigmaIetaIeta',       '#sigma_{i#etai#eta}(#gamma)',           lambda c : c._phSigmaIetaIeta[c.ph],                           (20, 0, 0.04)))
    plotList.append(Plot('photon_SigmaIetaIeta_small', '#sigma_{i#etai#eta}(#gamma)',           lambda c : c._phSigmaIetaIeta[c.ph],                           (80, 0, 0.04)))
    plotList.append(Plot('photon_hadOverEm',           'hadronicOverEm(#gamma)',                lambda c : c._phHadronicOverEm[c.ph],                          (20, 0, .025)))
    plotList.append(Plot('photon_phHadTowOverEm',      'hadronicTowerOverEm(#gamma)',           lambda c : c._phHadTowOverEm[c.ph],                            (20, 0, .025)))
    plotList.append(Plot('phJetDeltaR',                '#DeltaR(#gamma, j)',                    lambda c : c.phJetDeltaR,                                      [0, 0.1, 0.6, 1.1, 1.6, 2.1, 2.6, 3.1, 3.6, 4.1, 4.6]))
    plotList.append(Plot('phBJetDeltaR',               '#DeltaR(#gamma, b)',                    lambda c : c.phBJetDeltaR,                                     [0, 0.1, 0.6, 1.1, 1.6, 2.1, 2.6, 3.1, 3.6, 4.1, 4.6]))
    plotList.append(Plot('l1_pt',                      'p_{T}(l_{1}) (GeV)',                    lambda c : c.l1_pt,                                            (20, 25, 225)))
    plotList.append(Plot('l1_eta',                     '|#eta|(l_{1})',                         lambda c : abs(c._lEta[c.l1]),                                 (15, 0, 2.4)))
    plotList.append(Plot('l1_eta_small',               '|#eta|(l_{1})',                         lambda c : abs(c._lEta[c.l1]),                                 (50, 0, 2.4)))
    plotList.append(Plot('l1_phi',                     '#phi(l_{1})',                           lambda c : c._lPhi[c.l1],                                      (10, -pi, pi)))
    plotList.append(Plot('l1_relIso',                  'relIso(l_{1})',                         lambda c : c._relIso[c.l1],                                    (16, 0, 0.16)))
    plotList.append(Plot('l1_jetDeltaR',               '#DeltaR(l_{1}, j)',                     lambda c : c.l1JetDeltaR,                                      (20, 0, 5)))
    plotList.append(Plot('l1_Mva',                     'leptonMva output l1',                   lambda c : c._leptonMvatZq[c.l1],                              (84, -1.05, 1.05)))
    plotList.append(Plot('l2_pt',                      'p_{T}(l_{2}) (GeV)',                    lambda c : c.l2_pt,                                            (20, 15, 215)))
    plotList.append(Plot('l2_eta',                     '|#eta|(l_{2})',                         lambda c : abs(c._lEta[c.l2]),                                 (15, 0, 2.4)))
    plotList.append(Plot('l2_eta_small',               '|#eta|(l_{2})',                         lambda c : abs(c._lEta[c.l2]),                                 (50, 0, 2.4)))
    plotList.append(Plot('l2_phi',                     '#phi(l_{2})',                           lambda c : c._lPhi[c.l2],                                      (10, -pi, pi)))
    plotList.append(Plot('l2_relIso',                  'relIso(l_{2})',                         lambda c : c._relIso[c.l2],                                    (16, 0, 0.16)))
    plotList.append(Plot('l2_jetDeltaR',               '#DeltaR(l_{2}, j)',                     lambda c : c.l2JetDeltaR,                                      (20, 0, 5)))
    plotList.append(Plot('l2_Mva',                     'leptonMva output l2',                   lambda c : c._leptonMvatZq[c.l2],                              (84, -1.05, 1.05)))
    plotList.append(Plot('l_maxRelIso',                'max relIso(l_{1},l_{2})',               lambda c : max(c._relIso[c.l1],c._relIso[c.l2]),               (16, 0, 0.16)))
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
    plotList.append(Plot('j2_pt',                      'p_{T}(j_{2}) (GeV)',                    lambda c : c._jetSmearedPt[c.j2],                              (30, 30, 330)))
    plotList.append(Plot('j2_eta',                     '|#eta|(j_{2})',                         lambda c : abs(c._jetEta[c.j2]),                               (15, 0, 2.4)))
    plotList.append(Plot('j2_phi',                     '#phi(j_{2})',                           lambda c : c._jetPhi[c.j2],                                    (10, -pi, pi)))
    plotList.append(Plot('j2_deepCSV',                 'deepCSV(j_{2})',                        lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2],     (20, 0, 1)))
    plotList.append(Plot('dbj1_pt',                    'p_{T}(bj_{1}) (GeV)',                   lambda c : c._jetSmearedPt[c.dbj1],                            (30, 30, 330)))
    plotList.append(Plot('dbj2_pt',                    'p_{T}(bj_{2}) (GeV)',                   lambda c : c._jetSmearedPt[c.dbj2],                            (30, 30, 330)))
    plotList.append(Plot('dbj1_deepCSV',               'deepCSV(dbj_{1})',                      lambda c : c._jetDeepCsv_b[c.dbj1] + c._jetDeepCsv_bb[c.dbj1], (20, 0, 1)))
    plotList.append(Plot('dbj2_deepCSV',               'deepCSV(dbj_{2})',                      lambda c : c._jetDeepCsv_b[c.dbj2] + c._jetDeepCsv_bb[c.dbj2], (20, 0, 1)))
    plotList.append(Plot('signalRegions',              'signal region',                         lambda c : createSignalRegions(c),                             (10, 0, 10), histModifications=xAxisLabels(['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))
    plotList.append(Plot('signalRegionsZoom',          'signal region',                         lambda c : createSignalRegionsZoom(c),                         (8, 0, 8),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b'])))
    plotList.append(Plot('eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))
    plotList.append(Plot('genPhoton_pt',               'p_{T}(gen #gamma) (GeV)',               lambda c : c.genPhPt,                                          (10, 10, 110)))
    plotList.append(Plot('genPhoton_eta',              '|#eta|(gen #gamma)',                    lambda c : abs(c.genPhEta),                                    (15, 0, 2.5), overflowBin=None))
    plotList.append(Plot('genPhoton_minDeltaR',        'min #DeltaR(gen #gamma, other)',        lambda c : c.genPhMinDeltaR,                                   (15, 0, 1.5)))
    plotList.append(Plot('genPhoton_DeltaR',           '#DeltaR(gen #gamma, #gamma)',           lambda c : c.genPhDeltaR,                                      (15, 0, 0.3)))
    plotList.append(Plot('genPhoton_relPt',            'rel p_{T}',                             lambda c : c.genPhRelPt,                                       (20, -0.2, 0.2)))
    plotList.append(Plot('photonCategory',             'photonCategory',                        lambda c : photonCategoryNumber(c),                            (4, 0.5, 4.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake'])))
    plotList.append(Plot('phRawJetERatio',             'E photon / closest raw jet ',           lambda c : c._phE[c.ph] / c._jetE[closestRawJet(c)],           (50, 0, 5), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))    
    plotList.append(Plot('phRawJetDeltaR',             'raw #DeltaR(#gamma, j) ',               lambda c : rawJetDeltaR(c),                                    (45, 0, 0.3), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))    
    plotList.append(Plot('phL1DeltaR_small',           '#DeltaR(#gamma, l_{1})',                lambda c : c.phL1DeltaR,                                       (50, 0, 5)))
    plotList.append(Plot('phL2DeltaR_small',           '#DeltaR(#gamma, l_{2})',                lambda c : c.phL2DeltaR,                                       (50, 0, 5)))
    plotList.append(Plot('phLepDeltaR_small',          '#DeltaR(#gamma, l)',                    lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                    (50, 0, 5)))
    plotList.append(Plot('phJetDeltaR_small',          '#DeltaR(#gamma, j)',                    lambda c : c.phJetDeltaR,                                      (50, 0, 5)))
    plotList.append(Plot('phBJetDeltaR_small',         '#DeltaR(#gamma, b)',                    lambda c : c.phBJetDeltaR,                                     (50, 0, 5)))
    plotList.append(Plot('l1_jetDeltaR_small',         '#DeltaR(l_{1}, j)',                     lambda c : c.l1JetDeltaR,                                      (50, 0, 5)))
    plotList.append(Plot('l2_jetDeltaR_small',         '#DeltaR(l_{2}, j)',                     lambda c : c.l2JetDeltaR,                                      (50, 0, 5)))
    # NOTE TEMPORARY PLOTS
    plotList.append(Plot('rawLep1JetDeltaR',           'raw #DeltaR(#l1, j)',                    lambda c : rawLep1JetDeltaR(c),                               (50, 0, 1.0), overflowBin=None))
    plotList.append(Plot('rawLep2JetDeltaR',           'raw #DeltaR(#l2, j)',                    lambda c : rawLep2JetDeltaR(c),                               (50, 0, 1.0), overflowBin=None))
    plotList.append(Plot('rawLepJetDeltaR',            'raw #DeltaR(#l, j)',                     lambda c : rawLepJetDeltaR(c),                                (50, 0, 0.5), overflowBin=None))
    plotList.append(Plot('genLep1RawJetDeltaR',        'raw #DeltaR(gen l1, j)',                 lambda c : genLep1RawJetDeltaR(c),                            (50, 0, 1.0), overflowBin=None))
    plotList.append(Plot('genLep2RawJetDeltaR',        'raw #DeltaR(gen l2, j)',                 lambda c : genLep2RawJetDeltaR(c),                            (50, 0, 1.0), overflowBin=None))
    plotList.append(Plot('genLepRawJetDeltaR',         'raw #DeltaR(gen l, j)',                  lambda c : genLepRawJetDeltaR(c),                             (50, 0, 0.5), overflowBin=None))
    plotList.append(Plot('genLepRawJetNearPhDeltaR',   'raw #DeltaR(gen l, j near #gamma)',      lambda c : genLepRawJetNearPhDeltaR(c),                       (50, 0, 0.5), overflowBin=None))
    # plotList.append(Plot('photon_pt_ATL',              'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                           [20., 23., 26., 29., 32., 35., 40., 45., 50., 55., 65., 75., 85., 100., 130., 180., 300.]))
    # plotList.append(Plot('photon_pt_ATLB',             'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                           [20., 30., 40., 50., 65., 80., 100., 125., 160., 220., 300.]))
  # pylint: enable=C0301
    if args.tag.lower().count('phorigins'):
      plotList.append(Plot('photon_mom',              'photon mom particle',                lambda c : momDictFunc(c),                   (len(momList)+1, 0, len(momList)+1), histModifications=[xAxisLabels(nameList), customLabelSize(14)]))      

  if args.filterPlot:
    plotList[:] = [p for p in plotList if args.filterPlot in p.name]

  # if no kind of photon cut was made (also not in skim) (requiring nphotons=0 is allowed), or no Z-veto is applied -> can unblind
  phoReq = [selectPhoton, args.tag.count('pho'), args.selection.count('pho') and not args.selection.count('nphoton0')]
  noZReq = [args.selection.count('offZ'), args.selection.count('llgNoZ')]
  if not any(phoReq) or not any(noZReq):
    for p in plotList: p.blindRange = None
  return plotList

years = ['2016', '2017', '2018'] if args.year == 'all' else [args.year]
lumiScales = {'2016':35.863818448,
              '2017':41.529548819,
              '2018':59.688059536,
              }
lumiScales['comb'] = lumiScales['2018']

totalPlots = []

from ttg.tools.style import drawLumi

for year in years:
  # dumpArrays = [("_phChargedIsolation", lambda c : c._phChargedIsolation[c.ph]) , ("_phSigmaIetaIeta", lambda c : c._phSigmaIetaIeta[c.ph])]
  dumpArrays = [("_runNb", lambda c : c._runNb) , ("_eventNb", lambda c : c._eventNb), ("_lumiBlock", lambda c : c._lumiBlock)]
  dumpArrays = [(variable, expression, []) for variable, expression in dumpArrays]
  plots = makePlotList()
  stack = createStack(tuplesFile   = os.path.expandvars(tupleFiles[year]),
                    styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '_' + year + '.stack'),
                    channel      = args.channel,
                    replacements = getReplacementsForStack(args.sys, args.year)
                    )

  # link the newly loaded samples to their respective existing histograms in the plots
  for plot in plots:
    plot.stack = stack
    for sample in plot.histos.keys():
      for newSample in sum(stack, []):
        if sample.name == newSample.name: plot.histos[newSample] = plot.histos.pop(sample)
  

  log.info('Using stackFile ' + stackFile)
  loadedPlots = []
  if args.noOverwrite:
    for plot in plots:
      loaded = plot.loadFromCache(os.path.join(plotDir, year, args.tag, args.channel, args.selection))
      if loaded: loadedPlots.append(plot)    
    plotsToFill = [plot for plot in plots if not plot.name in [Lplot.name for Lplot in loadedPlots]]
    loadedPlots = [Lplot for Lplot in loadedPlots if Lplot.name in [plot.name for plot in plots]]
    log.info('Plots loaded from cache:')
    log.info([Lplot.name for Lplot in loadedPlots])
    log.info('Plots to be filled:')
    log.info([plot.name for plot in plotsToFill])
  else: 
    plotsToFill = plots

  #
  # Loop over events (except in case of showSys when the histograms are taken from the results.pkl file)
  #
  copySyst = year == '2016' and args.sys in ['hdampUp', 'hdampDown', 'ueUp', 'ueDown', 'erdUp', 'erdDown']

  if not args.showSys and not copySyst:
    if args.tag.count('phoCB'):                                                     reduceType = 'phoCB'
    elif args.tag.lower().count('photonmva'):                                       reduceType = 'photonMVA'
    else:                                                                           reduceType = 'pho'
    if args.tag.count('phoCBnew') or args.tag.count('phoCBfullnew'):                reduceType = 'phoCBnew' #for testing new skims
    if args.tag.lower().count('leptonmva'):                                         reduceType = 'leptonmva-' + reduceType
    if args.tag.count('base'):                                                      reduceType = 'base'
    if args.tag.count('phomvasb'):                                                  reduceType = 'phomvasb'
    if args.tag.count('phomvasbnew'):                                               reduceType = 'phomvasbnew'
    reduceType = applySysToReduceType(reduceType, args.sys)
    log.info("using reduceType " + reduceType)

    # NOTE TEMPORARY CODE
    MVAcut = None
    if args.tag.count('LMVA'):
      MVAcut = float(args.tag.split('LMVA')[1][0:4])
    
    invExtraLepCut = args.tag.lower().count("invextralepcut")
    extraLepCut = args.tag.lower().count("extralepcut") and not invExtraLepCut

    from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
    for sample in sum(stack, []):
      cutString, passingFunctions = cutStringAndFunctions(args.selection, args.channel)
      cutString = applySysToString(sample.name, args.sys, cutString)
      if args.sys and 'Scale' not in args.sys and sample.isData: continue
      c = sample.initTree(reducedType = reduceType)
      c.year = sample.name[:4] if year == "comb" else year
      lumiScale = lumiScales[c.year]
      c.data = sample.isData

      # Filter booleans
      c.genuine           = sample.texName.count('genuine') or args.tag.count("filterGenuine")
      c.misIdEle          = sample.texName.count('misidentified') or sample.texName.count('misIdEle') or sample.texName.count('nonprompt') or args.tag.count("filterMisIdEle")
      c.hadronicPhoton    = sample.texName.count('nonprompt') or sample.texName.count('hadronic photons') or sample.texName.count('hadronicPhoton') or args.tag.count("filterHadronic")
      c.hadronicFake      = sample.texName.count('nonprompt') or sample.texName.count('hadronic fakes') or sample.texName.count('hadronicFake') or args.tag.count("filterFake")
      c.checkMatch        = any([c.hadronicPhoton, c.misIdEle, c.hadronicFake, c.genuine])
      if args.tag.count('failOrSide'):
        c.failOrSide        = True
        c.failSigmaIetaIeta = False
        c.sideSigmaIetaIeta = False
        c.passSigmaIetaIeta = True
        c.sigmaIetaIeta1    = False
        c.sigmaIetaIeta2    = False
        c.failChgIso        = False
        c.passChgIso        = True
      else:
        c.failOrSide        = False
        c.failSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} fail')     or args.tag.count("failSigmaIetaIeta")
        c.sideSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} sideband') or args.tag.count("sidebandSigmaIetaIeta")
        c.passSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} pass') or args.tag.count("passSigmaIetaIeta") or args.tag.count("noChgIso")
        c.sigmaIetaIeta1    = sample.texName.count('sideband1') or args.tag.count("gapSigmaIetaIeta")
        c.sigmaIetaIeta2    = sample.texName.count('sideband2') 
        c.failChgIso        = args.tag.count("failChgIso") or sample.texName.count('chgIso fail')
        c.passChgIso        = args.tag.count("passChgIso") or sample.texName.count('chgIso pass')
          # FIXME Temporary for checking strange very low iso fake and had photons
        c.lowChgIso         = args.tag.count("lowchgIso") or sample.texName.count('lowchgIso')
        c.highChgIso         = args.tag.count("highchgIso") or sample.texName.count('highchgIso')



      if forward:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.0272 < #sigma_{i#etai#eta} < 0.032')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.032 < #sigma_{i#etai#eta}')
      else:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.01015 < #sigma_{i#etai#eta} < 0.012')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.012 < #sigma_{i#etai#eta}')


      for i in sample.eventLoop(cutString):
        c.GetEntry(i)
        c.ISRWeight = 1.
        c.FSRWeight = 1.
        if not sample.isData and args.sys:
          applySysToTree(sample.name, args.sys, c)

        if not passingFunctions(c): continue

        # FIXME unelegant temporary extra cuts 
        if MVAcut:
          if not (c._leptonMvatZq[c.l1] > MVAcut and c._leptonMvatZq[c.l2] > MVAcut): continue

        if extraLepCut and not lepCutCB(c): continue
        if invExtraLepCut and lepCutCB(c): continue

        if selectPhoton:
          if phoCBfull and not c._phCutBasedMedium[c.ph]:  continue
          if forward and abs(c._phEta[c.ph]) < 1.566:      continue
          if not forward and abs(c._phEta[c.ph]) > 1.4442: continue

          if c.failOrSide: # only fail Ch Iso OR sigma sideband 
            if checkSigmaIetaIeta(c) and checkChgIso(c): continue
          else:
            if not checkSigmaIetaIeta(c): continue  # filter for sigmaIetaIeta sideband based on filter booleans (pass or fail)
            if not checkChgIso(c):        continue  # filter for chargedIso sideband based on filter booleans (pass or fail)
          if not checkMatch(c):         continue  # filter using AN15-165 definitions based on filter booleans (genuine, hadronicPhoton, misIdEle or hadronicFake)

        if not (selectPhoton and c._phPtCorr[c.ph] > 20): c.phWeight  = 1.                             # Note: photon SF is 0 when pt < 20 GeV
        
        prefireWeight = 1. if c.year == '2018' or sample.isData else c._prefireWeight

        if sample.isData: eventWeight = 1.
        elif noWeight:    eventWeight = 1.
        elif MVAcut:      eventWeight = c.genWeight*c.puWeight*1.*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*lumiScale
        else:             eventWeight = c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*lumiScale
        
        if year == "comb": 
          eventWeight *= lumiScales['2018'] / lumiScales[c.year]

        fillPlots(plotsToFill, sample, eventWeight)

        if args.dumpArrays:
          for variable, expression, array in dumpArrays:
            if sample.isData: array.append((expression(c), 1., eventWeight))
            else:             array.append((expression(c), c.genWeight, eventWeight))

  if not args.showSys and copySyst:
    copySystPlots(plots, '2017', year, args.tag, args.channel, args.selection, args.sys)

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
  # Drawing the plots
  #
  noWarnings = True
  for plot in plots: # 1D plots
    if isinstance(plot, Plot2D): continue

    if not args.showSys:
      plot.saveToCache(os.path.join(plotDir, year, args.tag, args.channel, args.selection), args.sys)
      if not plot.blindRange == None and not year == '2016':
        for sample, histo in plot.histos.iteritems():
          if sample.isData:
            for bin in range(1, histo.GetNbinsX()+2):
              if any([plot.blindRange[i][0] < histo.GetBinCenter(bin) < plot.blindRange[i][1] for i in range(len(plot.blindRange))]) or len(plot.blindRange) == 0:
                histo.SetBinContent(bin, 0)

      if plot.name == "yield":
        log.info("Yields: ")
        for s, y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))

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

      if any (args.tag.count(sname) for sname in ['chisoHad','chisoFake','chisoNP']):
        extraArgs['ratio']   = {'yRange' : (0.0, 1.0), 'texY': 'chargedIso pass/fail'}

      if any (args.tag.lower().count(sname) for sname in ['failpass','ffp','pfp']):
        extraArgs['ratio']   = {'yRange' : (1.0, 8.0), 'texY': '#sigma_{i#etai#eta} pass/fail'}

      if(normalize or args.tag.count('compareChannels')):
        extraArgs['scaling'] = 'unity'
        extraArgs['ratio']   = {'yRange' : (0.1, 1.9), 'texY':'ratio'}
        normalizeToMC        = [False]

      if args.tag.count('compareTTSys'):
        extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}'}

      if args.tag.count('compareTTGammaSys'):
        extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}#gamma'}

      if args.year == 'comb':
        extraArgs['ratio']   = {'num': -1, 'den': 0}

      if args.tag.count('splitOverlay'):
        extraArgs['ratio']   = None

      if args.tag.count('phoReg'):
        extraArgs['ratio']   = None

      for norm in normalizeToMC:
        if norm: extraArgs['scaling'] = {0:1}
        for logY in [False, True]:
          # FIXME this used to be yRange = (0.0001, 0.75), why?
          if not logY and args.tag.count('sigmaIetaIeta') and plot.name.count('photon_chargedIso_bins_NO'): yRange = (0.0001, 0.35)
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
                    drawObjects       = drawLumi(None, lumiScales[year], isOnlySim=(args.channel=='noData')),
                    # fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
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
                    drawObjects    = drawLumi(None, lumiScales[year], isOnlySim=(args.channel=='noData')))
                    
  if args.dumpArrays: 
    dumpArrays = {variable: array for variable, expression, array in dumpArrays}
    dumpArrays["info"] = " ".join(s for s in [args.year, args.selection, args.channel, args.tag, args.sys] if s) 
    with open( os.path.join( os.path.join(plotDir, year, args.tag, args.channel, args.selection), 'dumpedArrays' + (args.sys if args.sys else '') + '.pkl') ,'wb') as f:
      pickle.dump(dumpArrays, f)

  if noWarnings: 
    log.info('Plots made for ' + year)
    if not args.year == 'all': log.info('Finished')
  else:          
    log.info('Could not produce all plots for ' + year)


#
# Drawing the full RunII plots if requested
#

if not args.year == 'all': exit(0)

# NOTE doing this in a sepatate code block seems like the better option for now 
lumiScale = lumiScales['2016']+lumiScales['2017']+lumiScales['2018'] 

noWarnings = True
for plot in totalPlots: # 1D plots
  if isinstance(plot, Plot2D): continue
  if not args.showSys:
    plot.saveToCache(os.path.join(plotDir, 'all', args.tag, args.channel, args.selection), args.sys)

    if not plot.blindRange == None:
      for sample, histo in plot.histos.iteritems():
        if sample.isData:
          for bin in range(1, histo.GetNbinsX()+2):
            if any([plot.blindRange[i][0] < histo.GetBinCenter(bin) < plot.blindRange[i][1] for i in range(len(plot.blindRange))]) or len(plot.blindRange) == 0:
              histo.SetBinContent(bin, 0)

    if plot.name == "yield":
      log.info("Yields: ")
      for s, y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))
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

    if any (args.tag.count(sname) for sname in ['chisoHad','chisoFake','chisoNP']):
      extraArgs['ratio']   = {'yRange' : (0.0, 1.0), 'texY': 'chargedIso pass/fail'}

    if any (args.tag.lower().count(sname) for sname in ['failpass','ffp','pfp']):
      extraArgs['ratio']   = {'yRange' : (1.0, 8.0), 'texY': '#sigma_{i#etai#eta} pass/fail'}

    if(normalize or args.tag.count('compareChannels')):
      extraArgs['scaling'] = 'unity'
      extraArgs['ratio']   = {'yRange' : (0.1, 1.9), 'texY':'ratio'}
      normalizeToMC        = [False]

    if args.tag.count('compareTTSys'):
      extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}'}

    if args.tag.count('compareTTGammaSys'):
      extraArgs['ratio']   = {'num': -1, 'texY':'ratios to t#bar{t}#gamma'}

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
                  # fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
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
