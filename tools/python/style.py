import ROOT, uuid, math
ROOT.TH1.SetDefaultSumw2()

ttgStyle = True # Set to False to return back to original style

#
# Set default ROOT style script
#
def setDefault():
  ROOT.gROOT.SetBatch(True)
  ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/ttg/tools/scripts/tdrstyle.C")
  ROOT.setTDRStyle()
  ROOT.gROOT.SetStyle('tdrStyle')
  ROOT.gStyle.SetPaintTextFormat("3.2f")
  ROOT.gStyle.SetPadTopMargin(0.07)
  ROOT.gStyle.SetPadLeftMargin(0.15)
  ROOT.gStyle.SetPadRightMargin(0.05)
  ROOT.gStyle.SetPadBottomMargin(0.13)
  ROOT.gROOT.ForceStyle()

def setDefault2D(isColZ=False):
  setDefault()
  if isColZ: ROOT.gStyle.SetPadRightMargin(0.15)
  ROOT.gStyle.SetTitleX(0.005)
  ROOT.gStyle.SetTitleY(0.985)
  ROOT.gStyle.SetPalette(1)
  ROOT.gROOT.ForceStyle()


#
# General style as provided by the 1l group [but most of it seems to get overwritten later on]
#
def ttgGeneralStyle():
  ROOT.gStyle.SetFrameBorderMode(0)
  ROOT.gStyle.SetCanvasBorderMode(0)
  ROOT.gStyle.SetPadBorderMode(0)

  ROOT.gStyle.SetFrameFillColor(0)
  ROOT.gStyle.SetPadColor(0)
  ROOT.gStyle.SetCanvasColor(0)
  ROOT.gStyle.SetTitleColor(1)
  ROOT.gStyle.SetStatColor(0)

  ROOT.gStyle.SetPaperSize(20, 26)
  ROOT.gStyle.SetPadTopMargin(0.08)
  ROOT.gStyle.SetPadRightMargin(0.12)
  ROOT.gStyle.SetPadBottomMargin(0.11)
  ROOT.gStyle.SetPadLeftMargin(0.12)
  ROOT.gStyle.SetPadTickX(1)
  ROOT.gStyle.SetPadTickY(1)

  ROOT.gStyle.SetTextFont(42) #132
  ROOT.gStyle.SetTextSize(0.09)
  ROOT.gStyle.SetLabelFont(42, "xyz")
  ROOT.gStyle.SetTitleFont(42, "xyz")
  ROOT.gStyle.SetLabelSize(0.055, "xyz") #0.035
  ROOT.gStyle.SetTitleSize(0.055, "xyz")
  ROOT.gStyle.SetTitleOffset(1.18, "y")

  ROOT.gStyle.SetMarkerStyle(8)
  ROOT.gStyle.SetHistLineWidth(2)
  ROOT.gStyle.SetLineWidth(1)

  ROOT.gStyle.SetOptTitle(0)
  ROOT.gStyle.SetOptStat(0) #("m")
  ROOT.gStyle.SetOptFit(0)

  ROOT.gStyle.cd()
  ROOT.gROOT.ForceStyle()



#
# A default canvas style, if yRatioWidth is specified a canvas.topPad and canvas.bottomPad are also created
#
def getDefaultCanvas(ratio):
  if ttgStyle: xWidth, yWidth, yRatioWidth = 800, 600, (0 if ratio else None)
  else:        xWidth, yWidth, yRatioWidth = 520, 500, (200 if ratio else None)
  setDefault()
  ttgGeneralStyle()

  if yRatioWidth:
    yWidth           += yRatioWidth
    bottomMargin      = yWidth/float(yRatioWidth)*ROOT.gStyle.GetPadBottomMargin()
    yBorder           = yRatioWidth/float(yWidth)

  canvas = ROOT.TCanvas(str(uuid.uuid4()), "canvas", 200, 10, xWidth, yWidth)

  def ttgPadStyle(pad):
    pad.SetFillColor(0)
    pad.SetBorderMode(0)
    pad.SetFrameFillStyle(0)
    pad.SetFrameBorderMode(0)
    pad.SetTickx(0)
    pad.SetTicky(0)

  def getPad(canvas, number):
    pad = canvas.cd(number)
    pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())
    pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
    pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
    pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
    if ttgStyle: ttgPadStyle(pad)
    return pad

  def defaultRatioDivision(canvas):
    canvas.Divide(1, 2, 0, 0)
    canvas.topPad = getPad(canvas, 1)
    canvas.topPad.SetBottomMargin(0)
    canvas.topPad.SetPad(canvas.topPad.GetX1(), yBorder, canvas.topPad.GetX2(), canvas.topPad.GetY2())
    canvas.bottomPad = getPad(canvas, 2)
    canvas.bottomPad.SetTopMargin(0)
    canvas.bottomPad.SetBottomMargin(bottomMargin)
    canvas.bottomPad.SetPad(canvas.bottomPad.GetX1(), canvas.bottomPad.GetY1(), canvas.bottomPad.GetX2(), yBorder)

  def ttgRatioDivision(canvas):
    padRatio   = 0.25
    padOverlap = 0 # this is much larger for the 1l group, but simply adds a huge blank space for us
    padGap     = 0.01
    canvas.Divide(1, 2, 0, 0)
    canvas.topPad = getPad(canvas, 1)
    canvas.topPad.SetPad(canvas.topPad.GetX1(), padRatio-padOverlap, canvas.topPad.GetX2(), canvas.topPad.GetY2())
    canvas.bottomPad = getPad(canvas, 2)
    canvas.bottomPad.SetTopMargin(0)
    canvas.bottomPad.SetPad(canvas.bottomPad.GetX1(), canvas.bottomPad.GetY1(), canvas.bottomPad.GetX2(), padRatio+padOverlap)
    canvas.topPad.SetTopMargin(0.08/(1-padRatio+padOverlap))
    canvas.topPad.SetBottomMargin((padOverlap+padGap)/(1-padRatio+padOverlap))
    canvas.bottomPad.SetTopMargin((padOverlap)/(padRatio+padOverlap))
    canvas.bottomPad.SetBottomMargin(0.12/(padRatio+padOverlap))

  if ratio and ttgStyle: ttgRatioDivision(canvas)
  elif yRatioWidth:      defaultRatioDivision(canvas)
  else:                  canvas.topPad = canvas

  return canvas



