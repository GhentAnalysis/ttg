#! /usr/bin/env python
import pickle
from ttg.plots.systematics import showSysList
import pdb
rounding = 2

# def getYieldMC(hists):
#   sumVal = 0.
#   for name, hist in hists.iteritems():
#     if not 'data' in name: 
#       sumVal += hist.Integral()
#   return sumVal


# def getYieldBKG(hists):
#   sumVal = 0.
#   for name, hist in hists.iteritems():
#     if not 'data' in name and not 'TTG' in name: 
#       sumVal += hist.Integral()
#   return sumVal

# def getYieldData(hists):
#   sumVal = 0.
#   sumSamples = []
#   for name, hist in hists.iteritems():
#     if 'data' in name: 
#       sumVal += hist.Integral()
#       sumSamples.append(name)
#       # print name
#   return sumVal

def sumHists(dict, sumkeys, antiSumKeys, scaleBkg=None):
  sumHist = None
  for name, hist in dict.iteritems():
    if (any((name.count(key) for key in sumkeys)) or not sumkeys) and (not any((name.count(key) for key in antiSumKeys)) or not antiSumKeys):
      if scaleBkg:
        if name.count(scaleBkg[0]) and not name.count('estimate'):
        # if name.count(scaleBkg[0]):
          hist = hist.Clone()
          hist.Scale(scaleBkg[1])
      if not sumHist: sumHist = hist.Clone()
      else: sumHist.Add(hist)
  return sumHist

# def sumHistsStatvar(dict, sumkeys, antiSumKeys, varBkg):
#   sumHistU = None
#   sumHistD = None
#   # sumHistOthers
#   for name, hist in dict.iteritems():
#     if (any((name.count(key) for key in sumkeys)) or not sumkeys) and (not any((name.count(key) for key in antiSumKeys)) or not antiSumKeys):
#       histu = hist.Clone()
#       histd = hist.Clone()
#       if name.count(varBkg):
#         for i in range(1, histu.GetXaxis().GetNbins()+1):
#           histu.SetBinContent(i, histu.GetBinContent(i) + histu.GetBinError(i))
#           histd.SetBinContent(i, histd.GetBinContent(i) - histd.GetBinError(i))
#       if not sumHistU: 
#         sumHistU = histu.Clone()
#         sumHistD = histd.Clone()
#       else: 
#         sumHistU.Add(histu)
#         sumHistD.Add(histd)
#   return sumHistU, sumHistD


def sumHistsStatvar(dict, sumkeys, antiSumKeys, varBkg):
  # least elegant code ever I know, leave me alone
  sumHistVar = None
  sumHistOthers = None
  for name, hist in dict.iteritems():
    if (any((name.count(key) for key in sumkeys)) or not sumkeys) and (not any((name.count(key) for key in antiSumKeys)) or not antiSumKeys):
      if name.count(varBkg):
        if not sumHistVar: 
          sumHistVar = hist.Clone()
        else:
          sumHistVar.Add(hist)
      else: 
        if not sumHistOthers: 
          sumHistOthers = hist.Clone()
        else:
          sumHistOthers.Add(hist)
  if sumHistVar and sumHistOthers:
    sumHistVarD = sumHistVar.Clone()
    for i in range(1, sumHistVar.GetXaxis().GetNbins()+1):
      sumHistVar.SetBinContent(i, sumHistVar.GetBinContent(i) + sumHistVar.GetBinError(i))
      sumHistVarD.SetBinContent(i, sumHistVarD.GetBinContent(i) - sumHistVar.GetBinError(i))
    sumHistVar.Add(sumHistOthers)
    sumHistVarD.Add(sumHistOthers)
    return sumHistVar, sumHistVarD
  elif sumHistVar:
    sumHistVarD = sumHistVar.Clone()
    for i in range(1, sumHistVar.GetXaxis().GetNbins()+1):
      sumHistVar.SetBinContent(i, sumHistVar.GetBinContent(i) + sumHistVar.GetBinError(i))
      sumHistVarD.SetBinContent(i, sumHistVarD.GetBinContent(i) - sumHistVar.GetBinError(i))
    return sumHistVar, sumHistVarD
  else:
    return sumHistOthers, sumHistOthers

def getStatErr(hists, MC):
  sumVal = 0.
  for name, hist in hists.iteritems():
    if MC ^ ('data' in name): 
      for i in range(1, hist.GetNbinsX()+1):
        sumVal += hist.GetBinError(i)**2.
  sumVal = sumVal**0.5
  return sumVal

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


