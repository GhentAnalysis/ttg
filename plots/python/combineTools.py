from ttg.tools.logger import getLogger, logLevel
log = getLogger()

import os,shutil,ROOT 

#
# Combine settings
#
release        = 'CMSSW_8_1_0'
arch           = 'slc6_amd64_gcc530'
version        = 'v7.0.6'

#
# Setup function for combine
#
def getCombineRelease():
  combineRelease = os.path.abspath(os.path.expandvars(os.path.join('$CMSSW_BASE','..', release)))
  if not os.path.exists(combineRelease):
    log.info('Setting up combine release')
    setupCommand  = 'cd ' + os.path.dirname(combineRelease) + ';'
    setupCommand += 'export SCRAM_ARCH=' + arch + ';'
    setupCommand += 'source $VO_CMS_SW_DIR/cmsset_default.sh;'
    setupCommand += 'scramv1 project CMSSW ' + version + ';'
    setupCommand += 'cd ' + combineRelease + '/src;'
    setupCommand += 'git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit;'
    setupCommand += 'cd HiggsAnalysis/CombinedLimit;'
    setupCommand += 'git fetch origin;git checkout ' + version + ';'
    setupCommand += 'eval `scramv1 runtime -sh`;scramv1 b clean;scramv1 b;'
    os.system(setupCommand)
  return combineRelease

#
# Run the maximum likelihood fit
#
def runMaximumLikelihoodFit(fileName):
  log.info('Running fit')
  os.system('(eval `scramv1 runtime -sh`;combine -M FitDiagnostics ' + fileName + '.txt)' + ('' if logLevel(log, 'DEBUG') else (' &> ' + fileName + '.log')))
  with open(fileName + '.log') as f:
    for line in f: log.warning(line.rstrip())
#
# Reads the fitted signal strength from the mlfit.root file
#
def getSignalStrength(filename):
  resultsFile = ROOT.TFile(filename)
  fitResults  = resultsFile.Get("fit_s").floatParsFinal()
  for r in [fitResults.at(i) for i in range(fitResults.getSize())]:
    if r.GetName() != 'r': continue
    result = (r.getVal(), r.getAsymErrorLo(), r.getAsymErrorHi())
    log.info('Result: %.2f %.2f/+%.2f' % result)
    return result

#
# Complete combine chain
#
def handleCombine(dataCard):
  currentRelease = os.getcwd()
  combineRelease = getCombineRelease()
  log.info('Moving to ' + combineRelease + ' to run combine')
  for f in [dataCard + '.txt', dataCard + '.root']:
    shutil.move(f, os.path.join(combineRelease, 'src', f))
  os.chdir(os.path.join(combineRelease, 'src'))

  runMaximumLikelihoodFit(dataCard)
  result = getSignalStrength('mlfit.root')
  shutil.move('mlfit.root', dataCard + '_results.root')
  os.chdir(currentRelease)
  return result

