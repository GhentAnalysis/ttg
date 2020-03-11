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
  systematics['hdamp'+i]      = []
  systematics['ue'+i]         = []
  systematics['erd'+i]        = []
  systematics['ephScale'+i]     = []
  systematics['ephRes'+i]       = []
  systematics['pu'+i]         = [('puWeight',      'puWeight'+i)]
  systematics['pf'+i]         = [('_prefireWeight', '_prefireWeight'+i)]
  systematics['phSF'+i]       = [('phWeight',      'phWeight'+i)]
  systematics['pvSF'+i]       = [('PVWeight',      'PVWeight'+i)]
  systematics['lSF'+i]        = [('lWeight',       'lWeight'+i)]
  systematics['trigger'+i]    = [('triggerWeight', 'triggerWeight'+i)]
  systematics['bTagl'+i]      = [('bTagWeight',    'bTagWeightl'+i)]
  systematics['bTagb'+i]      = [('bTagWeight',    'bTagWeightb'+i)]
  systematics['JEC'+i]        = [(v, v+'_JEC'+i) for v in varWithJetVariations]
  systematics['JER'+i]        = [(v, v+'_JER'+i) for v in varWithJetVariations]
  systematics['NP'+i]         = []

#
# Special case for q2 and PDF: multiple variations of which an envelope has to be taken
#
for i in ('Ru', 'Fu', 'RFu', 'Rd', 'Fd', 'RFd'):
  systematics['q2_' + i] = [('genWeight', 'weight_q2_'+i)]
# NOTE pdf temporarily off
# for i in range(0, 100):
#   systematics['pdf_' + str(i)] = [('genWeight', 'weight_pdf_'+str(i))]

#
# Compile list to systematic to show
#
showSysList = list(set(s.split('Up')[0].split('Down')[0].split('_')[0] for s in systematics.keys()))


#
# Defining linear systematics as "name : (sampleList, %)"
#
linearSystematics = {}
linearSystematics['lumi'] = (None, 2.5)

#
# Define linear systematics implemented as rate parameters
#
rateParameters = {}
rateParameters['TT_Dil']   = 5.5
rateParameters['ZG']       = 10
rateParameters['DY']       = 10
rateParameters['singleTop'] = 10
rateParameters['VVTo2L2Nu']    = 50   #other

#
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
    if (sys.count('Scale') or sys.count('Res')) and reduceType.count('pho'): reduceType += '-' + sys
  return reduceType

def getSigmaSyst(sys):
  if sys: 
    if sys == 'NPUp': return 1.
    elif sys == 'NPDown': return -1.
  return 0.


#
# Special systematic samples for hdamp, ue, and erd
#
def getReplacementsForStack(sys, year):
  if not sys:
    return {}
  # no syst variation variation samples for 2016 (in miniAODv3 at least)
  if not year == '2016':
    if sys in ['ueUp', 'ueDown', 'hdampUp', 'hdampDown']:
      return {'TT_Dil' : 'TT_Dil_' + sys.lower(), 'TT_Sem' : 'TT_Sem_' + sys.lower(), 'TT_Had' : 'TT_Had_' + sys.lower()}
    elif sys == 'erdUp' and year == '2017':
      return {'TT_Dil' : 'TT_Dil_erd', 'TT_Sem' : 'TT_Sem_erd', 'TT_Had' : 'TT_Had_erd'}
  return {}


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
