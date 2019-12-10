from ttg.tools.logger import getLogger, logLevel
log = getLogger()

from ttg.tools.helpers import plotDir, plotCombineDir
from ttg.tools.style import commonStyle, setDefault2D
import os, shutil, ROOT, socket, json, math

import numpy as np
import root_numpy as rnp
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

# Combine documentation:
# http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/

#
# Combine settings
#
release        = 'CMSSW_10_2_13'
arch           = 'slc7_amd64_gcc700'
version        = 'v8.0.1'

#
# Setup combine release and combineTool.py if not yet present, and returns its path
#
def initCombineTools(year, doCleaning=False, run='combine'):

    if doCleaning: os.system('rm -rf ' + run)
    
    if doCleaning: os.system('rm -rf ' + os.path.join(plotCombineDir, year, run))
    os.system('mkdir -p ' + os.path.join(plotCombineDir, year, run))
    
    indexFile = '$CMSSW_BASE/src/ttg/tools/php/index.php'
    if not os.path.exists(indexFile): os.system('cp ' + indexFile + ' ' + os.path.join(plotCombineDir, year, run + '/'))

def getCombineRelease():
  combineRelease = os.path.abspath(os.path.expandvars(os.path.join('$CMSSW_BASE', '..', release)))
  if not os.path.exists(combineRelease):
    log.info('Setting up combine release')
    log.info('This might not work on T2B, recommended release is now on SLC7, which only available on lxplus')
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
def handleCombine(dataCard, logFile, combineCommand, otherCommands = None, run='combine'):
    
    currentDir     = os.getcwd()
    combineRelease = getCombineRelease()
    os.system('rm ' + combineRelease + '/src/*.root &> /dev/null')
    log.debug('Moving to ' + combineRelease + ' to run combine')
    for f in [dataCard + '.txt', dataCard + '_shapes.root']:
        log.debug('Input file: ' + currentDir + '/' + run + '/' + f)
        newPath = os.path.join(combineRelease, 'src', f)
        shutil.copy(run + '/' + f, newPath)
    shutil.copy('../tools/python/diffNuisances.py', combineRelease + '/src/diffNuisances.py')
    os.system('cp $CMSSW_BASE/src/ttg/plots/data/sysMappings.json ' + combineRelease + '/src/CombineHarvester/CombineTools/scripts/sysMappings.json')
    os.chdir(os.path.join(combineRelease, 'src'))
    if logLevel(log, 'DEBUG'): combineCommand = combineCommand.replace('combine ', 'combine -v 2 ')
    os.system('(eval `scramv1 runtime -sh`; ' + combineCommand + ') &> ' + logFile + '.log')
    os.system('eval `scramv1 runtime -sh`;' + ';'.join(otherCommands) if otherCommands else '')
    os.system('mv *' + dataCard + '* ' + currentDir + '/' + run + '/')
    os.chdir(currentDir)

