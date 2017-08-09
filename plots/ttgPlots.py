#! /usr/bin/env python

#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--channel',        action='store',      default=None)
argParser.add_argument('--tag',            action='store',      default='eleCB-phoCB')
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,       help='do not launch subjobs')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


#
# Submit subjobs
#
if not args.isChild and args.selection is None:
  from ttg.tools.jobSubmitter import submitJobs
  selections = ['llg',
                'llg-looseLeptonVeto',
                'llg-looseLeptonVeto-mll40',
                'llg-looseLeptonVeto-offZ',
                'llg-looseLeptonVeto-offZ-llgNoZ',
                'llg-looseLeptonVeto-njet2p',
                'llg-looseLeptonVeto-mll40-offZ',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet3',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet4',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-btag1p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt40',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt60',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04-njet2p-btag1p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR04-gJetdR04-njet2p-deepbtag1p']

  selections = ['llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt40',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt60']

  if args.tag.count('QCD'):
    selections = ['pho','pho-njet1p','pho-njet2p','pho-njet2p-deepbtag1p','pho-njet2p-deepbtag1p-photonPt20','pho-njet2p-deepbtag1p-photonPt40','pho-njet2p-deepbtag1p-photonPt60']
  if args.channel:            channels = [args.channel]
  elif args.tag.count('QCD'): channels = ['noData']
  else:                       channels = ['ee','mumu','emu','SF','all','noData']
  for c in channels:
    if args.tag.count('sigmaIetaIeta') and (c=='noData' and not args.tag.count('QCD')): continue
    args.channel = c
    submitJobs(__file__, 'selection', selections, args, subLog=c)
  exit(0)


#
# Still very messy
#
import os, ROOT
from ttg.plots.plot           import Plot
from ttg.plots.plot2D         import Plot2D
from ttg.plots.cutInterpreter import cutInterpreter
from ttg.reduceTuple.objectSelection import photonSelector
from ttg.samples.Sample       import createStack
from math import pi

ROOT.gROOT.SetBatch(True)

if args.tag.count('split'):                            stackFile = 'split'
elif args.tag.count('ttbar'):                          stackFile = 'onlyttbar'
elif args.tag.count('match'):                          stackFile = 'match'
elif args.tag.count('prompt'):                         stackFile = 'prompt'
elif args.tag.count('DYLO'):                           stackFile = 'DY_LO'
elif args.tag.count('passSigmaIetaIetaMatch'):         stackFile = 'passSigmaIetaIetaMatch'
elif args.tag.count('failSigmaIetaIetaMatch'):         stackFile = 'failSigmaIetaIetaMatch'
elif args.tag.count('passSigmaIetaIeta'):              stackFile = 'passSigmaIetaIeta'
elif args.tag.count('failSigmaIetaIeta'):              stackFile = 'failSigmaIetaIeta'
elif args.tag.count('sigmaIetaIetaMC-evtType0'):       stackFile = 'sigmaIetaIeta-ttbar-eventType0'
elif args.tag.count('sigmaIetaIetaMC-evtType1'):       stackFile = 'sigmaIetaIeta-ttbar-eventType1'
elif args.tag.count('sigmaIetaIetaMC-evtType2'):       stackFile = 'sigmaIetaIeta-ttbar-eventType2'
elif args.tag.count('sigmaIetaIetaMC-hadronicPhoton'): stackFile = 'sigmaIetaIeta-ttbar-hadronicPhoton'
elif args.tag.count('sigmaIetaIetaMC'):
  if args.tag.count('powheg'):                         stackFile = 'sigmaIetaIeta-ttpow'
  else:                                                stackFile = 'sigmaIetaIeta-ttbar'
elif args.tag.count('sigmaIetaIetaQCD-nonprompt'):     stackFile = 'sigmaIetaIeta-QCD-nonprompt'
elif args.tag.count('sigmaIetaIetaQCD-evtType0'):      stackFile = 'sigmaIetaIeta-QCD-eventType0'
elif args.tag.count('sigmaIetaIetaQCD-evtType1'):      stackFile = 'sigmaIetaIeta-QCD-eventType1'
elif args.tag.count('sigmaIetaIetaQCD-evtType2'):      stackFile = 'sigmaIetaIeta-QCD-eventType2'
elif args.tag.count('sigmaIetaIetaQCD'):               stackFile = 'sigmaIetaIeta-QCD'
elif args.tag.count('randomConeCheck'):                stackFile = 'randomConeCheck'
elif args.tag.count('randomConeCheck'):                stackFile = 'randomConeCheck'
elif args.tag.count('sigmaIetaIeta'):                  stackFile = 'sigmaIetaIeta'
elif args.tag.count('powheg'):                         stackFile = 'powheg'
else:                                                  stackFile = 'default'

log.info('Using stackFile ' + stackFile)

stack = createStack(tuplesFile = os.path.join(os.environ['CMSSW_BASE'], 'src/ttg/samples/data/' + ('tuplesQCD.conf' if args.tag.count('QCD') else 'tuples.conf')),
                    styleFile  = os.path.join(os.environ['CMSSW_BASE'], 'src/ttg/samples/data', stackFile + '.stack'),
                    channel    = args.channel)

xAxisForYieldPlot = [lambda h : h.GetXaxis().SetBinLabel(1, "#mu#mu"),
                     lambda h : h.GetXaxis().SetBinLabel(2, "e#mu"),
                     lambda h : h.GetXaxis().SetBinLabel(3, "ee")]

phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
phoMva      = args.tag.count('phoMva')
phoMvaTight = args.tag.count('phoMvaTight')
eleCB       = args.tag.count('eleCB')
eleMva      = args.tag.count('eleMva')
sigmaieta   = args.tag.count('igmaIetaIeta')
forward     = args.tag.count('forward')
central     = args.tag.count('central')
useGap      = args.tag.count('gap')
randomCone  = args.tag.count('randomConeCheck')
match       = args.tag.count('match') or args.tag.count('hadronicPhoton')
promptCheck = args.tag.count('prompt')

plots = []
Plot.setDefaults(stack=stack, texY = '(1/N) dN/dx' if sigmaieta or randomCone else 'Events')

plots2D = []
Plot2D.setDefaults(stack=stack)

if randomCone:
  plots.append(Plot('photon_chargedIso',      'chargedIso(#gamma)',              lambda c : c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph],                  (20,0,20)))
  plots.append(Plot('photon_relChargedIso',   'chargedIso(#gamma)/p_{T}(#gamma)',lambda c : (c._phChargedIsolation[c.ph] if not c.data else c._phRandomConeChargedIsolation[c.ph])/c._phPt[c.ph],  (20,0,20)))

else:
  plots2D.append(Plot2D('chIso_vs_sigmaIetaIeta', 'chargedIso(#gamma)', lambda c : c._phChargedIsolation[c.ph], (20,0,20), '#sigma_{i#etai#eta}(#gamma)', lambda c : c._phSigmaIetaIeta[c.ph], (20,0,0.04)))

  plots.append(Plot('yield',                  'yield',                           lambda c : 1 if c.isMuMu else (2 if c.isEMu else 3),                                  (3, 0.5, 3.5)))
  plots.append(Plot('nVertex',                'vertex multiplicity',             lambda c : ord(c._nVertex),                                                           (50, 0, 50)))
  plots.append(Plot('nphoton',                'number of photons',               lambda c : sum([photonSelector(c, i, c) for i in range(ord(c._nPh))]),                (3, 0.5, 3.5)))
  plots.append(Plot('photon_pt',              'p_{T}(#gamma) (GeV)',             lambda c : c._phPt[c.ph],                                                             (20,15,115)))
  plots.append(Plot('photon_eta',             '|#eta|(#gamma)',                  lambda c : abs(c._phEta[c.ph]),                                                       (15,0,2.5)))
  plots.append(Plot('photon_phi',             '#phi(#gamma)',                    lambda c : c._phPhi[c.ph],                                                            (10,-pi,pi)))
  plots.append(Plot('photon_mva',             '#gamma-MVA',                      lambda c : c._phMva[c.ph],                                                            (20,-1,1)))
  plots.append(Plot('photon_chargedIso',      'chargedIso(#gamma)',              lambda c : c._phChargedIsolation[c.ph],                                               (20,0,20)))
  plots.append(Plot('photon_relChargedIso',   'chargedIso(#gamma)/p_{T}(#gamma)',lambda c : c._phChargedIsolation[c.ph]/c._phPt[c.ph],                                 (20,0,2)))
  plots.append(Plot('photon_neutralIso',      'neutralIso(#gamma)',              lambda c : c._phNeutralHadronIsolation[c.ph],                                         (25,0,5)))
  plots.append(Plot('photon_photonIso',       'photonIso(#gamma)',               lambda c : c._phPhotonIsolation[c.ph],                                                (32,0,8)))
  plots.append(Plot('photon_SigmaIetaIeta',   '#sigma_{i#etai#eta}(#gamma)',     lambda c : c._phSigmaIetaIeta[c.ph],                                                  (20,0,0.04)))
  plots.append(Plot('photon_hadOverEm',       'hadronicOverEm(#gamma)',          lambda c : c._phHadronicOverEm[c.ph],                                                 (20,0,.025)))
  if not args.tag.count('QCD'):
    plots.append(Plot('photon_randomConeIso',   'random cone chargedIso(#gamma)',  lambda c : c._phRandomConeChargedIsolation[c.ph],                                     (20,0,20)))
    plots.append(Plot('l1_pt',                  'p_{T}(l_{1}) (GeV)',              lambda c : c._lPt[c.l1],                                                              (20,0,200)))
    plots.append(Plot('l1_eta',                 '|#eta|(l_{1})',                   lambda c : abs(c._lEta[c.l1]),                                                        (15,0,2.4)))
    plots.append(Plot('l1_phi',                 '#phi(l_{1})',                     lambda c : c._lPhi[c.l1],                                                             (10,-pi,pi)))
    plots.append(Plot('l1_relIso',              'relIso(l_{1})',                   lambda c : c._relIso[c.l1],                                                           (10,0,0.12)))
    plots.append(Plot('l2_pt',                  'p_{T}(l_{2}) (GeV)',              lambda c : c._lPt[c.l2],                                                              (20,0,200)))
    plots.append(Plot('l2_eta',                 '|#eta|(l_{2})',                   lambda c : abs(c._lEta[c.l2]),                                                        (15,0,2.4)))
    plots.append(Plot('l2_phi',                 '#phi(l_{2})',                     lambda c : c._lPhi[c.l2],                                                             (10,-pi,pi)))
    plots.append(Plot('l2_relIso',              'relIso(l_{2})',                   lambda c : c._relIso[c.l2],                                                           (10,0,0.12)))
    plots.append(Plot('dl_mass',                'm(ll) (GeV)',                     lambda c : c.mll,                                                                     (40,0,200)))
    plots.append(Plot('l1g_mass',               'm(l_{1}#gamma) (GeV)',            lambda c : c.ml1g,                                                                    (40,0,200)))
    plots.append(Plot('l2g_mass',               'm(l_{2}#gamma) (GeV)',            lambda c : c.ml2g,                                                                    (40,0,200)))
    plots.append(Plot('phoPt_over_dlg_mass',    'p_{T}(#gamma)/m(ll#gamma)',       lambda c : c._phPt[c.ph]/c.mllg,                                                      (40,0,2)))
    plots.append(Plot('dlg_mass',               'm(ll#gamma) (GeV)',               lambda c : c.mllg,                                                                    (40,0,500)))
    plots.append(Plot('dlg_mass_zoom',          'm(ll#gamma) (GeV)',               lambda c : c.mllg,                                                                    (40,50,200)))
    plots.append(Plot('phL1DeltaR',             '#Delta R(#gamma, l_{1})',         lambda c : c.phL1DeltaR,                                                              (20,0,5)))
    plots.append(Plot('phL2DeltaR',             '#Delta R(#gamma, l_{2})',         lambda c : c.phL2DeltaR,                                                              (20,0,5)))
  plots.append(Plot('phLepDeltaR',            '#Delta R(#gamma, l)',             lambda c : c.phLepDeltaR,                                                             (20,0,5)))
  plots.append(Plot('phJetDeltaR',            '#Delta R(#gamma, j)',             lambda c : c.phJetDeltaR,                                                             (20,0,5)))
  plots.append(Plot('njets',                  'number of jets',                  lambda c : c.njets,                                                                   (8,0,8)))
  plots.append(Plot('nbtag',                  'number of medium b-tags (CSVv2)', lambda c : c.nbjets,                                                                  (4,0,4)))
  plots.append(Plot('j1_pt',                  'p_{T}(j_{1}) (GeV)',              lambda c : c._jetPt[c.j1]                                 if c.njets > 0 else -1,     (30,0,300)))
  plots.append(Plot('j1_eta',                 '|#eta|(j_{1})',                   lambda c : abs(c._jetEta[c.j1])                           if c.njets > 0 else -1,     (15,0,2.5)))
  plots.append(Plot('j1_phi',                 '#phi(j_{1})',                     lambda c : c._jetPhi[c.j1]                                if c.njets > 0 else -10,    (10,-pi,pi)))
  plots.append(Plot('j1_csvV2',               'CSVv2(j_{1})',                    lambda c : c._jetCsvV2[c.j1]                              if c.njets > 0 else -10,    (20, 0, 1)))
  plots.append(Plot('j1_deepCSV',             'deepCSV(j_{1})',                  lambda c : c._jetDeepCsv_b[c.j1] + c._jetDeepCsv_bb[c.j1] if c.njets > 0 else -10,    (20, 0, 1)))  # still buggy
  plots.append(Plot('j2_pt',                  'p_{T}(j_{2}) (GeV)',              lambda c : c._jetPt[c.j2]                                 if c.njets > 1 else -1,     (30,0,300)))
  plots.append(Plot('j2_eta',                 '|#eta|(j_{2})',                   lambda c : abs(c._jetEta[c.j2])                           if c.njets > 1 else -1,     (15,0,2.5)))
  plots.append(Plot('j2_phi',                 '#phi(j_{2})',                     lambda c : c._jetPhi[c.j2]                                if c.njets > 1 else -10,    (10,-pi,pi)))
  plots.append(Plot('j2_csvV2',               'CSVv2(j_{2})',                    lambda c : c._jetCsvV2[c.j2]                              if c.njets > 1 else -10,    (20, 0, 1)))
  plots.append(Plot('j2_deepCSV',             'deepCSV(j_{2})',                  lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2] if c.njets > 1 else -10,    (20, 0, 1)))

  if args.channel=='noData':
    plots.append(Plot('eventType',            'eventType',                       lambda c : c._ttgEventType,                                                                 (9, 0, 9)))
    if not args.tag.count('QCD'):
      plots.append(Plot('genPhoton_pt',         'p_{T}(gen #gamma) (GeV)',         lambda c : c._gen_phPt[c._phMatchMCPhotonAN15165[c.ph]] if c._phMatchMCPhotonAN15165[c.ph] > -1 else -1,     (10,10,110)))
      plots.append(Plot('genPhoton_eta',        '|#eta|(gen #gamma)',              lambda c : abs(c._gen_phEta[c._phMatchMCPhotonAN15165[c.ph]]) if c._phMatchMCPhotonAN15165[c.ph] > -1 else -1, (15,0,2.5)))


