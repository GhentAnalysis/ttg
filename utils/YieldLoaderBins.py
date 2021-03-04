#! /usr/bin/env python
import pickle

picklePaths = [
  '/storage_mnt/storage/user/jroels/public_html/ttG/2016/phoCBfull-compRewContribMCTTBAR-forNPclosure-TTDYEstAOZ/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/',
  '/storage_mnt/storage/user/jroels/public_html/ttG/2017/phoCBfull-compRewContribMCTTBAR-forNPclosure-TTDYEstAOZ/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/',
  '/storage_mnt/storage/user/jroels/public_html/ttG/2018/phoCBfull-compRewContribMCTTBAR-forNPclosure-TTDYEstAOZ/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/',
   '/storage_mnt/storage/user/jroels/public_html/ttG/all/phoCBfull-compRewContribMCTTBAR-forNPclosure-TTDYEstAOZ/noData/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/',
              ]


def sumHists(dict, plot, sumkeys, antiSumKeys):
  sumHist = None
  for name, hist in dict.iteritems():
    if any((name.count(key) for key in sumkeys)) and not any((name.count(key) for key in antiSumKeys)):
      if not sumHist: sumHist = hist.Clone()
      else: sumHist.Add(hist)
  return sumHist



# sumKeys = ['data']
# antiSumKeys = ['data']

rounding = 2

for picklePath in picklePaths:
  print '---------------------------------------------------------'
  print picklePath.replace('/storage_mnt/storage/user/jroels/public_html/ttG/','')
  print '---------------------------------------------------------'

  print('yield / channels')
  hists = pickle.load(open(picklePath+ 'yield.pkl'))['yield']
  ttmc = sumHists(hists, 'yield', ['TT_Dilt#bar{t} (nonprompt)'], ['nonprompt-estimate'])
  ttes = sumHists(hists, 'yield', ['nonprompt-estimate'], ['TT_Dilt#bar{t} (nonprompt)'])
  ttmc.Divide(ttes)

  for bin in range(1, ttmc.GetNbinsX() + 1 ):
    print(str(bin) + ':  ' + str(ttmc.GetBinContent(bin)) + ' +- '  + str(ttmc.GetBinError(bin) ))

  print('signal regions')
  hists = pickle.load(open(picklePath+ 'signalRegionsCap.pkl'))['signalRegionsCap']
  ttmc = sumHists(hists, 'signalRegionsCap', ['TT_Dilt#bar{t} (nonprompt)'], ['nonprompt-estimate'])
  ttes = sumHists(hists, 'signalRegionsCap', ['nonprompt-estimate'], ['TT_Dilt#bar{t} (nonprompt)'])
  ttmc.Divide(ttes)

  for bin in range(1, ttmc.GetNbinsX() + 1 ):
    print(str(bin) + ':  ' + str(ttmc.GetBinContent(bin)) + ' +- '  + str(ttmc.GetBinError(bin) ))

  print('phpt')
  hists = pickle.load(open(picklePath+ 'unfReco_phPt.pkl'))['unfReco_phPt']
  ttmc = sumHists(hists, 'unfReco_phPt', ['TT_Dilt#bar{t} (nonprompt)'], ['nonprompt-estimate'])
  ttes = sumHists(hists, 'unfReco_phPt', ['nonprompt-estimate'], ['TT_Dilt#bar{t} (nonprompt)'])
  ttmc.Divide(ttes)

  for bin in range(1, ttmc.GetNbinsX() + 2 ):
    print(str(bin) + ':  ' + str(ttmc.GetBinContent(bin)) + ' +- '  + str(ttmc.GetBinError(bin) ))


# for picklePath in picklePaths:
#   print '---------------------------------------------------------'
#   print picklePath.replace('/storage_mnt/storage/user/jroels/public_html/ttG/','')
#   print '---------------------------------------------------------'

#   print('yield / channels')
#   hists = pickle.load(open(picklePath+ 'yield.pkl'))['yield']
#   ttmc = sumHists(hists, 'yield', ['TT_Dilt#bar{t} (nonprompt)'], ['nonprompt-estimate'])
#   ttes = sumHists(hists, 'yield', ['nonprompt-estimate'], ['TT_Dilt#bar{t} (nonprompt)'])
#   print ttmc.Integral()/ttes.Integral()


  # nbins = hist.GetNbinsX() + 1 
  # for bin in range(1, nbins):
  # print str(bin) + ': ' + str(hist.GetBinContent(bin))
  # print val


  # for name, hist in hists.iteritems():
  #   print name + ': ' + str(round(hist.Integral(), rounding))

  # for key in sumKeys:
  #   print '---------------------------------------------------------'
  #   sumVal = 0.
  #   sumSamples = []
  #   print 'sum of samples containing string ' + key
  #   for name, hist in hists.iteritems():
  #     if key in name: 
  #       sumVal += hist.Integral()
  #       sumSamples.append(name)
  #   print 'samples in sum: ' + '+'.join(sumSamples)
  #   print 'summed yield: ' + str(round(sumVal, rounding))




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
#     if name.count(filter):
#       print name
#       nbins = hist.GetNbinsX() + 1 
#       for bin in range(1, nbins):
#         print str(bin) + ': ' + str(hist.GetBinContent(bin))
#   print val


