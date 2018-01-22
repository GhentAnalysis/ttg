from ttg.tools.logger import getLogger
log = getLogger()

#
# Plot class
# Still messy but it works reasonably
#
import ROOT, os, uuid, numpy
import cPickle as pickle
from math import sqrt
from ttg.tools.helpers import copyIndexPHP, copyGitInfo
from ttg.tools.lock import waitForLock, removeLock

def getLegendMaskedArea(legend_coordinates, pad):
  def constrain(x, interval=[0,1]):
    if x<interval[0]: return interval[0]
    elif x>=interval[0] and x<interval[1]: return x
    else: return interval[1]

  return {'yLowerEdge': constrain( 1.-(1.-legend_coordinates[1] - pad.GetTopMargin())/(1.-pad.GetTopMargin()-pad.GetBottomMargin()), interval=[0.3, 1] ),
          'xLowerEdge': constrain( (legend_coordinates[0] - pad.GetLeftMargin())/(1.-pad.GetLeftMargin()-pad.GetRightMargin()), interval = [0, 1] ),
          'xUpperEdge': constrain( (legend_coordinates[2] - pad.GetLeftMargin())/(1.-pad.GetLeftMargin()-pad.GetRightMargin()), interval = [0, 1] )}

def getHistFromPkl(resultFile, plotName, selector):
  waitForLock(resultFile)
  with open(resultFile, 'rb') as f: allPlots = pickle.load(f)
  removeLock(resultFile)
  filtered    = {s:h for s,h in allPlots[plotName].iteritems() if all(s.count(sel) for sel in selector)}
  if   len(filtered) == 1: return filtered[filtered.keys()[0]]
  elif len(filtered) > 1:  log.error('Multiple possibilities to look for ' + str(selector) + ': ' + str(filtered.keys()))
  else:                    log.error('Missing ' + str(selector) + ' for plot ' + plotName + ' in ' + resultFile)

