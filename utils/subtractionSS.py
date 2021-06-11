#! /usr/bin/env python
import pickle

picklePaths = [
  # '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull/all/llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20/yield.pkl',
  '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-niceEstimDD/all//llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/yield.pkl',
              ]

rounding = 2

for picklePath in picklePaths:
  hists = pickle.load(open(picklePath))['yield']
  print '---------------------------------------------------------'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  print '---------------------------------------------------------'

  for name, hist in hists.iteritems():
    print name + ': ' + str(round(hist.Integral(), rounding))

  print '---------------------------------------------------------'
  sumData = 0.
  sumBkg = 0.
  sumSig = 0.

  for name, hist in hists.iteritems():
    if 'data' in name: 
      sumData += hist.Integral()
    elif 'TTG' in name: 
      sumSig += hist.Integral()
    else:
      sumBkg += hist.Integral()

  print 'data: ' + str(round(sumData, rounding))
  print 'MC: ' + str(round(sumBkg+sumSig, rounding))
  print 'signal MC: ' + str(round(sumSig, rounding))
  print 'background MC: ' + str(round(sumBkg, rounding))
  print 'data - MC bkg: ' + str(round(sumData - sumBkg, rounding))
  print 'signal strength: ' + str(round((sumData - sumBkg) / sumSig, rounding+1))

