#! /usr/bin/env python
import pickle
from ttg.plots.systematics import showSysList

rounding = 2

def getYieldMC(hists):
  sumVal = 0.
  sumSamples = []
  for name, hist in hists.iteritems():
    if not 'data' in name: 
      sumVal += hist.Integral()
      sumSamples.append(name)
      # print name
  # print sumSamples
  return sumVal

def getYieldData(hists):
  sumVal = 0.
  sumSamples = []
  for name, hist in hists.iteritems():
    if 'data' in name: 
      sumVal += hist.Integral()
      sumSamples.append(name)
      # print name
  return sumVal

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
# variations.remove('pdf')
# variations = ['NP']

def getEffect(year):
  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/' + year + '/phoCBfull-reweightSigMLL/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/yield.pkl'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  varHists = pickle.load(open(picklePath))
  central = getYieldMC(varHists['yield'])
  rels ={}
  for var in variations:
    down = getYieldMC(varHists['yield' + var + 'Down'])
    up   = getYieldMC(varHists['yield' + var + 'Up'])
    relDown = round(100.*(down-central)/central, rounding)
    relUp   = round(100.*(up-central)/central, rounding)
    # print var + '\t\t' + str(round(central, rounding)) + '\t\t' + str(round(down, rounding)) + '\t  ' + str(relDown) + '\t\t' + str(round(up, rounding)) + '\t  ' + str(relUp)
    rels[var] = (relDown, relUp)
  mcstat = round(100.* getStatErr(varHists['yield'], True)  / getYieldData(varHists['yield']), rounding)
  dastat = round(100.* getStatErr(varHists['yield'], False) / getYieldData(varHists['yield']), rounding)
  rels['statMC'] = (mcstat, mcstat )
  rels['statDA'] = (dastat, dastat )

  return rels

varYears = {}
for year in ['2016', '2017', '2018']:
  varYears[year] = getEffect(year)
print '\t' '2016' + '\t \t' + '2017' + '\t \t' + '2018'
for sys in varYears['2016'].keys():
  print sys + '\t' + str(varYears['2016'][sys]) + '\t' + str(varYears['2017'][sys]) + '\t' + str(varYears['2018'][sys])