#! /usr/bin/env python

#
# Argument parser and logging
#
import os, argparse, copy, pickle
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--year',           action='store',      default=None,        help='year for which to plot, of not specified run for all 3', choices=['2016', '2017', '2018', 'all', 'comb'])
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--extraPlots',     action='store',      default='')
argParser.add_argument('--channel',        action='store',      default=None)
argParser.add_argument('--tag',            action='store',      default='phoCBfull')
argParser.add_argument('--sys',            action='store',      default='')
argParser.add_argument('--filterPlot',     action='store',      default=None)
argParser.add_argument('--noZgCorr',       action='store_true', default=False,       help='do not correct Zg shape and yield')
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

if args.noZgCorr: args.tag += '-noZgCorr'

#
# Check git and edit the info file
#
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo, deltaPhi, deltaR
if args.editInfo:
  editInfo(os.path.join(plotDir, args.tag))

#
# Systematics
#
from ttg.plots.systematics import getReplacementsForStack, systematics, linearSystematics, applySysToTree, applySysToString, applySysToReduceType, showSysList, getSigmaSyst

#
# Submit subjobs
#

import glob
for f in sorted(glob.glob("../samples/data/*.stack")):
  stackName = os.path.basename(f).split('.')[0]
  if not stackName[-5:] in ['_2016', '_2017', '_2018', '_comb']:
    log.warning('stack file without year label found (' + stackName + '), please remove or label properly')
    exit(0)

if not args.isChild:
  updateGitInfo()
  from ttg.tools.jobSubmitter import submitJobs
  from ttg.plots.variations   import getVariations
  if args.runSys and not os.path.exists(os.path.join(plotDir, args.year, args.tag, args.channel, args.selection, 'yield.pkl')):
    log.info('Make sure the nominal plots exist before running systematics')
    exit(0)
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
from ttg.plots.plot2D                 import Plot2D, add2DPlots, normalizeAlong
from ttg.plots.cutInterpreter         import cutStringAndFunctions
from ttg.samples.Sample               import createStack
from ttg.plots.photonCategories       import photonCategoryNumber, chgIsoCat
from ttg.plots.npWeight               import npWeight
from ttg.plots.ZgWeight               import ZgWeight
from math import pi

ROOT.gROOT.SetBatch(True)

# reduce string comparisons in loop --> store as booleans
phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
forward     = args.tag.count('forward')
prefire     = args.tag.count('prefireCheck')
noWeight    = args.tag.count('noWeight')
normalize   = any(args.tag.count(x) for x in ['sigmaIetaIeta', 'randomConeCheck', 'splitOverlay', 'compareWithTT', 'compareTTSys', 'compareTTGammaSys', 'normalize', 'IsoRegTTDil', 'IsoFPTTDil'])
onlyMC = args.tag.count('onlyMC')

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

tupleFiles = {y : os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_' + y + '.conf') for y in ['2016', '2017', '2018', 'comb']}

# when running over all years, just initialise the plots with the stack for 16
stack = createStack(tuplesFile   = os.path.expandvars(tupleFiles['2016' if args.year == 'all' else args.year]),
                    styleFile    = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '_' + ('2016' if args.year == 'all' else args.year) + '.stack'),
                    channel      = args.channel,
                    replacements = getReplacementsForStack(args.sys, args.year)
                    )

# NOTE temp
def nearestZ(tree):
  distmll  = abs(91.1876 - tree.mll)
  distmllg = abs(91.1876 - tree.mllg)
  if distmll < distmllg:
    return 0.
  else:
    return 1.

# NOTE always nominal values
def leptonPt(tree, index):
  return tree._lPtCorr[index]

def leptonE(tree, index):
  return tree._lECorr[index]

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  # log.info("got vect")
  return vector

def Zpt(tree):
  first  = getLorentzVector(leptonPt(tree, tree.l1), tree._lEta[tree.l1], tree._lPhi[tree.l1], leptonE(tree, tree.l1))
  second = getLorentzVector(leptonPt(tree, tree.l2), tree._lEta[tree.l2], tree._lPhi[tree.l2], leptonE(tree, tree.l2))
  return (first+second).Pt()

def plphpt(tree):
  try: return c._pl_phPt[0]
  except: return -99.

#
# Define plots
#
Plot.setDefaults(stack=stack, texY = ('(1/N) dN/dx' if normalize else 'Events'), modTexLeg = [('(genuine)', '')] if args.tag.lower().count('nice') else [])
Plot2D.setDefaults(stack=stack)

from ttg.plots.plotHelpers  import *

