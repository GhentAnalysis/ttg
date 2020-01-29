#!/usr/bin/env python
import ROOT
import sys, os


ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import os, argparse, sys
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--year',           action='store',      default=None)
argParser.add_argument('--dyExternal',     action='store_true')
argParser.add_argument('--dyExternalAll',  action='store_true')
args = argParser.parse_args()

extra = '_dyExternalAll' if args.dyExternalAll else ('_dyExternal' if args.dyExternal else '_new')

from ttg.tools.helpers import getObjFromFile, copyIndexPHP
import glob
def getPlot(path, name):
  h = None
  for f in glob.glob(path):
    if h: h.Add(getObjFromFile(f, name))
    else: h = getObjFromFile(f, name)
  if not h:
    print 'Did not find plot %s in %s!' % (name, path)
    ROOT.TFile(f).ls()
  return h

def getPlotNames():
  f = ROOT.TFile(glob.glob(args.year + '_new/*/*.root')[0])
  for k in f.GetListOfKeys():
    yield k.GetName()

ROOT.gROOT.LoadMacro('danystyle.C') 
ROOT.setTDRStyle()



# Plot name
plots = ['zmass',  'dxy', 'lmisshits', '3dIP', 'charge', 'dEtaInSeed', 'hovere', 'ooEmoop', 'pt', 'relIso3', 'eta', 'sigmaIetaIeta', 'photonPt', 'deltaR']
rebin = [      4,      1,           1,      1,        1,            1,        1,         1,    1,         1,     1,               1,          1,        1]
binmn = [     20,   0.01,           0,      0,       -1,            0,        0,         0,    0,         0,     0,               0,          0,        0]
binmx = [    200,      6,          10,     10,        1,          0.3,      0.1,      0.14,  100,      0.16,   2.5,           0.018,        100,        5]
log_x = [      0,      1,           0,      0,        0,            0,        0,         0,    0,         0,     0,               0,          0,        0]
log_y = [      0,      1,           1,      1,        0,            0,        0,         1,    1,         1,     0,               1,          0,        0]

nplot = len(plots)

# Labels
if args.dyExternal:
  labels = [
        #'W #plus jets',
        'Z (10-50) ext',
        'Z (10-50) int',
        'Z (>50) ext',
        'Z (>50) int',
        'W#gamma',
        'Z#gamma',
        #'WZ',
        #'ZZ#rightarrow4l',
        't#bar{t}(2l)',
        't#bar{t}(1l)',
        #'WZ#gamma'
    ]
elif args.dyExternalAll:
  labels = [
        #'W #plus jets',
        'Z (10-50) ext',
        'Z (10-50) int',
        'Z (>50) ext',
        'Z (>50) int',
        'W#gamma',
        #'WZ',
        #'ZZ#rightarrow4l',
        't#bar{t}(2l)',
        't#bar{t}(1l)',
        #'WZ#gamma'
    ]
else:
  labels = [
      #'W #plus jets',
      'Z (10-50)',
      'Z (>50)',
      'W#gamma',
      'Z#gamma',
      #'WZ',
      #'ZZ#rightarrow4l',
      't#bar{t}(2l)',
      't#bar{t}(1l)',
      #'WZ#gamma'
  ]


# Input file names
cols = {}
cols['W #plus jets'               ] = ROOT.kAzure-9
cols['Z (10-50)'                  ] = ROOT.kBlue-7
cols['Z (>50)'                    ] = ROOT.kBlue-10
cols['Z (10-50) ext'              ] = ROOT.kBlue-3
cols['Z (>50) ext'                ] = ROOT.kGreen-10
cols['Z (10-50) int'              ] = ROOT.kTeal-9
cols['Z (>50) int'                ] = ROOT.kCyan-10
cols['W#gamma'                    ] = ROOT.kViolet-9
cols['Z#gamma'                    ] = ROOT.kMagenta-10
cols['WZ'                         ] = ROOT.kPink+1
cols['ZZ#rightarrow4l'            ] = ROOT.kRed-7
cols['t#bar{t}(2l)'               ] = ROOT.kRed-10
#cols['t#bar{t}#rightarrowl#bar{t}'] = ROOT.kOrange-9
#cols['t#bar{t}#rightarrowtl'      ] = ROOT.kYellow-10
cols['t#bar{t}(1l)'               ] = ROOT.kOrange-9
cols['WZ#gamma'                   ] = ROOT.kSpring+1
#cols[] = ROOT.kGreen-10
#cols[] = ROOT.kTeal-9
#cols[] = ROOT.kCyan-10

# Histo classes
promptflavs = ['_promptEE', '_promptMM']
displflavs  = ['_displEE' , '_displMM' ]

outdir = '/user/tomc/public_html/hnl/danielePlots/%s' % (args.year + extra)


mcnames = {}
#mcnames['W #plus jets'               ] = 'WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8_realistic_v10_Fall17'
mcnames['Z (10-50)'                  ] = 'M-10to50'
mcnames['Z (10-50) ext'              ] = 'M-10to50_external' if args.dyExternal else 'M-10to50_externalAll'
mcnames['Z (10-50) int'              ] = 'M-10to50_internal'
mcnames['Z (>50)'                    ] = 'M-50'
mcnames['Z (>50) ext'                ] = 'M-50_external' if args.dyExternal else 'M-50_externalAll'
mcnames['Z (>50) int'                ] = 'M-50_internal'
mcnames['W#gamma'                    ] = 'WGToLNuG' 
mcnames['Z#gamma'                    ] = 'ZGTo2LG' if '2016' in args.year else 'ZGToLLG' # only buggy sample available for 2016
mcnames['WZ'                         ] = 'WZTo3LNu'
mcnames['ZZ#rightarrow4l'            ] = 'ZZTo4L'
mcnames['t#bar{t}(2l)'               ] = 'TTTo2L2Nu'
mcnames['t#bar{t}(1l)'               ] = 'TTToSemilepton' if '2016' in args.year else 'TTToSemiLeptonic'
mcnames['WZ#gamma'                   ] = 'WZG'
mcnames['WZZ'                        ] = 'WZZ'

