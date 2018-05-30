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
    "orOnZ":               "(abs(mll-91.1876)<15||abs(mll-91.1876)<15)&&!isEMu",
    "offZ":                "abs(mll-91.1876)>15||isEMu",
    "llgNoZ":              "abs(mllg-91.1876)>15||isEMu",

    "gLepdR04":            "phL1DeltaR>0.4&&phL2DeltaR>0.4",
    "gJetdR04":            "phJetDeltaR>0.4",
    "gJetdR02":            "phJetDeltaR>0.2",

    "l2gWindow":           "ml2g>55&&ml2g<80",
    "nol2gWindow":         "!(ml2g>55&&ml2g<80)",
  }

def photonPt(tree, min, max):
  if tree.ph_pt < min:         return False
  if max and tree.ph_pt > max: return False
  return True

continous_variables = [("mll", "mll"),("ml1g","ml1g"),('photonPt',(None, photonPt))]
discrete_variables  = [("njet", "njets"), ("btag", "nbjets"),("deepbtag","ndbjets")]

class cutInterpreter:

  @staticmethod
  def translate_cut(string):
    if string in special_cuts.keys(): return (special_cuts[string], None)

    # continous Variables
    for var, tree_var in continous_variables:
      if string.startswith(var):
        num_str = string[len(var):].replace("to","To").split("To")
        upper = None
        lower = None
        if len(num_str)==2:   lower, upper = num_str
        elif len(num_str)==1: lower = num_str[0]
        else:                 raise ValueError("Can't interpret string %s" % string)

        if type(tree_var)==type(()):
          tree_var, function = tree_var
          function_ = lambda t : function(t, float(lower), float(upper) if upper else None)
        else:
          function_ = None

        if tree_var:
          res_string = []
          if lower: res_string.append(tree_var+">="+lower)
          if upper: res_string.append(tree_var+"<"+upper)
          cutString = "&&".join(res_string)
        else:
          cutString = None
        return (cutString, function_)

    # discrete Variables
    for var, tree_var in discrete_variables:
      log.debug("Reading discrete cut %s as %s"%(var, tree_var))
      if string.startswith( var ):
        if string[len( var ):].replace("to","To").count("To"):
            raise NotImplementedError( "Can't interpret string with 'to' for discrete variable: %s. You just volunteered." % string )

        if type(tree_var)==type(()):
          tree_var, function = tree_var
          num_str = string[len(var):].replace("to","To").replace("p","").split("To")
          upper = None
          lower = None
          if len(num_str)==2:   lower, upper = num_str
          elif len(num_str)==1: lower = num_str[0]
          function_ = lambda t: function(t, int(lower), int(upper) if upper else None)
        else:
          function_ = None

        if tree_var:
          num_str = string[len(var):]
          if num_str[-1] == 'p' and len(num_str)==2:
            cutString = tree_var+">="+num_str[0]
          else:
            vls = [ tree_var+"=="+c for c in num_str ]
            if len(vls)==1: cutString = vls[0]
            else:           cutString = '('+'||'.join(vls)+')'
        else:
          cutString = None
        return (cutString, function_)

    raise ValueError( "Can't interpret string %s. All cuts %s" % (string,  ", ".join( [ c[0] for c in continous_variables + discrete_variables] +  special_cuts.keys() ) ) )

  @staticmethod
  def cutString(cuts, channel):
    strings   = []
    functions = []
    for cut in cuts.split('-'):
      (string, function) = cutInterpreter.translate_cut(cut)
      if string and string.count('||'): string = '(' + string + ')'                                                 #protect
      if string and string!='(1)':      strings.append(string)
      if function:                      functions.append(function)

    cutString        = "&&".join(strings) if len(strings) else '(1)'
    passingFunctions = (lambda t: all(f(t) for f in functions)) if len(functions) else (lambda t : True)

    if channel=="ee":   cutString += '&&isEE'
    if channel=="mumu": cutString += '&&isMuMu'
    if channel=="SF":   cutString += '&&(isMuMu||isEE)'
    if channel=="emu":  cutString += '&&isEMu'
    if channel=="e":    cutString += '&&isE'
    if channel=="mu":   cutString += '&&isMu'

    return cutString, passingFunctions
