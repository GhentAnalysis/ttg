from ttg.tools.logger import getLogger
log = getLogger()


#
# Defining shape systematics as "name : ([var, sysVar], [var2, sysVar2],...)"
#
systematics = {}
for i in ('Up', 'Down'):
  systematics['isr'+i]        = []
  systematics['fsr'+i]        = []
  systematics['eScale'+i]     = []
  systematics['eRes'+i]       = []
  systematics['phScale'+i]    = []
  systematics['phRes'+i]      = []
  systematics['pu'+i]         = [('puWeight',      'puWeight'+i)]
  systematics['phSF'+i]       = [('phWeight',      'phWeight'+i)]
  systematics['lSF'+i]        = [('lWeight',       'lWeight'+i)]
  systematics['trigger'+i]    = [('triggerWeight', 'triggerWeight'+i)]
  systematics['bTagl'+i]      = [('bTagWeight',    'bTagWeightl'+i)]
  systematics['bTagb'+i]      = [('bTagWeight',    'bTagWeightb'+i)]
  systematics['JEC'+i]        = [('njets',         'njets_JEC'+i),     ('ndbjets',    'ndbjets_JEC'+i), ('j1', 'j1_JEC'+i), ('j2', 'j2_JEC'+i), ('_jetPt', '_jetPt_JEC'+i)]
  systematics['JER'+i]        = [('njets',         'njets_JER'+i),     ('ndbjets',    'ndbjets_JER'+i), ('j1', 'j1_JER'+i), ('j2', 'j2_JER'+i), ('_jetPt', '_jetPt_JER'+i)]

#
# Special case for q2 and PDF: multiple variations of which an envelope has to be taken
#
for i in ('Ru','Fu','RFu','Rd','Fd','RFd'):
  systematics['q2_' + i] = [('genWeight', 'weight_q2_'+i)]
for i in range(0,100):
  systematics['pdf_' + str(i)] = [('genWeight', 'weight_pdf_'+str(i))]

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
rateParameters['TTJets']   = 5.5
rateParameters['ZG']       = 10
rateParameters['DY']       = 10
rateParameters['single-t'] = 10
rateParameters['other']    = 50


#
# Function to apply the systematic to the cutstring, tree branches, reduceType
# When ':' is used in the sysVar, the first part selects a specific sample on which the sysVar should be applied
#
def applySysToString(sample, sys, string):
  if sys:
    for var, sysVar in systematics[sys]:
      if sysVar.count(':'):
        s, sysVar = sysVar.split(':')
        if sample!=s: return string
      string = string.replace(var, sysVar)
  return string

def applySysToTree(sample, sys, tree):
  for var, sysVar in systematics[sys]:
    if sysVar.count(':'):
      s, sysVar = sysVar.split(':')
      if sample!=s: return
    setattr(tree, var, getattr(tree, sysVar))

def applySysToReduceType(reduceType, sys):
  if sys:
    if (sys.count('Scale') or sys.count('Res')) and reduceType.count('pho'): reduceType += '-' + sys
  return reduceType

#
# Special systematic samples for FSR and ISR
#
def getReplacementsForStack(sys):
  if sys and any([i==sys for i in ['fsrUp', 'fsrDown', 'isrUp', 'isrDown']]):
    return {'TTGamma' : 'TTGamma_' + sys.lower(), 'TTJets_pow' : 'TTJets_pow_' + sys.lower()}
  else:
    return {}


#
# Function for the q2 envelope using input histogram
#
def q2Sys(variations):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  for i in range(0, variations[0].GetNbinsX()+1):
    upHist.SetBinContent(  i, max([var.GetBinContent(i) for var in variations]))
    downHist.SetBinContent(i, min([var.GetBinContent(i) for var in variations]))
  return upHist, downHist

def constructQ2Sys(allPlots, plotName, stack):
  allPlots[plotName + 'q2Up'] = {}
  allPlots[plotName + 'q2Down'] = {}
  for histName in [s.name+s.texName for s in stack]:
    try:
      variations = [allPlots[plotName + 'q2_' + i][histName] for i in ('Ru','Fu','RFu','Rd','Fd','RFd')]
      allPlots[plotName + 'q2Up'][histName], allPlots[plotName + 'q2Down'][histName] = q2Sys(variations)
    except:
      log.warning('Missing q2 variations for ' + plotName + ' ' + histName + '!')
      allPlots[plotName + 'q2Up'][histName], allPlots[plotName + 'q2Down'][histName] = allPlots[plotName][histName], allPlots[plotName][histName]

#
# Function for the pdf RMS envelope using input histogram
#
from math import sqrt
def pdfSys(variations, nominal):
  upHist, downHist = variations[0].Clone(), variations[0].Clone()
  for i in range(0, variations[0].GetNbinsX()+1):
    pdfVarRms = sqrt(sum((nominal.GetBinContent(i) - var.GetBinContent(i))**2 for var in variations)/len(variations))
    upHist.SetBinContent(  i, nominal.GetBinContent(i) + pdfVarRms)
    downHist.SetBinContent(i, nominal.GetBinContent(i) - pdfVarRms)
  return upHist, downHist

def constructPdfSys(allPlots, plotName, stack):
  allPlots[plotName + 'pdfUp'] = {}
  allPlots[plotName + 'pdfDown'] = {}
  for histName in [s.name+s.texName for s in stack]:
    try:
      variations = [allPlots[plotName + 'pdf_' + str(i)][histName] for i in range(0, 100)]
      allPlots[plotName + 'pdfUp'][histName], allPlots[plotName + 'pdfDown'][histName] = pdfSys(variations, allPlots[plotName][histName])
    except:
      log.warning('Missing pdf variations for ' + plotName + ' ' + histName + '!')
      allPlots[plotName + 'pdfUp'][histName], allPlots[plotName + 'pdfDown'][histName] = allPlots[plotName][histName], allPlots[plotName][histName]