lumiScale = 35.9

cutString, passingFunctions = cutInterpreter.cutString(args.selection)
if not cutString: cutString = '(1)'
if args.channel=="ee":   cutString += '&&isEE'
if args.channel=="mumu": cutString += '&&isMuMu'
if args.channel=="emu":  cutString += '&&isEMu'

if eleMva:                  reduceType = 'eleMvaMedium'
elif args.tag.count('QCD'): reduceType = 'phoCB'
else:                       reduceType = 'eleCB-phoCB'


from ttg.reduceTuple.objectSelection import deltaR, looseLeptonSelector
from ttg.plots.photonCategories import isSignalPhoton, isHadronicPhoton, isGoodElectron, isHadronicFake
for sample in sum(stack, []):
  c = sample.initTree(reducedType = reduceType, skimType='singlePhoton' if args.tag.count('QCD') else 'dilep')
  c.QCD = args.tag.count('QCD')
  c.data = sample.texName.count('data')
  c.photonCutBased      = phoCB
  c.photonCutBasedTight = False
  c.photonMva           = phoMva
  for i in sample.eventLoop(cutString):
    c.GetEntry(i)
    if phoMva and c._phMva[c.ph] < (0.90 if phoMvaTight else 0.20): continue
    if phoCBfull and not c._phCutBasedMedium[c.ph]: continue

    if abs(c._phEta[c.ph]) > 1.4442 and abs(c._phEta[c.ph]) < 1.566: continue
    if forward and abs(c._phEta[c.ph]) < 1.566: continue
    if central and abs(c._phEta[c.ph]) > 1.4442: continue

    c.phLepDeltaR = 99
    for i in xrange(ord(c._nLight)):
      if not looseLeptonSelector(c, i): continue
      deltaR_ = deltaR(c._lEta[i], c._phEta[c.ph], c._lPhi[i], c._phPhi[c.ph])
      c.phLepDeltaR = min(c.phLepDeltaR, deltaR_)
    if c.phLepDeltaR < 0.1: continue

    if sigmaieta:
      upperCut = (0.01022 if abs(c._phEta[c.ph]) < 1.566 else  0.03001 )                      # forward region needs much higher cut
      lowerCut = (0.01022 if abs(c._phEta[c.ph]) < 1.566 else  0.03001 )                      # forward region needs much higher cut
      if useGap:
        upperCut = (0.01122 if abs(c._phEta[c.ph]) < 1.566 else  0.03201 )                      # forward region needs much higher cut
        lowerCut = (0.00922 if abs(c._phEta[c.ph]) < 1.566 else  0.03001 )                      # forward region needs much higher cut
      if   sample.texName.count('pass') and c._phSigmaIetaIeta[c.ph] > lowerCut: continue
      elif sample.texName.count('fail') and c._phSigmaIetaIeta[c.ph] < upperCut: continue
      if c._phSigmaIetaIeta[c.ph] > (0.016 if abs(c._phEta[c.ph]) < 1.566 else 0.04): continue


    if match:
      if sample.texName.count('genuine')        and not isSignalPhoton(c, c.ph):   continue
      if sample.texName.count('hadronicPhoton') and not isHadronicPhoton(c, c.ph): continue
      if sample.texName.count('misIdEle')       and not isGoodElectron(c, c.ph):   continue
      if sample.texName.count('hadronicFake')   and not isHadronicFake(c, c.ph):   continue

    if promptCheck:
      if sample.texName.count('non-prompt'):
        if c._phIsPrompt[c.ph]: continue
      elif sample.texName.count('prompt'):
        if not c._phIsPrompt[c.ph]: continue

    if not passingFunctions(c): continue

    # Note: photon SF is 0 when pt < 20 GeV
    if c.QCD:
      c.lWeight = 1.
      c.lTrackWeight = 1.
      c.triggerWeight = 1.
    eventWeight = 1. if sample.isData else c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*(c.phWeight if c._phPt[c.ph] > 20 else 1.)*c.bTagWeight*c.triggerWeight*lumiScale

    for plot in plots+plots2D: plot.fill(sample, eventWeight)


