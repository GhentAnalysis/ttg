#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)
import numpy 
import argparse
from scipy.stats.stats import pearsonr  
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--rot',      action='store_true', default=False)
argParser.add_argument('--source',   action='store',      default='allData17', help= 'What rotation matrix to use (irrelavant when not choosing rot option)')
argParser.add_argument('--sample',   action='store',      default='TTGamma_Pr_Dil')
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


avs     = [("weightSum",           lambda c : c._weight),                   # sums
          ("phSigmaIetaIetaSum",  lambda c : c._weight * c._phSigmaIetaIeta[c.ph]),
          ("phChargedIsolation",  lambda c : c._weight * c._phChargedIsolation[c.ph])]
# FIXME: some undefined variables in the lines of code below 
#rotAvs = [("weightSum",           lambda c : c._weight),                   # sums
#          ("val1Sum",             lambda c : c._weight * (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) ),
#          ("val2sum",             lambda c : c._weight * (C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) )]


samples = {"TT": "/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTT/noData/llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20/dumpedArrays.pkl",
          "TTG": "/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyTTG/noData/llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20/dumpedArrays.pkl",
          "DATA": "/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-onlyDATA/all/llg-looseLeptonVeto-mll40-offZ-llgNoZ-photonPt20/dumpedArrays.pkl",
}

dict = pickle.load(open(samples[args.sample],"r"))
log.info(dict["info"])

# FIXME mistake in here!!!
sig = numpy.array(dict["_phSigmaIetaIeta"]).transpose()
cha = numpy.array(dict["_phChargedIsolation"]).transpose()
avSig = numpy.average(sig)
avCha = numpy.average(cha)

w = numpy.sum(sig[1])
sSig = numpy.sum(sig[1] * numpy.square(sig - avSig))
sCha = numpy.sum(sig[1] * numpy.square(cha - avCha))
cov = numpy.sum(sig[1] * (sig - avSig) * (cha - avCha)) 
log.info(str(cov/(sSig * sCha)**0.5 ))

log.info(numpy.correlate(sig[0],cha[0])) 
log.info(pearsonr(sig[0],cha[0]))
# averages  = calcCorr(chain, [val[1] for val in toCalc])

# for valName, valSum in zip([val[0] for val in toCalc], averages):
#   log.info(valName + ": " + str(valSum))
# avgVal1  = averages[1]/averages[0]
# avgVal2 = averages[2]/averages[0]

# log.info("average " + toCalc[1][0] + " : "      + str(avgVal1))
# log.info("average " + toCalc[2][0] + " : "  + str(avgVal2))

# var    = [("sSig",    lambda c : c._weight * (c._phSigmaIetaIeta[c.ph]    - avgVal1)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
#           ("sCha",    lambda c : c._weight * (c._phChargedIsolation[c.ph] - avgVal2)**2. ),
#           ("cov",     lambda c : c._weight * (c._phSigmaIetaIeta[c.ph]    - avgVal1) * (c._phChargedIsolation[c.ph] - avgVal2))]

# rotVar = [("val1Vari",    lambda c : c._weight * ( (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) - avgVal1)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
#           ("val2Vari",    lambda c : c._weight * ( (C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) - avgVal2)**2. ),
#           ("cov12",       lambda c : c._weight * ( (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) - avgVal1) * ((C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) - avgVal2) )]

# toCalc = rotVar if args.rot else var

# variances  = calcCorr(chain, [val[1] for val in toCalc])

# for valName, valSum in zip([val[0] for val in toCalc], variances):
#   log.info(valName + ": " + str(valSum))

# log.info("correlation: " + str(variances[2]/(variances[0]*variances[1])**(0.5)))
