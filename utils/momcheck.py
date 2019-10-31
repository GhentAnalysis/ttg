#! /usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
from root_numpy import root2array
import numpy
import operator

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--sampleSet',   action='store',      default='TT')
args = argParser.parse_args()

path = '/storage_mnt/storage/user/gmestdac/public/reducedTuples/'
sets = {
"TT" : [ path + "2016-v1/phoCB-genBU/TT_Dil/*.root",  path + "2016-v1/phoCB-genBU/TT_Sem/*.root", path + "2016-v1/phoCB-genBU/TT_Had/*.root"],
"TTG" : [ path + "2016-v1/phoCB-genBU/TTGamma_Pr_Dil/*.root",  path + "2016-v1/phoCB-genBU/TTGamma_Pr_Sem/*.root", path + "2016-v1/phoCB-genBU/TTGamma_Pr_Had/*.root"],
}

phoMom = root2array(sets[args.sampleSet], treename="blackJackAndHookersTree", branches = "_gen_phMomPdg", warn_missing_tree = True)
vals = {}
for event in phoMom:
  for photon in event:
    if photon in vals.keys():
      vals[photon] +=1
    else: vals[photon] = 1

print("counts:")
print vals
print('-----------------------------------')
print("keys / appearing mom types:")
moms = vals.keys()
# moms = [abs(entry) for entry in moms]
# moms = list(set(moms))
# moms.sort()
# print moms

commonMoms = set([])
print("sorted by numbers:")
sortedMoms = sorted(vals.items(), key=operator.itemgetter(1), reverse=True)
# print sortedMoms
for entry in sortedMoms:
  if entry[1] > 0.001 * sortedMoms[0][1]:
    commonMoms.add(entry[0])
commonMoms = list(commonMoms)
commonMoms.sort()
print commonMoms