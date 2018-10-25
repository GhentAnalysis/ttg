from ttg.tools.logger import getLogger, logLevel
log = getLogger()

from ttg.tools.helpers import plotDir
from ttg.tools.style import commonStyle, setDefault2D
import os,shutil,ROOT,socket


#
# Combine settings
#
release        = 'CMSSW_8_1_0'
arch           = 'slc6_amd64_gcc530'
version        = 'v7.0.10'


#
# Setup combine release and combineTool.py if not yet present, and returns its path
#
def getCombineRelease():
  combineRelease = os.path.abspath(os.path.expandvars(os.path.join('$CMSSW_BASE','..', release)))
  if not os.path.exists(combineRelease):
    log.info('Setting up combine release')
    setupCommand  = 'cd ' + os.path.dirname(combineRelease) + ';'
    setupCommand += 'export SCRAM_ARCH=' + arch + ';'
    setupCommand += 'source $VO_CMS_SW_DIR/cmsset_default.sh;' if 'lxp' not in socket.gethostname() else ''
    setupCommand += 'scramv1 project CMSSW ' + release + ';'
    setupCommand += 'cd ' + combineRelease + '/src;'
    setupCommand += 'eval `scramv1 runtime -sh`;'
    setupCommand += 'git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit;'
    setupCommand += 'cd HiggsAnalysis/CombinedLimit;'
    setupCommand += 'git fetch origin;git checkout ' + version + ';'
    setupCommand += 'scramv1 b clean;scramv1 b -j 8;'
    setupCommand += 'curl -s "https://raw.githubusercontent.com/cms-analysis/CombineHarvester/master/CombineTools/scripts/sparse-checkout-ssh.sh" | bash;'
    setupCommand += 'scramv1 b -j 8;'
    os.system(setupCommand)
  return combineRelease


#
# Handle a combine command
#
def handleCombine(dataCard, logFile, combineCommand, otherCommands = []):
  currentDir     = os.getcwd()
  combineRelease = getCombineRelease()
  os.system('rm ' + combineRelease + '/src/*.root &> /dev/null')
  log.debug('Moving to ' + combineRelease + ' to run combine')
  for f in [dataCard + '.txt', dataCard + '_shapes.root']:
    log.debug('Input file: ' + currentDir + '/combine/' + f)
    newPath = os.path.join(combineRelease, 'src', f)
    shutil.copy('combine/' + f, newPath)
  shutil.copy('../tools/python/diffNuisances.py', combineRelease + '/src/diffNuisances.py')
  os.system('cp $CMSSW_BASE/src/ttg/plots/data/sysMappings.json ' + combineRelease + '/src/CombineHarvester/CombineTools/scripts/sysMappings.json')
  os.chdir(os.path.join(combineRelease, 'src'))
  if logLevel(log, 'DEBUG'): combineCommand = combineCommand.replace('combine ', 'combine -v 2 ')
  os.system('(eval `scramv1 runtime -sh`; ' + combineCommand + ') &> ' + logFile + '.log')
  os.system('eval `scramv1 runtime -sh`;' + ';'.join(otherCommands))
  os.system('mv *' + dataCard + '* ' + currentDir + '/combine/')
  os.chdir(currentDir)


#
# Reads the fitted signal strength from the fitDiagnostics.root file
#
def getParam(filename, param):
  resultsFile = ROOT.TFile(filename)
  fitResults  = resultsFile.Get("fit_s").floatParsFinal()
  for r in [fitResults.at(i) for i in range(fitResults.getSize())]:
    if r.GetName() != param: continue
    result = (r.getVal(), r.getAsymErrorLo(), r.getAsymErrorHi())
    log.info('Result for ' + param + ': %.2f %.2f/+%.2f' % result)
    return result

