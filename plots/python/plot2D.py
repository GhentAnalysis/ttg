from ttg.tools.logger import getLogger
log = getLogger()

#
# Plot2D class
# Still messy but it works reasonably
# Maybe to be merged with the 1D plot class
#
import ROOT, os, pickle, uuid
from ttg.tools.helpers import copyIndexPHP
from ttg.tools.lock import waitForLock, removeLock

#
# Plot class
#
class Plot2D:
  defaultStack        = None

  @staticmethod
  def setDefaults(stack = None):
      Plot2D.defaultStack        = stack

  def __init__(self, name, texX, varX, binningX, texY, varY, binningY, stack=None):
    self.stack       = stack       if stack else Plot2D.defaultStack
    self.name        = name
    self.texX        = texX
    self.texY        = texY
    self.varX        = varX
    self.varY        = varY

    if type(binningX)==type([]):   self.binningX = (len(binningX)-1, numpy.array(binningX))
    elif type(binningX)==type(()): self.binningX = binningX

    if type(binningY)==type([]):   self.binningY = (len(binningY)-1, numpy.array(binningY))
    elif type(binningY)==type(()): self.binningY = binningY

    self.histos = {}
    for s in sum(self.stack, []):
      name           = self.name + s.name
      self.histos[s] = ROOT.TH2F(name, name, *(self.binningX+self.binningY))


  def fill(self, sample, weight=1.):
    self.histos[sample].Fill(self.varX(sample.chain), self.varY(sample.chain), weight)


  #
  # Stacking the hist, called during the draw function
  #
  def stackHists(self, histsToStack, sorting=True):
    if sorting: histsToStack.sort(key=lambda h  : -h.Integral())

    # Add up stacks
    for i, h in enumerate(histsToStack):
      for j in range(i+1, len(histsToStack)):
        histsToStack[i].Add(histsToStack[j])

    return histsToStack[:1] # do not show sub-contributions in 2D


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

  def getYields(self, binX=None, binY=None):
    if binX and binY: return {s.name : h.GetBinContent(binX, binY) for s,h in self.histos.iteritems()}
    else:             return {s.name : h.Integral()                for s,h in self.histos.iteritems()}


  #
  # Draw function roughly stolen from Robert's RootTools, might need some cleanup, very lengthy
  #
  def draw(self, \
	  zRange = None,
          scaling = {}, 
	  extensions = ["pdf", "png", "root","C"], 
	  plot_directory = ".", 
	  logX = False, logY = False, logZ = True, 
	  drawObjects = [],
          drawOption = 'COLZ',
	  widths = {},
	  ):
    ''' plot: a Plot2D instance
	zRange: None ( = ROOT default) or [low, high] 
	extensions: ["pdf", "png", "root"] (default)
	logX: True/False (default), logY: True/False(default), logZ: True/False(default)
	drawObjects = [] Additional ROOT objects that are called by .Draw() 
	widths = {} (default) to update the widths. Values are {'y_width':500, 'x_width':500, 'y_ratio_width':200}
    '''

    import ttg.tools.style as style
    style.setDefault2D(drawOption=='COLZ')

    # default_widths    
    default_widths = {'y_width':500, 'x_width':500, 'y_ratio_width':200}
    default_widths.update(widths)

    histDict = {i: h.Clone() for i, h in self.histos.iteritems()}

    # Apply style to histograms and add overflow bin
    for s, h in histDict.iteritems():
      if hasattr(s, 'style2D'): s.style2D(h)
      h.texName = s.texName

    # Transform histDict --> histos where the stacks are added up
    # Note self.stack is of form [[A1, A2, A3,...],[B1,B2,...],...] where the sublists need to be stacked
    histos = []
    for stack in self.stack:
      histsToStack = [histDict[s] for s in stack]
      histos.append(self.stackHists(histsToStack))

    self.scaleStacks(histos, scaling)

    # delete canvas if it exists
    if hasattr("ROOT","c1"): del ROOT.c1 
    c1 = ROOT.TCanvas("ROOT.c1", "drawHistos", 200,10, default_widths['x_width'], default_widths['y_width'])

    c1.SetLogx(logX)
    c1.SetLogy(logY)
    c1.SetLogz(logZ)

    same = ""
    for histo in (sum(histos, []) if drawOption.count('SCAT') else histos[0]):
      histo.SetTitle('')
      histo.GetXaxis().SetTitle(self.texX)
      histo.GetYaxis().SetTitle(self.texY)
      if zRange is not None:
	  histo.GetZaxis().SetRangeUser( *zRange )
      # precision 3 fonts. see https://root.cern.ch/root/htmldoc//TAttText.html#T5
      histo.GetXaxis().SetTitleFont(43)
      histo.GetYaxis().SetTitleFont(43)
      histo.GetXaxis().SetLabelFont(43)
      histo.GetYaxis().SetLabelFont(43)
      histo.GetXaxis().SetTitleSize(24)
      histo.GetYaxis().SetTitleSize(24)
      histo.GetXaxis().SetLabelSize(20)
      histo.GetYaxis().SetLabelSize(20)

      # should probably go into a styler

      histo.Draw(drawOption+same)
      same = "same"

    c1.RedrawAxis()

    for o in drawObjects:
      try:    o.Draw()
      except: log.debug( "drawObjects has something I can't Draw(): %r", o)

    try:    os.makedirs(plot_directory)
    except: pass
    copyIndexPHP(plot_directory)

    log.info('Creating output files for ' + self.name)
    for extension in extensions:
      ofile = os.path.join( plot_directory, "%s.%s"%(self.name, extension) )
      c1.Print( ofile )
    del c1
