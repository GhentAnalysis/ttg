#! /usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)
from root_numpy import root2array
from sklearn.preprocessing import StandardScaler
from sklearn import decomposition
import numpy



# FIXME writing this to use only samples with weights of 1 (so also data)
# pho = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/TTGamma_Pr_Dil/TTGamma_Pr_Dil_*.root", treename="blackJackAndHookersTree", branches = "ph")
# sigVals = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/TTGamma_Pr_Dil/TTGamma_Pr_Dil_*.root", treename="blackJackAndHookersTree", branches = "_phSigmaIetaIeta")
# CIsVals = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/TTGamma_Pr_Dil/TTGamma_Pr_Dil_*.root", treename="blackJackAndHookersTree", branches = "_phChargedIsolation")

# pho = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/MuonEG/*.root", treename="blackJackAndHookersTree", branches = "ph", warn_missing_tree = True)
# sigVals = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/MuonEG/*.root", treename="blackJackAndHookersTree", branches = "_phSigmaIetaIeta", warn_missing_tree = True)
# CIsVals = root2array("/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/MuonEG/*.root", treename="blackJackAndHookersTree", branches = "_phChargedIsolation", warn_missing_tree = True)

allData= ["/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/MuonEG/*.root",
          "/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/DoubleEG/*.root",
          "/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/DoubleMuon/*.root",
          "/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/SingleMuon/*.root",
          "/storage_mnt/storage/user/gmestdac/public/reducedTuples/2017-v1/phoCB/SingleElectron/*.root"]
pho = root2array(allData, treename="blackJackAndHookersTree", branches = "ph", warn_missing_tree = True)
sigVals = root2array(allData, treename="blackJackAndHookersTree", branches = "_phSigmaIetaIeta", warn_missing_tree = True)
CIsVals = root2array(allData, treename="blackJackAndHookersTree", branches = "_phChargedIsolation", warn_missing_tree = True)

sigVals = sigVals * 1000. 

sigVals = numpy.array([sigVal[index] for index, sigVal in zip(pho,sigVals)])
CIsVals = numpy.array([CIsVal[index] for index, CIsVal in zip(pho,CIsVals)])

vals = numpy.array([sigVals,CIsVals]).transpose()
pca = decomposition.PCA(n_components=2)
pca.fit_transform(vals)
print pca.components_
# print pca
