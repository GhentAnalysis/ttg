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
      if not MCHist: MCHist = hist
      else: MCHist.Add(hist)
    else: continue
  return (MCHist, dataHist)


rd, ru = 0.95, 1.05
# rd, ru = 0.995, 1.005


labels = ['1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,#geq2b', '#geq3j,#geq3b']



# sysSets = [['AbsoluteUp', 'AbsoluteDown'],['AbsoluteUCUp', 'AbsoluteUCDown'],['BBEC1Up', 'BBEC1Down'],['BBEC1UCUp', 'BBEC1UCDown'],['EC2Up', 'EC2Down'],['EC2UCUp', 'EC2UCDown'],['FlavorQCDUp', 'FlavorQCDDown'],['HFUp', 'HFDown'],['HFUCUp', 'HFUCDown'],['JERUp', 'JERDown'],['NPUp', 'NPDown'],['RelativeBalUp', 'RelativeBalDown'],['RelativeSampleUCUp', 'RelativeSampleUCDown'],['bTagbUp', 'bTagbDown'],['bTaglUp', 'bTaglDown'],['ephResUp', 'ephResDown'],['ephScaleUp', 'ephScaleDown'],['fsrUp', 'fsrDown'],['isrUp', 'isrDown'],['lSFElStatUp', 'lSFElStatDown'],['lSFElSystUp', 'lSFElSystDown'],['lSFMuStatUp', 'lSFMuStatDown'],['lSFMuSystUp', 'lSFMuSystDown'],['pfUp', 'pfDown'],['phSFUp', 'phSFDown'],['puUp', 'puDown'],['pvSFUp', 'pvSFDown'],['trigStatEEUp', 'trigStatEEDown'],['trigStatEMUp', 'trigStatEMDown'],['trigStatMMUp', 'trigStatMMDown'],['trigSystUp', 'trigSystDown'],['ueUp', 'ueDown']]
# sysSets = [['bTagbUp', 'bTagbDown'],['bTaglUp', 'bTaglDown'],['ephResUp', 'ephResDown'],['ephScaleUp', 'ephScaleDown'],['fsrUp', 'fsrDown'],['isrUp', 'isrDown'],['lSFElStatUp', 'lSFElStatDown'],['lSFElSystUp', 'lSFElSystDown'],['lSFMuStatUp', 'lSFMuStatDown'],['lSFMuSystUp', 'lSFMuSystDown'],['pfUp', 'pfDown'],['phSFUp', 'phSFDown'],['puUp', 'puDown'],['pvSFUp', 'pvSFDown'],['trigStatEEUp', 'trigStatEEDown'],['trigStatEMUp', 'trigStatEMDown'],['trigStatMMUp', 'trigStatMMDown'],['trigSystUp', 'trigSystDown'],['ueUp', 'ueDown']]
sysSets = [['AbsoluteUp', 'AbsoluteDown'] ,['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')],['lSFElSystUp', 'lSFElSystDown'],['lSFMuSystUp', 'lSFMuSystDown']]
# sysSets = [['pdf_' + str(i) for i in range(0, 100)]]

plots = ['signalRegionsZoom', 'unfReco_phPt']

for systs in sysSets:
  for plot in plots:
    colors = 50*[ROOT.kRed + 2, ROOT.kRed-4, ROOT.kBlue + 2, ROOT.kBlue-4, ROOT.kGreen + 2, ROOT.kGreen-3]
    path = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + plot + '.pkl'

    hists = {}
    MC, data = sumHists(path, plot)
    for sys in systs:
      sysHist, _ = sumHists(path, plot + sys)
      sysHist.Divide(MC)
      hists[sys] = sysHist.Clone()

    c1 = ROOT.TCanvas('c', 'c', 1600, 700)

    if plot == 'signalRegionsZoom':
      for i, l in enumerate(labels):
        hists[systs[0]].GetXaxis().SetBinLabel(i+1, l)


    legend = ROOT.TLegend(0.15,0.91,0.95,0.96)
    for s, sys in enumerate(systs):
      if sys.count('Down'):
        hists[sys].SetLineStyle(2)
        hists[sys].SetLineColor(colors[s/2])
      elif sys.count('Up'):
        hists[sys].SetLineStyle(1)
        hists[sys].SetLineColor(colors[s/2])
      else:
        hists[sys].SetLineColor(colors[s])
        hists[sys].SetLineStyle(1)
        
      hists[sys].SetLineWidth(3)
      hists[sys].GetYaxis().SetRangeUser(rd, ru)
      hists[sys].SetTitle('')
      hists[sys].Draw('SAME HIST')
      legend.AddEntry(hists[sys], sys , 'L')

    legend.SetNColumns(6)
    legend.SetFillStyle(0)
    legend.SetLineStyle(0)
    legend.SetBorderSize(0)
    legend.Draw()



    l1 = ROOT.TLine(hists[systs[0]].GetBinLowEdge(1),1., hists[systs[0]].GetBinLowEdge(hists[systs[0]].GetXaxis().GetLast()+1),1.)
    l1.SetLineStyle(3)  
    l1.SetLineWidth(2)
    l1.Draw()
    c1.SaveAs('marSystPlots/' + systs[0] + plot + '.png')
