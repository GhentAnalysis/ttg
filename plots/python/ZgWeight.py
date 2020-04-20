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
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest/CHAN/llg-mll40-offZ-llgOnZ-photonPt20/signalRegions.pkl'
}

def getZgSR(picklePath, sys):
  hists = pickle.load(open(picklePath))['signalRegions' + sys]
  zHist = None
  for name, hist in hists.iteritems():
    if 'ZG' in name:
      if not zHist:zHist = hist
      else: zHist.Add(hist)
  return zHist

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
  def __init__(self, year, sys = '', nominal = '', sysNoZgCorr = ''):
    # sys variations are corrected to match signalRegion shape of nominal plots
    if sys:
      eeNom = getZgSR(nominal.replace('CHAN', 'ee'), sys = '')
      eeSys = getZgSR(sysNoZgCorr.replace('CHAN', 'ee'), sys = sys)
      eeNom.Divide(eeSys)
      for i in range(1, eeNom.GetNbinsX()+1):
        if eeNom.GetBinContent(i) < 0.000001: eeNom.SetBinContent(i, 1.)
      self.weightMapEE = eeNom
      assert self.weightMapEE

      mumuNom = getZgSR(nominal.replace('CHAN', 'mumu'), sys = '')
      mumuSys = getZgSR(sysNoZgCorr.replace('CHAN', 'mumu'), sys = sys)
      mumuNom.Divide(mumuSys)
      for i in range(1, mumuNom.GetNbinsX()+1):
        if mumuNom.GetBinContent(i) < 0.000001: mumuNom.SetBinContent(i, 1.)
      self.weightMapMUMU = mumuNom
      assert self.weightMapMUMU

    # nominal sample is corrected based on Zg sideband
    else:
      data, zg, otherMC = sumHists(sourceHists[year], 'ee')
      data.Add(otherMC, -1.)
      data.Divide(zg)
      for i in range(1, data.GetNbinsX()+1):
        if data.GetBinContent(i) < 0.000001: data.SetBinContent(i, 1.)
      self.weightMapEE = data
      assert self.weightMapEE

      data, zg, otherMC = sumHists(sourceHists[year], 'mumu')
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


if __name__ == '__main__':
  tester = ZgWeight('2016')
  tester.weightMap.Draw()