#! /usr/bin/env python
import ROOT, glob

eventTypes = None
for sample in ['TTJets_DiLept','TTJets_SingleLeptFromT','TT_TuneCUETP8M2T4','TTGamma_Dilept','TTGamma_SingleLept','TTGamma_Hadronic']:
  for f in glob.glob('/pnfs/iihe/cms/store/user/tomc/heavyNeutrino/'+sample+'*/*v26a/*/*/dilep_*.root'):
    f = ROOT.TFile(f)
    if not eventTypes: eventTypes   = f.Get('blackJackAndHookers/eventTypes')
    else:              eventTypes.Add(f.Get('blackJackAndHookers/eventTypes'))
  try:
    total   = eventTypes.Integral(0, 10)
    step1   = eventTypes.Integral(2, 10)
    step2   = eventTypes.Integral(3, 10)
    overlap = eventTypes.Integral(4, 10)
    print sample + ('\t1.\t%s%%' % str(float(step1)/float(total)*100))
    print sample + ('\t2.\t%s%%' % str(float(step2)/float(total)*100))
    print sample + ('\t3.\t%s%%' % str(float(overlap)/float(total)*100))
    print
  except:
    pass
