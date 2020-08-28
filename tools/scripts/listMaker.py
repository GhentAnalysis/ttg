import argparse, subprocess
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--year',           action='store',      default=None, choices=['2016','2017','2018'])
argParser.add_argument('--input',           action='store',      default=None)
args = argParser.parse_args()

pnfsPath = '/pnfs/iihe/cms/store/user/@USER@/heavyNeutrino/'

yearMap =  {'2016': 'RunIISummer16MiniAODv3',
            '2017': 'RunIIFall17MiniAODv2',
            '2018': 'RunIIAutumn18MiniAOD'}

xList = open(args.year + 'xList' + args.input, 'w')
hnList = open(args.year + 'hnList' + args.input, 'w')
nameMapping = {'ZZTo2L2Q': ('ZZTo2L2Q', 5),
                'THW_Hincl': ('tHW', 1),
                'ST_t-channel_antitop_4f_InclusiveDecays': ('singleTop_t_tbar_inc', 5),
                'WGToLNuG_01J_5f': ('WG', 3),
                'ZGToLLG_01J_5f_lowMLL': ('ZG_lowMLL', 15),
                'VVTo2L2Nu': ('VVTo2L2Nu', 5),
                'WZTo1L3Nu': ('WZTo1L3Nu', 1),
                'tZq_ll_4f': ('tZq',  10),
                'ZZTo4L': ('ZZTo4L', 3),
                'TTWW': ('TTWW', 1),
                'ttHToNonbb_M125': ('TTH', 1),
                'WWTo1L1Nu2Q': ('WWTo1L1Nu2Q', 1),
                'ZZZ': ('ZZZ', 1),
                'DYJetsToLL_M-50': ('DY_M50_LO', 150),
                'TGJets_lepton': ('tgjets_lep', 1),
                'TGJets_Tune': ('tgjets_inc', 1),
                'DYJetsToLL_M-10to50': ('DY_M10to50_LO', 3),
                'ZZTo2Q2Nu': ('ZZTo2Q2Nu', 3),
                'ST_tWll_5f_LO': ('tWll', 1),
                'GluGluToContinToZZTo4mu': ('GluGluToZZ_4mu', 1),
                'WZTo1L1Nu2Q': ('WZTo1L1Nu2Q', 3),
                'GluGluHToZZTo4L_M125': ('GluGluToH_ZZ', 1),
                'TTZZ': ('TTZZ', 1),
                'WZTo2L2Q': ('WZTo2L2Q', 10),
                'GluGluToContinToZZTo2e2mu': ('GluGluToZZ_2e2m', 3),
                'WWW_4F': ('WWW', 1),
                'TTWJetsToLNu': ('TTWToLNu', 1),
                'WZZ': ('WZZ', 1),
                'GluGluToContinToZZTo4e': ('GluGluToZZ_4e', 1),
                'ST_t-channel_top_4f_InclusiveDecays': ('singleTop_t_t_inc', 5),
                'THQ_Hincl': ('tHq', 1),
                'ST_tW_antitop_5f_NoFullyHadronic': ('singleTop_tW_tbar_noFuHa', 1),
                'ST_tW_top_5f_NoFullyHadronic': ('singleTop_tW_t_noFuHa', 1),
                'ST_tW_antitop_5f_inclusiveDecays': ('singleTop_tW_tbar_incl', 1),
                'ST_tW_top_5f_inclusiveDecays': ('singleTop_tW_t_incl', 1),
                'TTTT': ('TTTT', 1),
                'ST_s-channel_4f_leptonDecays': ('singleTop_s_lep', 1),
                'GluGluToContinToZZTo4tau': ('GluGluToZZ_4tau', 1),
                'WZTo3LNu': ('WZTo3LNu', 1),
                'GluGluToContinToZZTo2e2tau': ('GluGluToZZ_2e2tau', 1),
                'TTZToLL_M-1to10': ('TTZ_M1to10', 1),
                'WWToLNuQQ': ('WWToLNuQQ', 1),
                'TTZToLLNuNu_M-10': ('TTZ', 10),
                'WWZ': ('WWZ', 1),
                'TTWZ': ('TTWZ', 1),
                'GluGluToContinToZZTo2mu2tau': ('GluGluToZZ_2mu2tau', 1),
                'TTWJetsToQQ': ('TTWToQQ', 1),
                'ST_tWnunu_5f_LO': ('tWnunu', 1),
                'W1JetsToLNu': ('W1JetsToLNu', 1),
                'W2JetsToLNu': ('W2JetsToLNu', 1),
                'W3JetsToLNu': ('W3JetsToLNu', 1),
                'W4JetsToLNu': ('W4JetsToLNu', 1),
                'ttHTobb': ('ttHTobb', 1),
                'WGToLNuG': ('WGToLNuG', 3),
                'WWTo4Q': ('WWTo4Q', 3),
                'WJetsToQQ': ('WJetsToQQ', 1),
                'ST_s-channel_4f_hadronicDecays': ('singleTop_s_had', 1),
                'TTZToQQ': ('TTZToQQ', 3)
                }

