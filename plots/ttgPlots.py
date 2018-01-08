#! /usr/bin/env python

#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--channel',        action='store',      default=None)
argParser.add_argument('--tag',            action='store',      default='eleSusyLoose-phoCB')
argParser.add_argument('--sys',            action='store',      default=None)
argParser.add_argument('--runSys',         action='store_true', default=False)
argParser.add_argument('--showSys',        action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--runWillem',      action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

from ttg.tools.helpers import plotDir


#
# Systematics
#
from ttg.plots.systematics import systematics, linearSystematics, applySysToTree, applySysToString
if args.sys=='None': args.sys=None
if not (args.runSys or (args.showSys and args.isChild)): systematics = {}



#
# Submit subjobs
#
if not args.isChild and args.selection is None:
  from ttg.tools.jobSubmitter import submitJobs
  selections = ['llg',
                'llg-looseLeptonVeto',
                'llg-looseLeptonVeto-mll40',
                'llg-looseLeptonVeto-mll40-offZ',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt40',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt60',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04',
                #'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04-njet2p-deepbtag1p']

  if args.tag.count('QCD'):
    selections = ['pho','pho-njet1p','pho-njet2p','pho-njet2p-deepbtag1p','pho-njet2p-deepbtag1p-photonPt20','pho-njet2p-deepbtag1p-photonPt40','pho-njet2p-deepbtag1p-photonPt60']
  if args.tag.count('eleSusyLoose') and not args.tag.count('pho'):
    selections = ['ll-looseLeptonVeto-mll40', 'll-looseLeptonVeto-mll40-offZ', 'll-looseLeptonVeto-mll40-offZ-njet2p', 'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p']
  if args.tag.count('singleLep'):
    selections = ['lg-looseLeptonVeto', 'lg-looseLeptonVeto-njet3p', 'lg-looseLeptonVeto-njet4p', 'lg-looseLeptonVeto-njet4p-deepbtag1p', 'lg-looseLeptonVeto-njet4p-deepbtag2p']

  if args.channel:                        channels = [args.channel]
  elif args.tag.count('compareChannels'): channels = ['all']
  elif args.tag.count('QCD'):             channels = ['noData']
  elif args.tag.count('singleLep'):       channels = ['e','mu','noData']
  else:                                   channels = ['ee','mumu','emu','SF','all','noData']
  for s in ['None'] + systematics.keys():
    for c in channels:
    #  if args.tag.count('sigmaIetaIeta') and (c=='noData' and not args.tag.count('QCD') and not args.tag.count('singleLep')): continue
      args.channel = c
      args.sys     = s
      submitJobs(__file__, 'selection', selections, args, subLog=os.path.join(args.tag,c,s))
  exit(0)


#
# Initializing
#
import os, ROOT
from ttg.plots.plot           import Plot, xAxisLabels
from ttg.plots.plot2D         import Plot2D
from ttg.plots.cutInterpreter import cutInterpreter
from ttg.reduceTuple.objectSelection import photonSelector
from ttg.samples.Sample       import createStack
from ttg.plots.photonCategories import photonCategoryNumber
from math import pi

ROOT.gROOT.SetBatch(True)

phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
phoMva      = args.tag.count('phoMva')
phoMvaTight = args.tag.count('phoMvaTight')
eleCB       = args.tag.count('eleCB')
eleMva      = args.tag.count('eleMva')
sigmaieta   = args.tag.count('igmaIetaIeta')
forward     = args.tag.count('forward')
central     = args.tag.count('central')
randomCone  = args.tag.count('randomConeCheck')






#
# Create stack
#
import glob
stackFile = 'default'
for f in sorted(glob.glob("../samples/data/*.stack")):
  stackName = os.path.basename(f).split('.')[0]
  if args.tag.count(stackName):
    stackFile = stackName
    break
if args.tag.count('sigmaIetaIetaMatchMC'): stackFile = 'sigmaIetaIetaMatchMC'  # for some strange reason the glob.glob does noet always find this

log.info('Using stackFile ' + stackFile)

if args.tag.count('QCD'):         tuples = 'tuplesQCD.conf'
elif args.tag.count('singleLep'): tuples = 'tuplesSingleLep.conf'
else:                             tuples = 'tuples.conf'
stack = createStack(tuplesFile = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + tuples),
                    styleFile  = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '.stack'),
                    channel    = args.channel)


#
# Define plots
#

plots = []
Plot.setDefaults(stack=stack, texY = '(1/N) dN/dx' if sigmaieta or randomCone else 'Events')

