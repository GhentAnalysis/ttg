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
def handleCombine(dataCard, trackParameters = []):
  currentRelease = os.getcwd()
  combineRelease = getCombineRelease()
  log.info('Moving to ' + combineRelease + ' to run combine')
  for f in [dataCard + '.txt', dataCard + '.root']:
    shutil.move(f, os.path.join(combineRelease, 'src', f))
  os.chdir(os.path.join(combineRelease, 'src'))

  log.info('Running fit')
  os.system('(eval `scramv1 runtime -sh`;combine -M FitDiagnostics --skipBOnlyFit --trackParameters ' + ','.join(trackParameters) + ' ' + dataCard + '.txt)' + ('' if logLevel(log, 'DEBUG') else (' &> ' + dataCard + '.log')))
  try:
    result = getSignalStrength('fitDiagnostics.root')
  except:
    with open(dataCard + '.log') as f:
      for line in f: log.warning(line.rstrip())
  shutil.move('fitDiagnostics.root', dataCard + '_results.root')
  os.chdir(currentRelease)
  return result




# Temporary, should become way more complicated function or class to handle systematics
def writeCard(cardName, shapes, templates, extraLines):
  def tab(list):
    return ''.join([('%11s' % i) for i in list]) + '\n'

  with open(cardName + '.txt', 'w') as f:
    f.write('imax ' + str(len(shapes)) + '\n')
    f.write('jmax *\n')
    f.write('kmax *\n')
    f.write('-'*300 + '\n')
    f.write('shapes * * '+cardName+'.root $CHANNEL/$PROCESS $CHANNEL/$PROCESS_$SYSTEMATIC'+'\n')
    f.write('-'*300 + '\n')
    f.write(tab(['bin']+shapes))
    f.write(tab(['observation']+['-1']*len(shapes)))
    f.write('-'*300 + '\n')
    f.write(tab(['bin']    + [s    for s in shapes for i in range(len(templates))]))
    f.write(tab(['process']+ [t    for i in range(len(shapes)) for t in templates]))
    f.write(tab(['process']+ [t    for i in range(len(shapes)) for t in range(len(templates))]))
    f.write(tab(['rate']+    ['-1' for i in range(len(shapes)) for t in range(len(templates))]))
    f.write('-'*200 + '\n')
    for x in extraLines:
      f.write(x + '\n')
