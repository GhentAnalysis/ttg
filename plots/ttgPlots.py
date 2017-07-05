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
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-btag1p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR07',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR07-gJetdR07',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR07-gJetdR07-njet2p',
                'llg-looseLeptonVeto-mll40-offZ-llgNoZ-gLepdR07-gJetdR07-njet2p-btag1p']
  for c in ['ee','mumu','emu','SF','all','noData'] if not args.channel else [args.channel]:
    if args.tag.count('sigmaIetaIeta') and c=='noData': continue
    args.channel = c
    submitJobs(__file__, 'selection', selections, args, subLog=c)
  exit(0)


#
# Still very messy
#
import os, ROOT
from ttg.plots.plot           import Plot
from ttg.plots.cutInterpreter import cutInterpreter
from ttg.reduceTuple.objectSelection import photonSelector
from ttg.samples.Sample       import createStack
from math import pi

ROOT.gROOT.SetBatch(True)

if args.tag.count('split'):           stackFile = 'split'
elif args.tag.count('ttbar'):         stackFile = 'onlyttbar'
elif args.tag.count('sigmaIetaIeta'): stackFile = 'sigmaIetaIeta'
else:                                 stackFile = 'default'

stack = createStack(tuplesFile = os.path.join(os.environ['CMSSW_BASE'], 'src/ttg/samples/data/tuples.conf'),
                    styleFile  = os.path.join(os.environ['CMSSW_BASE'], 'src/ttg/samples/data', stackFile + '.stack'),
                    channel    = args.channel)


xAxisForYieldPlot = [lambda h : h.GetXaxis().SetBinLabel(1, "#mu#mu"),
                     lambda h : h.GetXaxis().SetBinLabel(2, "e#mu"),
                     lambda h : h.GetXaxis().SetBinLabel(3, "ee")]

plots = []
Plot.setDefaults(stack=stack)
plots.append(Plot('yield',                  'yield',                           lambda c : 1 if c.isMuMu else (2 if c.isEMu else 3),                                  (3, 0.5, 3.5)))
plots.append(Plot('nVertex',                'vertex multiplicity',             lambda c : ord(c._nVertex),                                                           (50, 0, 50)))
plots.append(Plot('nphoton',                'number of photons',               lambda c : sum([photonSelector(c, i, c) for i in range(ord(c._nPh))]),                (3, 0.5, 3.5)))
plots.append(Plot('photon_pt',              'p_{T}(#gamma) (GeV)',             lambda c : c._phPt[c.ph],                                                             (10,20,220)))
plots.append(Plot('photon_eta',             '|#eta|(#gamma)',                  lambda c : abs(c._phEta[c.ph]),                                                       (15,0,2.5)))
plots.append(Plot('photon_phi',             '#phi(#gamma)',                    lambda c : c._phPhi[c.ph],                                                            (10,-pi,pi)))
plots.append(Plot('photon_mva',             '#gamma-MVA',                      lambda c : c._phMva[c.ph],                                                            (20,-1,1)))
plots.append(Plot('photon_chargedIso',      'chargedIso(#gamma)',              lambda c : c._phChargedIsolation[c.ph],                                               (20,0,20)))
plots.append(Plot('photon_neutralIso',      'neutralIso(#gamma)',              lambda c : c._phNeutralHadronIsolation[c.ph],                                         (25,0,5)))
plots.append(Plot('photon_photonIso',       'photonIso(#gamma)',               lambda c : c._phPhotonIsolation[c.ph],                                                (32,0,8)))
plots.append(Plot('photon_SigmaIetaIeta',   '#sigma_{i#etai#eta}(#gamma)',     lambda c : c._phSigmaIetaIeta[c.ph],                                                  (20,0,0.04)))
plots.append(Plot('photon_hadOverEm',       'hadronicOverEm(#gamma)',          lambda c : c._phHadronicOverEm[c.ph],                                                 (20,0,.025)))
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
plots.append(Plot('dlg_mass',               'm(ll#gamma) (GeV)',               lambda c : c.mllg,                                                                    (40,0,500)))
plots.append(Plot('dlg_mass_zoom',          'm(ll#gamma) (GeV)',               lambda c : c.mllg,                                                                    (40,50,200)))
plots.append(Plot('phL1DeltaR',             '#Delta R(#gamma, l_{1})',         lambda c : c.phL1DeltaR,                                                              (20,0,5)))
plots.append(Plot('phL2DeltaR',             '#Delta R(#gamma, l_{2})',         lambda c : c.phL2DeltaR,                                                              (20,0,5)))
plots.append(Plot('phLepDeltaR',            '#Delta R(#gamma, l)',             lambda c : min(c.phL1DeltaR, c.phL2DeltaR),                                           (20,0,5)))
plots.append(Plot('phJetDeltaR',            '#Delta R(#gamma, j)',             lambda c : c.phJetDeltaR,                                                             (20,0,5)))
plots.append(Plot('njets',                  'number of jets',                  lambda c : c.njets,                                                                   (8,0,8)))
plots.append(Plot('nbtag',                  'number of medium b-tags (CSVv2)', lambda c : c.nbjets,                                                                  (4,0,4)))
plots.append(Plot('j1_pt',                  'p_{T}(j_{1}) (GeV)',              lambda c : c._jetPt[c.j1]                                 if c.njets > 0 else -1,     (30,0,300)))
plots.append(Plot('j1_eta',                 '|#eta|(j_{1})',                   lambda c : abs(c._jetEta[c.j1])                           if c.njets > 0 else -1,     (15,0,2.5)))
plots.append(Plot('j1_phi',                 '#phi(j_{1})',                     lambda c : c._jetPhi[c.j1]                                if c.njets > 0 else -10,    (10,-pi,pi)))
plots.append(Plot('j1_csvV2',               'CSVv2(j_{1})',                    lambda c : c._jetCsvV2[c.j1]                              if c.njets > 0 else -10,    (20, 0, 1)))
#plots.append(Plot('j1_deepCSV',             'deepCSV(j_{1})',                  lambda c : c._jetDeepCsv_b[c.j1] + c._jetDeepCsv_bb[c.j1] if c.njets > 0 else -10,    (20, 0, 1)))  # still buggy
plots.append(Plot('j2_pt',                  'p_{T}(j_{2}) (GeV)',              lambda c : c._jetPt[c.j2]                                 if c.njets > 1 else -1,     (30,0,300)))
plots.append(Plot('j2_eta',                 '|#eta|(j_{2})',                   lambda c : abs(c._jetEta[c.j2])                           if c.njets > 1 else -1,     (15,0,2.5)))
plots.append(Plot('j2_phi',                 '#phi(j_{2})',                     lambda c : c._jetPhi[c.j2]                                if c.njets > 1 else -10,    (10,-pi,pi)))
plots.append(Plot('j2_csvV2',               'CSVv2(j_{2})',                    lambda c : c._jetCsvV2[c.j2]                              if c.njets > 1 else -10,    (20, 0, 1)))
#plots.append(Plot('j2_deepCSV',             'deepCSV(j_{2})',                  lambda c : c._jetDeepCsv_b[c.j2] + c._jetDeepCsv_bb[c.j2] if c.njets > 1 else -10,    (20, 0, 1)))