#
# Get style functions which could be applied on the histograms
#
def commonStyle(histo):
  histo.GetXaxis().SetTitleFont(43)
  histo.GetYaxis().SetTitleFont(43)
  histo.GetXaxis().SetLabelFont(43)
  histo.GetYaxis().SetLabelFont(43)
  histo.GetXaxis().SetTitleSize(24)
  histo.GetYaxis().SetTitleSize(24)
  histo.GetXaxis().SetLabelSize(20)
  histo.GetYaxis().SetLabelSize(20)
  histo.GetYaxis().SetTitleOffset(1.5 if ttgStyle else 2)

def errorStyle(color, markerStyle = 20, markerSize = 1):
  def func(histo):
    commonStyle(histo)
    histo.SetLineColor(color)
    histo.SetMarkerSize(markerSize)
    histo.SetMarkerStyle(markerStyle)
    histo.SetMarkerColor(color)
    histo.SetLineWidth(1)
    histo.SetFillColor(0)
    histo.SetFillStyle(0)
    histo.drawOption  = "e1"
    histo.legendStyle = 'ep'
    return
  return func

def lineStyle(color, width = None, dotted=False, dashed=False):
  def func(histo):
    commonStyle(histo)
    histo.SetLineColor(color)
    histo.SetMarkerSize(0)
    histo.SetMarkerStyle(0)
    histo.SetFillColor(0)
    if dotted: histo.SetLineStyle(3)
    if dashed: histo.SetLineStyle(7)
    if width:  histo.SetLineWidth(width)
    histo.drawOption  = "hist"
    histo.legendStyle = "l"
    return
  return func

def fillStyle(color, lineColor = None):
  def func(histo):
    commonStyle(histo)
    histo.SetLineColor(lineColor if lineColor is not None else color)
    histo.SetMarkerSize(0)
    histo.SetMarkerStyle(0)
    histo.SetFillColor(color)
    histo.drawOption  = "hist"
    histo.legendStyle = "f"
    return
  return func


#
# drawTex function
#
def drawTex(line, align=11, size=0.04):
  tex = ROOT.TLatex()
  tex.SetNDC()
  tex.SetTextSize(size)
  tex.SetTextAlign(align)
  return tex.DrawLatex(*line)


#
# Common CMS information
#
def drawLumi(dataMCScale, lumiScale, isOnlySim=False):
  lines = [
    (11, (ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin(), 'CMS Simulation' if isOnlySim else 'CMS Preliminary')),
    (31, (1-ROOT.gStyle.GetPadRightMargin(), 1-ROOT.gStyle.GetPadTopMargin(), ('%3.1f fb{}^{-1} (13 TeV)'%lumiScale) + ('Scale %3.2f'%dataMCScale if dataMCScale else '')))
  ]
  return [drawTex(l, align) for align, l in lines]

#
# Coordinate tranformations between Axis and NDC
#
def fromAxisToNDC(pad, axisRange, coordinate, isY=False):
  log     = pad.GetLogy()           if isY else pad.GetLogx()
  minPad  = pad.GetBottomMargin()   if isY else pad.GetLeftMargin()
  maxPad  = (1.-pad.GetTopMargin()) if isY else (1.-pad.GetRightMargin())
  maxPad  = 1.-pad.GetTopMargin()   if isY else 1.-pad.GetRightMargin()
  minAxis = axisRange[0]
  maxAxis = axisRange[1]

  if log: return minPad + (math.log(coordinate)-math.log(minAxis))/(math.log(maxAxis)-math.log(minAxis))*(maxPad-minPad)
  else:   return minPad + (coordinate-minAxis)/(maxAxis-minAxis)*(maxPad-minPad)

def fromNDCToAxis(pad, axisRange, coordinate, isY=False):
  log     = pad.GetLogy()           if isY else pad.GetLogx()
  minPad  = pad.GetBottomMargin()   if isY else pad.GetLeftMargin()
  maxPad  = (1.-pad.GetTopMargin()) if isY else (1.-pad.GetRightMargin())
  minAxis = axisRange[0]
  maxAxis = axisRange[1]

  if log: return minAxis + math.exp((coordinate-minPad)/(maxPad-minPad)*(math.log(maxAxis)-math.log(minAxis)))
  else:   return minAxis + (coordinate-minPad)/(maxPad-minPad)*(maxAxis-minAxis)