#
# Run fit diagnostics
# Disable pylint "too many branches" until CMSSW has a recent pylint version which takes nested functions into account
#
def runFitDiagnostics(dataCard, year, trackParameters = None, toys = False, toyR = 1, statOnly=False, alsoBOnly=False, mode='exp', run='combine'):
    
    def getParam(filename, param):
        
        resultsFile = ROOT.TFile(filename)
        fitResults  = resultsFile.Get("fit_s").floatParsFinal()
        
        for r in [fitResults.at(i) for i in range(fitResults.getSize())]:
            
            if r.GetName() != param: continue
            result = (r.getVal(), r.getAsymErrorLo(), r.getAsymErrorHi())
            log.info('Result for ' + param + ': %.2f %.2f/+%.2f' % result)
            
            return result

    def getMatrix(filename, matrixType='covariance'):

        with open(os.path.expandvars('$CMSSW_BASE/src/ttg/plots/data/sysMappings.json')) as jsonFile:
            mappings = json.load(jsonFile)
            resultsFile = ROOT.TFile(filename)
            matrix      = resultsFile.Get("fit_s").covarianceMatrix() if matrixType=='covariance' else resultsFile.Get("fit_s").correlationMatrix()
            fitResults  = resultsFile.Get("fit_s").floatParsFinal()
            names       = [r.GetName() for r in [fitResults.at(i) for i in range(fitResults.getSize())]]
            names       = [(mappings[i] if i in mappings else i) for i in names]
            matrix   = ROOT.TH2D(matrix)
            
        for i in range(matrix.GetNbinsX()):
            matrix.GetXaxis().SetBinLabel(i+1, names[i])
        for j in range(matrix.GetNbinsY()):
            matrix.GetYaxis().SetBinLabel(j+1, names[j])
            
        setDefault2D()
        canvas = ROOT.TCanvas(matrixType + 'Matrix', matrixType + 'Matrix', 2000, 2000)
        canvas.SetRightMargin(0.15)
        commonStyle(matrix)
        matrix.GetXaxis().SetLabelSize(10)
        matrix.GetYaxis().SetLabelSize(10)
        matrix.SetMarkerSize(0.3)
        matrix.Draw("COLZ TEXT")
        
        plotName = 'statOnly_'+mode if statOnly else 'statSys_'+mode
        plotName = 'Matrix_' + plotName
        canvas.Print(os.path.join(plotCombineDir, year, run + '/', filename.split('/')[-1].replace('.root', '_' + matrixType + plotName + '.png')))
        canvas.Print(os.path.join(plotCombineDir, year, run + '/', filename.split('/')[-1].replace('.root', '_' + matrixType + plotName + '.pdf')))

    def getStatResult(logFile):
        with open('./' + run + '/' + logFile + '.log') as f:
            resultCount = 0
            for line in f:
                if 'FinalValue +/-  Error' in line: resultCount += 1
                if resultCount == 2 and '<none>' in line:
                    log.info('Stat result for r: %s %s %s' % tuple(line.split()[2:5]))
                    break
 
    def analyzeDiagnosticsFile(diagnosticsFile, logFile):
        try:
            getMatrix(diagnosticsFile, 'covariance')
            getMatrix(diagnosticsFile, 'correlation')
            return {param : getParam(diagnosticsFile, param) for param in ['r']+trackParameters}
        except:
            with open('./' + run + '/' + logFile + '.log') as f:
                for line in f: log.warning(line.rstrip())

    # Main block of runFitDiagnostics
    extraOptions = ' --robustFit=1 --rMax=10 --cminDefaultMinimizerStrategy=2 --setRobustFitTolerance=0.001 --saveShapes --saveWithUncertainties'
    if toys:            extraOptions += ' --expectSignal ' + str(toyR) + ' -t -1'
    if statOnly:        extraOptions += ' --justFit --profilingMode=none -v 2'
##    if statOnly:        extraOptions += ' --justFit --freezeParameters='+ ','.join(trackParameters) + ' -v 2'
    if not alsoBOnly:   extraOptions += ' --skipBOnlyFit'
    if trackParameters: extraOptions += ' --trackParameters ' + ','.join(trackParameters)

    if statOnly: logFile = dataCard + '_statOnly'
    elif toys:   logFile = dataCard + '_toys'
    else:        logFile = dataCard

    combineCommand  = 'text2workspace.py ' + dataCard + '.txt;'
    combineCommand += 'combine -M FitDiagnostics ' + extraOptions + ' ' + dataCard + '.root' + ' --saveWorkspace'
    print combineCommand
    
    otherCommands   = ['python diffNuisances.py             fitDiagnostics.root &> ' + dataCard + '_nuisances.txt',
                       'python diffNuisances.py -a          fitDiagnostics.root &> ' + dataCard + '_nuisances_full.txt',
                       'python diffNuisances.py    -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances.tex',
                       'python diffNuisances.py -a -f latex fitDiagnostics.root &> ' + dataCard + '_nuisances_full.tex',
                       'cp fitDiagnostics.root ' + dataCard + '_fitDiagnostics.root'] if not statOnly else []
                       
    log.info('Running FitDiagnostics' + (' (stat only)' if statOnly else ''))
    handleCombine(dataCard, logFile, combineCommand, otherCommands, run=run)
    currentDir = os.getcwd()
    combineRelease = getCombineRelease()
    inFileName = combineRelease+'/src/higgsCombineTest.FitDiagnostics.mH120.root'
    outFileName = currentDir+'/'+run+'/'+dataCard+'_FitDiag'
    if statOnly:
        outFileName += '_StatOnly'
        if toys:
            outFileName += '_Exp.root'
        else:
            outFileName += '_Obs.root'
    else:
        outFileName += '_StatSys'
        if toys:
            outFileName += '_Exp.root'
        else:
            outFileName += '_Obs.root'
        
    os.system('cp '+inFileName+' '+outFileName)

    if statOnly: 
        getStatResult(logFile)
    else:        
        return analyzeDiagnosticsFile('./' + run + '/' + dataCard + '_fitDiagnostics.root', logFile)

