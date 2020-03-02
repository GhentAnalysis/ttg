#! /usr/bin/env python
import pickle
from ttg.plots.systematics import showSysList

rounding = 2

def getYieldMC(hists):
  sumVal = 0.
  sumSamples = []
  for name, hist in hists.iteritems():
    if 'data' not in name: 
      sumVal += hist.Integral()
      sumSamples.append(name)
      print name
  return sumVal

variations = showSysList
variations.remove('q2')
variations.remove('pdf')

def getEffect(year):
  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/' + year + '/phoCBfull-reweight/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  varHists = pickle.load(open(picklePath))
  central = getYieldMC(varHists['signalRegions'])
  rels ={}
  for var in variations:
    down = getYieldMC(varHists['signalRegions' + var + 'Down'])
    up   = getYieldMC(varHists['signalRegions' + var + 'Up'])
    relDown = round(100.*abs((down-central)/central), rounding)
    relUp   = round(100.*abs((up-central)/central), rounding)
    # print var + '\t\t' + str(round(central, rounding)) + '\t\t' + str(round(down, rounding)) + '\t  ' + str(relDown) + '\t\t' + str(round(up, rounding)) + '\t  ' + str(relUp)
    rels[var] = (relDown, relUp)
  return rels

varYears = {}
for year in ['2016', '2017', '2018']:
  varYears[year] = getEffect(year)
print '\t' '2016' + '\t \t' + '2017' + '\t \t' + '2018'
for sys in varYears['2016'].keys():
  print sys + '\t' + str(varYears['2016'][sys]) + '\t' + str(varYears['2017'][sys]) + '\t' + str(varYears['2018'][sys])