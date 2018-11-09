defaultSelections = ['llg-looseLeptonVeto-mll40-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag2p-photonPt20',
                     ]

onZSelections     = ['llg-looseLeptonVeto-mll40-njet1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-signalRegion-photonPt20:SYS',
                     'llg-looseLeptonVeto-mll40-orOnZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-onZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20:SYS,POST',
                     ]

diffSelections    = ['llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20to30',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt30to50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phJetDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phJetDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phJetDeltaR1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phLepDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phLepDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-phLepDeltaR1',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20to30',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt30to50',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt50',
                     ]

dilepSelections   = ['ll-looseLeptonVeto-mll40-offZ:SYS',
                     'll-looseLeptonVeto-mll40-offZ-nphoton0:SYS',
                     'll-looseLeptonVeto-mll40-offZ-njet2p',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-nphoton0',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p-nphoton0'
                     ]



def getVariations(args, sysList):
  if args.selection:                                                 selections = [args.selection]
  elif not args.tag.count('pho') and args.tag.count('eleSusyLoose'): selections = dilepSelections
  elif args.tag=='eleSusyLoose-phoCBfull':                           selections = [(s+':SYS,POST') for s in defaultSelections + onZSelections] + diffSelections
  elif args.tag.count('phoCBfull'):                                  selections = defaultSelections + onZSelections
  else:                                                              selections = defaultSelections

  # When running sys or post-fit plots, reduce the selection
  if args.runSys or args.showSys: selections = [s for s in selections if 'SYS'  in s]
  if args.post:                   selections = [s for s in selections if 'POST' in s]
  selections = [s.split(':')[0] for s in selections]

  if args.channel:                        channels = [args.channel]
  elif args.tag.count('compareChannels'): channels = ['all']
  elif args.tag.count('splitOverlay'):    channels = ['noData']
  elif args.tag.count('randomConeCheck'): channels = ['ee','mumu','emu','SF','all']
  elif args.tag.count('igmaIetaIeta'):    channels = ['ee','mumu','emu','SF','all']
  else:                                   channels = ['ee','mumu','emu','SF','all','noData']

  variations = []
  for s in sysList:
    for c in channels:
      if c != 'SF' and c != 'noData': selections_ = [sel for sel in selections if not (('onZ' in sel) or ('OnZ' in sel))]
      else:                           selections_ = selections
      variations += [(sel, c, s) for sel in selections_]

  return ('selection', 'channel', 'sys'), variations