#
# Run significance
#
def runSignificance(dataCard, expected=False, run='combine'):
  command = 'combine -M Significance ' + dataCard + '.txt'
  logFile = dataCard + '_sig' + ('_expected' if expected else '')
  if expected: command += ' -t -1 --expectSignal=1'
  log.info('Running Significance')
  handleCombine(dataCard, logFile, command, run=run)
  with open('./' + run + '/' + logFile + '.log') as f:
    for line in f:
      if 'Significance:' in line:
        log.info(line.rstrip() + (' (expected)' if expected else ''))

def plotNLLScan(dataCard, year, mode = 'exp', trackParameters = None, freezeParameters = None, doRatio=False, rMin=0., rMax=10., run='combine'):
    
    log.info('Running NLL Scan for ' + mode)
    currentDir     = os.getcwd()
    combineRelease = getCombineRelease()
    statSysFile = currentDir + '/' + run + '/' + dataCard + '_MultiDimFit_' + mode + '.root'
    statFile = currentDir + '/' + run + '/' + dataCard + '_MultiDimFit_StatOnly_' + mode + '.root'
    
    units = '\'\''
    if doRatio == True:
        units = '\'\\times 10^{-3}\''
    
    if mode == 'obs':

        # Estimate best fit signal value and perform the NLL scan
        command = 'combine -M MultiDimFit ' + currentDir + '/' + run + '/' + dataCard + '.root --algo grid --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit --robustFit=1 --seed 777 --saveWorkspace;'
        command += 'mv ' + combineRelease + '/src/higgsCombineTTGFit.MultiDimFit.mH120.777.root ' + statSysFile + ';'
        command += 'combine -M MultiDimFit ' + currentDir + '/' + run + '/' + dataCard + '.root --algo none --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit --robustFit=1 --seed 777;'
        command += 'rm ' + combineRelease + '/src/higgsCombineTTGFit.MultiDimFit.mH120.777.root;'
        
        # Estimate contribution to the best fit signal value by freezing the systematic uncertainties
        command += 'combine -M MultiDimFit ' + statSysFile + ' --algo grid --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit.FreezeAll --robustFit=1 --freezeParameters=' + ','.join(freezeParameters) + ' --fastScan -v 2 --seed 777;'
        command += 'mv ' + combineRelease + '/src/higgsCombineTTGFit.FreezeAll.MultiDimFit.mH120.777.root ' + statFile + ';'
        
        # Plot the best fit LH scan results
        command += currentDir + '/python/./plot1DScanTTG.py ' + statSysFile + ' --units=' + units + ' --others \'' + statFile + ':FreezeAll:2\' -o scan --breakdown Syst,Stat;'
        command += 'mv ' + combineRelease + '/src/scan.pdf ' + os.path.join(plotCombineDir, year, run + '/') + dataCard + '_scan_obs.pdf;'
        command += 'mv ' + combineRelease + '/src/scan.png ' + os.path.join(plotCombineDir, year, run + '/') + dataCard + '_scan_obs.png;'
        
    elif mode == 'exp':
        
        # Estimate best fit signal value and perform the NLL scan
        command = 'combine -M MultiDimFit ' + currentDir + '/' + run + '/' + dataCard + '.root --algo grid --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit --robustFit=1 --seed 777 -t -1 --expectSignal 1 --saveWorkspace;'
        command += 'mv ' + combineRelease + '/src/higgsCombineTTGFit.MultiDimFit.mH120.777.root ' + statSysFile + ';'
        command += 'combine -M MultiDimFit ' + currentDir + '/' + run + '/' + dataCard + '.root --algo none --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit --robustFit=1 -t -1 --expectSignal 1 --seed 777;'
        command += 'rm ' + combineRelease + '/src/higgsCombineTTGFit.MultiDimFit.mH120.777.root;'
        
        # Estimate contribution to the best fit signal value by freezing the systematic uncertainties
        command += 'combine -M MultiDimFit ' + statSysFile + ' --algo grid --points 100 --rMin ' + str(rMin) + ' --rMax ' + str(rMax) + ' --name TTGFit.FreezeAll --robustFit=1 --freezeParameters=' + ','.join(freezeParameters) + ' --fastScan -v 2 --seed 777 -t -1 --expectSignal 1;'
        command += 'mv ' + combineRelease + '/src/higgsCombineTTGFit.FreezeAll.MultiDimFit.mH120.777.root ' + statFile + ';'
        
        # Plot the best fit LH scan results
        command += currentDir + '/python/./plot1DScanTTG.py ' + statSysFile + ' --units=' + units + ' --others \'' + statFile + ':FreezeAll:2\' -o scan --breakdown Syst,Stat;'
        command += 'mv ' + combineRelease + '/src/scan.pdf ' + os.path.join(plotCombineDir, year, run + '/') + dataCard + '_scan_exp.pdf;'
        command += 'mv ' + combineRelease + '/src/scan.png ' + os.path.join(plotCombineDir, year, run + '/') + dataCard + '_scan_exp.png;'

    handleCombine(dataCard, dataCard + '_nll_' + mode, command, run=run)
        
