from ttg.tools.logger import getLogger
log = getLogger()

varWithJetVariations = ['njets', 'ndbjets', 'j1', 'j2', '_jetSmearedPt', 'dbj1', 'dbj2', 'phJetDeltaR', 'phBJetDeltaR']

#
# Defining shape systematics as "name : ([var, sysVar], [var2, sysVar2],...)"
# pylint: disable=W0621
#
systematics = {}
for i in ('Up', 'Down'):
  systematics['isr'+i]        = [('ISRWeight',    'ISRWeight'+i)]
  systematics['fsr'+i]        = [('FSRWeight',    'FSRWeight'+i)]
  # systematics['ue'+i]         = []
  systematics['ephScale'+i]     = []
  systematics['ephRes'+i]       = []
  systematics['pu'+i]         = [('puWeight',      'puWeight'+i)]
  systematics['pf'+i]         = [('_prefireWeight', '_prefireWeight'+i)]
  systematics['phSF'+i]       = [('phWeight',      'phWeight'+i)]
  systematics['pvSF'+i]       = [('PVWeight',      'PVWeight'+i)]
  systematics['lSFElSyst'+i]      = [('lWeight',       'lWeightElSyst'+i)]
  systematics['lSFMuSyst'+i]      = [('lWeight',       'lWeightMuSyst'+i)]
  systematics['lSFElStat'+i]      = [('lWeight',       'lWeightElStat'+i)]
  systematics['lSFMuStat'+i]      = [('lWeight',       'lWeightMuStat'+i)]

  # systematics['lSFMuPS'+i]      = [('lWeight',       'lWeightPSSys'+i)]
  
  systematics['lTracking'+i]      = [('lTrackWeight',  'lTrackWeight'+i)]

  systematics['trigStatEE'+i]    = [('triggerWeight', 'triggerWeightStatEE'+i)]
  systematics['trigStatEM'+i]    = [('triggerWeight', 'triggerWeightStatEM'+i)]
  systematics['trigStatMM'+i]    = [('triggerWeight', 'triggerWeightStatMM'+i)]
  systematics['trigSyst'+i]    = [('triggerWeight', 'triggerWeightSyst'+i)]

  systematics['bTagl'+i]      = [('bTagWeight',    'bTagWeightl'+i)]
  systematics['bTagbUC'+i]      = [('bTagWeight',    'bTagWeightbUC'+i)]
  systematics['bTagbCO'+i]      = [('bTagWeight',    'bTagWeightbCO'+i)]

  systematics['JER'+i]        = [(v, v+'_JER'+i) for v in varWithJetVariations]
  systematics['NPFlat'+i]         = []
  systematics['NPHigh'+i]         = []

  for jecSys in ['Absolute','BBEC1','EC2','FlavorQCD','HF','RelativeBal','HFUC','AbsoluteUC','BBEC1UC','EC2UC','RelativeSampleUC']:
    systematics[jecSys+i]        = [(v, v+'_' + jecSys +i) for v in varWithJetVariations]
# # UC ones are full oncorrelated, other ones 100% correlated


# not in here -> 100% correlation
correlations = {
              # 'lSFElSyst' : correlated I guess ,
              # 'lSFMuSyst' : correlated I guess ,
              'lSFElStat' : 0 ,
              'lSFMuStat' : 0 ,
              'pvSF' : 0. , 
              'bTagbUC' : 0 , 
              'trigStatEE' : 0. ,
              'trigStatEM' : 0. ,
              'trigStatMM' : 0. ,
              'trigSyst' : 0 ,
              'HFUC' : 0.,
              'AbsoluteUC' : 0.,
              'BBEC1UC' : 0.,
              'EC2UC' : 0.,
              'RelativeSampleUC' : 0.
              }

#
# Special case for q2 and PDF: multiple variations of which an envelope has to be taken
# TODO switch to taking the rms for pdf
#
for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd'):
  systematics['q2_' + i] = [('genWeight', 'weight_q2_'+i)]

for i in range(0, 100):
  systematics['pdf_' + str(i)] = [('genWeight', 'weight_pdf_'+str(i))]

for i in ('1', '2', '3'):
  systematics['colRec_' + i] = []


# Compile list to systematic to show
#
showSysList = list(set(s.split('Up')[0].split('Down')[0].split('_')[0] for s in systematics.keys()))


#
# Defining linear systematics as "name : (sampleList, %)"
#
linearSystematics = {}

linearSystematics['ZG_norm']        = ('ZG',        3 )  #we consider 70% of the Zg yield to be constrained by the correction
linearSystematics['singleTop_norm'] = ('singleTop', 10)
linearSystematics['VVTo2L2Nu_norm'] = ('VVTo2L2Nu', 30)   #multiboson
linearSystematics['other_norm']     = ('other',     30)
linearSystematics['UE']     =         ('TTGamma',   1)

# linearSystematics['lumi'] = (None, 2.5)

#
# Define linear systematics implemented as rate parameters
#
rateParameters = {}
# # rateParameters['TT_Dil']   = 5.5
# # rateParameters['ZG']       = 10
# rateParameters['ZG']       = 3   #we consider 70% of the Zg yield to be constrained by the correction
# # rateParameters['DY']       = 10
# rateParameters['singleTop'] = 10
# rateParameters['VVTo2L2Nu']    = 30   #multiboson
# rateParameters['other']    = 30


