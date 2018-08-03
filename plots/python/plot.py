from ttg.tools.logger import getLogger
log = getLogger()

#
# Plot class
# Still messy, contains a lot of functions, but does a lot of automatized work
#
import ROOT, os, uuid, numpy, math
import cPickle as pickle
from math import sqrt
from ttg.tools.helpers import copyIndexPHP, copyGitInfo, plotDir, addHist
from ttg.tools.lock import lock
from ttg.tools.style import drawTex, getDefaultCanvas, fromAxisToNDC

#
# Apply the relative variation between source and sourceVar to the destination histogram
#
def applySysToOtherHist(source, sourceVar, destination):
  destinationVar = destination.Clone()
  for i in range(source.GetNbinsX()+1):
    modificationFactor = 1.+(source.GetBinContent(i)-sourceVar.GetBinContent(i))/source.GetBinContent(i) if source.GetBinContent(i) > 0 else 1.
    destinationVar.SetBinContent(i, modificationFactor*destination.GetBinContent(i))
  return destinationVar

#
# Load a histogram from pkl
#
loadedPkls = {}
def getHistFromPkl(subdirs, plotName, sys, *selectors):
  global loadePkls
  hist = None
  resultFile = os.path.join(*((plotDir,)+subdirs+(plotName +'.pkl',)))
  if os.path.isdir(os.path.dirname(resultFile)):
    if resultFile not in loadedPkls:
      with lock(resultFile, 'rb') as f: loadedPkls[resultFile] = pickle.load(f)
    for selector in selectors:
      filtered = {s:h for s,h in loadedPkls[resultFile][plotName+sys].iteritems() if all(s.count(sel) for sel in selector)}
      if len(filtered) == 1:   hist = addHist(hist, filtered[filtered.keys()[0]])
      elif len(filtered) > 1:  log.error('Multiple possibilities to look for ' + str(selector) + ': ' + str(filtered.keys()))
  else:                        log.error('Missing cache file ' + resultFile)
  if 'Scale' in sys and not any('MuonEG' in sel for sel in selectors):
    data    = getHistFromPkl(subdirs, plotName, '',   ['MuonEG'],['DoubleEG'],['DoubleMuon'])
    dataSys = getHistFromPkl(subdirs, plotName, sys,  ['MuonEG'],['DoubleEG'],['DoubleMuon'])
    hist = applySysToOtherHist(data, dataSys, hist)
  if not hist: log.error('Missing ' + str(selectors) + ' for plot ' + plotName + ' in ' + resultFile)
  return hist

#
# Get systematic uncertainty on sideband template: based on shape difference of ttbar hadronicFakes in sideband and nominal region
#
def applySidebandUnc(hist, plot, resultsDir, up):
  selection     = resultsDir.split('/')[-1]
  ttbarNominal  = getHistFromPkl(('sigmaIetaIeta-ttpow-hadronicFake-bins', 'all', selection), plot, '', ['TTJets','hadronicFake','pass'])
  ttbarSideband = getHistFromPkl(('sigmaIetaIeta-ttpow-hadronicFake-bins', 'all', selection), plot, '', ['TTJets','hadronicFake,0.012'])
  ttbarNominal.Scale(1/ttbarNominal.Integral())
  ttbarSideband.Scale(1/ttbarSideband.Integral())
  if up: return applySysToOtherHist(ttbarNominal, ttbarSideband, hist)
  else:  return applySysToOtherHist(ttbarSideband, ttbarNominal, hist)

#
# Returns histmodificator which applies labels to x-axis
#
def xAxisLabels(labels):
  def applyLabels(h):
    for i,l in enumerate(labels):
      h.GetXaxis().SetBinLabel(i+1, l)
  return [applyLabels]

