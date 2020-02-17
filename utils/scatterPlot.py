from ROOT import TCanvas, TGraph
from ROOT import gROOT, gStyle
from ROOT import TMultiGraph
from array import array
from ROOT import kRed, kBlue, kGreen, kOrange 
import pickle
import numpy 
from itertools import combinations

gROOT.SetBatch(True)
gStyle.SetOptStat(0)
# tdr.setTDRStyle()
# ROOT.gStyle.SetPaintTextFormat(paintformat)
gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")


picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfullmagic-splitOverlayMagDump/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/dumpedArrays.pkl'
file = pickle.load(open(picklePath, 'r'))

varList = [('_phSigmaIetaIeta', None), ('_phNeutralHadronIsolation', 5.), ('_phPhotonIsolation', 3.), ('_phChargedIsolation', None), ('puChargedHadronIso', 80.), ('phoWorstChargedIsolation', 80.)]

for varA, varB in combinations(varList, 2):

  c1 = TCanvas( 'c1', 'Scatter', 1000, 800)
  genCha = numpy.asarray([i[0] for i in file['TT_Dil_All_(genuine)'][varA[0]]])
  genNeu = numpy.asarray([i[0] for i in file['TT_Dil_All_(genuine)'][varB[0]]])
  genuine = TGraph( len(genCha), genCha, genNeu)
  genuine.SetMarkerColor( kOrange )
  genuine.SetMarkerStyle( 21 )
  genuine.SetMarkerSize( 0.5 )
  genuine.SetTitle("genuine")


  fakeCha = numpy.asarray([i[0] for i in file['TT_Dil'][varA[0]]])
  fakeNeu = numpy.asarray([i[0] for i in file['TT_Dil'][varB[0]]])
  fake = TGraph( len(fakeCha), fakeCha, fakeNeu)
  fake.SetMarkerColor( kBlue )
  fake.SetMarkerStyle( 21 )
  fake.SetMarkerSize( 0.5 )
  fake.SetTitle("fake")

  hadCha = numpy.asarray([i[0] for i in file['TT_Dil_All_(hadronicPhoton)'][varA[0]]])
  hadNeu = numpy.asarray([i[0] for i in file['TT_Dil_All_(hadronicPhoton)'][varB[0]]])
  had = TGraph( len(hadCha), hadCha, hadNeu)
  had.SetMarkerColor( kRed )
  had.SetMarkerStyle( 21 )
  had.SetMarkerSize( 0.5 )
  had.SetTitle("hadronic")


  magicCha = numpy.asarray([i[0] for i in file['TT_Dil_All_(magicPhoton)'][varA[0]]])
  magicNeu = numpy.asarray([i[0] for i in file['TT_Dil_All_(magicPhoton)'][varB[0]]])
  magic = TGraph( len(magicCha), magicCha, magicNeu)
  magic.SetMarkerColor( kGreen )
  magic.SetMarkerStyle( 21 )
  magic.SetMarkerSize( 0.5 )
  magic.SetTitle("magic")

  mg = TMultiGraph()


  mg.Add(genuine)
  mg.Add(fake)
  mg.Add(had)
  mg.Add(magic)
  mg.SetTitle(' ; ' + varA[0] + '; ' + varB[0] );
  c1.Draw()
  mg.Draw('AP')
  if varA[1]:
    mg.GetXaxis().SetRangeUser(0.,varA[1])
  if varB[1]: 
    mg.GetYaxis().SetRangeUser(0.,varB[1])
  c1.Update()
  c1.BuildLegend(0.8, 0.8, 0.9, 0.9)
  c1.SaveAs(varA[0] + varB[0] + '.pdf')