#
# Get r + uncertainties from JSON (because the impact version does always converge)
#
def extractSignalFromJSON(jsonFile):
  with open(jsonFile) as f:
    impacts = json.load(f)
    for p in impacts['POIs']:
      if p['name'] == 'r':
        return p['fit']

#
# Command to create impacts.json
#
def commandForImpactsJSON(dataCard, toys=False, toyR=1):
  extraArg = (' -t -1 --expectSignal=' + str(toyR)) if toys else ''
  command  = 'text2workspace.py ' + dataCard + '.txt -m 125;'
  command += 'mv ' + dataCard + '.root CombineHarvester/CombineTools/scripts;'
  command += 'cd CombineHarvester/CombineTools/scripts;'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root --doInitialFit' + extraArg + ';'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root --doFits --parallel 8' + extraArg + ';'
  command += './combineTool.py -M Impacts -m 125 -d ' + dataCard + '.root -o impacts.json' + extraArg + ';'
  return command


#
# Linearity check
#
def doLinearityCheck(dataCard, run='combine'):
    gr = ROOT.TGraphAsymmErrors()
    for i, r in enumerate([x/10. for x in xrange(1, 19)]):
        handleCombine(dataCard, dataCard + '_linCheck', commandForImpactsJSON(dataCard, toys=True, toyR=r, run=run))
        signalStrength = extractSignalFromJSON(os.path.join(getCombineRelease(), 'src/CombineHarvester/CombineTools/scripts/impacts.json'))
        gr.SetPoint(i, r, signalStrength[1])
        gr.SetPointError(i, 0, 0, signalStrength[1]-signalStrength[0], signalStrength[2]-signalStrength[1])
    c = ROOT.TCanvas('linearityCheck', 'linearityCheck', 700, 500)
    gr.Draw('ALPE')
    gr.GetXaxis().SetTitle("input signal strength")
    gr.GetYaxis().SetTitle("measured signal strength")
    c.SaveAs(os.path.join(plotCombineDir, year, run + '/') + 'linearityCheck.pdf')

#
# Run impacts
#
def runImpacts(dataCard, year, perPage=30, toys=False, toyR=1, poi=['r'], doRatio=False, run='combine'):
#    command  = commandForImpactsJSON(dataCard, toys, toyR)
    for p in poi:
        command  = commandForImpactsJSON(dataCard, toys, toyR)
        outName  = dataCard + '_impacts' + '_'+ p + ('_asimov' if toys else '')
        units = '\'\''
        if doRatio == True:
            if p == 'r': units = '\'\\times 10^{-3}\''
            else: units = '\'nb\''
        command += './plotImpacts.py -i impacts.json --units=' + units + ' --POI=' + p + ' --per-page=' + str(perPage) + ' --cms-label preliminary --translate sysMappings.json -o impacts;'
        command += 'mv impacts.pdf ../../../' + outName + '.pdf'
        log.info('Running Impacts for ' + p)
        log.info(command)
        handleCombine(dataCard, dataCard + '_impacts', command, run=run)
        with open('./' + run + '/' + dataCard + '_impacts.log') as f:
            for line in f:
                if "mv: cannot stat `impacts.pdf': No such file or directory" in line: log.error("Problem with running impacts")
                log.debug(line.rstrip())

        os.system('pdftoppm ' + run + '/' + outName + '.pdf ' + outName + ' -png;mogrify -trim ' + outName + '*.png')
        os.system('mv ' + outName + '-1.png ' + outName + '.png')
        os.system('mv ' + outName + '.png ' + os.path.join(plotCombineDir, year, run + '/'))
        os.system('mv ' + run + '/' + outName + '.pdf ' + os.path.join(plotCombineDir, year, run + '/'))
        shutil.copy(os.path.join(getCombineRelease(), 'src/CombineHarvester/CombineTools/scripts/impacts.json'), os.path.expandvars('$CMSSW_BASE/src/ttg/plots/' + run + '/' + outName + '.json'))

