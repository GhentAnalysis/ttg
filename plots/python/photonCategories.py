#
# Photon categorization functions
#
def photonCategoryNumber(tree):
  return tree._phTTGMatchCategory[tree.ph]

def checkMatch(tree):
  if not tree.checkMatch:                                          return True
  if tree.genuine        and tree._phTTGMatchCategory[tree.ph] == 1: return True
  if tree.hadronicPhoton and tree._phTTGMatchCategory[tree.ph] == 3: return True
  if tree.misIdEle       and tree._phTTGMatchCategory[tree.ph] == 2: return True
  if tree.hadronicFake   and tree._phTTGMatchCategory[tree.ph] == 4: return True
  return False

def checkSigmaIetaIeta(tree):
  # FIXME since cuts changed slightly, sideband cuts might also have to be changed. Is final elif "relaxed" arbitrary?
  central = abs(tree._phEtaSC[tree.ph]) < 1.479
  if   tree.passSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] >  (0.01015 if central else 0.0272)):                                                                 return False
  elif tree.failSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] <= (0.01015 if central else 0.0272)):                                                                 return False
  elif tree.sideSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] <  (0.012   if central else 0.032)):                                                                   return False
  elif tree.sigmaIetaIeta1    and (tree._phSigmaIetaIeta[tree.ph] <= (0.01015 if central else 0.0272) or tree._phSigmaIetaIeta[tree.ph] > (0.012 if central else 0.032)): return False
  elif tree.sigmaIetaIeta2    and (tree._phSigmaIetaIeta[tree.ph] <= (0.012   if central else 0.032)):                                                                   return False
  elif tree._phSigmaIetaIeta[tree.ph] > (0.02 if central else 0.04):                                                                                                    return False
  return True

def checkChgIso(tree):
  central = abs(tree._phEtaSC[tree.ph]) < 1.479
  if   tree.failChgIso and tree._phChargedIsolation[tree.ph] <= (1.141 if central else 1.051) : return False
  elif tree.passChgIso and tree._phChargedIsolation[tree.ph] >  (1.141 if central else 1.051) : return False
  return True

def chgIsoCat(tree):
  central = abs(tree._phEtaSC[tree.ph]) < 1.479
  return 1 * (tree._phChargedIsolation[tree.ph] <= (1.141 if central else 1.051))