print("WARNING:")
print("- add data samples yourself")
print("- add tags for storing particle level etc where needed")
print("- check for missing samples, samples with multiple versions")
print("- check if status * samples are available for those listed as missing")
print("- !give the heavyneutrino lists a name containing the year, this is necessary")


# TTGamma samples
samps = {'Dilept': ('_Dil', '1.496', '1.616'), 'SingleLept': ('_Sem', '5.076', '1.994'), 'Hadronic': ('_Had', '4.164', '2.565')}
varis = {'_TuneCP5_PSweights': '', 
              '_TuneCP5Down': '_ueDown',
              '_TuneCP5Up': '_ueUp',
              '_TuneCP5_erdON': '_erd',
              '_TuneEE5C': '_EE5C',
              '_ptGamma100-200': '_pt100_200',
              '_ptGamma200inf': '_pt100_inf'}
otherxsec = {
'Dilept_ptGamma100-200': '0.03469',
'Dilept_ptGamma200inf': '0.006874',
'SingleLept_ptGamma100-200': '0.1334',
'SingleLept_ptGamma200inf': '0.0273',
'Hadronic_ptGamma100-200': '0.1273',
'Hadronic_ptGamma200inf': '0.02727'
}
# for samp in samps.keys():
#   for var in varis.keys():
#     dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/TTGamma_"+ samp + var + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
#     if dasResult:
#       hnList.write(dasResult)
#       try: xsec = otherxsec[samp + var] + '*' + samps[samp][2]
#       except: xsec =  samps[samp][1] + '*' + samps[samp][2]
#       xList.write(('TTGamma' + samps[samp][0] + varis[var]).ljust(30) + (pnfsPath + dasResult.split('/')[1]).ljust(150) + '@LABEL@    5      ' + xsec + '\n')
#     else:
#       xList.write('% TTGamma sample ' + samp + var + ' missing\n')
#       print 'TTGamma sample ' + samp + var + ' missing'

# xList.write('\n\n\n')
# hnList.write('\n\n\n')


# # TTBar samples
# samps = {'TTTo2L2Nu': ('TT_Dil', '87.315'), 'TTToSemiLeptonic': ('TT_Sem', '364.352'), 'TTToHadronic': ('TT_Had', '380.095')}
# varis = {'_TuneCP5_PSweights_13TeV': '', 
#               '_TuneCP5down': '_ueDown',
#               '_TuneCP5up': '_ueUp',
#               '_TuneCP5_PSweights_erdON': '_erd',
#               '_hdampDOWN_TuneCP5': '_hdampdown',
#               '_hdampUP_TuneCP5': '_hdampup',
#               # NOTE backup samples, needed?
#               # /TTTo2L2Nu_TuneCP5_PSweights_mtop1695
#               # /TTTo2L2Nu_TuneCP5_PSweights_mtop1755
#               '_TuneCP5CR1_QCDbased': '_QCDbased',
#               '_TuneCP5CR2_GluonMove': '_GluonMove'
# }
# for samp in samps.keys():
#   for var in varis.keys():
#     dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/"+ samp + var + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
#     if dasResult:
#       hnList.write(dasResult)
#       xList.write((samps[samp][0] + varis[var]).ljust(30) + (pnfsPath +dasResult.split('/')[1]).ljust(150) + '@LABEL@    10     ' + samps[samp][1] + '\n')
#     else:
#       xList.write(('%' + samps[samp][0] + varis[var]).ljust(30) + '        missing or status not VALID        @LABEL@    10     ' + samps[samp][1] + '\n')
#       print samp + var + ' missing'

# xList.write('\n\n\n')
# hnList.write('\n\n\n')



