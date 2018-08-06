defaultSelections = ['llg-looseLeptonVeto-mll40-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag2p-photonPt20',
                     ]

onZSelections     = ['llg-looseLeptonVeto-mll40-njet1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-signalRegion-photonPt20',
                     'llg-looseLeptonVeto-mll40-orOnZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-onZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet1-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet1-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p-deepbtag1-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p-deepbtag2p-photonPt20',
                     ]

qcdSelections     = ['pho-photonPt20',
                     'pho-njet1p-photonPt20',
                     'pho-njet2p-photonPt20',
                     'pho-njet2p-deepbtag1p-photonPt20',
                     ]

dilepSelections   = ['ll-looseLeptonVeto-mll40', 
                     'll-looseLeptonVeto-mll40-offZ', 
                     'll-looseLeptonVeto-mll40-offZ-njet2p', 
                     'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p']

silepSelections   = ['lg-looseLeptonVeto-photonPt20',
                     'lg-looseLeptonVeto-njet3p-photonPt20', 
                     'lg-looseLeptonVeto-njet4p-photonPt20', 
                     'lg-looseLeptonVeto-njet4p-deepbtag1p-photonPt20', 
                     'lg-looseLeptonVeto-njet4p-deepbtag2p-photonPt20']

def getVariations(args, sysList):
  if args.selection:                                                 selections = [args.selection]
  elif args.tag.count('QCD'):                                        selections = qcdSelections
  elif args.tag.count('singleLep'):                                  selections = silepSelections
  elif not args.tag.count('pho') and args.tag.count('eleSusyLoose'): selections = dilepSelections
  elif args.tag.count('phoCBfull'):                                  selections = defaultSelections+onZSelections
  else:                                                              selections = defaultSelections

  if args.channel:                        channels = [args.channel]
  elif args.tag.count('compareChannels'): channels = ['all']
  elif args.tag.count('QCD'):             channels = ['noData']
  elif args.tag.count('splitOverlay'):    channels = ['noData']
  elif args.tag.count('singleLep'):       channels = ['e','mu','noData']
  elif args.tag.count('randomConeCheck'): channels = ['ee','mumu','emu','SF','all']
  elif args.tag.count('igmaIetaIeta'):    channels = ['ee','mumu','emu','SF','all']
  else:                                   channels = ['ee','mumu','emu','SF','all','noData']

  variations = []
  for s in sysList:
    for c in channels:
      if c != 'SF': selections_ = [sel for sel in selections if not (('onZ' in sel) or ('OnZ' in sel))]
      else:         selections_ = selections
      variations += [(sel, c, s) for sel in selections_]

  return ('selection', 'channel', 'sys'), variations
