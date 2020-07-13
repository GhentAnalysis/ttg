#! /usr/bin/env python
import pickle

picklePaths = [
  # '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull/all/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl',
  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-reweight/all/llg-mll40-signalRegion-offZ-llgNoZ-photonPt20/signalRegions.pkl',
              ]
sumKeys = ['data']
antiSumKeys = ['data']

rounding = 2


# # channel (or bin) yield printing
# # filter = 'TTGamma'
# filter = ''
# for picklePath in picklePaths:
#   hists = pickle.load(open(picklePath))['signalRegions']
#   # hists = pickle.load(open(picklePath))['yield']
#   print '---------------------------------------------------------'
#   print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
#   print '---------------------------------------------------------'
#   val = 0. 
#   for name, hist in hists.iteritems():
#     val += hist.GetBinError(2)
#     # if name.count(filter):
#     #   print name
#     #   nbins = hist.GetNbinsX() + 1 
#     #   for bin in range(1, nbins):
#     #     print str(bin) + ': ' + str(hist.GetBinContent(bin))
#   print val


# yield printing

variations = ['','erdUp','erdDown']
# variations = ['','isrUp','fsrUp','ueUp','hdampUp','erdUp','eScaleUp','eResUp','phScaleUp','phResUp','puUp','phSFUp','lSFUp','triggerUp','bTaglUp','bTagbUp','JECUp','JERUp','isrDown','fsrDown','ueDown','hdampDown','erdDown','eScaleDown','eResDown','phScaleDown','phResDown','puDown','phSFDown','lSFDown','triggerDown','bTaglDown','bTagbDown','JECDown','JERDown']

for var in variations:
  for picklePath in picklePaths:
    hists = pickle.load(open(picklePath))['signalRegions' + var]
    print '---------------------------------------------------------'
    print 'variation:' + var
    print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
    print '---------------------------------------------------------'

    # for name, hist in hists.iteritems():
      # print name + ': ' + str(round(hist.Integral(), rounding))

    # for key in sumKeys:
    #   print '---------------------------------------------------------'
    #   sumVal = 0.
    #   sumSamples = []
    #   print 'sum of samples containing string ' + key
    #   for name, hist in hists.iteritems():
    #     if key in name: 
    #       sumVal += hist.Integral()
    #       sumSamples.append(name)
    #   # print 'samples in sum: ' + '+'.join(sumSamples)
    #   print 'summed yield: ' + str(round(sumVal, rounding))

    for key in antiSumKeys:
      print '------------------------------------------'
      sumVal = 0.
      sumSamples = []
      print 'sum of samples NOT containing string ' + key
      for name, hist in hists.iteritems():
        if key not in name: 
          # sumVal += hist.Integral()
          sumVal += hist.GetBinContent(9)
          sumSamples.append(name)
      # print 'samples in sum: ' + '+'.join(sumSamples)
      print 'summed yield: ' + str(round(sumVal, rounding))