def getMatrix(filename, type='covariance'):
  import json
  with open(os.path.expandvars('$CMSSW_BASE/src/ttg/plots/data/sysMappings.json')) as jsonFile:
    mappings = json.load(jsonFile)
  resultsFile = ROOT.TFile(filename)
  matrix      = resultsFile.Get("fit_s").covarianceMatrix() if type=='covariance' else resultsFile.Get("fit_s").correlationMatrix()
  results     = resultsFile.Get("fit_s").floatParsFinal()
  fitResults  = resultsFile.Get("fit_s").floatParsFinal()
  names       = [r.GetName() for r in [fitResults.at(i) for i in range(fitResults.getSize())]]
  names       = [(mappings[i] if i in mappings else i) for i in names]
  matrix   = ROOT.TH2D(matrix)
  for i in range(matrix.GetNbinsX()):
    matrix.GetXaxis().SetBinLabel(i+1, names[i])
  for j in range(matrix.GetNbinsY()):
    matrix.GetYaxis().SetBinLabel(j+1, names[j])
  setDefault2D()
  canvas = ROOT.TCanvas(type + 'Matrix', type + 'Matrix', 2000, 2000)
  canvas.SetRightMargin(0.15)
  commonStyle(matrix)
  matrix.GetXaxis().SetLabelSize(10)
  matrix.GetYaxis().SetLabelSize(10)
  matrix.SetMarkerSize(0.3)
  matrix.Draw("COLZ TEXT")
  canvas.Print(os.path.join(plotDir, 'combinePlots', filename.split('/')[-1].replace('.root', '_' + type + 'Matrix.png')))
  canvas.Print(os.path.join(plotDir, 'combinePlots', filename.split('/')[-1].replace('.root', '_' + type + 'Matrix.pdf')))

#
# Run fit diagnostics
#
def runFitDiagnostics(dataCard, trackParameters = [], toys = False, statOnly=False, alsoBOnly=False):
  extraOptions = ' --robustFit=1 --rMax=100 --cminDefaultMinimizerStrategy=2 --setRobustFitTolerance=0.001 --saveShapes --saveWithUncertainties'
  if toys:                 extraOptions += ' --expectSignal 1 -t -1'
  if statOnly:             extraOptions += ' --justFit --profilingMode=none -v 2'
  if not alsoBOnly:        extraOptions += ' --skipBOnlyFit'
  if len(trackParameters): extraOptions += ' --trackParameters ' + ','.join(trackParameters)
  if statOnly: logFile = dataCard + '_statOnly'
  elif toys:   logFile = dataCard + '_toys'
  else:        logFile = dataCard
  combineCommand = 'text2workspace.py ' + dataCard + '.txt;'
  combineCommand+= 'combine -M FitDiagnostics ' + extraOptions + ' ' + dataCard + '.root'
  otherCommands  = ['python diffNuisances.py             fitDiagnostics.root &> ' + dataCard + '_nuisances.txt',
                    'python diffNuisances.py -a          fitDiagnostics.root &> ' + dataCard + '_nuisances_full.txt',
                    'python diffNuisances.py    -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances.tex',
                    'python diffNuisances.py -a -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances_full.tex',
                    'cp fitDiagnostics.root ' + dataCard + '_fitDiagnostics.root'] if not statOnly else []
  log.info('Running FitDiagnostics' + (' (stat only)' if statOnly else ''))
  handleCombine(dataCard, logFile, combineCommand, otherCommands)
  if statOnly:
    with open('./combine/' + logFile + '.log') as f:
      resultCount = 0
      for line in f:
        if 'FinalValue +/-  Error' in line: resultCount += 1
        if resultCount==2 and '<none>' in line:
          log.info('Stat result for r: %s %s %s' % tuple(line.split()[2:5]))
          break
  else:
    try:
      diagnosticsFile = './combine/' + dataCard + '_fitDiagnostics' + ('_stat' if statOnly else '') + '.root'
      getMatrix(diagnosticsFile, 'covariance')
      getMatrix(diagnosticsFile, 'correlation')
      return {param : getParam(diagnosticsFile, param) for param in ['r']+trackParameters}
    except:
      with open('./combine/' + logFile + '.log') as f:
        for line in f: log.warning(line.rstrip())


#
# Run significance
#
def runSignificance(dataCard, expected=False):
  command = 'combine -M Significance ' + dataCard + '.txt'
  logFile = dataCard + '_sig' + ('_expected' if expected else '')
  if expected: command += ' -t -1 --expectSignal=1'
  log.info('Running Significance')
  handleCombine(dataCard, logFile, command)
  with open('./combine/' + logFile + '.log') as f:
    for line in f:
      if 'Significance:' in line:
        log.info(line.rstrip() + (' (expected)' if expected else ''))


