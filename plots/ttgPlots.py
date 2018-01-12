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
argParser.add_argument('--filterPlot',     action='store',      default=None)
argParser.add_argument('--runSys',         action='store_true', default=False)
argParser.add_argument('--showSys',        action='store_true', default=False)
argParser.add_argument('--editInfo',       action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--runWillem',      action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
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
from ttg.plots.systematics import systematics, linearSystematics, applySysToTree, applySysToString
if args.sys=='None': args.sys=None
if not (args.runSys or (args.showSys and args.isChild)): systematics = {}



#
# Submit subjobs
#
if not args.isChild and (args.selection is None or args.channel is None):
  updateGitInfo()
  from ttg.tools.jobSubmitter import submitJobs

  if args.selection:
    selections = [args.selection]
  else:
    selections = ['llg',
                  'llg-looseLeptonVeto',
                  'llg-looseLeptonVeto-mll40',
                  'llg-looseLeptonVeto-mll40-offZ',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gJetdR02-njet2p-deepbtag1p',
                  'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gJetdR04-njet2p-deepbtag1p',
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
  elif args.tag.count('randomConeCheck'): channels = ['ee','mumu','emu','SF','all']
  else:                                   channels = ['ee','mumu','emu','SF','all','noData']
  for s in ['None'] + systematics.keys():
    for c in channels:
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

# reduce string comparisons in loop --> store as booleans
phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
forward     = args.tag.count('forward')
central     = args.tag.count('central')
zeroLep     = args.tag.count('QCD')
singleLep   = args.tag.count('singleLep')
normalize   = args.tag.count('igmaIetaIeta') or args.tag.count('randomConeCheck')




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
if args.tag.count('sigmaIetaIetaMatchMC'):   stackFile = 'sigmaIetaIetaMatchMC'    # for some strange reason the glob.glob does noet always find this
if args.tag.count('randomConeCheckMatchMC'): stackFile = 'randomConeCheckMatchMC'  # for some strange reason the glob.glob does noet always find this

log.info('Using stackFile ' + stackFile)

if zeroLep:     tuples = 'tuplesQCD.conf'
elif singleLep: tuples = 'tuplesSingleLep.conf'
else:           tuples = 'tuples.conf'

stack = createStack(tuplesFile = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + tuples),
                    styleFile  = os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/' + stackFile + '.stack'),
                    channel    = args.channel)


#
# Define plots
#

plots = []
Plot.setDefaults(stack=stack, texY = '(1/N) dN/dx' if normalize else 'Events')
Plot2D.setDefaults(stack=stack)

def channelNumbering(c):
  if singleLep: return (1 if c.isMu else 2)
  else:         return (1 if c.isMuMu else (2 if c.isEMu else 3))

if args.tag.count('randomConeCheck'):
  plots.append(Plot('photon_chargedIso',      'chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (20,0,20)))
  plots.append(Plot('photon_chargedIso_small','chargedIso(#gamma) (GeV)',         lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph]),               (80,0,20)))
  plots.append(Plot('photon_relChargedIso',   'chargedIso(#gamma)/p_{T}(#gamma)', lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c._phPt[c.ph], (20,0,2)))
else:
  plots.append(Plot2D('chIso_vs_sigmaIetaIeta', 'chargedIso(#gamma) (GeV)', lambda c : c._phChargedIsolation[c.ph], (20,0,20), '#sigma_{i#etai#eta}(#gamma)', lambda c : c._phSigmaIetaIeta[c.ph], (20,0,0.04)))

  plots.append(Plot('yield',                      'yield',                                lambda c : channelNumbering(c),                                (3, 0.5, 2.5 if singleLep else 3.5), histModifications=xAxisLabels(['#mu','e'] if singleLep else ['#mu#mu', 'e#mu', 'ee'])))
  plots.append(Plot('nVertex',                    'vertex multiplicity',                  lambda c : ord(c._nVertex),                                    (50, 0, 50)))
  plots.append(Plot('nTrueInt',                   'nTrueInt',                             lambda c : c._nTrueInt,                                        (50, 0, 50)))
  plots.append(Plot('nphoton',                    'number of photons',                    lambda c : c.nphotons,                                         (4, -0.5, 3.5)))
  plots.append(Plot('photon_pt',                  'p_{T}(#gamma) (GeV)',                  lambda c : c._phPt[c.ph],                                      (20,15,115)))
  plots.append(Plot('photon_eta',                 '|#eta|(#gamma)',                       lambda c : abs(c._phEta[c.ph]),                                (15,0,2.5)))
  plots.append(Plot('photon_phi',                 '#phi(#gamma)',                         lambda c : c._phPhi[c.ph],                                     (10,-pi,pi)))
  plots.append(Plot('photon_mva',                 '#gamma-MVA',                           lambda c : c._phMva[c.ph],                                     (20,-1,1)))
  plots.append(Plot('photon_chargedIso',          'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        (20,0,20)))
  plots.append(Plot('photon_chargedIso_NO',       'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        (20,0,20), overflowBin=None))
  plots.append(Plot('photon_chargedIso_bins',     'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441,1,2,3,5,10,20], normBinWidth=1, texY=('(1/N) dN / GeV' if normalize else 'Events / GeV')))
  plots.append(Plot('photon_chargedIso_bins_NO',  'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        [0, 0.441,1,2,3,5,10,20], normBinWidth=1, texY=('(1/N) dN / GeV' if normalize else 'Events / GeV'), overflowBin=None))
  plots.append(Plot('photon_chargedIso_small',    'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        (80,0,20)))
  plots.append(Plot('photon_chargedIso_small_NO', 'chargedIso(#gamma) (GeV)',             lambda c : c._phChargedIsolation[c.ph],                        (80,0,20), overflowBin=None))
  plots.append(Plot('photon_relChargedIso',       'chargedIso(#gamma)/p_{T}(#gamma)',     lambda c : c._phChargedIsolation[c.ph]/c._phPt[c.ph],          (20,0,2)))
  plots.append(Plot('photon_neutralIso',          'neutralIso(#gamma) (GeV)',             lambda c : c._phNeutralHadronIsolation[c.ph],                  (25,0,5)))
  plots.append(Plot('photon_photonIso',           'photonIso(#gamma) (GeV)',              lambda c : c._phPhotonIsolation[c.ph],                         (32,0,8)))
  plots.append(Plot('photon_SigmaIetaIeta',       '#sigma_{i#etai#eta}(#gamma)',          lambda c : c._phSigmaIetaIeta[c.ph],                           (20,0,0.04)))
  plots.append(Plot('photon_hadOverEm',           'hadronicOverEm(#gamma)',               lambda c : c._phHadronicOverEm[c.ph],                          (20,0,.025)))
  plots.append(Plot('phJetDeltaR',                '#Delta R(#gamma, j)',                  lambda c : c.phJetDeltaR,                                      (20,0,5)))
  plots.append(Plot('l1_pt',                      'p_{T}(l_{1}) (GeV)',                   lambda c : c._lPt[c.l1],                                       (20,0,200)))
  plots.append(Plot('l1_eta',                     '|#eta|(l_{1})',                        lambda c : abs(c._lEta[c.l1]),                                 (15,0,2.4)))
  plots.append(Plot('l1_phi',                     '#phi(l_{1})',                          lambda c : c._lPhi[c.l1],                                      (10,-pi,pi)))
  plots.append(Plot('l1_relIso',                  'relIso(l_{1})',                        lambda c : c._relIso[c.l1],                                    (10,0,0.12)))
  plots.append(Plot('l2_pt',                      'p_{T}(l_{2}) (GeV)',                   lambda c : c._lPt[c.l2],                                       (20,0,200)))
  plots.append(Plot('l2_eta',                     '|#eta|(l_{2})',                        lambda c : abs(c._lEta[c.l2]),                                 (15,0,2.4)))
  plots.append(Plot('l2_phi',                     '#phi(l_{2})',                          lambda c : c._lPhi[c.l2],                                      (10,-pi,pi)))
  plots.append(Plot('l2_relIso',                  'relIso(l_{2})',                        lambda c : c._relIso[c.l2],                                    (10,0,0.12)))
  plots.append(Plot('dl_mass',                    'm(ll) (GeV)',                          lambda c : c.mll,                                              (40,0,200)))
  plots.append(Plot('ll_deltaPhi',                '#Delta#phi(ll)',                       lambda c : deltaPhi(c._lPhi[c.l1], c._lPhi[c.l2]),             (10,0,pi)))
  plots.append(Plot('photon_randomConeIso',       'random cone chargedIso(#gamma) (Gev)', lambda c : c._phRandomConeChargedIsolation[c.ph],              (20,0,20)))
  plots.append(Plot('l1g_mass',                   'm(l_{1}#gamma) (GeV)',                 lambda c : c.ml1g,                                             (40,0,200)))
  plots.append(Plot('phL1DeltaR',                 '#Delta R(#gamma, l_{1})',              lambda c : c.phL1DeltaR,                                       (20,0,5)))
  plots.append(Plot('l2g_mass',                   'm(l_{2}#gamma) (GeV)',                 lambda c : c.ml2g,                                             (40,0,200)))
  plots.append(Plot('phL2DeltaR',                 '#Delta R(#gamma, l_{2})',              lambda c : c.phL2DeltaR,                                       (20,0,5)))
  plots.append(Plot('phoPt_over_dlg_mass',        'p_{T}(#gamma)/m(ll#gamma)',            lambda c : c._phPt[c.ph]/c.mllg,                               (40,0,2)))
  plots.append(Plot('dlg_mass',                   'm(ll#gamma) (GeV)',                    lambda c : c.mllg,                                             (40,0,500)))
  plots.append(Plot('dlg_mass_zoom',              'm(ll#gamma) (GeV)',                    lambda c : c.mllg,                                             (40,50,200)))
  plots.append(Plot('phLepDeltaR',                '#Delta R(#gamma, l)',                  lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                    (20,0,5)))
  plots.append(Plot('njets',                      'number of jets',                       lambda c : c.njets,                                            (8,0,8)))
  plots.append(Plot('nbtag',                      'number of medium b-tags (deepCSV)',    lambda c : c.ndbjets,                                          (4,0,4)))
  plots.append(Plot('j1_pt',                      'p_{T}(j_{1}) (GeV)',                   lambda c : c._jetPt[c.j1],                                     (30,30,330)))
  plots.append(Plot('j1_eta',                     '|#eta|(j_{1})',                        lambda c : abs(c._jetEta[c.j1]),                               (15,0,2.4)))
  plots.append(Plot('j1_phi',                     '#phi(j_{1})',                          lambda c : c._jetPhi[c.j1],                                    (10,-pi,pi)))
  plots.append(Plot('j1_csvV2',                   'CSVv2(j_{1})',                         lambda c : c._jetCsvV2[c.j1],                                  (20, 0, 1)))
  plots.append(Plot('j1_deepCSV',                 'deepCSV(j_{1})',                       lambda c : c._jetDeepCsv_b[c.j1] + c._jetDeepCsv_bb[c.j1],     (20, 0, 1)))
  plots.append(Plot('j2_pt',                      'p_{T}(j_{2}) (GeV)',                   lambda c : c._jetPt[c.j2],                                     (30,30,330)))
  plots.append(Plot('j2_eta',                     '|#eta|(j_{2})',                        lambda c : abs(c._jetEta[c.j2]),                               (15,0,2.4)))
  plots.append(Plot('j2_phi',                     '#phi(j_{2})',                          lambda c : c._jetPhi[c.j2],                                    (10,-pi,pi)))
  plots.append(Plot('j2_csvV2',                   'CSVv2(j_{2})',                         lambda c : c._jetCsvV2[c.j2],                                  (20, 0, 1)))
  plots.append(Plot('j2_deepCSV',                 'deepCSV(j_{2})',                       lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2],     (20, 0, 1)))
  plots.append(Plot('eventType',                  'eventType',                            lambda c : ord(c._ttgEventType),                               (9, 0, 9)))
  plots.append(Plot('genPhoton_pt',               'p_{T}(gen #gamma) (GeV)',              lambda c : c._phTTGMatchPt[c.ph],                              (10,10,110)))
  plots.append(Plot('genPhoton_eta',              '|#eta|(gen #gamma)',                   lambda c : abs(c._phTTGMatchEta[c.ph]),                        (15,0,2.5), overflowBin=None))
  plots.append(Plot('photonCategory',             'photonCategory',                       lambda c : photonCategoryNumber(c, c.ph),                      (4, 0.5, 4.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake'])))
  plots.append(Plot('photonCategoryOld',          'photonCategory (AN-15-165 def)',       lambda c : photonCategoryNumber(c, c.ph, oldDefinition=True),  (4, 0.5, 4.5), histModifications=xAxisLabels(['genuine', 'misIdEle', 'hadronic', 'fake'])))


if args.filterPlot:
  plots[:] = [p for p in plots if args.filterPlot in p.name]

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
  if args.channel=="SF":   cutString += '&&(isMuMu||isEE)'
  if args.channel=="emu":  cutString += '&&isEMu'
  if args.channel=="e":    cutString += '&&isE'
  if args.channel=="mu":   cutString += '&&isMu'

  if   args.tag.count('QCD'):                                                       reduceType = 'phoCB'
  elif args.tag.count('eleSusyLoose') and not args.tag.count('eleSusyLoose-phoCB'): reduceType = 'eleSusyLoose'
  else:                                                                             reduceType = 'eleSusyLoose-phoCB'

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


    c.data = sample.isData

    # Filter booleans
    oldDefinition       = args.tag.count('oldMatch')
    c.genuine           = sample.texName.count('genuine')
    c.hadronicPhoton    = sample.texName.count('hadronicPhoton')
    c.misIdEle          = sample.texName.count('misIdEle')
    c.hadronicFake      = sample.texName.count('hadronicFake')
    c.nonprompt         = sample.texName.count('non-prompt')
    c.prompt            = sample.texName.count('prompt') and not sample.texName.count('non-prompt')
    c.failSigmaIetaIeta = sample.texName.count('fail')
    c.passSigmaIetaIeta = sample.texName.count('pass') or args.tag.count("noChgIso")

    selectPhoton        = args.selection.count('llg') or args.tag.selection('lg')

    for i in sample.eventLoop(cutString):
      c.GetEntry(i)
      if zeroLep:
        c.lWeight = 1.
        c.lTrackWeight = 1.
        c.triggerWeight = 1.
      elif not sample.isData and args.sys:
        applySysToTree(args.sys, c)

      if not passingFunctions(c): continue

      if selectPhoton:
        if phoCBfull and not c._phCutBasedMedium[c.ph]:                  continue
        if forward and abs(c._phEta[c.ph]) < 1.566:                      continue
        if central and abs(c._phEta[c.ph]) > 1.4442:                     continue

        if not checkSigmaIetaIeta(c, c.ph):        continue  # filter for sigmaIetaIeta sideband based on filter booleans (pass or fail)
        if not checkMatch(c, c.ph, oldDefinition): continue  # filter using AN15-165 definitions based on filter booleans (genuine, hadronicPhoton, misIdEle or hadronicFake)
        if not checkPrompt(c, c.ph):               continue  # filter using PAT matching definitions based on filter booleans (prompt or non-prompt)

      if not (selectPhoton and c._phPt[c.ph] > 20): c.phWeight  = 1.                             # Note: photon SF is 0 when pt < 20 GeV
      if not sample.isData:                         c.puWeight  = puReweighting(c._nTrueInt)
      else:                                         c._nTrueInt = None

      if sample.isData: eventWeight = 1.
      else:             eventWeight = c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.bTagWeight*c.triggerWeight*lumiScale

      toRemove = []
      for plot in plots:
        try:
          plot.fill(sample, eventWeight)
        except:
          toRemove.append(plot)
          log.info('Not considering plot ' + plot.name + ' for this selection')
      for p in toRemove: plots.remove(p)


#
# Drawing the plots
#
from ttg.tools.style import drawLumi
for plot in plots: # 1D plots
  if isinstance(plot, Plot2D): continue
  if not args.showSys:
   plot.saveToCache(os.path.join(plotDir, args.tag, args.channel, args.selection), args.sys)
   if plot.name == "yield":
    log.info("Yields: ")
    for s,y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))

  extraArgs   = {}
  normalizeToMC = [False,True] if args.channel!='noData' else [False]
  if args.showSys:
    extraArgs['systematics']       = systematics
    extraArgs['linearSystematics'] = linearSystematics
    extraArgs['resultsDir']        = os.path.join(plotDir, args.tag, args.channel, args.selection)

  if args.channel!='noData' and not args.tag.count('singleLep'):
    extraArgs['ratio']   = {'yRange':(0.1,1.9), 'texY': 'data/MC'}

  if(normalize or args.tag.count('compareChannels')):
    extraArgs['scaling'] = 'unity'
    extraArgs['ratio']   = {'yRange':(0.1,1.9), 'texY':'ratio'}
    normalizeToMC        = [False]

  for norm in normalizeToMC:
    if norm: extraArgs['scaling'] = {0:1}
    for logY in [False, True]:
      extraTag  = '-log'    if logY else ''
      extraTag += '-sys'    if args.showSys else ''
      extraTag += '-normMC' if norm else ''
      plot.draw(plot_directory    = os.path.join(plotDir, args.tag, args.channel + extraTag, args.selection),
                logX              = False,
                logY              = logY,
                sorting           = True,
                yRange            = (0.003 if logY else 0.0001, "auto"),
                drawObjects       = drawLumi(None, lumiScale),
                **extraArgs
      )

if not args.sys:
  for plot in plots: # 2D plots
    if isinstance(plot, Plot): continue
    for logY in [False, True]:
      for option in ['SCAT', 'COLZ']:
        plot.draw(plot_directory = os.path.join(plotDir, args.tag, args.channel + ('-log' if logY else ''), args.selection, option),
                  logZ           = False,
                  drawOption     = option,
                  drawObjects    = drawLumi(None, lumiScale))
log.info('Finished')
