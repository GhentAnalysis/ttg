#! /usr/bin/env python
import pickle
from ttg.plots.systematics import showSysList, showSysListRunII

rounding = 4

def getYieldMC(hists):
  sumVal = 0.
  # sumSamples = []
  for name, hist in hists.iteritems():
    if not 'data' in name: 
      sumVal += hist.Integral()
      # sumSamples.append(name)
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


def getOutliers(var, varHists, totDown, totUp, totalCentral):
  outLiers = {}
  for name, hist in varHists['yield'].iteritems():
    if not 'data' in name:
      central = hist.Integral()
      if central == 0: continue
      down = varHists['yield' + var + 'Down'][name].Integral()
      up   = varHists['yield' + var + 'Up'][name].Integral()
      down = round(100.*(down-central)/central, rounding)
      up   = round(100.*(up-central)/central, rounding)
      if abs(up) > 2.0 * abs(totUp) or abs(down) > 2.0 * abs(totDown) or 'ZG' in name:
      # if abs(up) > 1.5 * abs(totUp) or abs(down) > 1.5 * abs(totDown) or 'ZG' in name:
        outLiers[name] = [down, up, str(round(100.* central/totalCentral, rounding)) + '%'  ]
  return outLiers

variations = showSysListRunII
# variations.remove('q2')
# variations.remove('pdf')
# variations = ['NP']
# https://homepage.iihe.ac.be/~gmestdac/ttG/2017/phoCBfull-defaultEstimDD-VR/ee//llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegionsZoom.pkl
def getEffect():
  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/all/phoCBfull-niceEstimDD-merged/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/yield.pkl'

  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  varHists = pickle.load(open(picklePath))
  central = getYieldMC(varHists['yield'])
  rels ={}
  outLiers={}
  for var in variations:
    try:
      down = getYieldMC(varHists['yield' + var + 'Down'])
      up   = getYieldMC(varHists['yield' + var + 'Up'])
      relDown = round(100.*(down-central)/central, rounding)
      relUp   = round(100.*(up-central)/central, rounding)
      # print var + '\t\t' + str(round(central, rounding)) + '\t\t' + str(round(down, rounding)) + '\t  ' + str(relDown) + '\t\t' + str(round(up, rounding)) + '\t  ' + str(relUp)
      rels[var] = (relDown, relUp)
      try:
        outLiers[var] = getOutliers(var, varHists, relDown, relUp, central)
      except Exception as ex:
        print ex
        outLiers[var] = {'err':'err'}
    except:
      rels[var] = ('nan', 'nan')
      outLiers[var] = {}
  mcstat = round(100.* getStatErr(varHists['yield'], True)  / getYieldData(varHists['yield']), rounding)
  dastat = round(100.* getStatErr(varHists['yield'], False) / getYieldData(varHists['yield']), rounding)
  rels['statMC'] = (mcstat, mcstat )
  rels['statDA'] = (dastat, dastat )

  return rels, outLiers

effect, outliers = getEffect()
# print effect
for sys in effect.keys():
  # print sys + '\t' + str(varYears['2016'][sys]),
  print sys + '\t' + str(effect[sys])
  # try:
  #   for name, effect in outYears['2016'][sys].iteritems():
  #   # for name, effect in outYears['2017'][sys].iteritems():
  #     print '\t' + name[:10] + '    ' + str(effect),
  # except:
  #   pass
  # print ''
