#
# 8 TeV - style matching, same as semi-leptonic group
#

from ttg.reduceTuple.objectSelection import deltaR

def isSignalPhoton(tree, index):
  mcIndex = tree._phMatchMCPhotonAN15165[index]
  if mcIndex < 0:                                                                                               return False
  if not tree._gen_phPassParentage[mcIndex]:                                                                    return False
  if (tree._gen_phPt[mcIndex] - tree._phPt[index])/tree._gen_phPt[mcIndex] > 0.1:                               return False
  if tree._gen_phMinDeltaR[mcIndex] < 0.2:                                                                      return False
  if deltaR(tree._gen_phEta[mcIndex], tree._phEta[index], tree._gen_phPhi[mcIndex], tree._phPhi[index]) > 0.01: return False
  if (tree._gen_phEta[mcIndex] - tree._phEta[index])/tree._gen_phEta[mcIndex] > 0.005:                          return False
  return True

def isHadronicPhoton(tree, index):
  mcIndex = tree._phMatchMCPhotonAN15165[index]
  if mcIndex < -1:                return False
  if isSignalPhoton(tree, index): return False
  return True

def isGoodElectron(tree, index):
  if isSignalPhoton(tree, index):   return False
  if isHadronicPhoton(tree, index): return False
  mcIndex = tree._phMatchMCLeptonAN15165[index]
  if mcIndex < 0:                                                                                             return False
  if (tree._gen_lPt[mcIndex] - tree._phPt[index])/tree._gen_lPt[mcIndex] > 0.1:                               return False
# if not tree._gen_lPassParentage[mcIndex]                                                                    return False # To be added to tuples
# if tree._gen_lMinDeltaR[mcIndex] < 0.2:                                                                     return False # To be added to tuples
  if deltaR(tree._gen_lEta[mcIndex], tree._phEta[index], tree._gen_lPhi[mcIndex], tree._phPhi[index]) > 0.04: return False
  if (tree._gen_lEta[mcIndex] - tree._phEta[index])/tree._gen_lEta[mcIndex] > 0.005:                          return False
  return True;

def isHadronicFake(tree, index):
  if isSignalPhoton(tree, index):   return False
  if isHadronicPhoton(tree, index): return False
  if isGoodElectron(tree, index):   return False
  return True

def checkMatch(tree, index, texName):
  if tree.genuine        and not isSignalPhoton(tree, index):   return False
  if tree.hadronicPhoton and not isHadronicPhoton(tree, index): return False
  if tree.misIdEle       and not isGoodElectron(tree, index):   return False
  if tree.hadronicFake   and not isHadronicFake(tree, index):   return False
  return True

def checkPrompt(tree, index, texName):
  if tree.nonprompt and tree._phIsPrompt[index]:     return False
  if tree.prompt    and not tree._phIsPrompt[index]: return False
  return True

def checkSigmaIetaIeta(tree, index, texName):
  upperCut = (0.01022 if abs(tree._phEta[index]) < 1.566 else  0.03001)                      # forward region needs much higher cut
  lowerCut = (0.01022 if abs(tree._phEta[index]) < 1.566 else  0.03001)                      # forward region needs much higher cut
  if   tree.passSigmaIetaIeta and tree._phSigmaIetaIeta[index] > lowerCut:                return False
  elif tree.failSigmaIetaIeta and tree._phSigmaIetaIeta[index] < upperCut:                return False
  if tree._phSigmaIetaIeta[index] > (0.016 if abs(tree._phEta[index]) < 1.566 else 0.04): return False
  return True
