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

sourceHists ={'2016': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/all/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl'
}

def sumHists(picklePath):
  hists = pickle.load(open(picklePath))['signalRegions']
  dHist = None
  zHist = None
  nonzHist = None
  for name, hist in hists.iteritems():
    if 'data' in name:
      if not dHist: dHist = hist
      else: dHist.Add(hist)
    elif 'ZG' in name:
      if not zHist:zHist = hist
      else: zHist.Add(hist)
    else:
      if not nonzHist: nonzHist = hist
      else: nonzHist.Add(hist)
  return (dHist, zHist, nonzHist)

class ZgWeight:
  def __init__(self, year):
    data, zg, otherMC = sumHists(sourceHists[year])
    data.Add(otherMC, -1.)
    data.Divide(zg)
    for i in range(1, data.GetNbinsX()+1):
      if data.GetBinContent(i) < 0.000001: data.SetBinContent(i, 1.)
    self.weightMap = data
    assert self.weightMap

  def getWeight(self, tree):
    return self.weightMap.GetBinContent(createSignalRegions(tree)+1)


if __name__ == '__main__':
  tester = ZgWeight('2016')
  tester.weightMap.Draw()