def drawObjects(dataMCScale, lumiScale):
  def drawTex(align, line):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(align)
    return tex.DrawLatex(*line)

  lines =[
    (11,(0.15, 0.95, 'CMS Preliminary')),
    (31,(0.95, 0.95, ('%3.1f fb{}^{-1} (13 TeV)'%lumiScale) + ('Scale %3.2f'%dataMCScale if dataMCScale else '')))
  ]
  return [drawTex(align, l) for align, l in lines]

import socket
baseDir = os.path.join('/afs/cern.ch/work/t/tomc/public/ttG/' if 'lxp' in socket.gethostname() else '/user/tomc/TTG/plots', args.tag)

for plot in plots2D:
  for log in [False, True]:
    for option in ['SCAT', 'COLZ']:
      plot.draw(plot_directory = os.path.join(baseDir, args.channel + ('-log' if log else ''), args.selection, option),
		logZ = False,
                drawOption = option,
		drawObjects = drawObjects(None, lumiScale))


for plot in plots:
  histModifications = []
  if plot.name == "yield":
    log.info("Yields: ")
    for s,y in plot.getYields().iteritems(): log.info('   ' + (s + ':').ljust(25) + str(y))
    histModifications += [lambda h : h.GetXaxis().SetBinLabel(1, "#mu#mu"),
                          lambda h : h.GetXaxis().SetBinLabel(2, "e#mu"),
                          lambda h : h.GetXaxis().SetBinLabel(3, "ee")]

  import socket
  baseDir = os.path.join('/afs/cern.ch/work/t/tomc/public/ttG/' if 'lxp' in socket.gethostname() else '/user/tomc/TTG/plots', args.tag)
  for log in [False, True]:
    plot.draw(plot_directory = os.path.join(baseDir, args.channel + ('-log' if log else ''), args.selection),
              ratio = None if (args.channel=='noData' and not (sigmaieta or randomCone)) else {'yRange':(0.1,1.9),'texY':('ratio' if sigmaieta or randomCone else 'data/MC')},
              logX = False, logY = log, sorting = True,
              yRange = (0.003, "auto") if log else (0.0001, "auto"),
              scaling = 'unity' if sigmaieta or randomCone else {},
              drawObjects = drawObjects(None, lumiScale),
              histModifications = histModifications,
    )
