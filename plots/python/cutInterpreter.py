from ttg.tools.logger import getLogger
log = getLogger()
#
# Class to interpret string based cuts
#

special_cuts = {
    'll':                  '(1)', # base string for dilep
    'llg':                 '(1)', # base string for dilep+photon
    'looseLeptonVeto':     'looseLeptonVeto',

    'onZ':                 'abs(mll-91.1876)<15&&!isEMu',
    'onZnar':              'abs(mll-91.1876)<10&&!isEMu',
    'onZverynar':          'abs(mll-91.1876)<5&&!isEMu',
    'llgOnZ':              'abs(mllg-91.1876)<15&&!isEMu',
    'orOnZ':               '(abs(mll-91.1876)<15||abs(mllg-91.1876)<15)&&!isEMu',
    'offZ':                'abs(mll-91.1876)>15||isEMu',
    'llgNoZ':              'abs(mllg-91.1876)>15||isEMu',

    'l2gWindow':           'ml2g>55&&ml2g<80',
    'nol2gWindow':         '!(ml2g>55&&ml2g<80)',

    'signalRegion':        '(njets>1)||(njets==1&&ndbjets==1)',   # signal regions small

    'all':                 '(1)',
    'noData':              '(1)',
    'ee':                  'isEE',
    'mumu':                'isMuMu',
    'SF':                  'isMuMu||isEE',
    'emu':                 'isEMu',
    'e':                   'isE',
    'mu':                  'isMu',
  }

def phLepDeltaR(tree, lower, upper):
  return (lower <= min(tree.phL1DeltaR, tree.phL2DeltaR) < upper)

# TODO currently this can not deal with combining years due to cuts being different
def phMVA(tree, lower, upper):
  return (lower <= tree._phMva[tree.ph] < upper)

def chIso(tree, lower, upper):
  return (lower <= tree._phChargedIsolation[tree.ph] < upper)

def puChargedHadronIso(tree, lower, upper):
  return (lower <= tree._puChargedHadronIso[tree.ph] < upper)

def phEta(tree, lower, upper):
  return (lower <= abs(tree._phEta[tree.ph]) < upper)

continous_variables = {'mll': 'mll', 'ml1g': 'ml1g', 'photonPt': 'ph_pt', 'phJetDeltaR': 'phJetDeltaR', 'phLepDeltaR': phLepDeltaR, 'genPhMinDeltaR' : 'genPhMinDeltaR', 'phMVA': phMVA, 'chIso':chIso, 'puChargedHadronIso' : puChargedHadronIso, 'photonEta': phEta}
discrete_variables  = {'njet': 'njets', 'btag': 'nbjets', 'deepbtag': 'ndbjets', 'nphoton': 'nphotons'}

# Need to disable the too many branches function because CMSSW has some ancient pylint release which does not exclude nested functions
def cutStringAndFunctions(cuts, channel): # pylint: disable=R0912

  def buildString(tree_var, lower, upper):
    if lower == upper: return tree_var + '==' + lower
    res_string = []
    if lower: res_string.append(tree_var+'>='+lower)
    if upper: res_string.append(tree_var+'<'+upper)
    return '&&'.join(res_string)

  def translate_cut(string): # pylint: disable=R0912
    if string in special_cuts: return special_cuts[string]

    for var, tree_var in continous_variables.items() + discrete_variables.items():
      if string.startswith(var):
        if string[len(var):].replace('to','To').count('To') or var in continous_variables:
          num_str = string[len(var):].replace('to','To').split('To')
          if len(num_str)==2:   lower, upper = num_str
          elif len(num_str)==1: lower, upper = num_str[0], None
          else:                 raise ValueError("Can't interpret string %s" % string)
        else:
          num_str = string[len(var):]
          if num_str[-1] == 'p': lower, upper = num_str.split('p')[0], None
          else:                  lower, upper = num_str, num_str

        # Can also use a function(tree, min, max) in case more complex variables want to be tested
        if callable(tree_var) and var in continous_variables: return (lambda t : tree_var(t, float(lower), float(upper) if upper else float('inf')))
        elif callable(tree_var):                              return (lambda t : tree_var(t, int(lower),   int(upper)   if upper else float('inf')))
        else:                                                 return buildString(tree_var, lower, upper)

    raise ValueError("Can't interpret string %s. All cuts %s" % (string, ', '.join(continous_variables.keys() + discrete_variables.keys() + special_cuts.keys())))


  strings, functions = [], []
  for cut in cuts.split('-') + [channel]:
    cut = cut.replace('NEG','-')
    interpretedCut = translate_cut(cut)
    if callable(interpretedCut):      functions.append(interpretedCut)
    elif interpretedCut.count('||'):  strings.append('(' + interpretedCut + ')') #protect for ||
    elif interpretedCut != '(1)':     strings.append(interpretedCut)

  cutString        = '&&'.join(strings) if len(strings) else '(1)'
  passingFunctions = (lambda t: all(f(t) for f in functions)) if len(functions) else (lambda t : True)

  return cutString, passingFunctions