def sumQuad(hists):
  summed = hists[0].Clone()
  summed.Reset('ICES')
  for hist in hists:
    hq = hist.Clone()
    hq.Multiply(hq)
    summed.Add(hq)
  for i in range(1, summed.GetXaxis().GetNbins()+1):
    summed.SetBinContent(i, summed.GetBinContent(i)**0.5)
  return summed

variations = showSysList
variations.remove('q2')
variations.remove('pdf')
# variations.remove('colRec')
# variations = ['NP']

totalDict = {'2016':{},'2017':{},'2018':{}}

def getEffect(year):

  picklePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/' + year + '/phoCBfull-niceEstimDD/all/llg-mll20-deepbtag1p-offZ-llgNoZ-photonPt20/unfReco_phPt.pkl'
  print picklePath.replace('/storage_mnt/storage/user/gmestdac/public_html/ttG/','')
  varHists = pickle.load(open(picklePath))

  # pdb.set_trace()
  nbins = varHists.values()[0].values()[0].GetXaxis().GetNbins()
  for varkey in varHists:
    for histkey in varHists[varkey]:
      varHists[varkey][histkey].SetBinContent(nbins, varHists[varkey][histkey].GetBinContent(nbins)+varHists[varkey][histkey].GetBinContent(nbins+1))
      varHists[varkey][histkey].SetBinError(nbins, (varHists[varkey][histkey].GetBinError(nbins)**2.+varHists[varkey][histkey].GetBinError(nbins+1)**2.)**0.5)
      varHists[varkey][histkey].SetBinContent(nbins+1, 0)
      varHists[varkey][histkey].SetBinError(nbins+1, 0)

  data = sumHists(varHists['unfReco_phPt'], ['data'], [])
  bkgNom = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'])
  subNom = data.Clone()
  subNom.Add(bkgNom, -1)
  signalNom = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)']
  subNom.Divide(signalNom)
  rels ={}
  for var in variations:
    try:
      bkgUp = sumHists(varHists['unfReco_phPt' + var + 'Up'], [], ['data', 'TTGamma'])
      bkgDown = sumHists(varHists['unfReco_phPt' + var + 'Down'], [], ['data', 'TTGamma'])
      subUp = data.Clone()
      subDown = data.Clone()
      # pdb.set_trace()
      subUp.Add(bkgUp, -1)
      subDown.Add(bkgDown, -1)
      signalUp = varHists['unfReco_phPt'+ var + 'Up']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      signalDown = varHists['unfReco_phPt'+ var + 'Down']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      subUp.Divide(signalUp)
      subDown.Divide(signalDown)
      subUp.Add(subNom, -1)
      subDown.Add(subNom, -1)
      subUp.Divide(subNom)
      subDown.Divide(subNom)
      ul, uh, dl, dh = 1., -1., -1., 1.
      for i in range(subNom.GetXaxis().GetNbins()+1):
        uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
        dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
        ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
        dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
      
      ul = round(100.*ul, rounding)
      uh = round(100.*uh, rounding)
      dl = round(100.*dl, rounding)
      dh = round(100.*dh, rounding)
      rels[var] = (dh, dl, ul, uh)
    except:
      rels[var] = ('nan', 'nan', 'nan', 'nan')
    totalDict[year][var] = (subUp.Clone('effectUp'), subDown.Clone('effectDown'))

  # COLOR RECONNECTION, pdf, and q2
  for var in ['colRec_1', 'colRec_2', 'colRec_3']:
    try:
      bkgUp = sumHists(varHists['unfReco_phPt' + var], [], ['data', 'TTGamma'])
      subUp = data.Clone()
      subUp.Add(bkgUp, -1)
      signalUp = varHists['unfReco_phPt'+ var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
      subUp.Divide(signalUp)
      subUp.Add(subNom, -1)
      ul, uh = 1., -1.
      for i in range(subNom.GetXaxis().GetNbins()+1):
        uh = max(uh, abs(subUp.GetBinContent(i)))
        ul = min(ul, abs(subUp.GetBinContent(i)) )
      ul = round(100.*ul, rounding)
      uh = round(100.*uh, rounding)
      rels[var] = (-uh, -ul, ul, uh)
    except:
      rels[var] = ('nan', 'nan', 'nan', 'nan')
    totalDict[year][var] = (subUp.Clone('effect'), subUp.Clone('effect'))

  sigpdfdict = {key.split('unfReco_phPt')[1] : val['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone() for key,val in varHists.iteritems() if key.count('pdf') or key == 'unfReco_phPt'}
  sigq2dict = {key.split('unfReco_phPt')[1] : val['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone() for key,val in varHists.iteritems() if key.count('q2') or key == 'unfReco_phPt'}
  sigmaxUp, sigmaxDown = getEnv(sigq2dict)
  sigrms = getRMS(sigpdfdict)

  bkgpdfdict = {key.split('unfReco_phPt')[1] :  sumHists(val, [], ['data', 'TTGamma']) for key,val in varHists.iteritems() if key.count('pdf') or key == 'unfReco_phPt'}
  bkgq2dict = {key.split('unfReco_phPt')[1] :  sumHists(val, [], ['data', 'TTGamma']) for key,val in varHists.iteritems() if key.count('q2') or key == 'unfReco_phPt'}
  bkgmaxUp, bkgmaxDown = getEnv(bkgq2dict)
  bkgrms = getRMS(bkgpdfdict)
  

  q2bkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'])
  q2bkgDown = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'])
  q2bkgUp.Add(bkgmaxUp)
  q2bkgDown.Add(bkgmaxDown)
  q2subUp = data.Clone()
  q2subDown = data.Clone()
  q2subUp.Add(q2bkgUp, -1)
  q2subDown.Add(q2bkgDown, -1)

  q2signalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  q2signalDown = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  q2signalUp.Add(sigmaxUp, -1)
  q2signalDown.Add(sigmaxDown, -1)

  q2subUp.Divide(signalUp)
  q2subDown.Divide(signalDown)
  q2subUp.Add(subNom, -1)
  q2subDown.Add(subNom, -1)
  q2subUp.Divide(subNom)
  q2subDown.Divide(subNom)
  ul, uh, dl, dh = 1., -1., -1., 1.
  for i in range(subNom.GetXaxis().GetNbins()+1):
    uh = max(uh, q2subUp.GetBinContent(i), q2subDown.GetBinContent(i))
    dh = min(dh, q2subUp.GetBinContent(i), q2subDown.GetBinContent(i))
    ul = min(ul, (q2subUp.GetBinContent(i) if q2subUp.GetBinContent(i) > 0. else 100.), (q2subDown.GetBinContent(i) if q2subDown.GetBinContent(i) > 0. else 100.))
    dl = max(dl, (q2subUp.GetBinContent(i) if q2subUp.GetBinContent(i) < 0. else -100.), (q2subDown.GetBinContent(i) if q2subDown.GetBinContent(i) < 0. else -100.))
  
  ul = round(100.*ul, rounding)
  uh = round(100.*uh, rounding)
  dl = round(100.*dl, rounding)
  dh = round(100.*dh, rounding)
  rels['q2'] = (dh, dl, ul, uh)
  totalDict[year]['q2'] = (q2subUp.Clone('effectUp'), q2subDown.Clone('effectDown'))

  pdfbkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'])
  pdfbkgUp.Add(bkgrms)
  pdfsubUp = data.Clone()
  pdfsubUp.Add(pdfbkgUp, -1)
  pdfsignalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
  pdfsignalUp.Add(sigrms)
  pdfsubUp.Divide(signalUp)
  pdfsubUp.Add(subNom, -1)
  pdfsubUp.Divide(subNom)
  ul, uh = 1., -1.
  for i in range(subNom.GetXaxis().GetNbins()+1):
    uh = max(uh, abs(pdfsubUp.GetBinContent(i)))
    ul = min(ul, abs(pdfsubUp.GetBinContent(i)) )
  ul = round(100.*ul, rounding)
  uh = round(100.*uh, rounding)
  rels['pdf'] = (-uh, -ul, ul, uh)
  totalDict[year]['pdf'] = (pdfsubUp.Clone('effect'), pdfsubUp.Clone('effect'))


  # pdb.set_trace()

# sumHists(varHists['unfReco_phPt' + var + 'Up'], [], ['data', 'TTGamma'])
# varHists['unfReco_phPt'+ var]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()

  # TODO 
  # rels['statMC'] = (mcstat, mcstat )
  # rels['statDA'] = (dastat, dastat )
  for bkg in [('ZG', 0.015), ('other', 0.3), ('singleTop', 0.1)]:
    bkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], (bkg[0], 1. + bkg[1]))
    bkgDown = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], (bkg[0], 1. - bkg[1]))
    subUp = data.Clone()
    subDown = data.Clone()
    subUp.Add(bkgUp, -1)
    subDown.Add(bkgDown, -1)
    signalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalDown = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    subUp.Divide(signalUp)
    subDown.Divide(signalDown)
    subUp.Add(subNom, -1)
    subDown.Add(subNom, -1)
    subUp.Divide(subNom)
    subDown.Divide(subNom)
    ul, uh, dl, dh = 1., -1., -1., 1.
    for i in range(subNom.GetXaxis().GetNbins()+1):
      uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
      dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
    
    ul = round(100.*ul, rounding)
    uh = round(100.*uh, rounding)
    dl = round(100.*dl, rounding)
    dh = round(100.*dh, rounding)
    rels[bkg[0] + 'Norm'] = (dh, dl, ul, uh)
    totalDict[year][bkg[0] + 'Norm'] = (subUp.Clone('effectUp'), subDown.Clone('effectDown'))


  for lumi in [('lumi_2016', 0.009), ('lumi_2017', 0.02), ('lumi_2018', 0.015)]:
    bkgUp = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], ('', 1. + lumi[1]))
    bkgDown = sumHists(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], ('', 1. - lumi[1]))
    subUp = data.Clone()
    subDown = data.Clone()
    subUp.Add(bkgUp, -1)
    subDown.Add(bkgDown, -1)
    signalUp = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalDown = varHists['unfReco_phPt']['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'].Clone()
    signalUp.Scale(1. + lumi[1])
    signalDown.Scale(1. - lumi[1])
    subUp.Divide(signalUp)
    subDown.Divide(signalDown)
    subUp.Add(subNom, -1)
    subDown.Add(subNom, -1)
    subUp.Divide(subNom)
    subDown.Divide(subNom)
    ul, uh, dl, dh = 1., -1., -1., 1.
    for i in range(subNom.GetXaxis().GetNbins()+1):
      uh = max(uh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      dh = min(dh, subUp.GetBinContent(i), subDown.GetBinContent(i))
      ul = min(ul, (subUp.GetBinContent(i) if subUp.GetBinContent(i) > 0. else 100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) > 0. else 100.))
      dl = max(dl, (subUp.GetBinContent(i) if subUp.GetBinContent(i) < 0. else -100.), (subDown.GetBinContent(i) if subDown.GetBinContent(i) < 0. else -100.))
    
    ul = round(100.*ul, rounding)
    uh = round(100.*uh, rounding)
    dl = round(100.*dl, rounding)
    dh = round(100.*dh, rounding)
    if not lumi[0].count(year):
      rels[lumi[0]] = (0., 0., 0., 0.)
    else:
      rels[lumi[0]] = (dh, dl, ul, uh)
    totalDict[year][lumi[0]] = (subUp.Clone('effectUp'), subDown.Clone('effectDown'))
    if not lumi[0].count(year):
      totalDict[year][lumi[0]][0].Reset('ICES')
      totalDict[year][lumi[0]][1].Reset('ICES')


  # data, MC, and NP est statistics
  # not putting this in rels
  # NOTE vary every background separately, then sum effects in quadrature right?
  statDict = {'2016':{},'2017':{},'2018':{}}

  # for key in varHists['unfReco_phPt'].keys():
  for key in ['data','estimate','(genuine)']:
    dataUp, dataDown = sumHistsStatvar(varHists['unfReco_phPt'], ['data'], [], key)
    bkgStatUp, bkgStatDown = sumHistsStatvar(varHists['unfReco_phPt'], [], ['data', 'TTGamma'], key)
    subUp = dataUp.Clone()
    subDown = dataDown.Clone()
    subUp.Add(bkgStatUp, -1)
    subDown.Add(bkgStatDown, -1)
    signalUp, signalDown = sumHistsStatvar(varHists['unfReco_phPt'], ['TTGamma'], [], key)
    subUp.Divide(signalUp)
    subDown.Divide(signalDown)
    subUp.Add(subNom, -1)
    subDown.Add(subNom, -1)
    subUp.Divide(subNom)
    subDown.Divide(subNom)
    # pdb.set_trace()
    statDict[year][key + 'stat'] = (subUp.Clone('effectUp'), subDown.Clone('effectDown'))
    # pdb.set_trace()

  totalDict[year]['nonpromptstat'] = statDict[year]['estimatestat']
  totalDict[year]['datastat'] = statDict[year]['datastat']
  totalDict[year]['allMCstat'] = statDict[year]['(genuine)stat']

  # totalDict[year]['otherMCstat'] = statDict[year]['other_Other+#gamma (genuine)Other+#gamma (genuine)stat']
  # totalDict[year]['TTGammaMCstat'] = statDict[year]['TTGamma_DilPCUTt#bar{t}#gamma (genuine)stat']
  # totalDict[year]['ZGMCstat'] = statDict[year]['ZG_Z#gamma (genuine)Z#gamma (genuine)stat']
  # totalDict[year]['singleTopMCstat'] = statDict[year]['singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)stat']

  # # pdb.set_trace()
  # npstatUp = sumQuad([statDict[year]['NPME_nonprompt-estimatenonprompt-estimatestat'][0], statDict[year]['NPEl_nonprompt-estimatenonprompt-estimatestat'][0], statDict[year]['NPMu_nonprompt-estimatenonprompt-estimatestat'][0] ])
  # datstatUp = sumQuad([statDict[year]['DoubleMuondatastat'][0], statDict[year]['MuonEGdatastat'][0], statDict[year]['DoubleEG_datadatastat'][0] ])
  # MCstatUp = sumQuad([totalDict[year]['otherMCstat'][0], totalDict[year]['singleTopMCstat'][0], totalDict[year]['ZGMCstat'][0], totalDict[year]['TTGammaMCstat'][0] ])

  # npstatDown = sumQuad([statDict[year]['NPME_nonprompt-estimatenonprompt-estimatestat'][1], statDict[year]['NPEl_nonprompt-estimatenonprompt-estimatestat'][1], statDict[year]['NPMu_nonprompt-estimatenonprompt-estimatestat'][1] ])
  # datstatDown = sumQuad([statDict[year]['DoubleMuondatastat'][1], statDict[year]['MuonEGdatastat'][1], statDict[year]['DoubleEG_datadatastat'][1] ])
  # MCstatDown = sumQuad([totalDict[year]['otherMCstat'][1], totalDict[year]['singleTopMCstat'][1], totalDict[year]['ZGMCstat'][1], totalDict[year]['TTGammaMCstat'][1] ])

  # MCstat
  

  # totalDict[year]['nonpromptstat'] = (npstatUp, npstatDown)
  # totalDict[year]['datastat'] = (datstatUp, datstatDown)
  # totalDict[year]['allMCstat'] = (MCstatUp, MCstatDown)



    # TODO add to dictionary
    # totalDict[year][bkg[0] + 'Norm'] = (subUp.Clone('effectUp'), subDown.Clone('effectDown'))





  return rels