#
# Run channel compatibility
#
def runCompatibility(dataCard, year, perPage=30, toys=False, doRatio=False, run='combine'):

    combineRelease = getCombineRelease()
    command  = 'combine -M ChannelCompatibilityCheck ' + dataCard + '.txt --saveFitResult'
    if toys:
        command += ' -t -1 --expectSignal 1'

    log.info('Running the check (stat+sys)')    

    outName = dataCard + '_cc'
    if toys: outName += '_exp'
    else: outName += '_obs'
    handleCombine(dataCard, outName, command, run=run)
    ccFile = dataCard + '_cc'
    rfile = 'higgsCombineTest.ChannelCompatibilityCheck.mH120.root'
    if toys: 
        ccFile += '_exp'
    else: 
        ccFile += '_obs'
    ccFile += '.root'
    statSysFile = run + '/' + ccFile
    os.system('mv ' + combineRelease + '/src/' + rfile + ' ' + statSysFile)
    
    flog = './' + run + '/' + outName + '.log'
    with open(flog) as f:
        for line in f:
            log.debug(line.rstrip())
            if 'fit' in line or 'Chi' in line: log.info(line.rstrip())

    log.info('Running the check (stat)')    

    command += ' --profilingMode=none'

    log.info(command)
    outName = dataCard + '_cc'
    if toys: outName += '_exp_statOnly'
    else: outName += '_obs_statOnly'
    handleCombine(dataCard, outName, command, run=run)
    ccFile = dataCard + '_cc'
    rfile = 'higgsCombineTest.ChannelCompatibilityCheck.mH120.root'
    if toys: 
        ccFile += '_exp_statOnly'
    else: 
        ccFile += '_obs_statOnly'
    ccFile += '.root'
    os.system('mv ' + combineRelease + '/src/' + rfile + ' ' + run + '/' + ccFile)        
    
    flog = './' + run + '/' + outName + '.log'
    with open(flog) as f:
        for line in f:
            log.debug(line.rstrip())
            if 'fit' in line or 'Chi' in line: log.info(line.rstrip())
            
#
# Goodness of fit
#
def goodnessOfFit(dataCard, algo='saturated', run='combine'):
    command  = 'combine -M GoodnessOfFit ' + dataCard + '.txt --algo=' + algo + ';'
    command += 'combine -M GoodnessOfFit ' + dataCard + '.txt --algo=' + algo + ' -t 1000' + (' --toysFreq' if algo=='saturated' else '') + ';'
    log.info('Running goodness of fit')
    handleCombine(dataCard, dataCard + '_gof', command, run=run)
    with open('./' + combine + '/' + dataCard + '_gof.log') as f:
        for line in f:
            log.debug(line.rstrip())

#
# Write the card including all systematics and shapes
# Might need refactoring
#
def writeCard(cardName, shapes, templates, templatesNoSys, extraLines, systematics, linearSystematics, scaleShape = None, run = 'combine'): # pylint: disable=R0914,R0913,R0912
  if not templatesNoSys: templatesNoSys = []

  def tab(entries, column='12'):
    return ''.join(['%25s' % entries[0]] + [(('%'+column+'s') % i) for i in entries[1:]]) + '\n'

  def linSys(info, template):
    if template not in templates: return '-'
    sample, value = info
    value = 1+value/100.
    if sample:
      if template.count(sample): return value
      else:                      return '-'
    else:                        return value

  def shapeSys(shape, template, sys):
    if ':' in sys:
      try:    selectTemplate, selectShape, sys   = sys.split(':')
      except: (selectTemplate, sys), selectShape = sys.split(':'), None
    else:     selectTemplate, selectShape, sys   = None, None, sys

    if not shape and not template: return sys

    if t in templatesNoSys:                             return '-'
    elif selectShape    and selectShape    != shape:    return '-'
    elif selectTemplate and selectTemplate != template: return '-'
    elif scaleShape and sys in scaleShape:              return '%.4f' % scaleShape[sys]
    elif sys == 'nonPrompt' and shape == 'tt':          return '-' # hacky way, but easiest to currently implement
    else:                                               return '1'

  cardFile = run + '/' + cardName + '.txt'
  print cardFile
  with open(cardFile, 'w') as f:
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
      f.write(tab([shapeSys(None, None, sys), 'shapeN'] + [shapeSys(s, t, sys) for s in shapes for t in templates+templatesNoSys]))

    f.write('-'*400 + '\n')
    for extraLine in extraLines:
      f.write(tab([x for x in extraLine.split()], column='18'))

