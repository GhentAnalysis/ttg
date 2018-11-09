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
  central = abs(tree._phEta[tree.ph]) < 1.566
  if   tree.passSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] > (0.01022 if central else 0.03001)):                                                                 return False
  elif tree.failSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] < (0.01022 if central else 0.03001)):                                                                 return False
  elif tree.sideSigmaIetaIeta and (tree._phSigmaIetaIeta[tree.ph] < (0.012   if central else 0.032)):                                                                   return False
  elif tree.sigmaIetaIeta1    and (tree._phSigmaIetaIeta[tree.ph] < (0.01022 if central else 0.03001) or tree._phSigmaIetaIeta[tree.ph] > (0.012 if central else 0.032)): return False
  elif tree.sigmaIetaIeta2    and (tree._phSigmaIetaIeta[tree.ph] < (0.012   if central else 0.032)):                                                                   return False
  elif tree._phSigmaIetaIeta[tree.ph] > (0.02 if central else 0.04):                                                                                                    return False
  return True

def checkChgIso(tree):
  if   tree.failChgIso and tree._phChargedIsolation[tree.ph] < 0.441: return False
  elif tree.passChgIso and tree._phChargedIsolation[tree.ph] > 0.441: return False
  return True
