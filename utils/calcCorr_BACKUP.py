#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
# argParser.add_argument('--tag',      action='store',      default='avg')
argParser.add_argument('--rot',      action='store_true', default=False)
argParser.add_argument('--source',   action='store',      default='allData17', help= 'What rotation matrix to use (irrelavant when not choosing rot option)')
argParser.add_argument('--sample',   action='store',      default='TTGamma_Pr_Dil')
argParser.add_argument('--year',     action='store',      default='None', choices=['2016', '2017', '2018'])
argParser.add_argument('--submit',   action='store_true', default=False,  help='submit the script, needed as for some large samples runtime exceeds 5 hours')
argParser.add_argument('--isChild',  action='store_true', default=False,  help='mark as subjob, will never submit subjobs by itself')
argParser.add_argument('--runLocal', action='store_true', default=False,  help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='do not launch subjobs, only show them')
argParser.add_argument('--debug',    action='store_true', default=False,  help='only run over first three files for debugging')
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#if not args.isChild and args.submit:
#  from ttg.tools.jobSubmitter import submitJobs
#  submitJobs(__file__, ('sample', 'year'), [(args.sample, args.year,)], argParser, subLog= args.source + '/' + args.year + args.sample , queue='highbw', jobLabel = "CO")
#  exit(0)

if not args.year:
  log.info("Specify the year")
  exit(0)

from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, goodJets
from ttg.samples.Sample import createSampleList, getSampleFromList

def calcCorr(c, expressions):  # pylint: disable=R0912
  
  valSums = zip([0.] * len(expressions), expressions)
  for i in sample.eventLoop():
    c.GetEntry(i)
    # if not selectLeptons(c, c, 2):       continue
    # if not selectPhotons(c, c, 2, True): continue
    # if not c._phTTGMatchCategory[c.ph] == 4 or c._phTTGMatchCategory[c.ph] == 2: continue
    if not c._phTTGMatchCategory[c.ph] == 4: continue
    # if c._phPtCorr[c.ph] > 60: continue
    valSums = [(val + expression(c), expression) for val, expression in valSums]

  return [val[0] for val in valSums]

# FIXME is reducetype phoCB low enough? the extrapolation happens "within" that skim so I guess this is good

sampleList           = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_'+ args.year +'.conf'))
sample               = getSampleFromList(sampleList, args.sample)
chain                = sample.initTree(reducedType = "phoCB", shortDebug=args.debug)
setIDSelection(chain, 'phoCB') #doesn't matter, running on reduced tuples, lepton selection pho reduced cut etc already applied

# available rotation matrixes determined using the pca script, of shape |a b|
#                                                            (a,b,c,d)  |c d|


# NOTE don't forget the 1000 factors below
rotMat = {
# "allData16": ( , , , )
"allData17": ( 0.63267834, 0.77441469, -0.77441469, 0.63267834),
# "allData18": ( , , , )
"DoubleMuon17" : (0.69633711, 0.71771487, -0.71771487, 0.69633711),
"DoubleEG17" : (0.64780629, 0.7618051, -0.7618051, 0.64780629),
"MuonEG17" : (0.33371998, 0.94267225, -0.94267225, 0.33371998),
"TTGamma_Pr_Dil17" : (0.74558727, 0.66640801, -0.66640801, 0.74558727),
"DoubleMuon17Decomp": (1.76026294e-01, -1.82030036, -1.82029790, 6.58861883e-02),
"allData17Decomp": (-1.40216775e-01, 1.35178279, -1.38386044, 4.93895529e-02),
"DM17failSig": (-2.33504901e-04, -3.48052948e-05, -3.99666972e-05, 2.21424411e-04)}
try:
  A, B, C, D = rotMat[args.source]
except:
  log.info("unknown source name, exiting")
  exit(0)

if sample.isData: 
  chain._weight = 1.

avs     = [("weightSum",           lambda c : c._weight),                   # sums
          ("phSigmaIetaIetaSum",  lambda c : c._weight * c._phSigmaIetaIeta[c.ph]),
          ("phChargedIsolation",  lambda c : c._weight * c._phChargedIsolation[c.ph])]

rotAvs = [("weightSum",           lambda c : c._weight),                   # sums
          ("val1Sum",             lambda c : c._weight * (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) ),
          ("val2sum",             lambda c : c._weight * (C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) )]

toCalc = rotAvs if args.rot else avs

averages  = calcCorr(chain, [val[1] for val in toCalc])

for valName, valSum in zip([val[0] for val in toCalc], averages):
  log.info(valName + ": " + str(valSum))
avgVal1  = averages[1]/averages[0]
avgVal2 = averages[2]/averages[0]

log.info("average " + toCalc[1][0] + " : "      + str(avgVal1))
log.info("average " + toCalc[2][0] + " : "  + str(avgVal2))

var    = [("sSig",    lambda c : c._weight * (c._phSigmaIetaIeta[c.ph]    - avgVal1)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
          ("sCha",    lambda c : c._weight * (c._phChargedIsolation[c.ph] - avgVal2)**2. ),
          ("cov",     lambda c : c._weight * (c._phSigmaIetaIeta[c.ph]    - avgVal1) * (c._phChargedIsolation[c.ph] - avgVal2))]

rotVar = [("val1Vari",    lambda c : c._weight * ( (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) - avgVal1)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
          ("val2Vari",    lambda c : c._weight * ( (C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) - avgVal2)**2. ),
          ("cov12",       lambda c : c._weight * ( (A * 1000. * c._phSigmaIetaIeta[c.ph] + B * c._phChargedIsolation[c.ph]) - avgVal1) * ((C * 1000. * c._phSigmaIetaIeta[c.ph] + D * c._phChargedIsolation[c.ph]) - avgVal2) )]

toCalc = rotVar if args.rot else var

variances  = calcCorr(chain, [val[1] for val in toCalc])

for valName, valSum in zip([val[0] for val in toCalc], variances):
  log.info(valName + ": " + str(valSum))

log.info("correlation: " + str(variances[2]/(variances[0]*variances[1])**(0.5)))
