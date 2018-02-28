import ROOT, uuid
ROOT.TH1.SetDefaultSumw2()

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
# A default canvas style, if yRatioWidth is specified a canvas.topPad and canvas.bottomPad are also created
#
def getDefaultCanvas(xWidth, yWidth, yRatioWidth=None):
  setDefault()

  if yRatioWidth:
    yWidth           += yRatioWidth
    bottomMargin      = yWidth/float(yRatioWidth)*ROOT.gStyle.GetPadBottomMargin()
    yBorder           = yRatioWidth/float(yWidth)

  canvas = ROOT.TCanvas(str(uuid.uuid4()), "canvas", 200,10, xWidth, yWidth)

  def getPad(canvas, number):
    pad = canvas.cd(number)
    pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())
    pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
    pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
    pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
    return pad

  if yRatioWidth:
    canvas.Divide(1,2,0,0)
    canvas.topPad = getPad(canvas, 1)
    canvas.topPad.SetBottomMargin(0)
    canvas.topPad.SetPad(canvas.topPad.GetX1(), yBorder, canvas.topPad.GetX2(), canvas.topPad.GetY2())
    canvas.bottomPad = getPad(canvas, 2)
    canvas.bottomPad.SetTopMargin(0)
    canvas.bottomPad.SetBottomMargin(bottomMargin)
    canvas.bottomPad.SetPad(canvas.bottomPad.GetX1(), canvas.bottomPad.GetY1(), canvas.bottomPad.GetX2(), yBorder)
  else:
    canvas.topPad = canvas

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


def errorStyle(color, markerStyle = 20, markerSize = 1):
  def func(histo):
    commonStyle(histo)
    histo.SetLineColor(color)
    histo.SetMarkerSize(markerSize)
    histo.SetMarkerStyle(20)
    histo.SetMarkerColor(color)
    histo.SetLineWidth(1)
    histo.SetFillColor(0)
    histo.SetFillStyle(0)
    histo.drawOption  ="e1"
    histo.legendStyle ='ep'
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
  lines =[
    (11, (0.15, 0.95, 'CMS Simulation' if isOnlySim else 'CMS Preliminary')),
    (31, (0.95, 0.95, ('%3.1f fb{}^{-1} (13 TeV)'%lumiScale) + ('Scale %3.2f'%dataMCScale if dataMCScale else '')))
  ]
  return [drawTex(l, align) for align, l in lines]
