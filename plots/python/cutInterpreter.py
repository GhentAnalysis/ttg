from ttg.tools.logger import getLogger
log = getLogger()
#
# Class to interpret string based cuts
# Still could use some cleanu Still could use some cleanup
#

import ROOT

special_cuts = {
    "pho":                 "(1)", # base string for QCD
    "ll":                  "(1)", # base string for dilep
    "llg":                 "(1)", # base string for dilep+photon
    "lg":                  "(1)", # base string for singlelep
    "looseLeptonVeto":     "looseLeptonVeto",

    "onZ":                 "abs(mll-91.1876)<15&&!isEMu",
    "llgOnZ":              "abs(mllg-91.1876)<15&&!isEMu",
    "orOnZ":               "(abs(mll-91.1876)<15||abs(mllg-91.1876)<15)&&!isEMu",
    "offZ":                "abs(mll-91.1876)>15||isEMu",
    "llgNoZ":              "abs(mllg-91.1876)>15||isEMu",

    "gLepdR04":            "phL1DeltaR>0.4&&phL2DeltaR>0.4",
    "gJetdR04":            "phJetDeltaR>0.4",
    "gJetdR02":            "phJetDeltaR>0.2",

    "l2gWindow":           "ml2g>55&&ml2g<80",
    "nol2gWindow":         "!(ml2g>55&&ml2g<80)",

    "signalRegion":        "(njets>1)||(njets==1&&ndbjets==1)",   # signal regions small
  }

def phLepDeltaR(tree, min, max):
  return (min <= min(c.phL1DeltaR, c.phL2DeltaR) < max)

continous_variables = [("mll", "mll"),("ml1g","ml1g"),('photonPt', 'ph_pt'), ('phJetDeltaR', 'phJetDeltaR'), ('phLepDeltaR', phLepDeltaR)]
discrete_variables  = [("njet", "njets"), ("btag", "nbjets"),("deepbtag","ndbjets"),("nphoton","nphotons")]

class cutInterpreter:

  @staticmethod
  def buildString(tree_var, lower, upper):
    res_string = []
    if lower: res_string.append(tree_var+">="+lower)
    if upper: res_string.append(tree_var+"<"+upper)
    return "&&".join(res_string)


  @staticmethod
  def translate_cut(string):
    if string in special_cuts.keys(): return special_cuts[string]

    # continous Variables
    for var, tree_var in continous_variables:
      if string.startswith(var):
        num_str = string[len(var):].replace("to","To").split("To")
        if len(num_str)==2:   lower, upper = num_str
        elif len(num_str)==1: lower, upper = num_str[0], None
        else:                 raise ValueError("Can't interpret string %s" % string)

        # Can also use a function(tree, min, max) in case more complex variables want to be tested
        if callable(tree_var): return (lambda t : tree_var(t, float(lower), float(upper) if upper else None))
        else:                  return buildString(tree_var, lower, upper)

    # discrete Variables
    for var, tree_var in discrete_variables:
      if string.startswith( var ):
        if string[len( var ):].replace("to","To").count("To"):
          num_str = string[len(var):].replace("to","To").replace("p","").split("To")
          if len(num_str)==2:   lower, upper = num_str
          elif len(num_str)==1: lower, upper = num_str[0], None
          else:                 raise ValueError("Can't interpret string %s" % string)
        else:
          num_str = string[len(var):]
          if num_str[-1] == 'p': lower, upper = num_str.split('p')[0], None
          else:                  lower, upper = num_str, str(int(num_str)+1)

        if callable(tree_var): return (lambda t: tree_var(t, int(lower), int(upper) if upper else None))
        else:                  return buildString(tree_var, lower, upper)

    raise ValueError( "Can't interpret string %s. All cuts %s" % (string,  ", ".join( [ c[0] for c in continous_variables + discrete_variables] +  special_cuts.keys() ) ) )

  @staticmethod
  def cutString(cuts, channel):
    strings, functions = [], []
    for cut in cuts.split('-'):
      interpretedCut = cutInterpreter.translate_cut(cut)
      if callable(interpretedCut):      functions.append(interpretedCut)
      elif interpretedCut.count('||'):  strings.append('(' + interpretedCut + ')') #protect for ||
      else interpretedCut != '(1)':     strings.append(interpretedCut)

    cutString        = "&&".join(strings) if len(strings) else '(1)'
    passingFunctions = (lambda t: all(f(t) for f in functions)) if len(functions) else (lambda t : True)

    if channel=="ee":   cutString += '&&isEE'
    if channel=="mumu": cutString += '&&isMuMu'
    if channel=="SF":   cutString += '&&(isMuMu||isEE)'
    if channel=="emu":  cutString += '&&isEMu'
    if channel=="e":    cutString += '&&isE'
    if channel=="mu":   cutString += '&&isMu'

    return cutString, passingFunctions
