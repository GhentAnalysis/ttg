#!/usr/bin/env python
import ROOT
import sys, os

ROOT.gROOT.LoadMacro('danystyle.C') 
ROOT.setTDRStyle()

ROOT.gROOT.SetBatch(True)

import os, argparse, sys
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--year',           action='store',      default=None)
argParser.add_argument('--dyExternal',     action='store_true')
argParser.add_argument('--dyExternalAll',     action='store_true')
args = argParser.parse_args()

extra = '_dyExternalAll' if args.dyExternalAll else ('_dyExternal' if args.dyExternal else '_new')


from ttg.tools.helpers import getObjFromFile
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


# Output file
#fout = ROOT.TFile('plots_3l_4l.root', 'recreate')

# Plot name
plots = ['zmass',  'dxy', 'lmisshits', 'zmass3',  'dxy3', 'lmisshits3',  'dxy_onz', 'lmisshits_onz',  'dxy3_onz', 'lmisshits3_onz']
rebin = [      4,      1,           1,        4,       1,            1,          1,               1,           1,                1]
binmn = [     20,   0.01,           0,       20,    0.01,            0,       0.01,               0,        0.01,                0]
binmx = [    200,      6,          10,      200,       6,           10,          6,              10,           6,               10]
log_x = [      0,      1,           0,        0,       1,            0,          1,               0,           1,                0]
log_y = [      0,      1,           1,        0,       1,            1,          1,               1,           1,                1]

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
try:    os.makedirs(outdir)
except: pass


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
    (11, (ROOT.gStyle.GetPadLeftMargin(),  1-ROOT.gStyle.GetPadTopMargin()+.03, 'CMS Preliminary')),
    (31, (1-ROOT.gStyle.GetPadRightMargin(), 1-ROOT.gStyle.GetPadTopMargin()+.03, ('%3.1f fb{}^{-1} (%s, 13 TeV)'% (lumi, args.year))))
  ]
  return [drawTex(l, align) for align, l in lines]



# Get plots
iplot=0
leg = ROOT.TLegend(0.75, 0.50, 0.95, 0.90)
leg.SetBorderSize(0)
leg.SetLineWidth(0)
leg.SetLineColor(0)
leg.SetFillStyle(0)
leg.SetFillColor(0)
for promptflav in promptflavs:
  for displflav in displflavs:
    suff = promptflav+displflav
    for plot in plots:
      if 'lmisshits' in plot and not 'EE' in displflav: continue
      print plot+suff
      hstk = ROOT.THStack(plot+suff, '')
      hbkg = ROOT.TH1D()
      isfirst = True
      for label in labels:
        h = getPlot(args.year + '_new/' +mcnames[label]+'/*.root', plot+suff)
        h.Rebin(rebin[iplot%nplot])
        for ibin in range(1, 1+h.GetNbinsX()):
            if h.GetBinContent(ibin)<0:
                h.SetBinError(ibin, h.GetBinError(ibin) + abs(h.GetBinContent(ibin)))
                h.SetBinContent(ibin, 0.)
        if isfirst:
            hbkg = h.Clone('total_'+plot+suff)
            isfirst = False
        else:
            hbkg.Add(h)
        h.SetFillColor(cols[label])
        hstk.Add(h)
        if iplot==0:
            leg.AddEntry(h, label, 'F')

      hdata = getPlot(args.year + '_new/' + dataname+'/*.root', plot+suff)
      hdata.SetMarkerStyle(20)
      hdata.SetMarkerSize(0.8)
      #hdata.Sumw2()
      hdata.Rebin(rebin[iplot%nplot])

      c = ROOT.TCanvas('c_'+plot+suff, 'c_'+plot+suff, 600, 700)
      p1 = ROOT.TPad('p1', 'p1', 0., 0., 1., 0.25)
      p2 = ROOT.TPad('p2', 'p2', 0., 0.25, 1., 1.)
      p1.SetBottomMargin(0.34)
      p1.SetTopMargin(0.02)
      p2.SetBottomMargin(0.01)
      c.Draw()
      p1.Draw()
      p1.SetLogx(log_x[iplot%nplot])
      p2.Draw()
      p2.cd()
      p2.SetLogx(log_x[iplot%nplot])
      p2.SetLogy(log_y[iplot%nplot])
      hstk.Draw('hist')
      hbkg.SetFillColor(ROOT.kBlack)
      hbkg.SetFillStyle(3003)
      #hbkg.SetMarkerStyle(20)
      hbkg.Draw('e2same')
      #hstk.GetXaxis().SetLimits(binmn[iplot%nplot], binmx[iplot%nplot])
      #hdata.GetXaxis().SetLimits(binmn[iplot%nplot], binmx[iplot%nplot])
      hdata.Draw('e1same')
      hstk.GetXaxis().SetLimits(binmn[iplot%nplot], binmx[iplot%nplot])
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
      ll = ROOT.TLine(binmn[iplot%nplot], 1., binmx[iplot%nplot], 1.)
      ll.SetLineWidth(2)
      ll.SetLineStyle(7)
      ll.SetLineColor(ROOT.kRed)
      ll.Draw('same')
      #hratio.GetXaxis().SetLimits(binmn[iplot%nplot], binmx[iplot%nplot])
      if 'dxy' in plots[iplot%nplot] and 'displMM' in suff:
          xaxislabel = hratio.GetXaxis().GetTitle()
          xaxislabel = xaxislabel.replace('e', '#mu')
          hratio.GetXaxis().SetTitle(xaxislabel)
      hratio.GetXaxis().SetRangeUser(binmn[iplot%nplot], binmx[iplot%nplot])
      #hratio.GetXaxis().SetLimits(binmn[iplot%nplot], binmx[iplot%nplot])
      hratio.GetXaxis().SetTitleSize(0.15)
      hratio.GetXaxis().SetLabelSize(0.10)
      hratio.GetYaxis().SetRangeUser(0.401, 1.599)
      hratio.GetYaxis().SetTitle('Data/MC')
      hratio.GetYaxis().SetTitleSize(0.14)
      hratio.GetYaxis().SetTitleOffset(0.50)
      hratio.GetYaxis().SetLabelSize(0.10)
      # for i in range(1, 1+hratio.GetNbinsX()):
      #     print ' - bin '+str(i)+': '+str(hbkg.GetBinContent(i))+' -> '+str(hratio.GetBinContent(i))

      #fout.cd()
      c.SaveAs(outdir + '/' + plot+suff+'.png')
      c.SaveAs(outdir + '/' + plot+suff+'.root')
      iplot += 1