dataname = 'data'


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
def drawLumi():
  if args.year=='2016':        lumi = 35.867
  elif args.year=='2016BCDEF': lumi = 35.867-16.3
  elif args.year=='2016GH':    lumi = 16.3 
  elif args.year=='2017':      lumi = 41.530
  elif args.year=='2018':      lumi = 59.688
  lines = [
    (11, (ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+.01, 'CMS Preliminary')),
    (31, (1-ROOT.gStyle.GetPadRightMargin(), 1-ROOT.gStyle.GetPadTopMargin()+.01, ('%3.1f fb{}^{-1} (%s, 13 TeV)'% (lumi, args.year))))
  ]
  return [drawTex(l, align) for align, l in lines]



# Get plots
for plot in getPlotNames():
  suff='prompt'+plot.split('_prompt')[-1]
  for i, plotSetting in enumerate(plots):
    if plotSetting in plot: 
      iplot=i
      break
  else:
    print 'No settings found for plot %s' %s

  hstk = ROOT.THStack(plot, '')
  hbkg = None 
  leg = ROOT.TLegend(0.75, 0.50, 0.95, 0.90)
  leg.SetBorderSize(0)
  leg.SetLineWidth(0)
  leg.SetLineColor(0)
  leg.SetFillStyle(0)
  leg.SetFillColor(0)

  for label in labels:
    h = getPlot(args.year + '_new/' +mcnames[label]+'/*.root', plot)
    h.Rebin(rebin[iplot])
    for ibin in range(1, 1+h.GetNbinsX()):
      if h.GetBinContent(ibin)<0:
        h.SetBinError(ibin, h.GetBinError(ibin) + abs(h.GetBinContent(ibin)))
        h.SetBinContent(ibin, 0.)
    if hbkg: hbkg.Add(h)
    else:    hbkg = h.Clone('total_'+plot)
    h.SetFillColor(cols[label])
    h.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
    hstk.Add(h)
    leg.AddEntry(h, label, 'F')

  hdata = getPlot(args.year + '_new/' + dataname+'/*.root', plot)
  hdata.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
  hdata.SetMarkerStyle(20)
  hdata.SetMarkerSize(0.8)
  hdata.Rebin(rebin[iplot])

  c = ROOT.TCanvas('c_'+plot, 'c_'+plot, 600, 700)
  p1 = ROOT.TPad('p1', 'p1', 0., 0., 1., 0.25)
  p2 = ROOT.TPad('p2', 'p2', 0., 0.25, 1., 1.)
  p1.SetBottomMargin(0.34)
  p1.SetTopMargin(0.02)
  p2.SetBottomMargin(0.01)
  c.Draw()
  p1.Draw()
  p1.SetLogx(log_x[iplot])
  p2.Draw()
  p2.cd()
  p2.SetLogx(log_x[iplot])
  p2.SetLogy(log_y[iplot])
  hbkg.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
  hdata.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
  hstk.Draw('hist')
  hstk.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
  hbkg.SetFillColor(ROOT.kBlack)
  hbkg.SetFillStyle(3003)
  hbkg.Draw('e2same')
  hdata.Draw('e1same')
  hstk.GetYaxis().SetTitle('Events')
  hstk.GetYaxis().SetTitleOffset(1.20)
  drawLumi()
  leg.Draw()
  hratio = hdata.Clone('ratio_'+plot+suff)
  hratio.Divide(hbkg)
  p1.cd()
  hratio.Draw('e1')
  p1.SetGridx()
  p1.SetGridy()
  ll = ROOT.TLine(binmn[iplot], 1., binmx[iplot], 1.)
  ll.SetLineWidth(2)
  ll.SetLineStyle(7)
  ll.SetLineColor(ROOT.kRed)
  ll.Draw('same')
  if 'dxy' in plot and 'displMM' in suff:
      xaxislabel = hratio.GetXaxis().GetTitle()
      xaxislabel = xaxislabel.replace('e', '#mu')
      hratio.GetXaxis().SetTitle(xaxislabel)
  hratio.GetXaxis().SetRangeUser(binmn[iplot], binmx[iplot])
  hratio.GetXaxis().SetTitleSize(0.15)
  hratio.GetXaxis().SetLabelSize(0.10)
  hratio.GetYaxis().SetRangeUser(0.401, 1.599)
  hratio.GetYaxis().SetTitle('Data/MC')
  hratio.GetYaxis().SetTitleSize(0.14)
  hratio.GetYaxis().SetTitleOffset(0.50)
  hratio.GetYaxis().SetLabelSize(0.10)
  if 'pt' in plot.split('_')[0]: hratio.GetXaxis().SetTitle('p_{t}(lep) [GeV]') # temporary, fixed in next run of analyzeZtoLLLLmass.py
  if 'Pt' in plot.split('_')[0]: hratio.GetXaxis().SetTitle('p_{t}(#gamma) [GeV]')

  zwindow = 'onz' if 'onz' in plot else 'allz'
  plotDir = os.path.join(outdir, zwindow, suff)
  copyIndexPHP(plotDir + '/', outdir)
  c.SaveAs(os.path.join(plotDir, plot+'.png'))
  c.SaveAs(os.path.join(plotDir, plot+'.pdf'))
  c.SaveAs(os.path.join(plotDir, plot+'.root'))
