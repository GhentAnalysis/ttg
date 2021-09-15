#! /usr/bin/env python
import pickle

categories = {'3': 'b               ',
'5': 'l from W (pythia)    ',
'6': 'W or dec (part of ME)',
'7': 'top                  ',
'8': 'ME                   '}
for cat, label in categories.iteritems():
    hists = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-topmass' + cat + '/all/llg-deepbtag1p-photonPt20/yield.pkl'))['yield']
    # print 'origin: ' + label
    nom  = hists['TT_Dilt#bar{t}dil (genuine)'].Integral()
    up  = hists['TT_Dil_mtupt#bar{t}dil mtUp(genuine)'].Integral()
    down = hists['TT_Dil_mtdownt#bar{t}dil mtDown (genuine)'].Integral()
    print 'origin: ' + label + ' \t up:' + str(round((up-nom)/nom*100., 1)) + '\% down: ' + str(round((down-nom)/nom*100., 1)) + '\%'
    # print '---------------------------------------------------------'



