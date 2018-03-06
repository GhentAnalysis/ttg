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
# Setup combine release if not yet present, and returns its path
#
def getCombineRelease():
  combineRelease = os.path.abspath(os.path.expandvars(os.path.join('$CMSSW_BASE','..', release)))
  if not os.path.exists(combineRelease):
    log.info('Setting up combine release')
    setupCommand  = 'cd ' + os.path.dirname(combineRelease) + ';'
    setupCommand += 'export SCRAM_ARCH=' + arch + ';'
    setupCommand += 'source $VO_CMS_SW_DIR/cmsset_default.sh;'
    setupCommand += 'scramv1 project CMSSW ' + release + ';'
    setupCommand += 'cd ' + combineRelease + '/src;'
    setupCommand += 'git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit;'
    setupCommand += 'cd HiggsAnalysis/CombinedLimit;'
    setupCommand += 'git fetch origin;git checkout ' + version + ';'
    setupCommand += 'eval `scramv1 runtime -sh`;scramv1 b clean;scramv1 b;'
    os.system(setupCommand)
  return combineRelease

#
# Handle a combine command
#
def handleCombine(dataCard, combineCommand, otherCommands = []):
  currentDir     = os.getcwd()
  combineRelease = getCombineRelease()
  log.info('Moving to ' + combineRelease + ' to run combine')
  for f in [dataCard + '.txt', dataCard + '.root']:
    log.info('Input file: ' + currentDir + '/combine/' + f)
    newPath = os.path.join(combineRelease, 'src', f)
    shutil.copy('combine/' + f, newPath)
  shutil.copy('../tools/python/diffNuisances.py', combineRelease + '/src/diffNuisances.py')
  os.chdir(os.path.join(combineRelease, 'src'))
  if logLevel(log, 'DEBUG'): verbosity = '-v 2'
  else:                      verbosity = '-v 0'
  os.system('(eval `scramv1 runtime -sh`; combine ' + verbosity + ' ' + combineCommand + ') &> ' + dataCard + '.log')
  os.system('mv *' + dataCard + '* ' + currentDir + '/combine/')
  os.system('eval `scramv1 runtime -sh`;' + ';'.join(otherCommands))
  os.chdir(currentDir)

#
# Reads the fitted signal strength from the fitDiagnostics.root file
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
# Run fit diagnostics
#
def runFitDiagnostics(dataCard, trackParameters = [], toys = None, statOnly=False):
  extraOptions = ''
  if toys:                 extraOptions += ' --toysFrequentist --noErrors --minos none --expectSignal 1 -t ' + str(toys)
  if statOnly:             extraOptions += ' --justFit --profilingMode=none'
  if len(trackParameters): extraOptions += ' --trackParameters ' + ','.join(trackParameters)
  combineCommand = '-M FitDiagnostics ' + extraOptions + ' ' + dataCard + '.txt'
  otherCommands  = ['python diffNuisances.py             fitDiagnostics.root &> ' + dataCard + '_nuisances.txt',
                    'python diffNuisances.py -a          fitDiagnostics.root &> ' + dataCard + '_nuisances_full.txt',
                    'python diffNuisances.py    -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances.tex',
                    'python diffNuisances.py -a -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances_full.tex',
                    'mv fitDiagnostics.root ' + dataCard + '_fitDiagnostics.root']
  log.info('Running FitDiagnostics')
  handleCombine(dataCard, combineCommand, otherCommands)
  try:
    result = getSignalStrength('./combine/' + dataCard + '_fitDiagnostics.root')
    return result
  except:
    with open('./combine/' + dataCard + '.log') as f:
      for line in f: log.warning(line.rstrip())

  return None

#
# Run significance
#
def runSignificance(dataCard, expected=False):
  command = '-M Significance ' + dataCard + '.txt'
  if expected: command += ' -t -1 --expectSignal=1'
  handleCombine(dataCard, command)
  with open('./combine/' + dataCard + '.log') as f:
    for line in f: log.info(line.rstrip())


#
# Run impacts (really need to find some real documentation for this)
#
def runImpacts(dataCard):
  command  = '-M MultiDimFit -n initialFit --algo singles ????????????'
  handleCombine(dataCard, command)
  with open('./combine/' + dataCard + '.log') as f:
    for line in f: log.info(line.rstrip())

# Write the card including all systematics and shapes
def writeCard(cardName, shapes, templates, extraLines, systematics, mcStatistics, linearSystematics):
  def tab(list):
    return ''.join(['%25s' % list[0]] + [('%12s' % i) for i in list[1:]]) + '\n'

  def linSys(info, template):
    sample, value = info
    value = 1+value/100.
    if sample:
      if template.count(sample): return value
      else:                      return '-'
    else:                        return value

  with open('combine/' + cardName + '.txt', 'w') as f:
    f.write('imax ' + str(len(shapes)) + '\n')
    f.write('jmax *\n')
    f.write('kmax *\n')
    f.write('-'*400 + '\n')
    f.write('shapes * * '+cardName+'.root $CHANNEL/$PROCESS $CHANNEL$SYSTEMATIC/$PROCESS'+'\n')
    f.write('-'*400 + '\n')
    f.write(tab(['bin']+shapes))
    f.write(tab(['observation']+['-1']*len(shapes)))
    f.write('-'*400 + '\n')
    f.write(tab(['bin','']    + [s    for s in shapes for i in range(len(templates))]))
    f.write(tab(['process','']+ [t    for i in range(len(shapes)) for t in templates]))
    f.write(tab(['process','']+ [t    for i in range(len(shapes)) for t in range(len(templates))]))
    f.write(tab(['rate','']+    ['-1' for i in range(len(shapes)) for t in range(len(templates))]))
    f.write('-'*400 + '\n')
    for sys, info in linearSystematics.iteritems():
      f.write(tab([sys, 'lnN'] + [linSys(info, t) for i in range(len(shapes)) for t in range(len(templates))]))
    for sys in [s.replace('Up','') for s in systematics if 'Up' in s]:
      f.write(tab([sys, 'shape'] + ['1' for i in range(len(shapes)) for t in range(len(templates))]))
    for sys in sorted(mcStatistics):
      f.write(tab([sys, 'shape'] + [('1' if sys.count(shapes[i]) and sys.count(templates[t]) else '-') for i in range(len(shapes)) for t in range(len(templates))]))
    f.write('-'*400 + '\n')
    for extraLine in extraLines:
      f.write(tab([x for x in extraLine.split()]))
