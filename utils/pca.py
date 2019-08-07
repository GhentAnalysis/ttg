#! /usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
from root_numpy import root2array
from sklearn.preprocessing import StandardScaler
from sklearn import decomposition
import numpy

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--sampleSet',   action='store',      default='allData16')
args = argParser.parse_args()

# FIXME writing this to use only samples with weights of 1 (so also data)
# some sets contain overlap, but that doesn't matter much as long as uncertainties on found values are not needed

path = '/storage_mnt/storage/user/gmestdac/public/reducedTuples/'
sets = {
"allData16" : [ path + "2016-v1/phoCB/MuonEG/*.root", path + "2016-v1/phoCB/DoubleEG/*.root", path + "2016-v1/phoCB/DoubleMuon/*.root", path + "2016-v1/phoCB/SingleMuon/*.root", path + "2016-v1/phoCB/SingleElectron/*.root"],
"allData17" : [ path + "2017-v1/phoCB/MuonEG/*.root", path + "2017-v1/phoCB/DoubleEG/*.root", path + "2017-v1/phoCB/DoubleMuon/*.root", path + "2017-v1/phoCB/SingleMuon/*.root", path + "2017-v1/phoCB/SingleElectron/*.root"],
"allData18" : [ path + "2018-v1/phoCB/MuonEG/*.root", path + "2018-v1/phoCB/EGamma/*.root", path + "2018-v1/phoCB/DoubleMuon/*.root", path + "2018-v1/phoCB/SingleMuon/*.root"],
"DoubleMuon17" : [ path + "2017-v1/phoCB/DoubleMuon/*.root"],
"DoubleEG17" : [ path + "2017-v1/phoCB/DoubleEG/*.root"],
"MuonEG17" : [ path + "2017-v1/phoCB/MuonEG/*.root"],
"TTGamma_Pr_Dil17" : [ path + "2017-v1/phoCB/TTGamma_Pr_Dil/*.root"]
      }

pho = root2array(sets[args.sampleSet], treename="blackJackAndHookersTree", branches = "ph", warn_missing_tree = True)
sigVals = root2array(sets[args.sampleSet], treename="blackJackAndHookersTree", branches = "_phSigmaIetaIeta", warn_missing_tree = True)
CIsVals = root2array(sets[args.sampleSet], treename="blackJackAndHookersTree", branches = "_phChargedIsolation", warn_missing_tree = True)

# scaling sigmaietaieta values to be of the same order as chIso, prevents tiny/huge values in rotation matrix + performs better 
sigVals = numpy.array([ 1000. * sigVal[index] for index, sigVal in zip(pho,sigVals)])
CIsVals = numpy.array([CIsVal[index] for index, CIsVal in zip(pho,CIsVals)])

vals = numpy.array([sigVals,CIsVals]).transpose()
pca = decomposition.PCA(n_components=2)
pca.fit_transform(vals)
print(args.sampleSet)
print pca.components_