with open(args.input, 'r') as f:
  lines = [line.rstrip() for line in f]
  for line in lines:
    try:
      name, xsec = line.split()
    except:
      name = line
      xsec = 'xsec missing'
    origName = name
    # samples for which we need syst variations or so, done separately
    specialSamples = ['TTGamma', 'TTTo2L2Nu', 'TTToHadronic', 'TTToSemiLeptonic']
    # samples we shouldn't use anymore, don't let them sneak back in
    # 'WWTo2L2Nu_13TeV-powheg' and 'ZZTo2L2Nu_13TeV_powheg_pythia8_ext1' are a subset of VVTo2L
    wrongSamples = ['WW_TuneCUETP8M1_13TeV-pythia8','WZ_TuneCUETP8M1_13TeV-pythia8','ZZ_TuneCUETP8M1_13TeV-pythia8','WGToLNuG_01J_5f_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8','ZGToLLG_01J_5f_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8','ZGToLLG_01J_LoosePtlPtg','WWTo2L2Nu_13TeV-powheg', 'ZZTo2L2Nu_13TeV_powheg_pythia8_ext1']
    if any((name.startswith(i) for i in specialSamples+wrongSamples)): continue
    dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/" + name + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
    certLevel = 'A'
    if not dasResult:
      certLevel = 'B'
      parts = name.replace('-','_').split('_')
      parts = [i for i in parts if not i in ['TuneCUETP8M2T4','TuneCUETP8M1', 'pythia8', '13TeV' , 'TuneCP5', 'PSweights', 'powheg', 'amcatnlo', 'amcatnloFXFX', 'ttHtranche3']]
      nameA = '*'.join(parts)
      dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/" + nameA + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
    #   # automatically check if it's just a tune difference
    #   name = name.replace('_13TeV-powheg_TuneCP5', '_TuneCP5_PSweights_13TeV-powheg-pythia8')
    #   name = name.replace('_TuneCP5_PSweights_13TeV-amcatnlo-pythia8', '_TuneCP5_13TeV-amcatnlo-pythia8')
    #   name = name.replace('TuneCUETP8M2T4', 'TuneCP5')
    #   name = name.replace('TuneCUETP8M1', 'TuneCP5')
    #   dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/" + name + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
    # if not dasResult:
    #   # automatically check if a close replacement exist
    #   for l in range(5, 2, -1):
    #     certLevel = 'C' + str(l)
    #     nameA = '_'.join(name.split('_')[0:l])
    #     dasResult = subprocess.check_output(["dasgoclient -query=\'dataset dataset=/" + nameA + "*/" + yearMap[args.year] +"*/MINIAODSIM\'"], shell=True)
    #     if dasResult:
    #       break
    
    if dasResult:
      # if certLevel != 'A':
        # print 'imperfect match, certainty level ' + certLevel
      # get matching samples (sample and extension counted as same), sorted by length, shortest one is usually noninal one
      sampMatch = sorted(list({i.split('/')[1] for i in dasResult.split()}), key=len)
      unsure = False
      if len(sampMatch) > 1:
        print 'WARNING: At attempt level ' + certLevel + ' more than one match for ' + name + ':'
        for i in sampMatch:
          print i
        hnList.write('\n #CHECK BLOCK BELOW, trying to replace sample ' + origName + '\n')
        unsure = True
      hnList.write(dasResult)
      if unsure:
        xList.write('\n%choice to be made in hn list and here, trying to replace sample ' + origName + '\n')
        for i in sampMatch:
          xList.write('%' + i + '\n')
        xList.write('\n')
        hnList.write('\n')
        continue

      matches = []
      for key in nameMapping.keys():
        if name.startswith(key):
          matches.append(key)
      if len(matches) ==1:
        xList.write(nameMapping[matches[0]][0].ljust(30) + (pnfsPath + list(sampMatch)[0]).ljust(150) + '@LABEL@    ' + str(nameMapping[matches[0]][1]).ljust(3) + '    ' + xsec + '\n')
      else:
        xList.write('@name me@'.ljust(30) + (pnfsPath + list(sampMatch)[0]).ljust(150) + '@LABEL@    ' + xsec + '\n')
        xList.write(str(matches))
    else:
      hnList.write('# nothing found for ' + name + '\n')
      xList.write('% missing or status not VALID  ' + name + '        @LABEL@    ' + xsec + '\n')
      print 'missing or status not VALID  ' + name 

