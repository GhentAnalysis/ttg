#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
import pickle
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadRightMargin(0.055)
ROOT.gStyle.SetPadLeftMargin(0.065)
import pdb

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()


def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  MCHist = None
  dataHist = None
  for name, hist in hists.iteritems():
    if 'data' in name:
      if not dataHist: dataHist = hist
      else: dataHist.Add(hist)
    elif 'ttg' in name.lower():
    # else:
      if not MCHist: MCHist = hist
      else: MCHist.Add(hist)
    else: continue
  return (MCHist, dataHist)


# rd, ru = 0.95, 1.05
rd, ru = 0.98, 1.02
# rd, ru = 0.995, 1.005


labels = ['1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b', '#geq3j,#geq3b']

channellabels = ['#mu#mu', 'e#mu', 'ee']


sysSets = [['pdf_' + str(i) for i in range(0, 100)]]

# plots = ['signalRegionsZoom', 'unfReco_phPt', 'yield', 'photon_pt_large', 'total']
plots = ['unfReco_phPt', 'yield']
# plots = ['unfReco_ll_absDeltaEta']


from math import sqrt
def pdfSys(variations, nominal):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  # print([(nominal.GetBinContent(6) - var.GetBinContent(6)) for var in variations])
  for i in range(0, variations[0].GetNbinsX()+2):
    pdfVarRms = sqrt(sum((nominal.GetBinContent(i) - var.GetBinContent(i))**2 for var in variations)/len(variations))
    upHist.SetBinContent(  i, pdfVarRms)
    downHist.SetBinContent(i, pdfVarRms)
  upHist.Divide(nominal)
  downHist.Divide(nominal)
  return upHist, downHist


def getpdfvars(path):
  nomMC, nomdata = sumHists(path, plot)
  MC = []

  for sys in ['pdf_' + str(i) for i in range(0, 100)]:
    sysHist, _ = sumHists(path, plot + sys)
    MC.append(sysHist.Clone())

  upMC, downMC = pdfSys(MC, nomMC)
  return (upMC.Clone(), downMC.Clone())

for plot in plots:
  colors = 50*[ROOT.kRed + 2, ROOT.kRed-4, ROOT.kBlue + 2, ROOT.kBlue-4, ROOT.kGreen + 2, ROOT.kGreen-3]

  up16, down16 = getpdfvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + plot + '.pkl')
  up17, down17 = getpdfvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + plot + '.pkl')
  up18, down18 = getpdfvars('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + plot + '.pkl')



  # pdb.set_trace()

  c1 = ROOT.TCanvas('c', 'c', 1600, 700)

  up16.SetLineColor(ROOT.kRed)
  up17.SetLineColor(ROOT.kGreen)
  up18.SetLineColor(ROOT.kBlue)

  up16.GetYaxis().SetRangeUser(0, 0.0025)
  up16.SetTitle('')

  up16.SetLineWidth(2)
  up17.SetLineWidth(2)
  up18.SetLineWidth(2)

  up16.Draw('hist')
  up17.Draw('hist same')
  up18.Draw('hist same')


  legend = ROOT.TLegend(0.15,0.90,0.95,0.98)
  legend.AddEntry(up16, '2016' , 'L')
  legend.AddEntry(up17, '2017' , 'L')
  legend.AddEntry(up18, '2018' , 'L')

  # if plot == 'signalRegionsZoom':
  #   for i, l in enumerate(labels):
  #     hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)

  # if plot == 'yield':
  #   for i, l in enumerate(channellabels):
  #     hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)

  # legend = ROOT.TLegend(0.15,0.91,0.95,0.96)
  # for s, sys in enumerate(systs):
  #   if sys.count('Down'):
  #     hists[sys].SetLineStyle(2)
  #     hists[sys].SetLineColor(colors[s/2])
  #   elif sys.count('Up'):
  #     hists[sys].SetLineStyle(1)
  #     hists[sys].SetLineColor(colors[s/2])
  #   else:
  #     hists[sys].SetLineColor(colors[s])
  #     hists[sys].SetLineStyle(1)
      
  #   hists[sys].SetLineWidth(3)
  #   hists[sys].GetYaxis().SetRangeUser(rd, ru)
  #   hists[sys].SetTitle('')
  #   hists[sys].Draw('SAME E1')
  #   legend.AddEntry(hists[sys], sys , 'L')

  legend.SetNColumns(3)
  legend.SetFillStyle(0)
  legend.SetLineStyle(0)
  legend.SetBorderSize(0)
  legend.Draw()



  # l1 = ROOT.TLine(hists[systs[0]].GetBinLowEdge(1),1., hists[systs[0]].GetBinLowEdge(hists[systs[0]].GetXaxis().GetLast()+1),1.)
  # l1.SetLineStyle(3)  
  # l1.SetLineWidth(2)
  # l1.Draw()
  
  c1.SaveAs('pdf3ycompt/' + plot + '.png')