def plotSys(fileName, regName, chanName, proc=[''], sys=[''], year='2016', run='combine', comb=False):

    sysShapes = []

    for s in sys:
        if 'Up' in s:
            sysShapes.append(s.replace('Up',''))
    
    f = ROOT.TFile(fileName, 'READ')
    
    procAr = {}
    
    for p in proc:

        procAr[p] = []
        
        nom = f.Get(regName + '_' + chanName + '/' + p)
        ar_nom = rnp.hist2array(nom, copy=True, return_edges=False)

        ar_stat = []
        for ib in range(0,nom.GetXaxis().GetNbins()):
            ar_stat.append(nom.GetBinError(ib+1))
        
        for s in sysShapes:
                        
            up = f.Get(regName + '_' + chanName + s + 'Up/' + p)
            down = f.Get(regName + '_' + chanName + s + 'Down/' + p)

            ar_up = rnp.hist2array(up, copy=True, return_edges=False)
            ar_down = rnp.hist2array(down, copy=True, return_edges=False)
            
            procAr[p].append([s, ar_nom, ar_up, ar_down, ar_stat])

    f.Close()

    for p in proc:
        
        sysAr = procAr[p]

        nSys = len(sysAr)

        nMaxRows = 5
        nMaxCols = int(math.ceil(float(nSys)/nMaxRows))

        fig, ax = plt.subplots(sharex='col', sharey=False, ncols=nMaxCols, nrows=nMaxRows)
        fig.suptitle('Systematic shape variations for ' + p)
        
        icol = 0
        irow = 0
        for i in range(0,nSys):

            sysName = sysAr[i][0]
            ar_nom = sysAr[i][1]
            ar_up = sysAr[i][2]
            ar_down = sysAr[i][3]
            ar_stat = sysAr[i][4]
            
            nb = len(ar_nom)
                        
            ar_statUp = []
            ar_statDown = []
            
            for ib in range(0,nb):
                nom = ar_nom[ib]
                ar_up[ib] = (ar_up[ib] - nom)/nom if nom != 0 else 0
                ar_down[ib] = (ar_down[ib] - nom)/nom if nom != 0 else 0
                statUnc = ar_stat[ib]/nom if nom != 0 else 0
                ar_statUp.append(statUnc)
                ar_statDown.append(-statUnc)

            ar_all = np.concatenate([ar_up, ar_down, ar_statUp, ar_statDown])
            upMax = max(ar_all)
            downMin = min(ar_all)

            ax[irow,icol].axhline(y=0.0, linestyle='--', color='black')
            ax[irow,icol].plot(ar_up, color='red', label=r'$\sigma_{+}$')
            ax[irow,icol].plot(ar_down, color='blue', label=r'$\sigma_{-}$')
            ax[irow,icol].plot(ar_statUp, color='yellow', label=r'$\sigma_{\mathrm{stat}}$', alpha=1.0)
            ax[irow,icol].plot(ar_statDown, color='yellow', alpha=1.0)
            ax[irow,icol].set_ylim(ymin=downMin*1.25, ymax=upMax*1.25)
#            ax[irow,icol].legend(loc='upper right')
            ax[irow,icol].text(0.05, 0.05, sysName, transform = ax[irow,icol].transAxes, fontsize=14, fontstyle='italic', weight='bold')
#            ax[irow,icol].set_ylabel(r'$\sigma$(A) / A')
#            ax[irow,icol].set_xlabel('Bin')

            irow += 1
            if (i+1) % nMaxRows == 0:
                icol += 1
                irow = 0

        if comb == True:
            figOutput = os.path.join(plotCombineDir, year, run + 'll/') + p + '_fracSys_' + chanName + '.pdf'
        else:
            figOutput = os.path.join(plotCombineDir, year, run + chanName + '/') + p + '_fracSys_' + chanName + '.pdf'
            
        plt.savefig(figOutput)
        plt.close()
        os.system('convert ' + figOutput + ' ' + figOutput.replace('pdf','png') + ' > /dev/null 2>&1')

