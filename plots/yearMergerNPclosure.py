#! /usr/bin/env python


#
# Argument parser and logging
#
import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',  action='store',      default='INFO',               help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
# argParser.add_argument('--tag',       action='store',      default='unfTest2',           help='Specify type of reducedTuple')
args = argParser.parse_args()

import ROOT
import pdb
import glob

ROOT.gROOT.SetBatch(True)

from ttg.tools.helpers import plotDir, getObjFromFile, lumiScales, lumiScalesRounded
import copy
import pickle
import numpy
from ttg.plots.systematics import showSysListRunII

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


def getRMS(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict[''].Clone()
  rms = nominal.Clone()
  rms.Reset('ICES')

  for var in histDict.keys():
    if var == '': continue
    histDict[var].Add(nominal, -1.)
    histDict[var].Multiply(histDict[var])
    rms.Add(histDict[var])

  nvars = len(histDict)-1

  for i in range(0, rms.GetXaxis().GetNbins()+1):
    rms.SetBinContent(i, (rms.GetBinContent(i)/nvars)**0.5)
  return rms

def getEnv(histDict):
# WARNING this modifies the systematics histograms, be aware if you look at them later in the code
  nominal = histDict[''].Clone()
  maxUp = nominal.Clone()
  maxUp.Reset('ICES')
  maxDown = maxUp.Clone()

  for var in histDict.keys(): 
    histDict[var].Add(nominal, -1.)

  for i in range(0, nominal.GetNbinsX()+1):
    maxUp.SetBinContent(  i, max([hist.GetBinContent(i) for hist in histDict.values()]))
    maxDown.SetBinContent(i, min([hist.GetBinContent(i) for hist in histDict.values()]))

  return maxUp, maxDown

lumiUnc = {
'lumi_1718'  : {'16': 0.    , '17': 0.006 , '18': 0.002 },
'lumi_2016'  : {'16': 0.009 , '17': 0.    , '18': 0.    },
'lumi_2017'  : {'16': 0.    , '17': 0.02  , '18': 0.    },
'lumi_2018'  : {'16': 0.    , '17': 0.    , '18': 0.015 },
'lumi_3Ycorr': {'16': 0.006 , '17': 0.009 , '18': 0.02  }
}

# distList = [
#   'unfReco_phLepDeltaR',
#   # 'unfReco_jetLepDeltaR',
#   # 'unfReco_jetPt',
#   # 'unfReco_ll_absDeltaEta',
#   # 'unfReco_ll_deltaPhi',
#   # 'unfReco_phAbsEta',
#   # 'unfReco_phBJetDeltaR',
#   # 'unfReco_phPt',
#   # 'unfReco_phLep1DeltaR',
#   # 'unfReco_phLep2DeltaR',
#   # 'unfReco_Z_pt',
#   # 'unfReco_l1l2_ptsum'
#   ]


# noYearCor = ['lSFElStat' ,'lSFMuStat' ,'pvSF' ,'trigStatEE','trigStatEM','trigStatMM','trigSyst' ,'HFUC' ,'AbsoluteUC' ,'BBEC1UC' ,'EC2UC' ,'RelativeSampleUC', 'bTagbUC']

noYearCor = [i.split('_2016')[0] for i in showSysListRunII if i.count('_2016')]
#################### main code ####################



# for channel in ['ee', 'emu', 'mumu', 'all']:
for channel in ['noData']:
  
  distList = glob.glob('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp/' + channel + '/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/*.pkl')
  distList = [i.split('/')[-1].split('.pkl')[0] for i in distList]

  if not os.path.exists('/storage_mnt/storage/user/gmestdac/public_html/ttG/all/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp-merged/' + channel + '/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/'):
    os.makedirs('/storage_mnt/storage/user/gmestdac/public_html/ttG/all/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp-merged/' + channel + '/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/')

  for dist in distList:
    log.info('running for plot '+ dist + ' in the channel ' + channel)
    try:
      reco16 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp/'+ channel +'/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
      reco17 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2017/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp/'+ channel +'/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))
      reco18 = pickle.load(open('/storage_mnt/storage/user/gmestdac/public_html/ttG/2018/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp/'+ channel +'/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl','r'))

      recoRunII = copy.deepcopy(reco16)

      for var in recoRunII.keys():
        direc = ''  # if nominal this just stays
        if var.count('Up'):
          var = var.split('Up')[0]
          direc = 'Up'
        elif var.count('Down'):
          var = var.split('Down')[0]
          direc = 'Down'

        if any(var.count(uncorVar) for uncorVar in noYearCor):
          recoRunII[var + '_2016' + direc] = {}
          recoRunII[var + '_2017' + direc] = {}
          recoRunII[var + '_2018' + direc] = {}
          for proc in recoRunII[var + direc].keys():
            # recoRunII[var + direc][proc] = None
            recoRunII[var + '_2016' + direc][proc] = reco16[var + direc][proc].Clone()
            recoRunII[var + '_2016' + direc][proc].Add(reco17[dist][proc])
            recoRunII[var + '_2016' + direc][proc].Add(reco18[dist][proc])

            recoRunII[var + '_2017' + direc][proc] = reco16[dist][proc].Clone()
            recoRunII[var + '_2017' + direc][proc].Add(reco17[var + direc][proc])
            recoRunII[var + '_2017' + direc][proc].Add(reco18[dist][proc])

            recoRunII[var + '_2018' + direc][proc] = reco16[dist][proc].Clone()
            recoRunII[var + '_2018' + direc][proc].Add(reco17[dist][proc])
            recoRunII[var + '_2018' + direc][proc].Add(reco18[var + direc][proc])
          del recoRunII[var + direc]

        else:
          for proc in recoRunII[var+direc].keys():
            recoRunII[var + direc][proc].Add(reco17[var + direc][proc])
            recoRunII[var + direc][proc].Add(reco18[var + direc][proc])

      # recoRunII[dist + 'fdpUp'] = {}
      # recoRunII[dist + 'fdpDown'] = {}
      # recoRunII[dist + '2qUp'] = {}
      # recoRunII[dist + '2qDown'] = {}

      # for proc in recoRunII[dist].keys():
      #   q2dict16 =  dict((var, reco16[dist + var][proc].Clone()) for var in ['']+['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
      #   pdfdict16 = dict((var, reco16[dist + var][proc].Clone()) for var in ['']+['pdf_' + str(i) for i in range(0, 100)])
      #   q2dict17 =  dict((var, reco17[dist + var][proc].Clone()) for var in ['']+['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
      #   pdfdict17 = dict((var, reco17[dist + var][proc].Clone()) for var in ['']+['pdf_' + str(i) for i in range(0, 100)])
      #   q2dict18 =  dict((var, reco18[dist + var][proc].Clone()) for var in ['']+['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')])
      #   pdfdict18 = dict((var, reco18[dist + var][proc].Clone()) for var in ['']+['pdf_' + str(i) for i in range(0, 100)])

        
      #   plq2Up16, plq2Down16 =  getEnv(q2dict16)
      #   rmspdf16 = getRMS(pdfdict16)

      #   plq2Up17, plq2Down17 =  getEnv(q2dict17)
      #   rmspdf17 = getRMS(pdfdict17)

      #   plq2Up18, plq2Down18 =  getEnv(q2dict18)
      #   rmspdf18 = getRMS(pdfdict18)

      #   recoRunII[dist + 'fdpUp'][proc] = recoRunII[dist][proc].Clone()
      #   recoRunII[dist + 'fdpDown'][proc] = recoRunII[dist][proc].Clone()
      #   recoRunII[dist + '2qUp'][proc] = recoRunII[dist][proc].Clone()
      #   recoRunII[dist + '2qDown'][proc] = recoRunII[dist][proc].Clone()

      #   recoRunII[dist + '2qUp'][proc].Add(plq2Up16)
      #   recoRunII[dist + '2qDown'][proc].Add(plq2Down16)
      #   recoRunII[dist + 'fdpUp'][proc].Add(rmspdf16)
      #   recoRunII[dist + 'fdpDown'][proc].Add(rmspdf16, -1)

      #   recoRunII[dist + '2qUp'][proc].Add(plq2Up17)
      #   recoRunII[dist + '2qDown'][proc].Add(plq2Down17)
      #   recoRunII[dist + 'fdpUp'][proc].Add(rmspdf17)
      #   recoRunII[dist + 'fdpDown'][proc].Add(rmspdf17, -1)

      #   recoRunII[dist + '2qUp'][proc].Add(plq2Up18)
      #   recoRunII[dist + '2qDown'][proc].Add(plq2Down18)
      #   recoRunII[dist + 'fdpUp'][proc].Add(rmspdf18)
      #   recoRunII[dist + 'fdpDown'][proc].Add(rmspdf18, -1)
      
      # for var in ['q2_' + i for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]:
      #   del recoRunII[dist + var]
      # for var in ['pdf_' + str(i) for i in range(0, 100)]:
      #   del recoRunII[dist + var]

      # for fac, direc in [(-1., 'Down'), (1., 'Up')]:
      #   recoRunII[dist + 'lumi_1718'   + direc] = {}
      #   recoRunII[dist + 'lumi_2016'   + direc] = {}
      #   recoRunII[dist + 'lumi_2017'   + direc] = {}
      #   recoRunII[dist + 'lumi_2018'   + direc] = {}
      #   recoRunII[dist + 'lumi_3Ycorr' + direc] = {}

      #   for proc in recoRunII[dist].keys():
      #     if proc.count('data'): continue
      #     factor = fac
      #     if proc.count('nonprompt'): factor = 0.  #maybe change to "estimate", see if that checks out though

      #     for lumunc in ['lumi_1718' , 'lumi_2016' , 'lumi_2017' , 'lumi_2018' , 'lumi_3Ycorr']:
      #       l16 = reco16[dist][proc].Clone()
      #       l17 = reco17[dist][proc].Clone()
      #       l18 = reco18[dist][proc].Clone()

      #       l16.Scale(1. + factor * lumiUnc[lumunc]['16'])
      #       l17.Scale(1. + factor * lumiUnc[lumunc]['17'])
      #       l18.Scale(1. + factor * lumiUnc[lumunc]['18'])

      #       # l16.Scale( (1. + lumiUnc[lumunc]['16'])**factor )
      #       # l17.Scale( (1. + lumiUnc[lumunc]['17'])**factor )
      #       # l18.Scale( (1. + lumiUnc[lumunc]['18'])**factor )

      #       l16.Add(l17)
      #       l16.Add(l18)
      #       recoRunII[dist + lumunc + direc][proc] = l16.Clone()

      # data skippen
      # nonprompt niet scalen maar wel writen





  # lumi_1718               lnN                -         1.006      1.002   
  # lumi_2016               lnN                1.009     -          -       
  # lumi_2017               lnN                -         1.02       -       
  # lumi_2018               lnN                -         -          1.015   
  # lumi_3Ycorr             lnN                1.006     1.009      1.02    

      pickle.dump(recoRunII, file('/storage_mnt/storage/user/gmestdac/public_html/ttG/all/phoCBfull-compRewContribMCTTBAR-forNPclosure-exp-merged/' + channel + '/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/' + dist + '.pkl', 'w'))
    except Exception as e:
      log.info(e)
      log.info('failed for distribution '+ dist)