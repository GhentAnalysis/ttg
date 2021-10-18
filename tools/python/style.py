import ROOT, uuid, math
ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

ttgStyle = True # Set to False to return back to original style

#
# Set default ROOT style script
#
def setDefault():
  ROOT.gROOT.SetBatch(True)
  # loading a macro twice causes a crash in some ROOT versions
  try:
    ROOT.setTDRStyle()
  except:
    ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/ttg/tools/scripts/tdrstyle.C")
    ROOT.setTDRStyle()
  ROOT.gROOT.SetStyle('tdrStyle')
  ROOT.gStyle.SetPaintTextFormat("3.2f")
  ROOT.gStyle.SetPadTopMargin(0.07)
  ROOT.gStyle.SetPadLeftMargin(0.15)
  ROOT.gStyle.SetPadRightMargin(0.05)
  ROOT.gStyle.SetPadBottomMargin(0.16)
  ROOT.gROOT.ForceStyle()

def setDefault2D(isColZ=False):
  setDefault()
  if isColZ: ROOT.gStyle.SetPadRightMargin(0.15)
  # ROOT.gStyle.SetTitleX(0.5)
  # ROOT.gStyle.SetTitleOffset(0.1, 'X')
  ROOT.gStyle.SetTitleY(0.985)
  ROOT.gStyle.SetPadBottomMargin(0.11)
  ROOT.gStyle.SetPadRightMargin(0.15)
  ROOT.gStyle.SetPaintTextFormat("3.2f")
  ROOT.gStyle.SetTextSize(0.07)
  ROOT.gStyle.SetOptStat(0)
  ROOT.gStyle.SetPalette(95)
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
  ROOT.gStyle.SetPadRightMargin(0.09)
  ROOT.gStyle.SetPadBottomMargin(0.12)
  ROOT.gStyle.SetPadLeftMargin(0.15)
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

  canvas = ROOT.TCanvas('c' + str(uuid.uuid4()).replace('-','') , "canvas", 200, 10, xWidth, yWidth)

  def ttgPadStyle(pad):
    pad.SetFillColor(0)
    pad.SetBorderMode(0)
    pad.SetFrameFillStyle(0)
    pad.SetFrameBorderMode(0)
    pad.SetTickx(1)
    pad.SetTicky(1)

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
    padRatio   = 0.3
    padOverlap = 0 # this is much larger for the 1l group, but simply adds a huge blank space for us
    # padGap     = 0.01
    padGap     = 0.0
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
  histo.GetXaxis().SetTitleSize(30)
  histo.GetYaxis().SetTitleSize(30)
  histo.GetXaxis().SetLabelSize(30)
  histo.GetYaxis().SetLabelSize(30)
  histo.GetYaxis().SetTitleOffset(1.5 if ttgStyle else 2)
  histo.GetXaxis().SetTitleOffset(0.7 if ttgStyle else 2)

def errorStyle(color, markerStyle = 20, markerSize = 1.3):
  def func(histo):
    commonStyle(histo)
    histo.SetLineColor(color)
    histo.SetMarkerSize(markerSize)
    histo.SetMarkerStyle(markerStyle)
    histo.SetMarkerColor(color)
    histo.SetLineWidth(2)
    histo.SetFillColor(0)
    histo.SetFillStyle(0)
    histo.drawOption  = "e"
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
def drawTex(line, align=11, size=0.045, angle=0):
  tex = ROOT.TLatex()
  tex.SetNDC()
  tex.SetTextSize(size)
  tex.SetTextAlign(align)
  tex.SetTextAngle(angle)
  tex.SetTextFont(42)
  return tex.DrawLatex(*line)


#
# Common CMS information
#
def drawLumi(dataMCScale, lumiScale, isOnlySim=False):
  lines = [
    (11, (ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.01, "#bf{CMS} #it{Simulation}" if isOnlySim else "#bf{CMS} #it{Preliminary}")),
    (31, (1-ROOT.gStyle.GetPadRightMargin()-0.04, 1-ROOT.gStyle.GetPadTopMargin()+0.01, ("%3.0f fb{}^{#minus 1} (13 TeV)"%lumiScale) + ("Scale %3.2f"%dataMCScale if dataMCScale else '')))

  ]
  return [drawTex(l, align, size=0.07) for align, l in lines]

def drawLumi2D(dataMCScale, lumiScale, isOnlySim=False):
  lines = [
    (11, (ROOT.gStyle.GetPadLeftMargin()+0.05,  1-ROOT.gStyle.GetPadTopMargin()+0.015, "#bf{CMS} #it{Simulation}" if isOnlySim else "#bf{CMS} #it{Preliminary}")),
    (31, (1-ROOT.gStyle.GetPadRightMargin()-0.04, 1-ROOT.gStyle.GetPadTopMargin()+0.015, ("%3.0f fb{}^{#minus 1} (13 TeV)"%lumiScale) + ("Scale %3.2f"%dataMCScale if dataMCScale else '')))

  ]
  return [drawTex(l, align, size=0.04) for align, l in lines]

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