varYears = {}
for year in ['2016', '2017', '2018']:
  varYears[year] = getEffect(year)
print (20*' ') + '2016' + (26*' ') + '2017' +  (26*' ') + '2018'+  (26*' ') + 'overall'
for sys in varYears['2016'].keys():
  # if not sys.count('lumi'): continue
  odh = min(varYears[y][sys][0] for y in ['2016', '2017', '2018'])
  odl = max(varYears[y][sys][1] for y in ['2016', '2017', '2018'])
  oul = min(varYears[y][sys][2] for y in ['2016', '2017', '2018'])
  ouh = max(varYears[y][sys][3] for y in ['2016', '2017', '2018'])
  print (sys+'                   ')[:20] + (str(varYears['2016'][sys])+'                   ')[:30] + (str(varYears['2017'][sys])+'                   ')[:30] + (str(varYears['2018'][sys])+'                   ')[:30]+ str((odh, odl, oul, ouh))


# get bincontents from totaldict
totalerrs = {'2016':{},'2017':{},'2018':{}}
for year in ['2016', '2017', '2018']:
  for key in totalDict[year].keys():
    totalerrs[year][key] = ([],[])
    for i in range(1, totalDict[year][key][0].GetNbinsX()+1):
      totalerrs[year][key][0].append(round(100.*totalDict[year][key][0].GetBinContent(i), 3))
      totalerrs[year][key][1].append(round(100.*totalDict[year][key][1].GetBinContent(i), 3))

pickle.dump(totalDict , file('effectsHist.pkl' ,'w'))
pickle.dump(totalerrs , file('effectsList.pkl' ,'w'))
print 'datastat   ' + str(totalerrs['2016']['datastat'])
print 'nonpromptstat   ' + str(totalerrs['2016']['nonpromptstat'])
print 'allMCstat   ' + str(totalerrs['2016']['allMCstat'])
print 'datastat   ' + str(totalerrs['2017']['datastat'])
print 'nonpromptstat   ' + str(totalerrs['2017']['nonpromptstat'])
print 'allMCstat   ' + str(totalerrs['2017']['allMCstat'])
print 'datastat   ' + str(totalerrs['2018']['datastat'])
print 'nonpromptstat   ' + str(totalerrs['2018']['nonpromptstat'])
print 'allMCstat   ' + str(totalerrs['2018']['allMCstat'])