def plotCC(dataCard, year, poi='r', rMin = 0.5, rMax=1.5, run='combine', mode='exp', addNominal = True):

    currentDir = os.getcwd()
    
    c1 = ROOT.TCanvas("c1")
    c1.SetLeftMargin(0.2)
    c1.SetBottomMargin(0.2)
#    c1.SetGridx(1)

    statSysFile = ROOT.TFile(currentDir + '/' + run + '/' + dataCard + '_cc_' + mode + '.root')
    statOnlyFile = ROOT.TFile(currentDir + '/' + run + '/' + dataCard + '_cc_' + mode + '_statOnly.root')
    
    fit_nominal = statSysFile.Get("fit_nominal")
    fit_alternate = statSysFile.Get("fit_alternate")

    fit_nominal_statOnly = statOnlyFile.Get("fit_nominal")
    fit_alternate_statOnly = statOnlyFile.Get("fit_alternate")
    
    rFit = fit_nominal.floatParsFinal().find(poi)
    rFitStat = fit_nominal_statOnly.floatParsFinal().find(poi)
    if rFit == 0 or rFitStat == 0:
        print "Nominal fit does not contain parameter " + poi
        return

    prefix = "_ChannelCompatibilityCheck_%s_" % (poi)

    nChann = 0
    nElem = fit_alternate.floatParsFinal().getSize()
    nElem_nominal = fit_nominal.floatParsFinal().getSize()
    
    for i in range(0,nElem):
        if prefix in fit_alternate.floatParsFinal().at(i).GetName():
            nChann += 1
            
    nBins = nChann
    if addNominal:
        nBins += 1

    frame = ROOT.TH2F("frame", ";Best fit of #sigma^{t#bar{t}#gamma}/#sigma^{t#bar{t}#gamma}_{SM};", 1, max(rFit.getMin(),rMin), min(rFit.getMax(),rMax), nBins, 0, nBins)

    points = ROOT.TGraphAsymmErrors(nBins)
    pointsStatOnly = ROOT.TGraphAsymmErrors(nBins)
    
    iChann = 0
    for i in range(0,nElem):
        
        if prefix in fit_alternate.floatParsFinal().at(i).GetName():
            
            ri = fit_alternate.floatParsFinal().at(i)
            ri_statOnly = fit_alternate_statOnly.floatParsFinal().at(iChann)
            
            channel = ri.GetName().replace(prefix,'')
            channel = channel.replace('sr_','').replace('ratio_','').replace('emu',r'e\mu').replace('ee',r'ee').replace('mumu',r'\mu\mu')
            
            points.SetPoint(iChann, ri.getVal(), iChann+0.5)
            points.SetPointError(iChann, -ri.getAsymErrorLo(), ri.getAsymErrorHi(), 0, 0)

            pointsStatOnly.SetPoint(iChann, ri_statOnly.getVal(), iChann+0.5)
            pointsStatOnly.SetPointError(iChann, -ri_statOnly.getAsymErrorLo(), ri_statOnly.getAsymErrorHi(), 0, 0)
            
            iChann += 1
            frame.GetYaxis().SetBinLabel(iChann, channel)
    
    if addNominal:
            
        points.SetPoint(iChann, rFit.getVal(), iChann+0.5)
        points.SetPointError(iChann, -rFit.getAsymErrorLo(), rFit.getAsymErrorHi(), 0, 0)
        
        pointsStatOnly.SetPoint(iChann, rFitStat.getVal(), iChann+0.5)
        pointsStatOnly.SetPointError(iChann, -rFitStat.getAsymErrorLo(), rFitStat.getAsymErrorHi(), 0, 0)
        
        channel = 'combined'
        iChann += 1
        frame.GetYaxis().SetBinLabel(iChann, channel)
        
    points.SetLineColor(ROOT.kRed+1)
    points.SetLineWidth(3)
    points.SetMarkerStyle(20)

    pointsStatOnly.SetLineColor(ROOT.kBlue+1)
    pointsStatOnly.SetLineWidth(10)
    pointsStatOnly.SetMarkerStyle(20)
    
    frame.GetXaxis().SetTitleSize(0.05)
    frame.GetXaxis().SetLabelSize(0.04)
    frame.GetYaxis().SetLabelSize(0.06)
    
    frame.Draw()
    
    ROOT.gStyle.SetOptStat(0)
 
