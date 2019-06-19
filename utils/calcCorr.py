#! /usr/bin/env python
import ROOT, pickle, os
ROOT.gROOT.SetBatch(True)

import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--tag',      action='store',      default='avg')
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

if not args.isChild and args.submit:
  from ttg.tools.jobSubmitter import submitJobs
  submitJobs(__file__, ('sample', 'year'), [(args.sample, args.year,)], argParser, subLog= args.tag + '/' + args.year + args.sample , queue='highbw', jobLabel = "CO")
  exit(0)

if not args.year:
  log.info("Specify the year")
  exit(0)

from ttg.reduceTuple.objectSelection import setIDSelection, selectLeptons, selectPhotons, goodJets
from ttg.samples.Sample import createSampleList, getSampleFromList

def calcCorr(c, expressions):  # pylint: disable=R0912
  
  # FIXME: temporarily until new trees available
  
  if not hasattr(c, '_phHadTowOverEm'):
    def switchBranches(default, variation):
      return lambda chain: setattr(chain, default, getattr(chain, variation))
    log.warning('_phHadTowOverEm does not exists, taking _phHadronicOverEm for now')
    branchModifications = [switchBranches('_phHadTowOverEm', '_phHadronicOverEm')]
  else:
    branchModifications = []
  
  valSums = zip([0.] * len(expressions), expressions)
  for i in sample.eventLoop():
    c.GetEntry(i)
    for s in branchModifications: s(c) # FIXME: temporarily until _phHadTowOverEm becomes available
    # if not selectLeptons(c, c, 2):       continue
    # if not selectPhotons(c, c, 2, True): continue
    valSums = [(val + expression(c), expression) for val, expression in valSums]

  return [val[0] for val in valSums]

# FIXME is reducetype phoCB low enough? the extrapolation happens "within" that skim so I guess this is good

sampleList           = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_'+ args.year +'.conf'))
sample               = getSampleFromList(sampleList, args.sample)
chain                = sample.initTree(reducedType = "phoCB", shortDebug=args.debug)
setIDSelection(chain, 'phoCB')

totWeight =349951.0
avgVal1 =5004451.58303/totWeight
avgVal2 =-2894023.18958/totWeight

if sample.isData: 
  chain._weight = 1.

if args.tag.count("corr"):
  values = [("sSig",    lambda c : c._weight * (c._phSigmaIetaIeta[c.ph] - avgSig)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
            ("sCha",    lambda c : c._weight * (c._phChargedIsolation[c.ph] - avgCIso)**2. ),
            ("cov",     lambda c : c._weight * (c._phSigmaIetaIeta[c.ph] - avgSig) * (c._phChargedIsolation[c.ph] - avgCIso))]

elif args.tag.count("avg"):
  values = [("weightSum",           lambda c : c._weight),                   # sums
            ("phSigmaIetaIetaSum",  lambda c : c._weight * c._phSigmaIetaIeta[c.ph]),
            ("phChargedIsolation",   lambda c : c._weight * c._phChargedIsolation[c.ph])]

# based on all 2017 data::
if args.tag.count("corrRot"):
  values = [("val1Vari",    lambda c : c._weight * ( (0.63267834 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.77441469 * c._phChargedIsolation[c.ph]) - avgVal1)**2. ),                   # weighted variances and covariance  (need to divide wy sum of weight)
            ("val2Vari",    lambda c : c._weight * ( (-0.77441469 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.63267834 * c._phChargedIsolation[c.ph]) - avgVal2)**2. ),
            ("cov12",       lambda c : c._weight * ((0.63267834 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.77441469 * c._phChargedIsolation[c.ph]) - avgVal1) * ((-0.77441469 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.63267834 * c._phChargedIsolation[c.ph]) - avgVal2) )]

elif args.tag.count('avgRot'):
  values = [("weightSum",           lambda c : c._weight),                   # sums
            ("val1Sum",             lambda c : c._weight * (0.63267834 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.77441469 * c._phChargedIsolation[c.ph]) ),
            ("val2sum",             lambda c : c._weight * (-0.77441469 * 1000. * c._phSigmaIetaIeta[c.ph] + 0.63267834 * c._phChargedIsolation[c.ph]) )]

else:
  log.warning("tag not understood")
  exit(0)


valSums = calcCorr(chain, [val[1] for val in values])
for valName, valSum in zip([val[0] for val in values], valSums):
  log.info(valName + ": " + str(valSum))
if args.tag.count("corr"):
  log.info(valSums[2]/(valSums[0]*valSums[1])**(0.5))
log.info('Finished')