# Plot definitions (allow long lines, and switch off unneeded lambda warning, because lambdas are needed)
def makePlotList():
  # pylint: disable=C0301,W0108
  plotList = []
  if args.tag.count('randomConeCheck'):
    plotList.append(Plot('photon_chargedIso',          'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (20, 0, 20)))
    plotList.append(Plot('photon_chargedIso_small',    'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (80, 0, 20)))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)', lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c.ph_pt, (20, 0, 2)))
  else:
    plotList.append(Plot('yield',                      'yield',                                 lambda c : channelNumbering(c),                                (3,  0.5, 3.5), histModifications=xAxisLabels(['#mu#mu', 'e#mu', 'ee'])))
    plotList.append(Plot('nVertex',                    'vertex multiplicity',                   lambda c : c._nVertex,                                         (50, 0, 50)))
    plotList.append(Plot('nTrueInt',                   'nTrueInt',                              lambda c : c._nTrueInt,                                        (50, 0, 50)))
    plotList.append(Plot('nphoton',                    'number of photons',                     lambda c : c.nphotons,                                         (4,  -0.5, 3.5)))
    plotList.append(Plot('photon_pt',                  'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            (24, 15, 135)))
    plotList.append(Plot('photon_pt_large',            'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            [15., 30., 45., 60., 80., 120.]))
    plotList.append(Plot('photon_pt_EGM',              'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                            [20., 35., 50., 100., 200., 500., 600.]))
    plotList.append(Plot('photon_eta',                 '|#eta|(#gamma)',                        lambda c : abs(c._phEta[c.ph]),                                (15, 0, 2.5)))
    plotList.append(Plot('photon_eta_large',           '|#eta|(#gamma)',                        lambda c : abs(c._phEta[c.ph]),                                [0, 0.15, 0.3, 0.45, 0.60, 0.75, 0.9, 1.05, 1.2, 1.5, 1.8, 2.1, 2.5]))
    plotList.append(Plot('photon_phi',                 '#phi(#gamma)',                          lambda c : c._phPhi[c.ph],                                     (10, -pi, pi)))
    plotList.append(Plot('photon_mva_S16v1',           '#gamma-MVA S16v1',                      lambda c : c._phMvaS16v1[c.ph],                                (20, -1, 1)))
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
    plotList.append(Plot('photon_chargedIso_tiny',     'chargedIso(#gamma) (GeV)',              lambda c : c._phChargedIsolation[c.ph],                        (50, 0, 5)))
    plotList.append(Plot('photon_chargedIso_tiny_NO',  'chargedIso(#gamma) (GeV)',              lambda c : c._phChargedIsolation[c.ph],                        (50, 0, 5), overflowBin = None))
    plotList.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)',      lambda c : c._phChargedIsolation[c.ph]/c.ph_pt,                (20, 0, 2)))
    plotList.append(Plot('photon_neutralIso',          'neutralIso(#gamma) (GeV)',              lambda c : c._phNeutralHadronIsolation[c.ph],                  (25, 0, 5)))
    plotList.append(Plot('photon_photonIso',           'photonIso(#gamma) (GeV)',               lambda c : c._phPhotonIsolation[c.ph],                         (32, 0, 8)))
    plotList.append(Plot('photon_SigmaIetaIeta',       '#sigma_{i#etai#eta}(#gamma)',           lambda c : c._phSigmaIetaIeta[c.ph],                           (20, 0, 0.04)))
    plotList.append(Plot('photon_SigmaIetaIeta_small', '#sigma_{i#etai#eta}(#gamma)',           lambda c : c._phSigmaIetaIeta[c.ph],                           (80, 0, 0.04)))
    plotList.append(Plot('photon_hadOverEm',           'hadronicOverEm(#gamma)',                lambda c : c._phHadronicOverEm[c.ph],                          (100, 0, .025)))
    plotList.append(Plot('photon_phHadTowOverEm',      'hadronicTowerOverEm(#gamma)',           lambda c : c._phHadTowOverEm[c.ph],                            (100, 0, .025)))
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
    plotList.append(Plot('l_maxRelIso',                'max relIso(l_{1},l_{2})',               lambda c : max(c._relIso[c.l1], c._relIso[c.l2]),              (16, 0, 0.16)))
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
    plotList.append(Plot('signalRegionsZoomAlt',       'signal region',                         lambda c : min(6, createSignalRegionsZoom(c)),                 (7, 0, 7),   histModifications=xAxisLabels(['2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b'])))
    plotList.append(Plot('eventType',                  'eventType',                             lambda c : c._ttgEventType,                                    (9, 0, 9)))
    plotList.append(Plot('genPhoton_pt',               'p_{T}(gen #gamma) (GeV)',               lambda c : c.genPhPt,                                          (10, 10, 110)))
    plotList.append(Plot('genPhoton_eta',              '|#eta|(gen #gamma)',                    lambda c : abs(c.genPhEta),                                    (15, 0, 2.5), overflowBin=None))
    plotList.append(Plot('genPhoton_minDeltaR',        'min #DeltaR(gen #gamma, other)',        lambda c : c.genPhMinDeltaR,                                   (15, 0, 1.5)))
    plotList.append(Plot('genPhoton_DeltaR',           '#DeltaR(gen #gamma, #gamma)',           lambda c : c.genPhDeltaR,                                      (30, 0, 0.6)))
    plotList.append(Plot('genPhoton_relPt',            'rel p_{T}',                             lambda c : c.genPhRelPt,                                       (20, -0.2, 0.2)))
    plotList.append(Plot('photonCategory',             'photonCategory',                        lambda c : photonCategoryNumber(c),                            (7, 0.5, 7.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake', 'magic', 'unmHad', 'unmFake'])))
    plotList.append(Plot('phRawJetERatio',             'E photon / closest raw jet ',           lambda c : c._phECorr[c.ph] / c._jetE[closestRawJet(c)],           (50, 0, 5), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))
    plotList.append(Plot('phRawJetDeltaR',             'raw #DeltaR(#gamma, j) ',               lambda c : rawJetDeltaR(c),                                    (45, 0, 0.3), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))
    plotList.append(Plot('phL1DeltaR_small',           '#DeltaR(#gamma, l_{1})',                lambda c : c.phL1DeltaR,                                       (50, 0, 5)))
    plotList.append(Plot('phL2DeltaR_small',           '#DeltaR(#gamma, l_{2})',                lambda c : c.phL2DeltaR,                                       (50, 0, 5)))
    plotList.append(Plot('phLepDeltaR_small',          '#DeltaR(#gamma, l)',                    lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                    (50, 0, 5)))
    plotList.append(Plot('phJetDeltaR_small',          '#DeltaR(#gamma, j)',                    lambda c : c.phJetDeltaR,                                      (50, 0, 5)))
    plotList.append(Plot('phBJetDeltaR_small',         '#DeltaR(#gamma, b)',                    lambda c : c.phBJetDeltaR,                                     (50, 0, 5)))
    plotList.append(Plot('l1_jetDeltaR_small',         '#DeltaR(l_{1}, j)',                     lambda c : c.l1JetDeltaR,                                      (50, 0, 5)))
    plotList.append(Plot('l2_jetDeltaR_small',         '#DeltaR(l_{2}, j)',                     lambda c : c.l2JetDeltaR,                                      (50, 0, 5)))
    plotList.append(Plot('rhoCorrCharged',             'Photon charged rho correction (GeV)',   lambda c : c._rhoCorrCharged[c.ph],                            (40, 0, 2), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('rhoCorrNeutral',             'Photon neutral rho correction (GeV)',   lambda c : c._rhoCorrNeutral[c.ph],                            (40, 0, 8), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('rhoCorrPhotons',             'Photon photon  rho correction (GeV)',   lambda c : c._rhoCorrPhotons[c.ph],                            (40, 0, 8), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('puChargedHadronIso',         'Photon puChargedHadronIso (GeV)',       lambda c : c._puChargedHadronIso[c.ph],                        (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('phoWorstChargedIsolation',   'Photon phoWorstChargedIsolation (GeV)', lambda c : c._phoWorstChargedIsolation[c.ph],                  (20, 0, 20), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV')))
    plotList.append(Plot('phRawJetDeltaR_WIDE',             'raw #DeltaR(#gamma, j) ',          lambda c : rawJetDeltaR(c),                                    (15, 0, 0.3), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))
    plotList.append(Plot('photon_neutralOverCharged',  'Photon neutral/charged had. iso.',      lambda c : NoverCha(c),                                        (20, -1, 4)))
    plotList.append(Plot('photon_chargedOverNeutral',  'Photon charged/neutral had. iso.',      lambda c : ChaOverN(c),                                        (20, -1, 4)))
    plotList.append(Plot('photon_relNeutralIso',       'neutralIso(#gamma)/p_{T}(#gamma)',      lambda c : c._phNeutralHadronIsolation[c.ph]/c.ph_pt,          (20, 0, 0.2)))
    plotList.append(Plot('photon_relPhotonIso',        'photonIso(#gamma)/p_{T}(#gamma)',       lambda c : c._phPhotonIsolation[c.ph]/c.ph_pt,                 (20, 0, 0.2)))
    # plotList.append(Plot('phRawJetERatio',             'E photon / closest raw jet ',           lambda c : c._phE[c.ph] / c._jetE[closestRawJet(c)],           (50, 0, 5), normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))
    plotList.append(Plot('rawJetDeepCSV',              'deepCSV(closest raw jet)',              lambda c : c._jetDeepCsv_b[closestRawJet(c)] + c._jetDeepCsv_bb[closestRawJet(c)],     (20, 0, 1)))
    plotList.append(Plot2D('photon_pt_eta', 'p_{T}(#gamma) (GeV)', lambda c : c.ph_pt , [15., 30., 45., 60., 80., 120.], '|#eta|(#gamma)', lambda c : abs(c._phEta[c.ph]), [0, 0.15, 0.3, 0.45, 0.60, 0.75, 0.9, 1.05, 1.2, 1.5, 1.8, 2.1, 2.5]))
    plotList.append(Plot2D('photon_pt_etaB', 'p_{T}(#gamma) (GeV)', lambda c : c.ph_pt , [15., 30., 45., 60., 120.], '|#eta|(#gamma)', lambda c : abs(c._phEta[c.ph]), [0, 0.3, 0.60, 0.9, 1.5, 1.8, 2.5]))
    plotList.append(Plot2D('photon_pt_vspl', 'p_{T}(#gamma) (GeV)', lambda c : c.ph_pt , (12, 20, 140), 'PL p_{T}(#gamma) (GeV)', lambda c : plphpt(c) , (12, 20, 140)))
    plotList.append(Plot2D('photon_pt_vsplx', 'p_{T}(#gamma) (GeV)', lambda c : c.ph_pt , (12, 20, 140), 'PL p_{T}(#gamma) (GeV)', lambda c : plphpt(c) , (12, 20, 140), histModifications=normalizeAlong('x') ))
    plotList.append(Plot2D('photon_pt_vsply', 'p_{T}(#gamma) (GeV)', lambda c : c.ph_pt , (12, 20, 140), 'PL p_{T}(#gamma) (GeV)', lambda c : plphpt(c) , (12, 20, 140), histModifications=normalizeAlong('y') ))
# TODO temp 
    # plotList.append(Plot('max_l_SigmaIetaIeta', '#sigma_{i#etai#eta}(l max)',           lambda c : max(c._lElectronSigmaIetaIeta[c.l1], c._lElectronSigmaIetaIeta[c.l2]),                           (80, 0, 0.04)))
    # plotList.append(Plot('max_l_SigmaIetaIetaFP', '#sigma_{i#etai#eta}(l max)',           lambda c : max(c._lElectronSigmaIetaIeta[c.l1], c._lElectronSigmaIetaIeta[c.l2]),                           [-0.01,0.011,0.8]))
    # plotList.append(Plot2D('mll_mllg', 'm(ll) (GeV)', lambda c : c.mll , (25, 0, 500), 'm(ll#gamma) (GeV)', lambda c : c.mllg , (40, 0, 800) ))
# 
    # plotList.append(Plot('nearestZ',   'nearestZ',   lambda c : nearestZ(c),                                       [0., 1., 2.], normBinWidth = 1, texY = ('(1/N) dN / GeV' if normalize else 'Events / GeV') ))    
    # plotList.append(Plot('Z_pt',                  'p_{T}(Z) (GeV)',                   lambda c : Zpt(c),                                            (20, 10, 200)))
    # plotList.append(Plot('ZplusPho_pt',           'p_{T}(Z) + p_{T}(pho) (GeV)',                   lambda c : Zpt(c)+c.ph_pt,                (30, 10, 300)))
    # plotList.append(Plot('phMomType',             'phMomType',                                     lambda c : c.genPhMomPdg,                 (50, -25, 25)))
    # plotList.append(Plot('phMomTypeB',            'phMomType',                                     lambda c : abs(c.genPhMomPdg),            [0,8.5,9.5,10.5,18.5,20.5,21.5,22.5,23.5,24.5,25.5], histModifications=xAxisLabels(['quark','/','lepton','/','g','pho','Z','W','/'])))

    # extra plots only produced when asked
    if args.extraPlots.lower().count('cj'):
      plotList.append(Plot('j1jetNeutralHadronFraction',   'j1jetNeutralHadronFraction',        lambda c : jetNeutralHadronFraction(c, c.j1),                  (20, 0., 1.)))
      plotList.append(Plot('j1jetChargedHadronFraction',   'j1jetChargedHadronFraction',        lambda c : jetChargedHadronFraction(c, c.j1),                  (20, 0., 1.)))
      plotList.append(Plot('j1jetNeutralEmFraction',       'j1jetNeutralEmFraction',            lambda c : jetNeutralEmFraction(c, c.j1),                      (20, 0., 1.)))
      plotList.append(Plot('j1jetChargedEmFraction',       'j1jetChargedEmFraction',            lambda c : jetChargedEmFraction(c, c.j1),                      (20, 0., 1.)))
      plotList.append(Plot('j1jetHFHadronFraction',        'j1jetHFHadronFraction',             lambda c : jetHFHadronFraction(c, c.j1),                       (20, 0., 1.)))
      plotList.append(Plot('j1jetHFEmFraction',            'j1jetHFEmFraction',                 lambda c : jetHFEmFraction(c, c.j1),                           (20, 0., 1.)))
      plotList.append(Plot('jCljetNeutralHadronFraction',  'jCljetNeutralHadronFraction',       lambda c : jetNeutralHadronFraction(c, c.jCl),                 (20, 0., 1.)))
      plotList.append(Plot('jCljetChargedHadronFraction',  'jCljetChargedHadronFraction',       lambda c : jetChargedHadronFraction(c, c.jCl),                 (20, 0., 1.)))
      plotList.append(Plot('jCljetNeutralEmFraction',      'jCljetNeutralEmFraction',           lambda c : jetNeutralEmFraction(c, c.jCl),                     (20, 0., 1.)))
      plotList.append(Plot('jCljetChargedEmFraction',      'jCljetChargedEmFraction',           lambda c : jetChargedEmFraction(c, c.jCl),                     (20, 0., 1.)))
      plotList.append(Plot('jCljetHFHadronFraction',       'jCljetHFHadronFraction',            lambda c : jetHFHadronFraction(c, c.jCl),                      (20, 0., 1.)))
      plotList.append(Plot('jCljetHFEmFraction',           'jCljetHFEmFraction',                lambda c : jetHFEmFraction(c, c.jCl),                          (20, 0., 1.)))
      plotList.append(Plot('jClPt',                        'p_{T}(j_{1}) (GeV)',                lambda c : c._jetSmearedPt[c.jCl],                             (30, 30, 330)))
      plotList.append(Plot('jClPhoPtDiff',                 'p_{T}(j_{1}) (GeV)',                lambda c : abs(c._jetSmearedPt[c.jCl] - c.ph_pt),              (30, 30, 330)))
      plotList.append(Plot('jClPhoPtDiffRel',              'jcl pt - ph pt/ ph pt',             lambda c : abs(c._jetSmearedPt[c.jCl] - c.ph_pt)/c.ph_pt ,     (20, 0., 4.)))
    if args.extraPlots.lower().count('raw'):
      plotList.append(Plot('phRawJetEDiffRel',             'E photon - closest raw jet/ photon', lambda c : abs(c._phE[c.ph] - c._jetE[closestRawJet(c)])/c._phE[c.ph], (20, 0., 4.)))
      plotList.append(Plot('rawLep1JetDeltaR',           'raw #DeltaR(#l1, j)',                    lambda c : rawLep1JetDeltaR(c),                               (50, 0, 1.0), overflowBin=None))
      plotList.append(Plot('rawLep2JetDeltaR',           'raw #DeltaR(#l2, j)',                    lambda c : rawLep2JetDeltaR(c),                               (50, 0, 1.0), overflowBin=None))
      plotList.append(Plot('rawLepJetDeltaR',            'raw #DeltaR(#l, j)',                     lambda c : rawLepJetDeltaR(c),                                (50, 0, 0.5), overflowBin=None))
      plotList.append(Plot('genLep1RawJetDeltaR',        'raw #DeltaR(gen l1, j)',                 lambda c : genLep1RawJetDeltaR(c),                            (50, 0, 1.0), overflowBin=None))
      plotList.append(Plot('genLep2RawJetDeltaR',        'raw #DeltaR(gen l2, j)',                 lambda c : genLep2RawJetDeltaR(c),                            (50, 0, 1.0), overflowBin=None))
      plotList.append(Plot('genLepRawJetDeltaR',         'raw #DeltaR(gen l, j)',                  lambda c : genLepRawJetDeltaR(c),                             (50, 0, 0.5), overflowBin=None))
      plotList.append(Plot('genLepRawJetNearPhDeltaR',   'raw #DeltaR(gen l, j near #gamma)',      lambda c : genLepRawJetNearPhDeltaR(c),                       (50, 0, 0.5), overflowBin=None))
      plotList.append(Plot('photon_mom',                 'photon mom particle',                    lambda c : momDictFunc(c),                                    (len(momList)+1, 0, len(momList)+1), histModifications=[xAxisLabels(nameList), customLabelSize(14)]))
      plotList.append(Plot('photon_pt_ATL',              'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                           [20., 23., 26., 29., 32., 35., 40., 45., 50., 55., 65., 75., 85., 100., 130., 180., 300.]))
      plotList.append(Plot('photon_pt_ATLB',             'p_{T}(#gamma) (GeV)',                   lambda c : c.ph_pt,                                           [20., 30., 40., 50., 65., 80., 100., 125., 160., 220., 300.]))
  # pylint: enable=C0301

  if args.filterPlot:
    plotList[:] = [p for p in plotList if args.filterPlot in p.name]

  isSR = args.tag.lower().count('phocbfull') or (args.selection.count('passChgIso') and args.selection.count('passSigmaIetaIeta'))
  # any sideband selection means we can unblind
  isSideband = [args.selection.count('sidebandSigmaIetaIeta'), args.selection.count('failChgIso'), args.selection.count('onZ'), args.selection.count('llgOnZ')]
  doBlind = isSR and not any(isSideband)
  if not doBlind:
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
  # TODO check if still needed
  copySyst = False
  # copySyst = year == '2016' and args.sys in ['hdampUp', 'hdampDown', 'ueUp', 'ueDown', 'erdDown', 'isrUp', 'isrDown', 'fsrUp', 'fsrDown']
  # copySyst = copySyst or (year == '2018' and args.sys in ['erdUp', 'erdDown', 'ephResDown', 'ephResUp', 'ephScaleDown', 'ephScaleUp'])
  if not args.showSys and not copySyst:

    if args.tag.lower().count('phocb'):                                             reduceType = 'phoCB-SKRT'
    # elif args.tag.count('phoCB-ZGorig') or args.tag.count('phoCBfull-ZGorig'):        reduceType = 'phoCB-ZGorig'
    else:                                                                           reduceType = 'pho'
    if args.tag.lower().count('leptonmva'):                                         reduceType = 'leptonmva-' + reduceType
    if args.tag.count('base'):                                                      reduceType = 'base'
    origReducetype = reduceType
    reduceType = applySysToReduceType(reduceType, args.sys)
    log.info("using reduceType " + reduceType)

    from ttg.plots.photonCategories import checkMatch, checkSigmaIetaIeta, checkChgIso
    dumpArrays = {}
    origCB = phoCBfull
    origTag = args.tag
    for sample in sum(stack, []):

      dumpArray = [("ph_pt", lambda c : c.ph_pt),
                   ("pl_ph_pt", lambda c : plphpt(c))]
      dumpArray = [(variable, expression, []) for variable, expression in dumpArray]
      weightArray = []
      cutString, passingFunctions = cutStringAndFunctions(args.selection, args.channel)
      if not sample.isData and args.sys:
        cutString = applySysToString(sample.name, args.sys, cutString)


      NPestimate        = sample.texName.lower().count('estimate')
      if args.sys and sample.isData and not NPestimate: continue
      # when estimating from the sideband the selection is changed for just these samples
      if NPestimate:
        phoCBfull = False
        args.tag = args.tag.replace('passSigmaIetaIeta','')
        args.tag = args.tag.replace('passChgIso','')
        args.tag = args.tag.replace('phoCBfull','')
        args.tag = args.tag + '-passChgIso-sidebandSigmaIetaIeta'

      c = sample.initTree(reducedType = origReducetype if NPestimate else reduceType)
      # c = sample.initTree(reducedType = origReducetype if ((args.sys.count('Scale') or args.sys.count('Res')) and NPestimate) else reduceType)
      c.year = sample.name[:4] if year == "comb" else year
      lumiScale = lumiScales[c.year]
      c.data = sample.isData

      c.NPestimate = NPestimate

      # Filter booleans
      c.genuine           = sample.texName.count('genuine') or args.tag.count("filterGenuine")
      c.misIdEle          = sample.texName.count('misidentified') or sample.texName.count('misIdEle') or sample.texName.count('nonprompt') or args.tag.count("filterMisIdEle")
      c.hadronicPhoton    = sample.texName.count('nonprompt') or sample.texName.count('hadronic photons') or sample.texName.count('hadronicPhoton') or args.tag.count("filterHadronic")
      c.hadronicFake      = sample.texName.count('nonprompt') or sample.texName.count('hadronic fakes') or sample.texName.count('hadronicFake') or args.tag.count("filterFake")
      c.magicPhoton       = sample.texName.count('nonprompt') or sample.texName.count('magic photons') or sample.texName.count('magicPhoton') or args.tag.count("filterMagic")
      c.mHad              = sample.texName.count('nonprompt') or sample.texName.count('mHad')   or sample.texName.count('mhad')   or args.tag.count("filtermHad")
      c.mFake             = sample.texName.count('nonprompt') or sample.texName.count('mFake')  or sample.texName.count('mfake')  or args.tag.count("filtermFake")
      c.unmHad            = sample.texName.count('nonprompt') or sample.texName.count('unmHad')   or sample.texName.count('unmhad')   or args.tag.count("filterUnmHad")
      c.unmFake           = sample.texName.count('nonprompt') or sample.texName.count('unmFake')  or sample.texName.count('unmfake')  or args.tag.count("filterUnmFake")
      c.checkMatch        = any([c.hadronicPhoton, c.misIdEle, c.hadronicFake, c.genuine, c.magicPhoton, c.mHad, c.mFake, c.unmHad, c.unmFake])
      c.nonPrompt         = any([c.hadronicPhoton, c.misIdEle, c.hadronicFake, c.magicPhoton, c.mHad, c.mFake, c.unmHad, c.unmFake])

      c.failSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} fail')     or args.tag.count("failSigmaIetaIeta")
      c.sideSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} sideband') or args.tag.count("sidebandSigmaIetaIeta")
      c.passSigmaIetaIeta = sample.texName.count('#sigma_{i#etai#eta} pass') or args.tag.count("passSigmaIetaIeta") or args.tag.count("noChgIso")
      c.sigmaIetaIeta1    = sample.texName.count('sideband1') or args.tag.count("gapSigmaIetaIeta")
      c.sigmaIetaIeta2    = sample.texName.count('sideband2') 
      c.failChgIso        = args.tag.count("failChgIso") or sample.texName.count('chgIso fail')
      c.passChgIso        = args.tag.count("passChgIso") or sample.texName.count('chgIso pass')
      c.lowChgIso         = args.tag.count("lowchgIso") or sample.texName.count('lowchgIso')
      c.highChgIso        = args.tag.count("highchgIso") or sample.texName.count('highchgIso')

      if forward:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.0272 < #sigma_{i#etai#eta} < 0.032')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.032 < #sigma_{i#etai#eta}')
      else:
        if   c.sigmaIetaIeta1: sample.texName = sample.texName.replace('sideband1', '0.01015 < #sigma_{i#etai#eta} < 0.012')
        elif c.sigmaIetaIeta2: sample.texName = sample.texName.replace('sideband2', '0.012 < #sigma_{i#etai#eta}')
      
      # when creating input plots for corrections corrections can obviously not be applied yet
      altS = '-signalRegion-'
      if NPestimate and args.selection.count('signalRegionA'): altS  = '-signalRegionA-'
      if NPestimate and args.selection.count('signalRegionB'): altS  = '-signalRegionB-'
      if NPestimate and args.selection.count('signalRegionAB'): altS = '-signalRegionAB-'

      npReweight = npWeight(c.year, sigma = getSigmaSyst(args.sys), altS=altS)
      if not args.noZgCorr:
        try:
          # Zg correction factors are systematic-specific unless specified otherwise
          ZgReweight = ZgWeight(c.year, sys = '' if args.tag.lower().count('methoda') else args.sys)
        except Exception as ex:
          log.debug(ex)
          log.warning('No Zg estimate source plots available, no problem if not used later')
          pass

      for i in sample.eventLoop(cutString):
        c.GetEntry(i)
        c.ISRWeight = 1.
        c.FSRWeight = 1.
        if not sample.isData and args.sys:
          applySysToTree(sample.name, args.sys, c)

        if not passingFunctions(c): continue
        if selectPhoton:
          if phoCBfull and not c._phCutBasedMedium[c.ph]:  continue
          if forward and abs(c._phEta[c.ph]) < 1.566:      continue
          if not forward and abs(c._phEta[c.ph]) > 1.4442: continue
          if not checkSigmaIetaIeta(c): continue  # filter for sigmaIetaIeta sideband based on filter booleans (pass or fail)
          if not checkChgIso(c):        continue  # filter for chargedIso sideband based on filter booleans (pass or fail)
          if not sample.isData and not checkMatch(c):         continue  # filter using AN15-165 definitions based on filter booleans (genuine, hadronicPhoton, misIdEle or hadronicFake)

        if not (selectPhoton and c.ph_pt > 20): 
          c.phWeight  = 1.                             # Note: photon SF is 0 when pt < 20 GeV
          c.PVWeight  = 1.
        
        prefireWeight = 1. if c.year == '2018' or sample.isData else c._prefireWeight
        
        estWeight = npReweight.getWeight(c, sample.isData)

        if sample.name.lower().count('zg') and not args.noZgCorr:
          zgw = ZgReweight.getWeight(c, channel = channelNumbering(c))
        else: zgw = 1.

        if sample.isData: eventWeight = estWeight
        elif noWeight:    eventWeight = 1.
        else:             eventWeight = c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*prefireWeight*lumiScale*c.ISRWeight*c.FSRWeight*c.PVWeight*estWeight*zgw

        if year == "comb": 
          eventWeight *= lumiScales['2018'] / lumiScales[c.year]

        fillPlots(plotsToFill, sample, eventWeight)

        if args.dumpArrays:
          for variable, expression, array in dumpArray:
            array.append(expression(c))
          weightArray.append(eventWeight)
      dumpArrays[sample.name + sample.texName] = {variable: array for variable, expression, array in dumpArray}
      dumpArrays[sample.name + sample.texName]['eventWeight'] = weightArray
      phoCBfull = origCB
      args.tag = origTag
  if not args.showSys and copySyst:
    copySystPlots(plots, '2017', year, args.tag, args.channel, args.selection, args.sys)
  # TODO to to be implemented
  # if args.sys and any(x in 'args.sys' for x in ['q2','pdf']) and not args.showSys:
  #  freezeTTGYield(plots, year, args.tag, args.channel, args.selection)

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
        if sample.isData and not 'estimate' in sample.texName:
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
      normalizeToMC = [False, True] if (args.channel != 'noData' and not onlyMC) else [False]
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
        extraArgs['postFitInfo']       = (year + ('chgIsoFit_dd_all' if args.tag.count('matchCombined') else 'srFit')) if args.post else None
        # log.info(extraArgs['postFitInfo'])
        extraArgs['resultsDir']        = os.path.join(plotDir, year, args.tag, args.channel, args.selection)


      if args.channel != 'noData':
        extraArgs['ratio']   = {'yRange' : (0.4, 1.6), 'texY': 'data/MC'}

      if args.channel == 'noData' and args.tag.count('compRewAll'):
        extraArgs['ratio']   = {'yRange' : (0.2, 1.8), 'texY': 'prediction/MC'}

      if any (args.tag.count(sname) for sname in ['chisoHad', 'chisoFake', 'chisoNP']):
        extraArgs['ratio']   = {'yRange' : (0.0, 1.0), 'texY': 'chargedIso pass/fail'}

      if any (args.tag.lower().count(sname) for sname in ['failpass', 'ffp', 'pfp']):
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

      if args.tag.count('IsoRegTTDil'):
        extraArgs['ratio']   = None

      if args.tag.count('norat'):
        extraArgs['ratio']   = None

      for norm in normalizeToMC:
        if norm: extraArgs['scaling'] = {0:1}
        for logY in [False, True]:
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
                    sorting           = False,
                    yRange            = yRange if yRange else (0.003 if logY else 0.0001, "auto"),
                    drawObjects       = drawLumi(None, lumiScales[year], isOnlySim=(args.channel=='noData' or onlyMC)),
                    # fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
                    **extraArgs
          )
          extraArgs['saveGitInfo'] = False
          if err: noWarnings = False

  if not args.sys:
    for plot in plots: # 2D plots
      if not hasattr(plot, 'varY'): continue
      if not args.showSys:
        plot.applyMods()
        plot.saveToCache(os.path.join(plotDir, year, args.tag, args.channel, args.selection), args.sys)
      for logY in [False, True]:
        for option in ['SCAT', 'COLZ', 'COLZ TEXT']:
          plot.draw(plot_directory = os.path.join(plotDir, year, args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                    logZ           = False,
                    drawOption     = option,
                    drawObjects    = drawLumi(None, lumiScales[year], isOnlySim=(args.channel=='noData' or onlyMC)))
                    
  if args.dumpArrays: 
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
# NOTE plotting systematics for 3 years combined is not tested, very likely doesn't work

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
      if sample.isData and not 'estimate' in sample.texName:
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
    normalizeToMC = [False, True] if (args.channel != 'noData' and not onlyMC) else [False]
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
      # extraArgs['postFitInfo']       = year + ('chgIsoFit_dd_all' if args.tag.count('matchCombined') else 'srFit') if args.post else None


    if args.channel != 'noData':
      extraArgs['ratio']   = {'yRange' : (0.4, 1.6), 'texY': 'data/MC'}

    if any (args.tag.count(sname) for sname in ['chisoHad', 'chisoFake', 'chisoNP']):
      extraArgs['ratio']   = {'yRange' : (0.0, 1.0), 'texY': 'chargedIso pass/fail'}

    if any (args.tag.lower().count(sname) for sname in ['failpass', 'ffp', 'pfp']):
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
                  sorting           = False,
                  yRange            = yRange if yRange else (0.003 if logY else 0.0001, "auto"),
                  drawObjects       = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData' or onlyMC)),
                  # fakesFromSideband = ('matchCombined' in args.tag and args.selection=='llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'),
                  **extraArgs
        )
        extraArgs['saveGitInfo'] = False
        if err: noWarnings = False

if not args.sys:
  for plot in totalPlots: # 2D plots
    if not hasattr(plot, 'varY'): continue
    if not args.showSys:
      plot.applyMods()
      plot.saveToCache(os.path.join(plotDir, 'all', args.tag, args.channel, args.selection), args.sys)
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ', 'COLZ TEXT']:
        plot.draw(plot_directory = os.path.join(plotDir, 'all', args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScale, isOnlySim=(args.channel=='noData' or onlyMC)))
if noWarnings: log.info('Finished')
else:          log.info('Could not produce all plots - finished')
