#
# 8 TeV - style matching, same as semi-leptonic group
#

from ttg.reduceTuple.objectSelection import deltaR

def isSignalPhoton(tree, index):
  mcIndex = tree._phMatchMCPhotonAN15165[index]
  if mcIndex < 0:                                                                                  return False
  if not tree._gen_phPassParentage[mcIndex]:                                                       return False
  if (tree._gen_phPt[mcIndex] - tree._phPt[index])/tree._gen_phPt[mcIndex] > 0.1:                  return False
  if c._gen_phMinDeltaR[mcIndex] < 0.2:                                                            return False
  if deltaR(c._gen_phEta[mcIndex], c._phEta[index], c._gen_phPhi[mcIndex], c._phPhi[c.ph]) > 0.01: return False
  if (c._gen_phEta[mcIndex] - c._phEta[index])/c._gen_phEta[mcIndex] > 0.005:                      return False
  return True

def isHadronicPhoton(tree, index):
  mcIndex = tree._phMatchMCPhotonAN15165[index]
  if mcIndex < -1:                return False
  if isSignalPhoton(tree, index): return False
  return True

def isGoodElectron(tree, index):
  mcIndex = tree._phMatchMCLeptonAN15165[index]
  if mcIndex < 0:                                                                                return False
  if (tree._gen_lPt[mcIndex] - tree._phPt[index])/tree._gen_lPt[mcIndex] > 0.1:                  return False
# if not tree._gen_lPassParentage[mcIndex]                                                       return False # To be added to tuples
# if c._gen_lMinDeltaR[mcIndex] < 0.2:                                                           return False # To be added to tuples
  if deltaR(c._gen_lEta[mcIndex], c._phEta[index], c._gen_lPhi[mcIndex], c._phPhi[c.ph]) > 0.04: return False
  if (c._gen_lEta[mcIndex] - c._phEta[index])/c._gen_lEta[mcIndex] > 0.005:                      return False
  return True;

def isHadronicFake(tree, index):
  if isSignalPhoton(tree, index):   return False
  if isHadronicPhoton(tree, index): return False
  if isGoodElectron(tree, index):   return False
  return True