if args.channel=='noData':
  plots.append(Plot('eventType',            'eventType',                       lambda c : c._ttgEventType,                               (9, 0, 9)))


lumiScale = 35.9

phoCB       = args.tag.count('phoCB')
phoCBfull   = args.tag.count('phoCBfull')
phoMva      = args.tag.count('phoMva')
phoMvaTight = args.tag.count('phoMvaTight')
eleCB       = args.tag.count('eleCB')
eleMva      = args.tag.count('eleMva')
sigmaieta   = args.tag.count('sigmaIetaIeta')
forward     = args.tag.count('forward')
central     = args.tag.count('central')

cutString, passingFunctions = cutInterpreter.cutString(args.selection)
if not cutString: cutString = '(1)'
if args.channel=="ee":   cutString += '&&isEE'
if args.channel=="mumu": cutString += '&&isMuMu'
if args.channel=="emu":  cutString += '&&isEMu'




for sample in sum(stack, []):
  c = sample.initTree(reducedType = 'eleMvaMedium' if eleMva else 'eleCB-phoCB')
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

    if sigmaieta:
      cut = (0.01022 if abs(c._phEta[c.ph]) < 1.566 else  0.03001 )                      # forward region needs much higher cut
      if   sample.texName.count('pass') and c._phSigmaIetaIeta[c.ph] > cut: continue
      elif sample.texName.count('fail') and c._phSigmaIetaIeta[c.ph] < cut: continue

    if sample.name.count('DY') and args.selection.count('njet'): continue # statistics too low
    if not passingFunctions(c): continue

    eventWeight = 1. if sample.isData else c.genWeight*c.puWeight*c.lWeight*c.lTrackWeight*c.phWeight*c.triggerWeight*lumiScale

    for plot in plots: plot.fill(sample, eventWeight)


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


for plot in plots:
  histModifications = []
  if plot.name == "yield":
    histModifications += [lambda h : h.GetXaxis().SetBinLabel(1, "#mu#mu"),
                          lambda h : h.GetXaxis().SetBinLabel(2, "e#mu"),
                          lambda h : h.GetXaxis().SetBinLabel(3, "ee")]

  baseDir = '/user/tomc/TTG/plots/' + args.tag
  for log in [False, True]:
    plot.draw(plot_directory = os.path.join(baseDir + '/' + args.channel + ('-log' if log else '') + '/' + args.selection),
              ratio = None if args.channel=='noData' else {'yRange':(0.1,1.9)}, 
              logX = False, logY = log, sorting = True, 
              yRange = (0.003, "auto"),
              scaling = {1:0} if sigmaieta else {},
              drawObjects = drawObjects(None, lumiScale),
              histModifications = histModifications,
    )
