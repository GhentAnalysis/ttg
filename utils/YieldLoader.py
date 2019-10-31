#! /usr/bin/env python
import pickle

# picklePaths = ['/storage_mnt/storage/user/gmestdac/public_html/ttG/2016PreOct22/leptonmva-phoCBfull/all/llg-mll40-offZ-llgNoZ-photonPt20/yield.pkl']
# picklePaths = ['/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull/noData/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl']
# picklePaths = ['/storage_mnt/storage/user/gmestdac/public_html/ttG/2016PreOct22/phoCBfull/emu/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl']


picklePaths = ['/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull/noData/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl',
                '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull/noData/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20-phLepDeltaR0.4/yield.pkl',
                '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/leptonmva-phoCBfull/noData/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl',
                '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/leptonmva-phoCBfull/noData/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20-phLepDeltaR0.4/yield.pkl']


sumKeys = ['data']
antiSumKeys = ['data']

rounding = 2


# channel (or bin) yield printing
filter = 'TTGamma'
for picklePath in picklePaths:
  hists = pickle.load(open(picklePath))['yield']
  print '---------------------------------------------------------'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  print '---------------------------------------------------------'

  for name, hist in hists.iteritems():
    if name.count(filter):
      print name
      nbins = hist.GetNbinsX() + 1 
      for bin in range(1, nbins):
        print str(bin) + ': ' + str(hist.GetBinContent(bin))


# yield printing
for picklePath in picklePaths:
  hists = pickle.load(open(picklePath))['yield']
  print '---------------------------------------------------------'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  print '---------------------------------------------------------'

  for name, hist in hists.iteritems():
    print name + ': ' + str(round(hist.Integral(), rounding))

  for key in sumKeys:
    print '---------------------------------------------------------'
    sumVal = 0.
    sumSamples = []
    print 'sum of samples containing string ' + key
    for name, hist in hists.iteritems():
      if key in name: 
        sumVal += hist.Integral()
        sumSamples.append(name)
    print 'samples in sum: ' + '+'.join(sumSamples)
    print 'summed yield: ' + str(round(sumVal, rounding))

  for key in antiSumKeys:
    print '------------------------------------------'
    sumVal = 0.
    sumSamples = []
    print 'sum of samples NOT containing string ' + key
    for name, hist in hists.iteritems():
      if key not in name: 
        sumVal += hist.Integral()
        sumSamples.append(name)
    print 'samples in sum: ' + '+'.join(sumSamples)
    print 'summed yield: ' + str(round(sumVal, rounding))