# Function to apply the systematic to the cutstring, tree branches, reduceType
# When ':' is used in the sysVar, the first part selects a specific sample on which the sysVar should be applied
#
def applySysToString(sample, sys, string):
  if sys:
    for var, sysVar in systematics[sys]:
      if sysVar.count(':'):
        s, sysVar = sysVar.split(':')
        if sample != s: return string
      string = string.replace(var, sysVar)
  return string

def applySysToTree(sample, sys, tree):
  for var, sysVar in systematics[sys]:
    if sysVar.count(':'):
      s, sysVar = sysVar.split(':')
      if sample != s: return
    try: setattr(tree, var, getattr(tree, sysVar))
    except: return

def applySysToReduceType(reduceType, sys):
  if sys:
    if sys.count('Scale') or sys.count('Res'): reduceType += '-' + sys
  return reduceType

def getSigmaSystFlat(sys):
  if sys: 
    if sys == 'NPFlatUp': return 1.
    elif sys == 'NPFlatDown': return -1.
  return 0.

def getSigmaSystHigh(sys):
  if sys: 
    if sys == 'NPHighUp': return 1.
    elif sys == 'NPHighDown': return -1.
  return 0.


# Special systematic samples for hdamp, ue, and erd
#
def getReplacementsForStack(sys, year):
  if sys:
    ttgsampsw = {'colRec_1':'CR1','colRec_2':'CR2','colRec_3':'erd', 'ueDown':'uedown', 'ueUp':'ueup'}
    if sys in ttgsampsw.keys():
      sw = ttgsampsw[sys]
      return {'TTGamma_DilPCUT' : 'TTGamma_Dil_' + sw, 'TTGamma_SemPCUT' : 'TTGamma_Sem_' + sw,  'TTGamma_HadPCUT' : 'TTGamma_Had',
              'TTGamma_DilA' : 'DROP',                 'TTGamma_SemA' : 'DROP',                  'TTGamma_HadA' : 'DROP',
              'TTGamma_DilB' : 'DROP',                 'TTGamma_SemB' : 'DROP',                  'TTGamma_HadB' : 'DROP'
              }
  else: return {}


#
# Function for the q2 envelope using input histogram
#
def q2Sys(variations):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  for i in range(0, variations[0].GetNbinsX()+2):
    upHist.SetBinContent(  i, max([var.GetBinContent(i) for var in variations]))
    downHist.SetBinContent(i, min([var.GetBinContent(i) for var in variations]))
  return upHist, downHist

def constructQ2Sys(allPlots, plotName, stack, force=False):
  if (plotName + 'q2Up') in allPlots and not force: return
  allPlots[plotName + 'q2Up'] = {}
  allPlots[plotName + 'q2Down'] = {}
  for histName in [s.name+s.texName for s in stack]:
    try:
      variations = [allPlots[plotName + 'q2_' + i][histName] for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd')]
    except:
      log.warning('Missing q2 variations for ' + plotName + ' ' + histName + '!')
      variations = [allPlots[plotName][histName]]
    allPlots[plotName + 'q2Up'][histName], allPlots[plotName + 'q2Down'][histName] = q2Sys(variations)

#
# Function for the pdf RMS envelope using input histogram
#
from math import sqrt
def pdfSys(variations, nominal):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  for i in range(0, variations[0].GetNbinsX()+2):
    pdfVarRms = sqrt(sum((nominal.GetBinContent(i) - var.GetBinContent(i))**2 for var in variations)/len(variations))
    upHist.SetBinContent(  i, nominal.GetBinContent(i) + pdfVarRms)
    downHist.SetBinContent(i, nominal.GetBinContent(i) - pdfVarRms)
  return upHist, downHist

def constructPdfSys(allPlots, plotName, stack, force=False):
  if (plotName + 'pdfUp') in allPlots and not force: return
  allPlots[plotName + 'pdfUp'] = {}
  allPlots[plotName + 'pdfDown'] = {}
  for histName in [s.name+s.texName for s in stack]:
    try:
      variations = [allPlots[plotName + 'pdf_' + str(i)][histName] for i in range(0, 100)]
    except:
      log.warning('Missing pdf variations for ' + plotName + ' ' + histName + '!')
      variations = [allPlots[plotName][histName]]
    allPlots[plotName + 'pdfUp'][histName], allPlots[plotName + 'pdfDown'][histName] = pdfSys(variations, allPlots[plotName][histName])


#
# Function for the color reconnection envelope using input histogram
# there is no up/down sample for these, take max deviation and us it to produce up/down variations
def CRSys(variations, nominal):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  for i in range(0, variations[0].GetNbinsX()+2):
    maxdev = max([abs(var.GetBinContent(i) - nominal.GetBinContent(i)) for var in variations])
    upHist.SetBinContent(  i, nominal.GetBinContent(i) + maxdev )
    downHist.SetBinContent(i, nominal.GetBinContent(i) - maxdev )
  return upHist, downHist

def constructCRSys(allPlots, plotName, stack, force=False):
  allPlots[plotName + 'colRecUp'] = {}
  allPlots[plotName + 'colRecDown'] = {}
  for histName in [s.name+s.texName for s in stack]:
    try:
      variations = [allPlots[plotName + 'colRec_' + i][histName] for i in ('1', '2', '3')]
    except:
      log.warning('Missing color reconnection variations for ' + plotName + ' ' + histName + '!')
      variations = [allPlots[plotName][histName]]
    allPlots[plotName + 'colRecUp'][histName], allPlots[plotName + 'colRecDown'][histName] = CRSys(variations, allPlots[plotName][histName])