plots2D = []
Plot2D.setDefaults(stack=stack)

if randomCone:
  plots.append(Plot('photon_chargedIso',      'chargedIso(#gamma) (GeV)',         lambda c : c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph],                  (20,0,20)))
  plots.append(Plot('photon_chargedIso_small','chargedIso(#gamma) (GeV)',         lambda c : c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph],                  (80,0,20)))
  plots.append(Plot('photon_relChargedIso',   'chargedIso(#gamma)/p_{T}(#gamma)',lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c._phPt[c.ph],   (20,0,2)))

else:
  if args.selection.count('lg') or args.selection.count('pho'):
    plots2D.append(Plot2D('chIso_vs_sigmaIetaIeta', 'chargedIso(#gamma) (GeV)', lambda c : c._phChargedIsolation[c.ph], (20,0,20), '#sigma_{i#etai#eta}(#gamma)', lambda c : c._phSigmaIetaIeta[c.ph], (20,0,0.04)))

  if args.selection.count('ll'):
    plots.append(Plot('yield',                    'yield',                                lambda c : 1 if c.isMuMu else (2 if c.isEMu else 3),                                (3, 0.5, 3.5), histModifications=xAxisLabels(['#mu#mu', 'e#mu', 'ee'])))
  elif args.selection.count('lg'):
    plots.append(Plot('yield',                    'yield',                                lambda c : 1 if c.isMu else 2,                                                    (3, 0.5, 3.5), histModifications=xAxisLabels(['#mu', 'e'])))
  plots.append(Plot('nVertex',                  'vertex multiplicity',                  lambda c : ord(c._nVertex),                                                         (50, 0, 50)))
  plots.append(Plot('nTrueInt',                 'nTrueInt',                             lambda c : c._nTrueInt,                                                             (50, 0, 50)))
  plots.append(Plot('nphoton',                  'number of photons',                    lambda c : sum([c._phCutBasedMedium[i] for i in c.photons]),                        (4, -0.5, 3.5)))
  if args.selection.count('lg') or args.selection.count('pho'):
    plots.append(Plot('photon_pt',                'p_{T}(#gamma) (GeV)',                  lambda c : c._phPt[c.ph],                                                           (20,15,115)))
    plots.append(Plot('photon_eta',               '|#eta|(#gamma)',                       lambda c : abs(c._phEta[c.ph]),                                                     (15,0,2.5)))
    plots.append(Plot('photon_phi',               '#phi(#gamma)',                         lambda c : c._phPhi[c.ph],                                                          (10,-pi,pi)))
    plots.append(Plot('photon_mva',               '#gamma-MVA',                           lambda c : c._phMva[c.ph],                                                          (20,-1,1)))
    plots.append(Plot('photon_chargedIso',        'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                                             (20,0,20)))
    plots.append(Plot('photon_chargedIso_NO',     'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                                             (20,0,20), overflowBin=None))
    plots.append(Plot('photon_chargedIso_bins',   'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                                             [0, 0.441,1,2,3,5,10,20], normBinWidth=1, texY=('(1/N) dN / GeV' if sigmaieta or randomCone else 'Events / GeV')))
    plots.append(Plot('photon_chargedIso_bins_NO','chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                                             [0, 0.441,1,2,3,5,10,20], normBinWidth=1, texY=('(1/N) dN / GeV' if sigmaieta or randomCone else 'Events / GeV'), overflowBin=None))
    plots.append(Plot('photon_chargedIso_small',  'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                                             (80,0,20)))
    plots.append(Plot('photon_chargedIso_small_NO','chargedIso(#gamma) (GeV)',            lambda c : c._phChargedIsolation[c.ph],                                             (80,0,20), overflowBin=None))
    plots.append(Plot('photon_relChargedIso',     'chargedIso(#gamma)/p_{T}(#gamma)',     lambda c : c._phChargedIsolation[c.ph]/c._phPt[c.ph],                               (20,0,2)))
    plots.append(Plot('photon_neutralIso',        'neutralIso(#gamma) (GeV)',             lambda c : c._phNeutralHadronIsolation[c.ph],                                       (25,0,5)))
    plots.append(Plot('photon_photonIso',         'photonIso(#gamma) (GeV)',              lambda c : c._phPhotonIsolation[c.ph],                                              (32,0,8)))
    plots.append(Plot('photon_SigmaIetaIeta',     '#sigma_{i#etai#eta}(#gamma)',          lambda c : c._phSigmaIetaIeta[c.ph],                                                (20,0,0.04)))
    plots.append(Plot('photon_hadOverEm',         'hadronicOverEm(#gamma)',               lambda c : c._phHadronicOverEm[c.ph],                                               (20,0,.025)))
    plots.append(Plot('phJetDeltaR',              '#Delta R(#gamma, j)',                  lambda c : c.phJetDeltaR,                                                           (20,0,5)))
  if args.selection.count('lg') or args.selection.count('ll'):
    plots.append(Plot('l1_pt',                  'p_{T}(l_{1}) (GeV)',                   lambda c : c._lPt[c.l1],                                                            (20,0,200)))
    plots.append(Plot('l1_eta',                 '|#eta|(l_{1})',                        lambda c : abs(c._lEta[c.l1]),                                                      (15,0,2.4)))
    plots.append(Plot('l1_phi',                 '#phi(l_{1})',                          lambda c : c._lPhi[c.l1],                                                           (10,-pi,pi)))
    plots.append(Plot('l1_relIso',              'relIso(l_{1})',                        lambda c : c._relIso[c.l1],                                                         (10,0,0.12)))
  if args.selection.count('ll'):
    plots.append(Plot('l2_pt',                  'p_{T}(l_{2}) (GeV)',                   lambda c : c._lPt[c.l2],                                                            (20,0,200)))
    plots.append(Plot('l2_eta',                 '|#eta|(l_{2})',                        lambda c : abs(c._lEta[c.l2]),                                                      (15,0,2.4)))
    plots.append(Plot('l2_phi',                 '#phi(l_{2})',                          lambda c : c._lPhi[c.l2],                                                           (10,-pi,pi)))
    plots.append(Plot('l2_relIso',              'relIso(l_{2})',                        lambda c : c._relIso[c.l2],                                                         (10,0,0.12)))
    plots.append(Plot('dl_mass',                'm(ll) (GeV)',                          lambda c : c.mll,                                                                   (40,0,200)))
  if args.selection.count('lg'):
    plots.append(Plot('photon_randomConeIso',   'random cone chargedIso(#gamma) (Gev)', lambda c : c._phRandomConeChargedIsolation[c.ph],                                   (20,0,20)))
    plots.append(Plot('l1g_mass',               'm(l_{1}#gamma) (GeV)',                 lambda c : c.ml1g,                                                                  (40,0,200)))
    plots.append(Plot('phL1DeltaR',             '#Delta R(#gamma, l_{1})',              lambda c : c.phL1DeltaR,                                                            (20,0,5)))
  if args.selection.count('llg'):
    plots.append(Plot('l2g_mass',               'm(l_{2}#gamma) (GeV)',                 lambda c : c.ml2g,                                                                  (40,0,200)))
    plots.append(Plot('phL2DeltaR',             '#Delta R(#gamma, l_{2})',              lambda c : c.phL2DeltaR,                                                            (20,0,5)))
    plots.append(Plot('phoPt_over_dlg_mass',    'p_{T}(#gamma)/m(ll#gamma)',            lambda c : c._phPt[c.ph]/c.mllg,                                                    (40,0,2)))
    plots.append(Plot('dlg_mass',               'm(ll#gamma) (GeV)',                    lambda c : c.mllg,                                                                  (40,0,500)))
    plots.append(Plot('dlg_mass_zoom',          'm(ll#gamma) (GeV)',                    lambda c : c.mllg,                                                                  (40,50,200)))
    plots.append(Plot('phLepDeltaR',            '#Delta R(#gamma, l)',                  lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                                         (20,0,5)))
  plots.append(Plot('njets',                    'number of jets',                       lambda c : c.njets,                                                                 (8,0,8)))
  plots.append(Plot('nbtag',                    'number of medium b-tags (deepCSV)',    lambda c : c.ndbjets,                                                               (4,0,4)))
  plots.append(Plot('j1_pt',                    'p_{T}(j_{1}) (GeV)',                   lambda c : c._jetPt[c.j1]                                 if c.j1 >= 0 else -1,     (30,0,300)))
  plots.append(Plot('j1_eta',                   '|#eta|(j_{1})',                        lambda c : abs(c._jetEta[c.j1])                           if c.j1 >= 0 else -1,     (15,0,2.5)))
  plots.append(Plot('j1_phi',                   '#phi(j_{1})',                          lambda c : c._jetPhi[c.j1]                                if c.j1 >= 0 else -10,    (10,-pi,pi)))
  plots.append(Plot('j1_csvV2',                 'CSVv2(j_{1})',                         lambda c : c._jetCsvV2[c.j1]                              if c.j1 >= 0 else -10,    (20, 0, 1)))
  plots.append(Plot('j1_deepCSV',               'deepCSV(j_{1})',                       lambda c : c._jetDeepCsv_b[c.j1] + c._jetDeepCsv_bb[c.j1] if c.j1 >= 0 else -10,    (20, 0, 1)))  # still buggy
  plots.append(Plot('j2_pt',                    'p_{T}(j_{2}) (GeV)',                   lambda c : c._jetPt[c.j2]                                 if c.j2 >= 0 else -1,     (30,0,300)))
  plots.append(Plot('j2_eta',                   '|#eta|(j_{2})',                        lambda c : abs(c._jetEta[c.j2])                           if c.j2 >= 0 else -1,     (15,0,2.5)))
  plots.append(Plot('j2_phi',                   '#phi(j_{2})',                          lambda c : c._jetPhi[c.j2]                                if c.j2 >= 0 else -10,    (10,-pi,pi)))
  plots.append(Plot('j2_csvV2',                 'CSVv2(j_{2})',                         lambda c : c._jetCsvV2[c.j2]                              if c.j2 >= 0 else -10,    (20, 0, 1)))
  plots.append(Plot('j2_deepCSV',               'deepCSV(j_{2})',                       lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2] if c.j2 >= 0 else -10,    (20, 0, 1)))

  if args.channel=='noData':
    plots.append(Plot('eventType',              'eventType',                            lambda c : c._ttgEventType,                                                           (9, 0, 9)))
    if args.tag.count('llg'):
      plots.append(Plot('genPhoton_pt',         'p_{T}(gen #gamma) (GeV)',              lambda c : c._gen_phPt[c._phMatchMCPhotonAN15165[c.ph]] if c._phMatchMCPhotonAN15165[c.ph] > -1 else -1,     (10,10,110)))
      plots.append(Plot('genPhoton_eta',        '|#eta|(gen #gamma)',                   lambda c : abs(c._gen_phEta[c._phMatchMCPhotonAN15165[c.ph]]) if c._phMatchMCPhotonAN15165[c.ph] > -1 else -1, (15,0,2.5)))
      plots.append(Plot('photonCategory',       'photonCategory',                       lambda c : photonCategoryNumber(c, c.ph, oldDefinition),                                                      (4, 0.5, 4.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake'])))


lumiScale = 35.9







#
# Loop over events (except in case of showSys when the histograms are taken from the results.pkl file)
#
if not args.showSys:
  cutString, passingFunctions = cutInterpreter.cutString(args.selection)
  if not cutString: cutString = '(1)'
  if args.sys:      cutString = applySysToString(args.sys, cutString)

  if args.channel=="ee":   cutString += '&&isEE'
  if args.channel=="mumu": cutString += '&&isMuMu'
  if args.channel=="emu":  cutString += '&&isEMu'
  if args.channel=="e":    cutString += '&&isE'
  if args.channel=="mu":   cutString += '&&isMu'

  if   args.tag.count('QCD'):                reduceType = 'phoCB'
  elif args.tag.count('CBLoose'):            reduceType = 'eleCBLoose-phoCB'
  elif args.tag.count('CBTight'):            reduceType = 'eleCB-phoCB'
  elif args.tag.count('eleSusyLoose-phoCB'): reduceType = 'eleSusyLoose-phoCB'
  elif args.tag.count('match'):              reduceType = 'eleSusyLoose-phoCB'
  elif args.tag.count('eleSusyLoose'):       reduceType = 'eleSusyLoose'
  elif args.tag.count('sigmaIetaIeta'):      reduceType = 'eleSusyLoose-phoCB'

  from ttg.reduceTuple.objectSelection import deltaR, looseLeptonSelector, selectPhotons
  from ttg.plots.photonCategories import checkMatch, checkPrompt, checkSigmaIetaIeta
  for sample in sum(stack, []):
    if args.sys and sample.isData: continue
    c = sample.initTree(reducedType = reduceType, skimType='singlePhoton' if args.tag.count('QCD') else 'dilep')

    if not sample.isData:
      from ttg.reduceTuple.puReweighting import getReweightingFunction
      if args.tag.count('puDown'): puWeights = 'PU_2016_36000_XSecDown'
      elif args.tag.count('puUp'): puWeights = 'PU_2016_36000_XSecUp'
      else:                        puWeights = 'PU_2016_36000_XSecCentral'
      puReweighting = getReweightingFunction(data=puWeights, useWillem=args.runWillem, useMC=sample.getTrueInteractions(reduced=True))


    c.QCD  = args.tag.count('QCD')
    c.data = sample.isData

    # Filter booleans
    oldDefinition       = args.tag.count('oldMatching')
    c.genuine           = sample.texName.count('genuine')
    c.hadronicPhoton    = sample.texName.count('hadronicPhoton')
    c.misIdEle          = sample.texName.count('misIdEle')
    c.hadronicFake      = sample.texName.count('hadronicFake')
    c.nonprompt         = sample.texName.count('non-prompt')
    c.prompt            = sample.texName.count('prompt') and not sample.texName.count('non-prompt')
    c.failSigmaIetaIeta = sample.texName.count('fail')
    c.passSigmaIetaIeta = sample.texName.count('pass') or args.tag.count("noChgIso")

    c.selectPhoton        = args.selection.count('llg')
    c.photonCutBased      = phoCB
    c.photonCutBasedTight = False
    c.photonMva           = phoMva
    for i in sample.eventLoop(cutString):
      c.GetEntry(i)
      if c.QCD:
        c.lWeight = 1.
        c.lTrackWeight = 1.
        c.triggerWeight = 1.
      elif not sample.isData:
        if args.sys: applySysToTree(args.sys, c)

      if not passingFunctions(c): continue

      selectPhotons(c, c, False, (2 if args.selection.count('ll') else (1 if args.selection.count('lg') else 0)))
      if c.selectPhoton:
        if phoMva and c._phMva[c.ph] < (0.90 if phoMvaTight else 0.20):  continue
        if phoCBfull and not c._phCutBasedMedium[c.ph]:                  continue
        if abs(c._phEta[c.ph]) > 1.4442 and abs(c._phEta[c.ph]) < 1.566: continue
        if forward and abs(c._phEta[c.ph]) < 1.566:                      continue
        if central and abs(c._phEta[c.ph]) > 1.4442:                     continue

        if not checkSigmaIetaIeta(c, c.ph):        continue  # filter for sigmaIetaIeta sideband based on filter booleans (pass or fail)
        if not checkMatch(c, c.ph, oldDefinition): continue  # filter using AN15-165 definitions based on filter booleans (genuine, hadronicPhoton, misIdEle or hadronicFake)
        if not checkPrompt(c, c.ph):               continue  # filter using PAT matching definitions based on filter booleans (prompt or non-prompt)


      # Note: photon SF is 0 when pt < 20 GeV
      if not sample.isData: c.puWeight = puReweighting(c._nTrueInt)
      else: c._nTrueInt = -1
      eventWeight = 1. if sample.isData else (c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*(c.phWeight if c.selectPhoton and c._phPt[c.ph] > 20 else 1.)*c.bTagWeight*c.triggerWeight*lumiScale)

      for plot in plots+plots2D: plot.fill(sample, eventWeight)


#
# Drawing the plots
#
from ttg.tools.style import drawLumi
for plot in plots:
  if not args.showSys:
   plot.saveToCache(os.path.join(plotDir, args.tag, args.channel, args.selection), args.sys)
   if plot.name == "yield":
    log.info("Yields: ")
    for s,y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))

  extraArgs = {}
  if args.showSys:
    extraArgs['systematics']       = systematics
    extraArgs['linearSystematics'] = linearSystematics
    extraArgs['resultsDir']        = os.path.join(plotDir, args.tag, args.channel, args.selection)

  if args.channel!='noData' and not args.tag.count('singleLep'):
    extraArgs['ratio']   = {'yRange':(0.1,1.9), 'texY': 'data/MC'}

  if (sigmaieta or randomCone or args.tag.count('compareChannels')):
    extraArgs['scaling'] = 'unity'
    extraArgs['ratio']   = {'yRange':(0.1,1.9), 'texY':'ratio'}

  for logY in [False, True]:
    logTag = '-log' if logY else ''
    sysTag = '-sys' if args.showSys else ''
    plot.draw(plot_directory    = os.path.join(plotDir, args.tag, args.channel + logTag + sysTag, args.selection),
              logX              = False,
              logY              = logY,
              sorting           = True,
              yRange            = (0.003 if logY else 0.0001, "auto"),
              drawObjects       = drawLumi(None, lumiScale),
              **extraArgs
    )

if not args.sys:
  for plot in plots2D:
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ']:
        plot.draw(plot_directory = os.path.join(plotDir, args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScale))
log.info('Finished')
