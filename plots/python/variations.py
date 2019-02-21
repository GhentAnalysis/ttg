defaultSelections = ['llg-looseLeptonVeto-mll40-photonPt20',
                     'llg-looseLeptonVeto-mll40-signalRegion-photonPt20:SYS',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt30',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt40',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt60',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt70',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet1-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag0-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-njet2p-deepbtag2p-photonPt20',
                     'llg-looseLeptonVeto-mll40-orOnZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-onZ-photonPt20',
                     'llg-looseLeptonVeto-mll40-llgOnZ-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20:SYS,POST',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet1p',
                     'llg-looseLeptonVeto-mll40-llgOnZ-njet2p',
                     ]

diffSelections    = ['llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20to30',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt30to50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phJetDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phJetDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phJetDeltaR1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phLepDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phLepDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20-phLepDeltaR1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phJetDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phJetDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phJetDeltaR1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phLepDeltaR0to0.4',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phLepDeltaR0.4to1',
                     'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt50-phLepDeltaR1',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt20to30',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt30to50',
                     'llg-looseLeptonVeto-mll40-llgOnZ-signalRegion-photonPt50',
                     ]

dilepSelections   = ['ll-looseLeptonVeto-mll40-offZ:SYS',
                     'll-looseLeptonVeto-mll40-offZ-nphoton0:SYS',
                     'll-looseLeptonVeto-mll40-offZ-signalRegion:SYS',
                     'll-looseLeptonVeto-mll40-offZ-signalRegion-nphoton0:SYS',
                     'll-looseLeptonVeto-mll40-offZ-njet2p',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-nphoton0',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p',
                     'll-looseLeptonVeto-mll40-offZ-njet2p-deepbtag1p-nphoton0'
                     ]

#
# Get the selections to consider for a given tag/channel
# On-Z selection only retained for SF/noData with the default phoCBfull tag
# When running sys or post-fit plots, reduce the selection
#
def getSelections(tag, channel, sys, post):
  if not tag.count('pho') and tag.count('eleSusyLoose'): selections = dilepSelections
  elif tag == 'compareWithTT':                           selections = [i for i in dilepSelections if 'photon' not in i]
  elif tag == 'eleSusyLoose-phoCBfull':                  selections = [(s+':SYS,POST') for s in defaultSelections] + diffSelections
  else:                                                  selections = defaultSelections

  if channel not in ['SF', 'noData'] or not tag.count('phoCBfull'):
    selections = [s for s in selections if not s.lower().count('onz')]

  if sys:  selections = [s for s in selections if 'SYS'  in s]
  if post: selections = [s for s in selections if 'POST' in s]

  return [s.split(':')[0] for s in selections]

#
# Get the (selection, channel, sys) variations to consider for the ttgPlots.py script
#
def getVariations(args, sysList):
  if args.channel:                        channels = [args.channel]
  elif args.tag.count('compareChannels'): channels = ['all']
  elif args.tag.count('splitOverlay'):    channels = ['noData']
  elif args.tag.count('randomConeCheck'): channels = ['ee', 'mumu', 'emu', 'SF', 'all']
  elif args.tag.count('igmaIetaIeta'):    channels = ['ee', 'mumu', 'emu', 'SF', 'all']
  else:                                   channels = ['ee', 'mumu', 'emu', 'SF', 'all', 'noData']

  variations = []
  for c in channels:
    if args.selection: selections = [args.selection]
    else:              selections = getSelections(args.tag, c, args.runSys or args.showSys, args.post)
    variations += [(sel, c, s) for sel in selections for s in sysList]

  return ('selection', 'channel', 'sys'), variations