#
# Run impacts
#
def runImpacts(dataCard, perPage=30, toys=False):
  extraArg = ' -t -1 --expectSignal=1' if toys else ''
  command  = 'text2workspace.py ' + dataCard + '.txt -m 125;'
  command += 'mv ' + dataCard + '.root CombineHarvester/CombineTools/scripts;'
  command += 'cd CombineHarvester/CombineTools/scripts;'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root --doInitialFit' + extraArg + ';'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root --doFits --parallel 8' + extraArg + ';'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root -o impacts.json' + extraArg + ';'
  command += './plotImpacts.py -i impacts.json --per-page=' + str(perPage) + ' --cms-label preliminary --translate sysMappings.json -o impacts;'
  command += 'mv impacts.pdf ../../../' + dataCard + '_impacts' + ('_asimov' if toys else '') + '.pdf'
  log.info('Running Impacts')
  handleCombine(dataCard, dataCard + '_impacts', command)
  with open('./combine/' + dataCard + '_impacts.log') as f:
    for line in f:
      if "mv: cannot stat `impacts.pdf': No such file or directory" in line: log.error("Problem with running impacts")
      log.debug(line.rstrip())
  os.system("pdftoppm combine/" + dataCard + "_impacts" + ('_asimov' if toys else '') + ".pdf " + dataCard + "_impacts" + ('_asimov' if toys else '') + " -png;mogrify -trim " + dataCard + "_impacts*.png")
  os.system("mkdir -p ~/www/ttG/combinePlots/")
  os.system("cp $CMSSW_BASE/src/ttg/tools/php/index.php ~/www/ttG/combinePlots/")
  os.system("mv " + dataCard + "_impacts*.png ~/www/ttG/combinePlots/")


#
# Goodness of fit
#
def goodnessOfFit(dataCard, algo='saturated'):
  command  = 'combine -M GoodnessOfFit ' + dataCard + '.txt --algo=' + algo + ';'
  command += 'combine -M GoodnessOfFit ' + dataCard + '.txt --algo=' + algo + ' -t 1000' + (' --toysFreq' if algo=='saturated' else '') + ';'
  log.info('Running goodness of fit')
  handleCombine(dataCard, dataCard + '_gof', command)
  with open('./combine/' + dataCard + '_gof.log') as f:
    for line in f:
      log.debug(line.rstrip())


#
# Write the card including all systematics and shapes
#
def writeCard(cardName, shapes, templates, templatesNoSys, extraLines, systematics, linearSystematics, scaleShape = {}):
  def tab(list, column='12'):
    return ''.join(['%25s' % list[0]] + [(('%'+column+'s') % i) for i in list[1:]]) + '\n'

  def linSys(info, template):
    if template not in templates: return '-'
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
    f.write('shapes * * '+cardName+'_shapes.root $CHANNEL/$PROCESS $CHANNEL$SYSTEMATIC/$PROCESS'+'\n')
    f.write('-'*400 + '\n')
    f.write(tab(['bin']+shapes))
    f.write(tab(['observation']+['-1']*len(shapes)))
    f.write('-'*400 + '\n')
    f.write(tab(['bin','']    + [s    for s in shapes for t in templates+templatesNoSys]))
    f.write(tab(['process','']+ [t    for s in shapes for t in templates+templatesNoSys]))
    f.write(tab(['process','']+ [t    for s in shapes for t in range(len(templates+templatesNoSys))]))
    f.write(tab(['rate','']+    ['-1' for s in shapes for t in templates+templatesNoSys]))
    f.write('-'*400 + '\n')

    for sys, info in linearSystematics.iteritems():
      f.write(tab([sys, 'lnN'] + [linSys(info, t) for s in shapes for t in templates+templatesNoSys]))

    for sys in systematics:
      if ':' in sys:
        try:         sample, shape, sys   = sys.split(':')
        except:      (sample, sys), shape = sys.split(':'), None
      else:          sample, shape, sys   = None, None, sys
      f.write(tab([sys, 'shape'] + [('-' if (sample and t!=sample) or t in templatesNoSys or (shape and s != shape) else ('%.4f' % scaleShape[sys] if sys in scaleShape else '1')) for s in shapes for t in templates+templatesNoSys]))

    f.write('-'*400 + '\n')
    for extraLine in extraLines:
      f.write(tab([x for x in extraLine.split()], column='18'))
