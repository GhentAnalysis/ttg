from ttg.tools.logger import getLogger
log = getLogger()
#
# Class to interpret string based cuts
# Still could use some cleanu Still could use some cleanup
#

import ROOT

special_cuts = {
    "llg":                 "(1)", # base string
    "looseLeptonVeto":     "looseLeptonVeto",

    "onZ":                 "abs(mll-91.1876)<15||!isEMu",
    "offZ":                "abs(mll-91.1876)>15||isEMu",
    "llgNoZ":              "abs(mllg-91.1876)>15||isEMu",

    "gLepdR07":            "phL1DeltaR>0.7&&phL2DeltaR>0.7",
    "gJetdR07":            "phJetDeltaR>0.7",
  }

continous_variables = [("mll", "mll")]
discrete_variables  = [("njet", "njets"), ("btag", "nbjets")]

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
  def cutString(cuts):
    strings   = []
    functions = []
    for cut in cuts.split('-'):
      (string, function) = cutInterpreter.translate_cut(cut)
      if string.count('||'):       string = '(' + string + ')'                                                 #protect
      if string and string!='(1)': strings.append(string)
      if function:                 functions.append(function)

    cutString        = "&&".join(strings) if len(strings) else None
    passingFunctions = (lambda t: all(f(t) for f in functions)) if len(functions) else (lambda t : True)

    return cutString, passingFunctions
