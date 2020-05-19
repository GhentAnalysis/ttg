#
# weights for correcting Zg shape and yield using on-Zg, off-DY control region
#
# NOTE currently both Zg genuine and nonprompt will be scaled/corrected, shouldn't matter much but this seems most correct

import os
from ttg.tools.helpers import getObjFromFile, multiply
from ttg.tools.uncFloat import UncFloat
from ttg.plots.plotHelpers import createSignalRegions
import pickle
import time

sourceHists ={'2016': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017PreApr27/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl'
}

def sumHists(picklePath, channel, sys = ''):
  hists = pickle.load(open(picklePath.replace('CHAN', channel)))['signalRegions' + sys]
  zHist = None
  nonzHist = None
  for name, hist in hists.iteritems():
    if 'data' in name:
      continue
    elif 'ZG' in name:
      if not zHist:zHist = hist
      else: zHist.Add(hist)
    else:
      if not nonzHist: nonzHist = hist
      else: nonzHist.Add(hist)

  # data is 0 in syst variation histograms, always use nominal
  nomHists = pickle.load(open(picklePath.replace('CHAN', channel)))['signalRegions']
  dHist = None
  for name, hist in nomHists.iteritems():
    if 'data' in name:
      if not dHist: dHist = hist
      else: dHist.Add(hist)

  return (dHist, zHist, nonzHist)

class ZgWeight:
  def __init__(self, year, sys = ''):
    # in the on-Zg regions there is no DD NP estimate -> ttbar sample variations have an effect, but don't in SR. 
    # might need to rethink this when ttgamma syst samples are used. although ttgamma is negigible on-Zg
    if any([s in sys for s in ['erd', 'hdamp', 'ue']]): sys = ''
    data, zg, otherMC = sumHists(sourceHists[year], 'ee', sys = sys)
    data.Add(otherMC, -1.)
    data.Divide(zg)
    for i in range(1, data.GetNbinsX()+1):
      if data.GetBinContent(i) < 0.000001: data.SetBinContent(i, 1.)
    self.weightMapEE = data
    assert self.weightMapEE

    data, zg, otherMC = sumHists(sourceHists[year], 'mumu', sys = sys)
    data.Add(otherMC, -1.)
    data.Divide(zg)
    for i in range(1, data.GetNbinsX()+1):
      if data.GetBinContent(i) < 0.000001: data.SetBinContent(i, 1.)
    self.weightMapMUMU = data
    assert self.weightMapMUMU

  def getWeight(self, tree, channel):
    if channel == 1:
      return self.weightMapMUMU.GetBinContent(createSignalRegions(tree)+1)
    elif channel == 3:
      return self.weightMapEE.GetBinContent(createSignalRegions(tree)+1)
    else: 
      return 1.

# NOTE different numbering etc than above, used by systematics plotter function
  def getWeightTest(self, sr, channel):
    if channel == 0:
      return self.weightMapEE.GetBinContent(sr)
    elif channel == 1:
      return self.weightMapMUMU.GetBinContent(sr)
    else: 
      return 1.


if __name__ == '__main__':
  tester = ZgWeight('2016')
  tester.weightMap.Draw()
