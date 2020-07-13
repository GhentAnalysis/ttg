#
# nonprompt photon background estimation weights
#

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
import pickle
import time
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat('e')
ROOT.gStyle.SetPadRightMargin(0.12)

ROOT.TH1.SetDefaultSumw2()
ROOT.TH2.SetDefaultSumw2()

sourceHists ={'2016': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
              '2017': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
              '2018': ( '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl',
                        '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest/all/llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10/photon_pt_etaB.pkl'),
}

  
#   A/B             ch Iso  BD         ch Iso     BD
#   C/D                     AC                    AC
#   A= B*(C/D)             sigma               onZ-offZ
# def __init__(self, year, selection):

def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  nHist = None
  gHist = None
  dHist = None
  for name, hist in hists.iteritems():
    if 'nonprompt' in name:
      if not nHist: nHist = hist
      else: nHist.Add(hist)
    elif 'genuine' in name:
      if not gHist: gHist = hist
      else: gHist.Add(hist)
    elif 'data' in name:
      if not dHist: dHist = hist
      else: dHist.Add(hist)
    else:
      print 'warning ' + name
  return (nHist, gHist, dHist)

for year in ['2016', '2017', '2018']:
  A, B, C, D = (sumHists(file, 'photon_pt_etaB') for file in sourceHists[year])
  for type in [('nonp', 0), ('data', 2), ('genu', 1)]:
    for reg in [("A", A[type[1]]), ("B", B[type[1]]), ("C", C[type[1]]), ("D", D[type[1]])]:
      # yield plotting
      c1 = ROOT.TCanvas('c', 'c', 900, 800)
      reg[1].SetTitle('Yield')
      reg[1].Draw('COLZ TEXT E')
      c1.SaveAs('gridPlots/' + year + '_' + type[0] + '_' + reg[0] + '_yield' + '.pdf')

      ROOT.gStyle.SetPaintTextFormat("4.4f")
      # normalized yield plotting
      #  TODO put total yield in title or so
      c2 = ROOT.TCanvas('c', 'c', 900, 800)
      shapeHist = reg[1].Clone()
      integ = reg[1].Integral()
      for i in range(1, shapeHist.GetNbinsX()+1):
        for j in range(1, shapeHist.GetNbinsY()+1):
          shapeHist.SetBinContent(i, j, reg[1].GetBinContent(i, j)/ integ)
          shapeHist.SetBinError(i, j, reg[1].GetBinError(i, j)/ integ)
      shapeHist.SetTitle('Shape - normalized yield')
      shapeHist.Draw('COLZ TEXT E')
      c2.SaveAs('gridPlots/' + year + '_' + type[0] + '_' + reg[0] + '_shape' + '.pdf')
      ROOT.gStyle.SetPaintTextFormat("2.2f")

      # stat unc plotting
      # c3 = ROOT.TCanvas('c', 'c', 900, 800)
      # errHist = reg[1].Clone()
      # for i in range(1, errHist.GetNbinsX()+1):
      #   for j in range(1, errHist.GetNbinsY()+1):
      #     errHist.SetBinContent(i, j, abs(reg[1].GetBinError(i, j)))
      # errHist.Draw('COLZ TEXT')
      # errHist.SetTitle('Statistical Error')      
      # c3.SaveAs('gridPlots/' + year + '_' + type[0] + '_' + reg[0] + '_err' + '.pdf')
  for reg in [("A", A), ("B", B), ("C", C), ("D", D)]:
    reg[1][0].Add(reg[1][1])
    c4 = ROOT.TCanvas('c', 'c', 900, 800)
    reg[1][0].Draw('COLZ TEXT E')
    c4.SaveAs('gridPlots/' + year + '_MC_' + reg[0] + '_yield' + '.pdf')


  A, B, C, D = (sumHists(file, 'photon_pt_etaB') for file in sourceHists[year])
  B[2].Add(B[1] ,-1.)
  C[2].Add(C[1] ,-1.)
  D[2].Add(D[1], -1.)
  C[2].Divide(D[2])
  B[2].Multiply(C[2])
  AestData = B[2]
  C[0].Divide(D[0])                 # A est MC = B*C/D
  B[0].Multiply(C[0])
  B[0].Add(A[0], -1.)               # relative deviation MC prediction A from MC A  (AMC -ApredMC)/AMC
  B[0].Divide(A[0])
  c6 = ROOT.TCanvas('c', 'c', 900, 800)
  AestData.Draw('COLZ TEXT E')
  c6.SaveAs('gridPlots/' + year + '_data_' + '_predYield' + '.pdf')
  print AestData.Integral()

  A[2].Add(A[1] ,-1.)
  c7 = ROOT.TCanvas('c', 'c', 900, 800)
  A[2].Draw('COLZ TEXT E')
  c7.SaveAs('gridPlots/' + year + '_data_' + '_npYield' + '.pdf')
  print A[2].Integral()

  AestData.Divide(A[0])             # divide by A MC to get weights
  c5 = ROOT.TCanvas('c', 'c', 900, 800)
  AestData.Draw('COLZ TEXT E')
  c5.SaveAs('gridPlots/' + year + '_data_' + '_weight' + '.pdf')