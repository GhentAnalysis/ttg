from ttg.tools.logger import getLogger
log = getLogger()

#
# Plot class
# Still messy but it works reasonably 
#
import ROOT, os, pickle, uuid
from math import sqrt
from ttg.tools.helpers import copyIndexPHP
from ttg.tools.lock import waitForLock, removeLock

def getLegendMaskedArea(legend_coordinates, pad):
  def constrain(x, interval=[0,1]):
    if x<interval[0]: return interval[0]
    elif x>=interval[0] and x<interval[1]: return x
    else: return interval[1]

  return {'yLowerEdge': constrain( 1.-(1.-legend_coordinates[1] - pad.GetTopMargin())/(1.-pad.GetTopMargin()-pad.GetBottomMargin()), interval=[0.3, 1] ),
          'xLowerEdge': constrain( (legend_coordinates[0] - pad.GetLeftMargin())/(1.-pad.GetLeftMargin()-pad.GetRightMargin()), interval = [0, 1] ),
          'xUpperEdge': constrain( (legend_coordinates[2] - pad.GetLeftMargin())/(1.-pad.GetLeftMargin()-pad.GetRightMargin()), interval = [0, 1] )}



#
# Plot class
#
class Plot:
  defaultStack        = None
  defaultTexY         = None
  defaultOverflowBin  = None

  @staticmethod
  def setDefaults(stack = None, texY="Events", overflowBin='upper'):
      Plot.defaultStack        = stack
      Plot.defaultTexY         = texY
      Plot.defaultOverflowBin  = overflowBin

  def __init__(self, name, texX, varX, binning, stack=None, texY=None, overflowBin=None):
    self.stack       = stack       if stack else Plot.defaultStack
    self.texY        = texY        if texY else Plot.defaultTexY
    self.overflowBin = overflowBin if overflowBin else Plot.defaultOverflowBin
    self.name        = name
    self.texX        = texX
    self.varX        = varX


    if type(binning)==type([]):   self.binning = (len(binning)-1, numpy.array(binning))
    elif type(binning)==type(()): self.binning = binning

    self.histos = {}
    for s in sum(self.stack, []):
      name           = self.name + s.name
      self.histos[s] = ROOT.TH1F(name, name, *self.binning)


  def fill(self, sample, weight=1.):
    self.histos[sample].Fill(self.varX(sample.chain), weight)


  #
  # Add an overflow bin, optionally called from the draw function
  #
  def addOverFlowBin1D(self, histo, addOverFlowBin = None):
    if addOverFlowBin is not None and not hasattr(histo, 'overflowApplied'):
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
        factor = 1./stack[0].Integral()
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

        factor = histos[target][0].Integral()/source_yield
        for h in histos[source]: h.Scale(factor)

  #
  # Save the histogram to a results.cache file, useful when you need to to further operations on it later
  #
  def saveToCache(self, dir):
    try:    os.makedirs(os.path.join(dir))
    except: pass

    resultFile = os.path.join(dir, 'results.pkl')

    waitForLock(resultFile)
    if os.path.exists(resultFile):
      allPlots = pickle.load(file(resultFile))
      allPlots.update({self.name : self.histos})
    else:
      allPlots = {self.name : self.histos}
    pickle.dump(allPlots, file(resultFile, 'w'))
    removeLock(resultFile)
    log.info("Plot " + self.name + " saved to cache")

  def getYields(self, bin=None):
    if bin: return {s.name : h.GetBinContent(bin) for s,h in self.histos.iteritems()}
    else:   return {s.name : h.Integral()         for s,h in self.histos.iteritems()}


  #
  # Draw function roughly stolen from Robert's RootTools, might need some cleanup, very lengthy
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

    import ttg.tools.style as style
    style.setDefault()
    defaultRatioStyle = {'num':1, 'den':0, 'logY':False, 'style':None, 'texY': 'Data / MC', 'yRange': (0.5, 1.5), 'drawObjects':[]}

    # default_widths    
    default_widths = {'y_width':500, 'x_width':500, 'y_ratio_width':200}
    if ratio is not None: default_widths['x_width'] = 520
    default_widths.update(widths)

    # Make sure ratio dict has all the keys by updating the default
    if ratio is not None:
      if type(ratio)!=type({}): raise ValueError( "'ratio' must be dict (default: {}). General form is '%r'." % defaultRatioStyle)
      defaultRatioStyle.update(ratio)
      ratio = defaultRatioStyle

    histDict = {i: h.Clone() for i, h in self.histos.iteritems()}

    # Apply style to histograms and add overflow bin
    for s, h in histDict.iteritems():
      if hasattr(s, 'style'): s.style(h)
      h.texName = s.texName
      self.addOverFlowBin1D(h, self.overflowBin)

    # Transform histDict --> histos where the stacks are added up
    # Note self.stack is of form [[A1, A2, A3,...],[B1,B2,...],...] where the sublists need to be stacked
    histos = []
    for stack in self.stack:
      histsToStack = [histDict[s] for s in stack]
      histos.append(self.stackHists(histsToStack))


    self.scaleStacks(histos, scaling)

    # Make canvas and if there is a ratio plot adjust the size of the pads
    if ratio is not None:
      default_widths['y_width'] += default_widths['y_ratio_width']
      scaleFacRatioPad           = default_widths['y_width']/float(default_widths['y_ratio_width'])
      y_border                   = default_widths['y_ratio_width']/float(default_widths['y_width'])

    # delete canvas if it exists
    if hasattr("ROOT","c1"): del ROOT.c1 
    c1 = ROOT.TCanvas(self.name + str(uuid.uuid4()), "drawHistos",200,10, default_widths['x_width'], default_widths['y_width'])

    if ratio is not None:
        c1.Divide(1,2,0,0)
        topPad = c1.cd(1)
        topPad.SetBottomMargin(0)
        topPad.SetLeftMargin(0.15)
        topPad.SetTopMargin(0.07)
        topPad.SetRightMargin(0.05)
        topPad.SetPad(topPad.GetX1(), y_border, topPad.GetX2(), topPad.GetY2())
        bottomPad = c1.cd(2)
        bottomPad.SetTopMargin(0)
        bottomPad.SetRightMargin(0.05)
        bottomPad.SetLeftMargin(0.15)
        bottomPad.SetBottomMargin(scaleFacRatioPad*0.13)
        bottomPad.SetPad(bottomPad.GetX1(), bottomPad.GetY1(), bottomPad.GetX2(), y_border)
    else:
        topPad = c1
        topPad.SetBottomMargin(0.13)
        topPad.SetLeftMargin(0.15)
        topPad.SetTopMargin(0.07)
        topPad.SetRightMargin(0.05)

    for modification in canvasModifications: modification(c1)

    topPad.cd()

    # Range on y axis: Start with default
    if not yRange=="auto" and not (type(yRange)==type(()) and len(yRange)==2):
      raise ValueError( "'yRange' must bei either 'auto' or (yMin, yMax) where yMin/Max can be 'auto'. Got: %r"%yRange )

    max_ = max(l[0].GetMaximum() for l in histos)
    min_ = min(l[0].GetMinimum() for l in histos)

    # If legend is in the form (tuple, int) then the number of columns is provided
    legendColumns = 1
    if len(legend) == 2:
      legendColumns = legend[1]
      legend        = legend[0]

    #Calculate legend coordinates in gPad coordinates
    if legend is not None:
      if legend=="auto": legendCoordinates = (0.50,0.9-0.05*sum(map(len, histos)),0.92,0.9)
      else:              legendCoordinates = legend 

    if logY:
      yMax_ = 10**0.5*max_
      yMin_ = 0.7
    else:
      yMax_ = 1.2*max_
      yMin_ = 0 if min_>0 else 1.2*min_
    if type(yRange)==type(()) and len(yRange)==2:
      yMin_ = yRange[0] if not yRange[0]=="auto" else yMin_
      yMax_ = yRange[1] if not yRange[1]=="auto" else yMax_

    #Avoid overlap with the legend
    if (yRange=="auto" or yRange[1]=="auto") and (legend is not None):
      scaleFactor = 1
      # Get x-range and y
      legendMaskedArea = getLegendMaskedArea(legendCoordinates, topPad)
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
      topPad.SetLogy(logY)
      topPad.SetLogx(logX)
      h.GetYaxis().SetRangeUser(yMin_, yMax_)
      h.GetXaxis().SetTitle(self.texX)
      h.GetYaxis().SetTitle(self.texY)
      # precision 3 fonts. see https://root.cern.ch/root/htmldoc//TAttText.html#T5
      h.GetXaxis().SetTitleFont(43)
      h.GetYaxis().SetTitleFont(43)
      h.GetXaxis().SetLabelFont(43)
      h.GetYaxis().SetLabelFont(43)
      h.GetXaxis().SetTitleSize(24)
      h.GetYaxis().SetTitleSize(24)
      h.GetXaxis().SetLabelSize(20)
      h.GetYaxis().SetLabelSize(20)

      if ratio is None: h.GetYaxis().SetTitleOffset(1.3)
      else:             h.GetYaxis().SetTitleOffset(1.6)

      for modification in histModifications: modification(h)

      if drawOption=="e1": dataHist = h
      h.Draw(drawOption+same)
      same = "same"

    topPad.RedrawAxis()
    # Make the legend
    if legend is not None:
      legend_ = ROOT.TLegend(*legendCoordinates)
      legend_.SetNColumns(legendColumns)
      legend_.SetFillStyle(0)
      legend_.SetShadowColor(ROOT.kWhite)
      legend_.SetBorderSize(0)
      for h in sum(histos, []): legend_.AddEntry(h, h.texName, h.legendStyle)
      legend_.Draw()

    for o in drawObjects:
      try:    o.Draw()
      except: log.debug( "drawObjects has something I can't Draw(): %r", o)

    # Make a ratio plot
    if ratio is not None:
      bottomPad.cd()
      num = histos[ratio['num']][0]
      den = histos[ratio['den']][0]
      h_ratio = num.Clone()
      h_ratio.Divide(den)

      if ratio['style'] is not None: ratio['style'](h_ratio) 

      h_ratio.GetXaxis().SetTitle(self.texX)
      h_ratio.GetYaxis().SetTitle(ratio['texY'])

      h_ratio.GetXaxis().SetTitleFont(43)
      h_ratio.GetYaxis().SetTitleFont(43)
      h_ratio.GetXaxis().SetLabelFont(43)
      h_ratio.GetYaxis().SetLabelFont(43)
      h_ratio.GetXaxis().SetTitleSize(24)
      h_ratio.GetYaxis().SetTitleSize(24)
      h_ratio.GetXaxis().SetLabelSize(20)
      h_ratio.GetYaxis().SetLabelSize(20)

      h_ratio.GetXaxis().SetTitleOffset( 3.2 )
      h_ratio.GetYaxis().SetTitleOffset( 1.6 )

      h_ratio.GetXaxis().SetTickLength( 0.03*3 )
      h_ratio.GetYaxis().SetTickLength( 0.03*2 )


      h_ratio.GetYaxis().SetRangeUser( *ratio['yRange'] )
      h_ratio.GetYaxis().SetNdivisions(505)

      for modification in ratioModifications: modification(h_ratio)

      drawOption = num.drawOption if hasattr(num, "drawOption") else "hist"
      if drawOption == "e1":                          # hacking to show error bars within panel when central value is off scale
        graph = ROOT.TGraphAsymmErrors(dataHist)      # cloning from datahist in order to get layout
        graph.Set(0)
        for bin in range(1, h_ratio.GetNbinsX()+1):
          if den.GetBinContent(bin) > 0 and den.GetBinContent(bin) > 0:
	    h_ratio.SetBinError(bin, 0.0001)          # do not show error bars on hist, those are taken overf by the TGraphAsymmErrors
	    center  = h_ratio.GetBinCenter(bin)
	    val     = h_ratio.GetBinContent(bin)
	    errUp   = num.GetBinErrorUp(bin)/den.GetBinContent(bin) if val > 0 else 0
	    errDown = num.GetBinErrorLow(bin)/den.GetBinContent(bin) if val > 0 else 0
	    graph.SetPoint(bin, center, val)
	    graph.SetPointError(bin, 0, 0, errDown, errUp)
        h_ratio.Draw("e0")
        graph.Draw("P0 same")
      else:
        h_ratio.Draw(drawOption)

      bottomPad.SetLogx(logX)
      bottomPad.SetLogy(ratio['logY'])

      line = ROOT.TPolyLine(2)
      line.SetPoint(0, h_ratio.GetXaxis().GetXmin(), 1.)
      line.SetPoint(1, h_ratio.GetXaxis().GetXmax(), 1.)
      line.SetLineWidth(1)
      line.Draw()

      for o in ratio['drawObjects']:
        try:    o.Draw()
        except: log.debug( "ratio['drawObjects'] has something I can't Draw(): %r", o)

    try:    os.makedirs(plot_directory)
    except: pass
    copyIndexPHP(plot_directory)

    c1.cd()

    log.info('Creating output files for ' + self.name)
    for extension in extensions:
      ofile = os.path.join( plot_directory, "%s.%s"%(self.name, extension) )
      c1.Print( ofile )
    del c1