#
# Normalize binwidth when non-unifor bin width is used
#
def normalizeBinWidth(hist, norm=None):
  if norm:
    for i in range(hist.GetXaxis().GetNbins()+1):
      val   = hist.GetBinContent(i)
      err   = hist.GetBinError(i)
      width = hist.GetBinWidth(i)
      hist.SetBinContent(i, val/(width/norm))
      hist.SetBinError(i, err/(width/norm))


#
# Function which fills all plots and removes them when the lamdbda fails (e.g. because var is not defined)
#
def fillPlots(plots, c, sample, eventWeight):
  removePlots = False
  for plot in plots:
    try:
      plot.fill(sample, eventWeight)
    except:
      if removePlots: toRemove.append(plot)
      else:           toRemove = [plot]
      removePlots = True
      log.info('Not considering plot ' + plot.name + ' for this selection')
  if removePlots:
    for p in toRemove: plots.remove(p)
    toRemove = []


#
# Plot class
#
class Plot:
  defaultStack        = None
  defaultTexY         = None
  defaultOverflowBin  = None
  defaultNormBinWidth = None

  @staticmethod
  def setDefaults(stack = None, texY="Events", overflowBin='upper'):
      Plot.defaultStack        = stack
      Plot.defaultTexY         = texY
      Plot.defaultOverflowBin  = overflowBin

  def __init__(self, name, texX, varX, binning, stack=None, texY=None, overflowBin='default', normBinWidth='default', histModifications=[]):
    self.stack             = stack        if stack else Plot.defaultStack
    self.texY              = texY         if texY else Plot.defaultTexY
    self.overflowBin       = overflowBin  if overflowBin!='default'  else Plot.defaultOverflowBin
    self.normBinWidth      = normBinWidth if normBinWidth!='default' else Plot.defaultNormBinWidth
    self.name              = name
    self.texX              = texX
    self.varX              = varX
    self.histModifications = histModifications
    self.scaleFactor       = None

    if type(binning)==type([]):   self.binning = (len(binning)-1, numpy.array(binning))
    elif type(binning)==type(()): self.binning = binning

    self.histos = {}
    for s in sum(self.stack, []):
      name           = self.name + s.name
      self.histos[s] = ROOT.TH1F(name, name, *self.binning)


  #
  # Add an overflow bin, optionally called from the draw function
  #
  def addOverFlowBin1D(self, histo, addOverFlowBin = None):
    if addOverFlowBin and not hasattr(histo, 'overflowApplied'):
      if addOverFlowBin.lower() == "upper" or addOverFlowBin.lower() == "both":
          nbins = histo.GetNbinsX()
          histo.SetBinContent(nbins, histo.GetBinContent(nbins) + histo.GetBinContent(nbins + 1))
          histo.SetBinError(nbins, sqrt(histo.GetBinError(nbins)**2 + histo.GetBinError(nbins + 1)**2))
      if addOverFlowBin.lower() == "lower" or addOverFlowBin.lower() == "both":
          histo.SetBinContent(1, histo.GetBinContent(0) + histo.GetBinContent(1))
          histo.SetBinError(1, sqrt(histo.GetBinError(0)**2 + histo.GetBinError(1)**2))
      histo.overflowApplied = True

  def fill(self, sample, weight=1.):
    self.histos[sample].Fill(self.varX(sample.chain), weight)

  #
  # Stacking the hist, called during the draw function
  #
  def stackHists(self, histsToStack, sorting=True):
    # Merge if texName is the same
    for i in range(len(histsToStack)):
      if not histsToStack[i]: continue
      for j in range(i+1, len(histsToStack)):
        if not histsToStack[j]: continue
        if histsToStack[i].texName == histsToStack[j].texName:
          histsToStack[i].Add(histsToStack[j])
          histsToStack[j] = None
    histsToStack = [h for h in histsToStack if h]

    if sorting: histsToStack.sort(key=lambda h  : -h.Integral())

    # Add up stacks
    for i, h in enumerate(histsToStack):
      for j in range(i+1, len(histsToStack)):
        histsToStack[i].Add(histsToStack[j])

    if h.legendStyle != 'f': return histsToStack[:1] # do not show sub-contributions when line or errorstyle
    else:                    return histsToStack


  #
  # Scaling options, optionally called from the draw function
  #
  def scaleStacks(self, histos, scaling):
    if scaling=="unity":
      for stack in histos:
        if not stack[0].Integral() > 0: continue
        if self.normBinWidth: factor = 1./stack[0].Integral('width') # actually not fully correct for figures with overflow bin, should check
        else:                 factor = 1./stack[0].Integral()
        for h in stack: h.Scale(factor)
    else:
      if not isinstance(scaling, dict):
        raise ValueError( "'scaling' must be of the form {0:1, 2:3} which normalizes stack[0] to stack[1] etc. Got '%r'" % scaling )
      for source, target in scaling.iteritems():
        if not (isinstance(source, int) and isinstance(target, int) ):
          raise ValueError( "Scaling should be {0:1, 1:2, ...}. Expected ints, got %r %r"%( source, target ) )

        source_yield = histos[source][0].Integral()

        if source_yield == 0:
          log.warning( "Requested to scale empty Stack? Do nothing." )
          continue

        self.scaleFactor = histos[target][0].Integral()/source_yield
        for h in histos[source]: h.Scale(self.scaleFactor)
        if len(scaling) == 1:
          self.textNDC = 0.82
          return [drawTex((0.2, 0.85, 'Scaling: %.2f' % self.scaleFactor))]
    return []

  #
  # Save the histogram to a results.cache file, useful when you need to do further operations on it later
  #
  def saveToCache(self, dir, sys):
    try:    os.makedirs(os.path.join(dir))
    except: pass

    resultFile = os.path.join(dir, self.name + '.pkl')
    histos     = {s.name+s.texName: h for s, h in self.histos.iteritems()}
    plotName   = self.name+(sys if sys else '')
    try:
      with lock(resultFile, 'rb', keepLock=True) as f: allPlots = pickle.load(f)
      allPlots.update({plotName : histos})
    except:
      allPlots = {plotName : histos}
    with lock(resultFile, 'wb', existingLock=True) as f: pickle.dump(allPlots, f)
    log.info("Plot " + plotName + " saved to cache")


  #
  # Load from cache
  #
  def loadFromCache(self, resultsDir):
    resultsFile = os.path.join(resultsDir, self.name + '.pkl')
    try:
      with lock(resultsFile, 'rb') as f: allPlots = pickle.load(f)
      for s in self.histos.keys():
        self.histos[s] = allPlots[self.name][s.name+s.texName]
    except:
      log.warning('No resultsfile for ' + self.name + '.pkl')
      return True

  #
  # Get Yields
  #
  def getYields(self, bin=None):
    if bin: return {s.name : h.GetBinContent(bin) for s,h in self.histos.iteritems()}
    else:   return {s.name : h.Integral()         for s,h in self.histos.iteritems()}


  #
  # Make a correct ratio graph (also working for poisson errors, and showing error bars for points outside of y-axis range)
  #
  def makeRatioGraph(self, num, den):
    graph = ROOT.TGraphAsymmErrors(num)
    graph.Set(0)
    for bin in range(1, num.GetNbinsX()+1):
      if den.GetBinContent(bin) > 0:
        center  = num.GetBinCenter(bin)
        val     = num.GetBinContent(bin)/den.GetBinContent(bin)
        errUp   = num.GetBinErrorUp(bin)/den.GetBinContent(bin)  if val > 0 else 0
        errDown = num.GetBinErrorLow(bin)/den.GetBinContent(bin) if val > 0 else 0
        graph.SetPoint(bin, center, val)
        graph.SetPointError(bin, 0, 0, errDown, errUp)
    return graph



  #
  # Get ratio line
  #
  def getRatioLine(self):
    line = ROOT.TPolyLine(2)
    line.SetPoint(0, self.xmin, 1.)
    line.SetPoint(1, self.xmax, 1.)
    line.SetLineWidth(1)
    return line

  #
  # Get legend
  #
  def getLegend(self, columns, coordinates, histos):
    legend = ROOT.TLegend(*coordinates)
    legend.SetNColumns(columns)
    legend.SetFillStyle(0)
    legend.SetShadowColor(ROOT.kWhite)
    legend.SetBorderSize(0)
    for h in sum(histos, []): legend.AddEntry(h, h.texName, h.legendStyle)
    return legend


  #
  # Applying post-fit values
  #
  def applyPostFitScaling(self, postFitInfo):
    for sample, h in self.histos.iteritems():
      for key,value in postFitInfo.iteritems():
        if key in sample.name or key in sample.texName:
          log.debug('Applying post-fit scaling value of ' + str(value) + ' to ' + sample.name)
          h.Scale(value)


  #
  # Adding systematics to MC
  # stackForSys       --> list of samples which are stacked
  # systematics       --> dictionary of systematics, as given in systematics.py
  # linearSystematics --> dictionary of linear systematics, as given in systematics.py
  # resultsDir        --> directory where to find the .pkl files which should be filled before with histogram for all the systematic variations
  # postFitInfo       --> dictionary (name, scalefactor) to apply scalefactors to specific samples
  # addMCStat         --> include MC statistics in the uncertainty band
  #
  def calcSystematics(self, stackForSys, systematics, linearSystematics, resultsDir, postFitInfo=None, addMCStat=True):
    resultsFile = os.path.join(resultsDir, self.name + '.pkl')
    with lock(resultsFile, 'rb') as f: allPlots = pickle.load(f)

    sysKeys = [sys.replace('Up', '') for sys in systematics.keys() if sys.count('Up')]
    if addMCStat:
      sysKeys += [s.name + s.texName + 'Stat' for s in stackForSys]

    histos_summed = {}
    for sys in [None] + [(s + 'Up') for s in sysKeys] + [(s + 'Down') for s in sysKeys]:
      if sys and not any(x in sys for x in ['Stat', 'sideBand', 'Scale']): plotName = self.name+sys                                    # in the 2D cache, the first key is plotname+sys
      else:                                                                plotName = self.name                                        # for nominal and some exceptions 

      if plotName not in allPlots:                                                                                                     # check if sys variation has been run already
        log.error('No ' + sys + ' variation found for ' +  self.name)

      histos_summed[sys] = None
      for histName in [s.name+s.texName for s in stackForSys]:                                                                         # in the 2D cache, the second key is name+texName of the sample
        if sys and 'Scale' in sys and not 'noData' in resultsDir:                                                                      # ugly hack to apply scale systematics on MC instead of data (only when data is available)
          data, dataSys = None, None
          for d in [d for d in allPlots[self.name] if d.count('data')]:                                                                # for data (if available depending on ee, mumu, emu, SF)
            data    = addHist(data,    allPlots[self.name][d])                                                                         # get nominal for data
            dataSys = addHist(dataSys, allPlots[self.name+sys][d])                                                                     # and the eScale or phScale sys for data
          h = applySysToOtherHist(data, dataSys, allPlots[plotName][histName])                                                         # apply the eScale or phScale sys on MC
        elif sys and 'sideBand' in sys:                                                                                                # ugly hack to apply side band uncertainty
          h = applySidebandUnc(allPlots[self.name][histName], self.name, resultsDir, 'Up' in sys)
        else:                                                                                                                          # normal case, simply taken from cache
          h = allPlots[plotName][histName]

        if sys and 'StatUp' in sys and sys.replace('StatUp', '') in histName:                                                          # MC statistics for plots
          for i in range(0, h.GetNbinsX()+1):
            h.SetBinContent(i, h.GetBinContent(i)+h.GetBinError(i))
        if sys and 'StatDown' in sys and  sys.replace('StatDown', '') in histName:
          for i in range(0, h.GetNbinsX()+1):
            h.SetBinContent(i, h.GetBinContent(i)-h.GetBinError(i))

        if postFitInfo:                                                                                                                # apply post-fit scalefactors if available
          for i in postFitInfo:
            if histName.count(i): h.Scale(postFitInfo[i])
        if h.Integral()==0: log.debug("Found empty histogram %s:%s in %s/%s.pkl", plotName, histName, resultsDir, self.name)
        if self.scaleFactor: h.Scale(self.scaleFactor)
        normalizeBinWidth(h, self.normBinWidth)
        self.addOverFlowBin1D(h, self.overflowBin)

        histos_summed[sys] = addHist(histos_summed[sys], h)

    h_sys = {}
    for sys in sysKeys:
      h_sys[sys] = histos_summed[sys+'Up'].Clone()
      h_sys[sys].Scale(-1)
      h_sys[sys].Add(histos_summed[sys+'Down'])

    h_rel_err = histos_summed[None].Clone()
    h_rel_err.Reset()

    # Adding the systematics in quadrature
    for k in h_sys.keys():
      for ib in range(h_rel_err.GetNbinsX()+1):
        h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (h_sys[k].GetBinContent(ib)/2)**2 )

    for sampleFilter, unc in linearSystematics.values():
      for ib in range(h_rel_err.GetNbinsX()+1):
        if sampleFilter: uncertainty = unc/100*sum([h.GetBinContent(ib) for s,h in self.histos.iteritems() if any([s.name.count(f) for f in sampleFilter])])
        else:            uncertainty = unc/100*sum([h.GetBinContent(ib) for s,h in self.histos.iteritems()])
        h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + uncertainty**2)

    for ib in range(h_rel_err.GetNbinsX()+1):
      h_rel_err.SetBinContent(ib, sqrt(h_rel_err.GetBinContent(ib)))

    # Divide by the summed hist to get relative errors, and return
    h_rel_err.Divide(histos_summed[None])
    return h_rel_err

  #
  # Get the boxes for the systematic band
  #
  def getSystematicBoxes(self, totalMC, ratio = False):
    def constrain(low, up, x):
      return min(max(x, low), up)

    boxes = []
    for ib in range(1, 1 + totalMC.GetNbinsX()):
      val = totalMC.GetBinContent(ib)
      if val > 0:
        sys   = totalMC.sysValues.GetBinContent(ib)
        xmin  = constrain(self.xmin,  self.xmax,  totalMC.GetXaxis().GetBinLowEdge(ib))
        xmax  = constrain(self.xmin,  self.xmax,  totalMC.GetXaxis().GetBinUpEdge(ib))
        ymin  = constrain(self.yrmin if ratio else self.ymin, self.yrmax if ratio else self.ymax, (1-sys) if ratio else (1-sys)*val)
        ymax  = constrain(self.yrmin if ratio else self.ymin, self.yrmax if ratio else self.ymax, (1+sys) if ratio else (1+sys)*val)
        box   = ROOT.TBox(xmin, ymin,  xmax, ymax)
        box.SetLineColor(ROOT.kBlack)
        box.SetFillStyle(3444)
        box.SetFillColor(ROOT.kBlack)
        boxes.append(box)
    return boxes

  #
  # Get filled bins in plot
  #
  def getFilledBins(self, yMax, threshold=0):
    return [i for i in range(1, yMax.GetNbinsX()+1) if yMax.GetBinContent(i) > threshold]

  #
  # Remove empty bins from plot
  #
  def removeEmptyBins(self, histos, yMax, threshold):
    filledBins = self.getFilledBins(yMax, threshold)
    self.xmin  = yMax.GetBinLowEdge(filledBins[0])
    self.xmax  = yMax.GetBinLowEdge(filledBins[-1]+1)

  #
  # Avoid legend overlap in pad for given legend coordinates and yMax histogram, returns proposed ymax
  #
  def avoidLegendOverlap(self, pad, yMax, coordinates, logY):
    ymax = yMax.GetMaximum()
    for i in range(1, 1 + yMax.GetNbinsX()):
      xLowerEdge = fromAxisToNDC(pad, [self.xmin, self.xmax], yMax.GetBinLowEdge(i))
      xUpperEdge = fromAxisToNDC(pad, [self.xmin, self.xmax], yMax.GetBinLowEdge(i+1))

      # maximum allowed fraction in bin to avoid overlap with legend
      marginsNDC = 1-pad.GetTopMargin()-pad.GetBottomMargin()
      if xUpperEdge > coordinates[0] and xLowerEdge < coordinates[2]: maxFraction = (max(0.3, coordinates[1]-pad.GetBottomMargin()))/marginsNDC
      else:                                                           maxFraction = min(marginsNDC-yMax.GetTickLength(), self.textNDC)/marginsNDC

      try:
        if logY: scaledMax = math.exp(math.log(self.ymin) + (math.log(yMax.GetBinContent(i)) - math.log(self.ymin))/maxFraction)
        else:    scaledMax = self.ymin + (yMax.GetBinContent(i) - self.ymin)/maxFraction
        ymax = max(ymax, scaledMax)
      except:
        pass
    return ymax


  #
  # Draw function
  #
  def draw(self, \
          yRange = "auto",
          extensions = ["pdf", "png", "root","C"],
          plot_directory = ".",
          logX = False, logY = True,
          ratio = None,
          scaling = {},
          sorting = False,
          legend = "auto",
          drawObjects = [],
          widths = {},
          canvasModifications = [],
          histModifications = [],
          ratioModifications = [],
          systematics = {},
          linearSystematics = {},
          addMCStat = True,
          resultsDir = None,
          postFitInfo = None,
          saveGitInfo = True,
          ):
    ''' yRange: 'auto' (default) or [low, high] where low/high can be 'auto'
        extensions: ["pdf", "png", "root"] (default)
        logX: True/False (default), logY: True(default)/False
        ratio: 'auto'(default) corresponds to {'num':1, 'den':0, 'logY':False, 'style':None, 'texY': 'Data / MC', 'yRange': (0.5, 1.5), 'drawObjects': []}
        scaling: {} (default). Scaling the i-th stack to the j-th is done by scaling = {i:j} with i,j integers
        sorting: True/False(default) Whether or not to sort the components of a stack wrt Integral
        legend: "auto" (default) or [x_low, y_low, x_high, y_high] or None. ([<legend_coordinates>], n) divides the legend into n columns.
        drawObjects = [] Additional ROOT objects that are called by .Draw()
        widths = {} (default) to update the widths. Values are {'y_width':500, 'x_width':500, 'y_ratio_width':200}
        canvasModifications = [] could be used to pass on lambdas to modify the canvas
    '''

    self.textNDC = 1
    # Canvas widths
    default_widths = {'y_width':500, 'x_width': 520, 'y_ratio_width': (200 if ratio else None)}
    default_widths.update(widths)

    # Make sure ratio dict has all the keys by updating the default
    if ratio:
      defaultRatioStyle = {'num':1, 'den':0, 'logY':False, 'style':None, 'texY': 'obs./exp.', 'yRange': (0.5, 1.5), 'drawObjects':[]}
      if type(ratio)!=type({}): raise ValueError( "'ratio' must be dict (default: {}). General form is '%r'." % defaultRatioStyle)
      defaultRatioStyle.update(ratio)
      ratio = defaultRatioStyle

    # If a results directory is given, we can load the histograms from former runs
    if resultsDir:
      err = self.loadFromCache(resultsDir)
      if err: return True

    if postFitInfo: self.applyPostFitScaling(postFitInfo)

    histDict = {i: h.Clone() for i, h in self.histos.iteritems()}

    # Check if at least one entry is present
    if not sum([h.Integral() for h in self.histos.values()]) > 0:
      log.info('Empty histograms for ' + self.name + ', skipping')
      return

    # Apply style to histograms + normalize bin width + add overflow bin
    for s, h in histDict.iteritems():
      if hasattr(s, 'style'): s.style(h)
      h.texName = s.texName
      normalizeBinWidth(h, self.normBinWidth)
      self.addOverFlowBin1D(h, self.overflowBin)

    # Transform histDict --> histos where the stacks are added up
    # Note self.stack is of form [[A1, A2, A3,...],[B1,B2,...],...] where the sublists need to be stacked
    histos = []
    for stack in self.stack:
      histsToStack = [histDict[s] for s in stack]
      histos.append(self.stackHists(histsToStack))

    drawObjects += self.scaleStacks(histos, scaling)

    # Calculate the systematics on the first stack
    if len(systematics) or len(linearSystematics):
      histos[0][0].sysValues = self.calcSystematics(self.stack[0], systematics, linearSystematics, resultsDir, postFitInfo, addMCStat)

    # Get minimum and maximum boundaries for the plot, including statistical and systematic errors
    yMax, yMin = histos[0][0].Clone(), histos[0][0].Clone()
    for h in (s[0] for s in histos):
      for i in range(1, 1 + h.GetNbinsX()):
        yMax.SetBinContent(i, max(yMax.GetBinContent(i), h.GetBinContent(i)*((1+h.sysValues.GetBinContent(i)) if hasattr(h, 'sysValues') else 1) + h.GetBinError(i)))
        yMin.SetBinContent(i, min(yMin.GetBinContent(i), h.GetBinContent(i)*((1-h.sysValues.GetBinContent(i)) if hasattr(h, 'sysValues') else 1) - h.GetBinError(i)))

    # Check if at least two bins are filled, otherwise skip, unless yield
    if len(self.getFilledBins(yMax)) < 2 and self.name != 'yield':
      log.info('Seems all events end up in the same bin for ' + self.name + ', will not produce output for this uninteresting plot')
      return

    # Get the canvas, which includes canvas.topPad and canvas.bottomPad
    canvas = getDefaultCanvas(default_widths['x_width'], default_widths['y_width'], default_widths['y_ratio_width'])
    for modification in canvasModifications: modification(canvas)

    canvas.topPad.cd()

    # Range on y axis and remove empty bins
    self.ymin = yRange[0] if (yRange!="auto" and yRange[0]!="auto") else (0.7 if logY else (0 if yMin.GetMinimum() >0 else 1.2*yMin.GetMinimum()))
    self.ymax = yRange[1] if (yRange!="auto" and yRange[1]!="auto") else (1.2*yMax.GetMaximum())
    self.yrmin, self.yrmax = ratio['yRange'] if ratio else (None, None)

    # Remove empty bins from the edges (or when they are too small to see)
    self.removeEmptyBins(histos, yMax, self.ymin if (logY or self.ymin < 0) else yMax.GetMaximum()/100.)

    # If legend is in the form (tuple, int) then the number of columns is provided
    if len(legend) == 2: legendColumns, legend = legend[1], legend[0]
    else:                legendColumns, legend = 1, legend

    # Legend coordinates + optimization of y-axis, try both left and right corner in case of auto legend + auto y-axis
    if legend:
      if legend=="auto":
        left           = canvas.topPad.GetLeftMargin() + yMax.GetTickLength('Y') + 0.01
        right          = 1 - canvas.topPad.GetRightMargin() - yMax.GetTickLength('Y') - 0.01
        top            = 1 - canvas.topPad.GetTopMargin() - yMax.GetTickLength() - 0.01
        bottom         = max(0.4, top - 0.045*sum(map(len, histos)))
        tryCoordinates = [(left, bottom, left+0.35, top), (right-0.35, bottom, right, top)]
      else:
        tryCoordinates = [legend]

      #Avoid overlap with the legend
      if yRange=="auto" or yRange[1]=="auto":
        self.ymax = None
        for coordinates in tryCoordinates:
          ymax = self.avoidLegendOverlap(canvas.topPad, yMax, coordinates, logY)
          if (not self.ymax) or ymax < self.ymax:
            self.ymax = ymax
            legendCoordinates = coordinates
      else:
        legendCoordinates = tryCoordinates[0]

    # Draw the histos
    same = ""
    for h in sum(histos, []):
      drawOption = h.drawOption if hasattr(h, "drawOption") else "hist"
      canvas.topPad.SetLogy(logY)
      canvas.topPad.SetLogx(logX)
      h.GetXaxis().SetRangeUser(self.xmin, self.xmax)
      h.GetYaxis().SetRangeUser(self.ymin, self.ymax)
      h.GetXaxis().SetTitle(self.texX)
      h.GetYaxis().SetTitle(self.texY)

      if ratio is None: h.GetYaxis().SetTitleOffset(1.6)
      else:             h.GetYaxis().SetTitleOffset(2.0)

      for modification in histModifications+self.histModifications: modification(h)

      h.Draw(drawOption+same)
      same = "same"

    canvas.topPad.RedrawAxis()

    for h in (s[0] for s in histos):
      if hasattr(h, 'sysValues'):
        drawObjects                     += self.getSystematicBoxes(h)
        if ratio: ratio['drawObjects']  += self.getSystematicBoxes(h, ratio=True)

    if legend: drawObjects += [self.getLegend(legendColumns, legendCoordinates, histos)]
    for o in drawObjects:
      try:    o.Draw()
      except: log.debug( "drawObjects has something I can't Draw(): %r", o)

    # Make a ratio plot
    if ratio:
      canvas.bottomPad.cd()
      num = histos[ratio['num']][0]
      den = histos[ratio['den']][0]

      h_ratio = num.Clone()
      h_ratio.Divide(den)

      if ratio['style']: ratio['style'](h_ratio)

      h_ratio.GetXaxis().SetTitle(self.texX)
      h_ratio.GetYaxis().SetTitle(ratio['texY'])

      h_ratio.GetXaxis().SetTitleOffset(3.2)
      h_ratio.GetYaxis().SetTitleOffset(2.0)

      h_ratio.GetXaxis().SetTickLength( 0.03*3 )
      h_ratio.GetYaxis().SetTickLength( 0.03*2 )

      h_ratio.GetYaxis().SetRangeUser(self.yrmin, self.yrmax)
      h_ratio.GetXaxis().SetRangeUser(self.xmin, self.xmax)
      h_ratio.GetYaxis().SetNdivisions(505)

      for modification in ratioModifications: modification(h_ratio)

      if num.drawOption == "e1":
        for bin in range(1, h_ratio.GetNbinsX()+1): h_ratio.SetBinError(bin, 0.0001)     # do not show error bars on hist, those are taken overf by the TGraphAsymmErrors
        h_ratio.Draw("e0")
        graph = self.makeRatioGraph(num, den)
        if den.drawOption == "e1":                                                       # show error bars from denominator
          graph2 = self.makeRatioGraph(den, den)
          graph2.Draw("0 same")
        graph.Draw("P0 same")
      else:
        h_ratio.Draw(num.drawOption)

      canvas.bottomPad.SetLogx(logX)
      canvas.bottomPad.SetLogy(ratio['logY'])

      ratio['drawObjects'] += [self.getRatioLine()]
      for o in ratio['drawObjects']:
        try:    o.Draw()
        except: log.debug( "ratio['drawObjects'] has something I can't Draw(): %r", o)

    try:    os.makedirs(plot_directory)
    except: pass
    copyIndexPHP(plot_directory)

    canvas.cd()

    if saveGitInfo: copyGitInfo(os.path.join(plot_directory, self.name + '.gitInfo'))
    log.info('Creating output files for ' + self.name)
    for extension in extensions:
      ofile = os.path.join(plot_directory, "%s.%s"%(self.name, extension))
      canvas.Print(ofile)
