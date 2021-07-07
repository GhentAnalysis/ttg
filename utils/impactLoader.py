#! /usr/bin/env python
import pickle
from ttg.plots.systematics import showSysList
import pdb
rounding = 2

# def getYieldMC(hists):
#   sumVal = 0.
#   for name, hist in hists.iteritems():
#     if not 'data' in name: 
#       sumVal += hist.Integral()
#   return sumVal


# def getYieldBKG(hists):
#   sumVal = 0.
#   for name, hist in hists.iteritems():
#     if not 'data' in name and not 'TTG' in name: 
#       sumVal += hist.Integral()
#   return sumVal

# def getYieldData(hists):
#   sumVal = 0.
#   sumSamples = []
#   for name, hist in hists.iteritems():
#     if 'data' in name: 
#       sumVal += hist.Integral()
#       sumSamples.append(name)
#       # print name
#   return sumVal

def sumHists(dict, sumkeys, antiSumKeys, scaleBkg=None):
  sumHist = None
  for name, hist in dict.iteritems():
    if (any((name.count(key) for key in sumkeys)) or not sumkeys) and (not any((name.count(key) for key in antiSumKeys)) or not antiSumKeys):
      if scaleBkg:
        if name.count(scaleBkg[0]) and not name.count('estimate'):
        # if name.count(scaleBkg[0]):
          hist = hist.Clone()
          hist.Scale(scaleBkg[1])
      if not sumHist: sumHist = hist.Clone()
      else: sumHist.Add(hist)
  return sumHist

def getStatErr(hists, MC):
  sumVal = 0.
  for name, hist in hists.iteritems():
    if MC ^ ('data' in name): 
      for i in range(1, hist.GetNbinsX()+1):
        sumVal += hist.GetBinError(i)**2.
  sumVal = sumVal**0.5
  return sumVal



variations = showSysList
variations.remove('q2')
variations.remove('pdf')
variations.remove('colRec')
# variations = ['NP']
def getEffect(year):

  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/' + year + '/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/unfReco_phPt.pkl'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  varHists = pickle.load(open(picklePath))
  data = sumHists(varHists['unfReco_phPt'], ['data'], [])
  bkgNom = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'])
  subNom = data.Clone()
  subNom.Add(bkgNom, -1)
  signalNom = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  subNom.Divide(signalNom)
  rels ={}
  for var in variations:
    try:
      bkgUp = sumHists(varHists['unfReco_phPt' + var + 'Up'], [], ['data', 'TTGamma'])
      bkgDown = sumHists(varHists['unfReco_phPt' + var + 'Down'], [], ['data', 'TTGamma'])
      subUp = data.Clone()
      subDown = data.Clone()
      # pdb.set_trace()
      subUp.Add(bkgUp, -1)
      subDown.Add(bkgDown, -1)
      signalUp = varHists['unfReco_phPt'+ var + 'Up']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      signalDown = varHists['unfReco_phPt'+ var + 'Down']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      subUp.Divide(signalUp)
      subDown.Divide(signalDown)
      subUp.Add(subNom, -1)
      subDown.Add(subNom, -1)
      ul, uh, dl, dh = 1., -1., -1., 1.
      for i in range(subNom.GetXaxis().GetNbins()+1):
        uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
        dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
        ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
        dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
      
      ul = round(100.*ul, rounding)
      uh = round(100.*uh, rounding)
      dl = round(100.*dl, rounding)
      dh = round(100.*dh, rounding)
      rels[var] = (dh, dl, ul, uh)
    except:
      rels[var] = ('nan', 'nan', 'nan', 'nan')

  # TODO 
  # rels['statMC'] = (mcstat, mcstat )
  # rels['statDA'] = (dastat, dastat )
  for bkg in [('ZG', 0.015), ('other', 0.3), ('singleTop', 0.1)]:
    bkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], (bkg[0], 1. + bkg[1]))
    bkgDown = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], (bkg[0], 1. - bkg[1]))
    subUp = data.Clone()
    subDown = data.Clone()
    subUp.Add(bkgUp, -1)
    subDown.Add(bkgDown, -1)
    signalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalDown = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    subUp.Divide(signalUp)
    subDown.Divide(signalDown)
    subUp.Add(subNom, -1)
    subDown.Add(subNom, -1)
    ul, uh, dl, dh = 1., -1., -1., 1.
    for i in range(subNom.GetXaxis().GetNbins()+1):
      uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
      dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
    
    ul = round(100.*ul, rounding)
    uh = round(100.*uh, rounding)
    dl = round(100.*dl, rounding)
    dh = round(100.*dh, rounding)
    rels[bkg[0] + 'Norm'] = (dh, dl, ul, uh)

  for lumi in [('lumi_2016', 0.009), ('lumi_2017', 0.02), ('lumi_2018', 0.015)]:
    bkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], ('', 1. + lumi[1]))
    bkgDown = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], ('', 1. - lumi[1]))
    subUp = data.Clone()
    subDown = data.Clone()
    subUp.Add(bkgUp, -1)
    subDown.Add(bkgDown, -1)
    signalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalDown = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalUp.Scale(1. + lumi[1])
    signalDown.Scale(1. - lumi[1])
    subUp.Divide(signalUp)
    subDown.Divide(signalDown)
    subUp.Add(subNom, -1)
    subDown.Add(subNom, -1)
    ul, uh, dl, dh = 1., -1., -1., 1.
    for i in range(subNom.GetXaxis().GetNbins()+1):
      uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
      dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
    
    ul = round(100.*ul, rounding)
    uh = round(100.*uh, rounding)
    dl = round(100.*dl, rounding)
    dh = round(100.*dh, rounding)
    if not lumi[0].count(year):
      rels[lumi[0]] = (0., 0., 0., 0.)
    else:
      rels[lumi[0]] = (dh, dl, ul, uh)
  return rels

varYears = {}
for year in ['2016', '2017', '2018']:
  varYears[year] = getEffect(year)
print (20*' ') + '2016' + (26*' ') + '2017' +  (26*' ') + '2018'+  (26*' ') + 'overall'
for sys in varYears['2016'].keys():
  # if not sys.count('lumi'): continue
  odh = min(varYears[y][sys][0] for y in ['2016', '2017', '2018'])
  odl = max(varYears[y][sys][1] for y in ['2016', '2017', '2018'])
  oul = min(varYears[y][sys][2] for y in ['2016', '2017', '2018'])
  ouh = max(varYears[y][sys][3] for y in ['2016', '2017', '2018'])
  print (sys+'                   ')[:20] + (str(varYears['2016'][sys])+'                   ')[:30] + (str(varYears['2017'][sys])+'                   ')[:30] + (str(varYears['2018'][sys])+'                   ')[:30]+ str((odh, odl, oul, ouh))