def xAxisLabels(labels):
  def applyLabels(h):
    for i,l in enumerate(labels):
      h.GetXaxis().SetBinLabel(i+1, l)
  return [applyLabels]

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
        factor = 1./stack[0].Integral()
        for h in stack: h.Scale(factor)
    else:
      from ttg.tools.style import drawTex
      if not isinstance(scaling, dict):
        raise ValueError( "'scaling' must be of the form {0:1, 2:3} which normalizes stack[0] to stack[1] etc. Got '%r'" % scaling )
      for source, target in scaling.iteritems():
        if not (isinstance(source, int) and isinstance(target, int) ):
          raise ValueError( "Scaling should be {0:1, 1:2, ...}. Expected ints, got %r %r"%( source, target ) )

        source_yield = histos[source][0].Integral()

        if source_yield == 0:
          log.warning( "Requested to scale empty Stack? Do nothing." )
          continue

        factor = histos[target][0].Integral()/source_yield
        for h in histos[source]: h.Scale(factor)
        if len(scaling) == 1: return [drawTex((0.2, 0.8, 'Scaling: %.2f' % factor))]
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
    waitForLock(resultFile)
    try:
      if os.path.exists(resultFile):
        with open(resultFile, 'rb') as f:
          allPlots = pickle.load(f)
          allPlots.update({plotName : histos})
      else:
        allPlots = {plotName : histos}
      with open(resultFile, 'wb') as f:
        pickle.dump(allPlots, f)
      log.info("Plot " + plotName + " saved to cache")
    except:
      log.warning("Could not save " + plotName + " to cache")
    removeLock(resultFile)


  #
  # Load from cache
  #
  def loadFromCache(self, resultsDir):
    resultsFile = os.path.join(resultsDir, self.name + '.pkl')
    waitForLock(resultsFile)
    with open(resultsFile, 'rb') as f:
      allPlots = pickle.load(f)
    removeLock(resultsFile)
    try:
      for s in self.histos.keys():
        self.histos[s] = allPlots[self.name][s.name+s.texName]
    except:
      return True

  #
  # Get Yields
  #
  def getYields(self, bin=None):
    if bin: return {s.name : h.GetBinContent(bin) for s,h in self.histos.iteritems()}
    else:   return {s.name : h.Integral()         for s,h in self.histos.iteritems()}


  #
  # Normalize binwidth when non-unifor bin width is used
  #
  def normalizeBinWidth(self, hist, norm=None):
    if norm:
      for i in range(hist.GetXaxis().GetNbins()+1):
        val   = hist.GetBinContent(i)
        err   = hist.GetBinError(i)
        width = hist.GetBinWidth(i)
        hist.SetBinContent(i, val/(width/norm))
        hist.SetBinError(i, err/(width/norm))


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
  def getRatioLine(self, min, max):
    line = ROOT.TPolyLine(2)
    line.SetPoint(0, min, 1.)
    line.SetPoint(1, max, 1.)
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
  # Adding systematics to MC (assuming MC is first in the stack list)
  #
  def getSystematicBand(self, systematics, linearSystematics, resultsDir):
    resultsFile = os.path.join(resultsDir, self.name + '.pkl')
    waitForLock(resultsFile)
    with open(resultsFile, 'rb') as f:
      allPlots = pickle.load(f)
    removeLock(resultsFile)

    def sumHistos(list):
      sum = list[0].Clone()
      for h in list[1:]: sum.Add(h)
      return sum

    histNames = [s.name+s.texName for s in self.stack[0]]

    histos_summed = {}
    for sys in systematics.keys() + [None]:
      plotName = self.name+(sys if sys else '')
      if plotName not in allPlots.keys(): log.error('No ' + sys + ' variation found for ' +  self.name)
      for histName in histNames:
        h = allPlots[plotName][histName]
        if h.Integral()==0: log.warning("Found empty histogram %s:%s in %s/%s.pkl. Please rerun with --runSys option first.", plotName, histName, resultsDir, self.name)
        self.addOverFlowBin1D(h, self.overflowBin)
        self.normalizeBinWidth(h, self.normBinWidth)

      histos_summed[sys] = sumHistos([allPlots[plotName][histName] for histName in histNames])
      # TODO: need to scale something?

    sysList = [sys.replace('Up','') for sys in systematics if sys.count('Up')]

    h_sys = {}
    for sys in sysList:
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

    # Divide by the summed hist to get relative errors
    h_rel_err.Divide(histos_summed[None])

    boxes = []
    ratio_boxes = []
    for ib in range(1, 1 + h_rel_err.GetNbinsX() ):
      val = histos_summed[None].GetBinContent(ib)
      if val<0: continue
      sys = h_rel_err.GetBinContent(ib)
      box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max([0.003, (1-sys)*val]), h_rel_err.GetXaxis().GetBinUpEdge(ib), max([0.003, (1+sys)*val]) )
      box.SetLineColor(ROOT.kBlack)
      box.SetFillStyle(3444)
      box.SetFillColor(ROOT.kBlack)
      r_box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max(0.1, 1-sys), h_rel_err.GetXaxis().GetBinUpEdge(ib), min(1.9, 1+sys) )
      r_box.SetLineColor(ROOT.kBlack)
      r_box.SetFillStyle(3444)
      r_box.SetFillColor(ROOT.kBlack)
      boxes.append( box )
      ratio_boxes.append( r_box )

    return boxes, ratio_boxes







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
          resultsDir = None,
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

    histDict = {i: h.Clone() for i, h in self.histos.iteritems()}

    # Apply style to histograms + normalize bin width + add overflow bin
    for s, h in histDict.iteritems():
      if hasattr(s, 'style'): s.style(h)
      h.texName = s.texName
      self.normalizeBinWidth(h, self.normBinWidth)
      self.addOverFlowBin1D(h, self.overflowBin)

    # Transform histDict --> histos where the stacks are added up
    # Note self.stack is of form [[A1, A2, A3,...],[B1,B2,...],...] where the sublists need to be stacked
    histos = []
    for stack in self.stack:
      histsToStack = [histDict[s] for s in stack]
      histos.append(self.stackHists(histsToStack))

    drawObjects += self.scaleStacks(histos, scaling)

    # Get the canvas, which includes canvas.topPad and canvas.bottomPad
    import ttg.tools.style as style
    canvas = style.getDefaultCanvas(default_widths['x_width'], default_widths['y_width'], default_widths['y_ratio_width'])
    for modification in canvasModifications: modification(canvas)

    canvas.topPad.cd()

    # Range on y axis
    max_ = max(l[0].GetMaximum() for l in histos)
    min_ = min(l[0].GetMinimum() for l in histos)

    if logY: (yMin_, yMax_) = (0.7, 10**0.5*max_)
    else:    (yMin_, yMax_) = (0 if min_>0 else 1.2*min_, 1.2*max_)

    if type(yRange)==type(()) and len(yRange)==2:
      yMin_ = yRange[0] if not yRange[0]=="auto" else yMin_
      yMax_ = yRange[1] if not yRange[1]=="auto" else yMax_


    # If legend is in the form (tuple, int) then the number of columns is provided
    if len(legend) == 2: legendColumns, legend = legend[1], legend[0]
    else:                legendColumns, legend = 1, legend

    #Calculate legend coordinates in gPad coordinates
    if legend:
      if legend=="auto": legendCoordinates = (0.50,0.9-0.05*sum(map(len, histos)),0.92,0.9)
      else:              legendCoordinates = legend

    #Avoid overlap with the legend
    if (yRange=="auto" or yRange[1]=="auto") and legend:
      scaleFactor = 1
      # Get x-range and y
      legendMaskedArea = getLegendMaskedArea(legendCoordinates, canvas.topPad)
      for histo in [h[0] for h in histos]:
        for i in range(1, 1 + histo.GetNbinsX()):
          # low/high bin edge in the units of the x axis
          xLowerEdge_axis = histo.GetBinLowEdge(i)
          xUpperEdge_axis = histo.GetBinLowEdge(i)+histo.GetBinWidth(i)
          # linear transformation to gPad system
          xLowerEdge  = (xLowerEdge_axis - histo.GetXaxis().GetXmin())/(histo.GetXaxis().GetXmax() - histo.GetXaxis().GetXmin())
          xUpperEdge  = (xUpperEdge_axis - histo.GetXaxis().GetXmin())/(histo.GetXaxis().GetXmax() - histo.GetXaxis().GetXmin())

          # maximum allowed fraction in given bin wrt to the legendMaskedArea: Either all (1) or legendMaskedArea['yLowerEdge']
          if xUpperEdge>legendMaskedArea['xLowerEdge'] and xLowerEdge<legendMaskedArea['xUpperEdge']: maxFraction = legendMaskedArea['yLowerEdge']
          else:                                                                                       maxFraction = 1
          maxFraction *=0.8

          # Use: (y - yMin_) / (sf*yMax_ - yMin_) = maxFraction (and y->log(y) in log case).
          # Compute the maximum required scale factor s.
          y = histo.GetBinContent(i)
          try:
            if logY: new_sf = yMin_/yMax_*(y/yMin_)**(1./maxFraction) if y>0 else 1
            else:    new_sf = 1./yMax_*(yMin_ + (y-yMin_)/maxFraction )
            scaleFactor = new_sf if new_sf>scaleFactor else scaleFactor
          except ZeroDivisionError:
            pass

      # Apply scale factor to avoid legend
      yMax_ = scaleFactor*yMax_

    # Draw the histos
    same = ""
    for h in sum(histos, []):
      drawOption = h.drawOption if hasattr(h, "drawOption") else "hist"
      canvas.topPad.SetLogy(logY)
      canvas.topPad.SetLogx(logX)
      h.GetYaxis().SetRangeUser(yMin_, yMax_)
      h.GetXaxis().SetTitle(self.texX)
      h.GetYaxis().SetTitle(self.texY)

      if ratio is None: h.GetYaxis().SetTitleOffset(1.3)
      else:             h.GetYaxis().SetTitleOffset(1.6)

      for modification in histModifications+self.histModifications: modification(h)

      h.Draw(drawOption+same)
      same = "same"

    canvas.topPad.RedrawAxis()

    if len(systematics) or len(linearSystematics):
      boxes, ratioBoxes                = self.getSystematicBand(systematics, linearSystematics, resultsDir)
      drawObjects                     += boxes
      if ratio: ratio['drawObjects']  += ratioBoxes

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

      h_ratio.GetXaxis().SetTitleOffset( 3.2 )
      h_ratio.GetYaxis().SetTitleOffset( 1.6 )

      h_ratio.GetXaxis().SetTickLength( 0.03*3 )
      h_ratio.GetYaxis().SetTickLength( 0.03*2 )

      h_ratio.GetYaxis().SetRangeUser( *ratio['yRange'] )
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

      ratio['drawObjects'] += [self.getRatioLine(h_ratio.GetXaxis().GetXmin(), h_ratio.GetXaxis().GetXmax())]
      for o in ratio['drawObjects']:
        try:    o.Draw()
        except: log.debug( "ratio['drawObjects'] has something I can't Draw(): %r", o)

    try:    os.makedirs(plot_directory)
    except: pass
    copyIndexPHP(plot_directory)

    canvas.cd()

    copyGitInfo(os.path.join(plot_directory, self.name + '.gitInfo'))
    log.info('Creating output files for ' + self.name)
    for extension in extensions:
      ofile = os.path.join(plot_directory, "%s.%s"%(self.name, extension))
      canvas.Print(ofile)
