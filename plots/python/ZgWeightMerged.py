#
# weights for correcting Zg shape and yield using on-Zg, off-DY control region
#
# NOTE currently both Zg genuine and nonprompt will be scaled/corrected, shouldn't matter much but this seems most correct

from ttg.plots.plotHelpers import createSignalRegions
import os
import pickle
import time
import pdb
import ROOT
sourceHists ={'2016': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-forZgest-noZgCorr/CHAN/llg-mll20-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2017': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-forZgest-noZgCorr/CHAN/llg-mll20-offZ-llgOnZ-photonPt20/signalRegions.pkl',
              '2018': '/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-forZgest-noZgCorr/CHAN/llg-mll20-offZ-llgOnZ-photonPt20/signalRegions.pkl'
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




class ZgWeightTotal:
  def __init__(self, sys = ''):
    # in the on-Zg regions there is no DD NP estimate -> ttbar sample variations have an effect, but don't in SR. 
    # might need to rethink this when ttgamma syst samples are used. although ttgamma is negigible on-Zg
    if any([s in sys for s in ['erd', 'hdamp', 'ue', 'NP', 'colRec', 'bFrag']]): sys = ''
    data, zg, otherMC = sumHists(sourceHists['2016'], 'ee', sys = sys)
    data17ee, zg17ee, otherMC17ee = sumHists(sourceHists['2017'], 'ee', sys = sys)
    data18ee, zg18ee, otherMC18ee = sumHists(sourceHists['2018'], 'ee', sys = sys)
    datamm, zgmm, otherMCmm = sumHists(sourceHists['2016'], 'mumu', sys = sys)
    data17mm, zg17mm, otherMC17mm = sumHists(sourceHists['2017'], 'mumu', sys = sys)
    data18mm, zg18mm, otherMC18mm = sumHists(sourceHists['2018'], 'mumu', sys = sys)

    data.Add(data17ee)
    data.Add(data18ee)
    zg.Add(zg17ee)
    zg.Add(zg18ee)
    otherMC.Add(otherMC17ee)
    otherMC.Add(otherMC18ee)

    datamm.Add(data17mm)
    datamm.Add(data18mm)
    zgmm.Add(zg17mm)
    zgmm.Add(zg18mm)
    otherMCmm.Add(otherMC17mm)
    otherMCmm.Add(otherMC18mm)

    data.Add(datamm)
    zg.Add(zgmm)
    otherMC.Add(otherMCmm)

# TODO merge the last two bins
    data.SetBinContent(9, data.GetBinContent(9) + data.GetBinContent(10))
    data.SetBinError(9, (data.GetBinError(9)**2 + data.GetBinError(10)**2)**0.5)
    data.SetBinContent(10, 0)
    data.SetBinError(10, 0)

    zg.SetBinContent(9, zg.GetBinContent(9) + zg.GetBinContent(10))
    zg.SetBinError(9, (zg.GetBinError(9)**2 + zg.GetBinError(10)**2)**0.5)
    zg.SetBinContent(10, 0)
    zg.SetBinError(10, 0)

    otherMC.SetBinContent(9, otherMC.GetBinContent(9) + otherMC.GetBinContent(10))
    otherMC.SetBinError(9, (otherMC.GetBinError(9)**2 + otherMC.GetBinError(10)**2)**0.5)
    otherMC.SetBinContent(10, 0)
    otherMC.SetBinError(10, 0)

    data.Add(otherMC, -1.)
    data.Divide(zg)

    data.SetBinContent(10, 0)
    data.SetBinError(10, 0)


    for i in range(1, data.GetNbinsX()+1):
      if data.GetBinContent(i) < 0.000001: data.SetBinContent(i, 1.)
    self.weightMap = data.Clone()
    assert self.weightMap


  def getWeight(self, tree, channel):
    if channel == 1 or channel == 3:
      return self.weightMap.GetBinContent(min(createSignalRegions(tree)+1, 9))
    else: 
      return 1.