#    globalFitBand = ROOT.TBox(rFit.getVal()+rFit.getAsymErrorLo(), 0, rFit.getVal()+rFit.getAsymErrorHi(), nChann)
#    globalFitBand.SetFillStyle(3013)
#    globalFitBand.SetFillColor(ROOT.kRed)
#    globalFitBand.SetLineStyle(0)
#    globalFitBand.DrawClone()

#    statFitBand = ROOT.TBox(rFitStat.getVal()+rFitStat.getAsymErrorLo(), 0, rFitStat.getVal()+rFitStat.getAsymErrorHi(), nChann)
#    statFitBand.SetFillStyle(3013)
#    statFitBand.SetFillColor(ROOT.kBlue)
#    statFitBand.SetLineStyle(0)
#    statFitBand.DrawClone()
    
#    globalFitLine = ROOT.TLine(rFit.getVal(), 0, rFit.getVal(), nChann)    
#    globalFitLine.SetLineWidth(4)
#    globalFitLine.SetLineColor(ROOT.kRed)
#    globalFitLine.DrawClone()

#    statFitLine = ROOT.TLine(rFitStat.getVal(), 0, rFitStat.getVal(), nChann)    
#    statFitLine.SetLineWidth(10)
#    statFitLine.SetLineColor(ROOT.kBlue)
#    statFitLine.DrawClone()

    if addNominal:
        sep = ROOT.TLine(c1.GetUxmin(),3,c1.GetUxmax(),3)
        sep.SetLineColor(ROOT.kBlack)
        sep.SetLineWidth(1)
        sep.SetLineStyle(2)
        sep.Draw()

    sm = ROOT.TLine(1,c1.GetUymin(),1,c1.GetUymax())
    sm.SetLineColor(ROOT.kGray)
    sm.SetLineWidth(3)
    sm.SetLineStyle(1)
    sm.Draw()
        
    points.Draw("P Z SAME")
    pointsStatOnly.Draw("P Z SAME")
    
    leg = ROOT.TLegend(0.75, 0.80, 0.90, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(points, 'stat+sys', "l")
    leg.AddEntry(pointsStatOnly, 'stat', "l")
    leg.Draw()

    for i in range(0,nBins):
        
        tex = ROOT.TLatex()
        tex.SetTextSize(0.03)
        
        v = points.GetX()[i]
        errLow = points.GetErrorXlow(i)
        errHigh = points.GetErrorXhigh(i)
        errStatLow = pointsStatOnly.GetErrorXlow(i)
        errStatHigh = pointsStatOnly.GetErrorXhigh(i)
        errSysLow = math.sqrt(errLow*errLow-errStatLow*errStatLow)
        errSysHigh = math.sqrt(errHigh*errHigh-errStatHigh*errStatHigh)

        v_Str = "%.3f" % v
        v_errLow_Str = "%.3f" % errLow
        v_errHigh_Str = "%.3f" % errHigh
        v_errStatLow_Str = "%.3f" % errStatLow
        v_errStatHigh_Str = "%.3f" % errStatHigh
        v_errSysLow_Str = "%.3f" % errSysLow
        v_errSysHigh_Str = "%.3f" % errSysHigh
        
        chLabel = frame.GetYaxis().GetBinLabel(i+1)
        chanName = "_{" + chLabel + "}"
        if chLabel == 'combined': chanName = ''
        
        lab = "\hat{\mu}" + chanName + " = " + v_Str + "^{+" + v_errStatHigh_Str + "}_{-" + v_errStatLow_Str + "}(stat)"
        lab += "^{+" + v_errSysHigh_Str + "}_{-" + v_errSysLow_Str + "}(sys)"
        ypos = (frame.GetYaxis().GetBinCenter(i)*0.7+1)/float(nBins)+0.08
        tex.DrawLatexNDC(0.25,ypos,lab)

    figOutput = os.path.join(plotCombineDir, year, run + '/') + dataCard + '_cc_' + mode + '.pdf'
    
    c1.Print(figOutput)
    
    os.system('convert ' + figOutput + ' ' + figOutput.replace('pdf','png') + ' > /dev/null 2>&1')
        
