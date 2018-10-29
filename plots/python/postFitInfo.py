from ttg.tools.logger import getLogger, logLevel
log = getLogger()
import ROOT, os
from ttg.plots.systematics import rateParameters

def mapName(name):
  if name=='r': return 'TTGamma_norm'
  else:         return name

def getPullsAndConstraints(dataCard = 'srFit'):
  pullsAndConstraints = {}
  filename    = os.path.expandvars('$CMSSW_BASE/src/ttg/plots/combine/' + dataCard + '_fitDiagnostics.root')
  resultsFile = ROOT.TFile(filename)
  fitResults  = resultsFile.Get("fit_s").floatParsFinal()
  for r in [fitResults.at(i) for i in range(fitResults.getSize())]:
    pullsAndConstraints[mapName(r.GetName())] = (r.getVal(), r.getAsymErrorHi())
  return pullsAndConstraints

#
# Applying post-fit values, given a dictionary of sample --> histogram or pkl-histname --> histogram
#
def applyPostFitScaling(histos, postFitInfo):
  pullsAndConstraints = getPullsAndConstraints(postFitInfo)
  for i in pullsAndConstraints:
    if 'norm' in i:
      for sample, h in histos.iteritems():
        try:    match = sample.name.count(i.split('_')[0]) or sample.texName.count(i.split('_')[0])
        except: match = sample.count(i.split('_')[0])
        if match:
          value = pullsAndConstraints[i][0]
          h.Scale(value)
          try:    log.debug('Applying post-fit scaling value of ' + str(value) + ' to ' + sample.name)
          except: log.debug('Applying post-fit scaling value of ' + str(value) + ' to ' + sample)
          break
      else:
        log.warning('Could not find where to apply post-fit scaling for ' + i)


