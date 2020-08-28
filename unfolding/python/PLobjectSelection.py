from ttg.tools.logger  import getLogger
from ttg.tools.helpers import deltaR
from math import sqrt, atan, pi, tan
from math import log as logar
import ROOT
import os

log = getLogger()

#
# All functions to select objects, as well as some functions which add new variables based on the selected objects to the tree
#

#
# Helper functions
#
def getSortKey(item): return item[0]

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  return vector



# LEPTONS
def PLleptonSelector(tree, index):
  if tree._pl_lPt[index] < 15:          return False
  if abs(tree._pl_lEta[index]) > 2.4:   return False
  else:                                 return True

def PLselectLeptons(t, n):
  t.PLleptons = [i for i in xrange(t._pl_nL) if PLleptonSelector(t, i)]
  ptAndIndex        = [(t._pl_lPt[i], i) for i in t.PLleptons]
  if len(ptAndIndex) < 2: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.PLl1              = ptAndIndex[0][1]
  n.PLl2              = ptAndIndex[1][1]
  n.PLl1_pt           = ptAndIndex[0][0]
  n.PLl2_pt           = ptAndIndex[1][0]
  n.PLisEE            = (t._pl_lFlavor[n.PLl1]==0 and t._pl_lFlavor[n.PLl2]==0)
  n.PLisEMu           = (t._pl_lFlavor[n.PLl1]==0 and t._pl_lFlavor[n.PLl2]==1) or (t._pl_lFlavor[n.PLl1]==1 and t._pl_lFlavor[n.PLl2]==0)
  n.PLisMuMu          = (t._pl_lFlavor[n.PLl1]==1 and t._pl_lFlavor[n.PLl2]==1)
  n.PLisOS            = t._pl_lCharge[n.PLl1] != t._pl_lCharge[n.PLl2]
  return n.PLl1_pt > 25 and n.PLisOS


# PHOTON
def PLphotonSelector(tree, index, n):
  if abs(tree._pl_phEta[index]) > 2.5:                                                                 return False
  if tree._pl_phPt[index] < 20:                                                                        return False
  for i in [n.PLl1, n.PLl2]:
    if deltaR(tree._pl_lEta[i], tree._pl_phEta[index], tree._pl_lPhi[i], tree._pl_phPhi[index]) < 0.4: return False
  return True

def PLselectPhotons(t, n):
  t.PLphotons  = [p for p in range(t._pl_nPh) if PLphotonSelector(t, p, n)]
  n.PLnphotons = len(t.PLphotons)
  if n.PLnphotons == 1:
    n.PLph    = t.PLphotons[0]
    n.PLph_pt = t._pl_phPt[n.PLph]
    n.PLph_Eta = t._pl_phEta[n.PLph]
    return True
  else:
    return False

# JETS
def PLisGoodJet(tree, n, index):
  if not abs(tree._pl_jetEta[index]) < 2.4: return False
  if deltaR(tree._pl_jetEta[index], tree._pl_phEta[n.PLph], tree._pl_jetPhi[index], tree._pl_phPhi[n.PLph]) < 0.1: return False
  
  for lep in tree.PLleptons:
    if deltaR(tree._pl_jetEta[index], tree._pl_lEta[lep], tree._pl_jetPhi[index], tree._pl_lPhi[lep]) < 0.4: return False
  return True

# just store 1 "jets match" bool?

def PLgoodJets(t, n):
  allGoodJets = [i for i in xrange(t._pl_nJets) if PLisGoodJet(t, n, i)]
  setattr(t, 'PLjets',  [i for i in allGoodJets if getattr(t, '_pl_jetPt')[i] > 30])
  setattr(n, 'PLnjets', len(getattr(t, 'PLjets')))
  setattr(n, 'PLj1', getattr(t, 'PLjets')[0] if getattr(n, 'PLnjets') > 0 else -1)
  setattr(n, 'PLj2', getattr(t, 'PLjets')[1] if getattr(n, 'PLnjets') > 1 else -1)
  # setattr(n, 'PLj3', getattr(t, 'PLjets')[0] if getattr(n, 'PLnjets') > 2 else -1)
  # setattr(n, 'PLj4', getattr(t, 'PLjets')[1] if getattr(n, 'PLnjets') > 3 else -1)
  # setattr(n, 'PLj5', getattr(t, 'PLjets')[0] if getattr(n, 'PLnjets') > 4 else -1)
  # setattr(n, 'PLj6', getattr(t, 'PLjets')[1] if getattr(n, 'PLnjets') > 5 else -1)

def PLbJets(t, n):
  setattr(t, 'PLdbjets',  [i for i in getattr(t, 'PLjets') if t._pl_jetHadronFlavor[i] == 5])
  setattr(n, 'PLndbjets', len(getattr(t, 'PLdbjets')))
  # setattr(n, 'PLdbj1', getattr(t, 'PLdbjets')[0] if getattr(n, 'PLndbjets') > 0 else -1)
  # setattr(n, 'PLdbj2', getattr(t, 'PLdbjets')[1] if getattr(n, 'PLndbjets') > 1 else -1)
  # setattr(n, 'PLdbj3', getattr(t, 'PLdbjets')[2] if getattr(n, 'PLndbjets') > 2 else -1)
  # setattr(n, 'PLdbj4', getattr(t, 'PLdbjets')[3] if getattr(n, 'PLndbjets') > 3 else -1)

def PLmakeInvariantMasses(t, n):
  first  = getLorentzVector(n.PLl1_pt, t._pl_lEta[n.PLl1], t._pl_lPhi[n.PLl1], t._pl_lE[n.PLl1])   if len(t.PLleptons) > 0 else None
  second = getLorentzVector(n.PLl2_pt, t._pl_lEta[n.PLl2], t._pl_lPhi[n.PLl2], t._pl_lE[n.PLl2])   if len(t.PLleptons) > 1 else None
  photon = getLorentzVector(n.PLph_pt, t._pl_phEta[n.PLph], t._pl_phPhi[n.PLph], t._pl_phE[n.PLph]) if len(t.PLphotons) > 0 else None

  n.PLmll  = (first+second).M()        if first and second else -1
  n.PLmllg = (first+second+photon).M() if first and second and photon else -1
  n.PLml1g = (first+photon).M()        if first and photon else -1
  n.PLml2g = (second+photon).M()       if second and photon else -1


def PLmakeDeltaR(t, n):
  n.PLphL1DeltaR   = deltaR(t._pl_lEta[n.PLl1], t._pl_phEta[n.PLph], t._pl_lPhi[n.PLl1], t._pl_phPhi[n.PLph]) if len(t.PLphotons) > 0 and len(t.PLleptons) > 0 else -1
  n.PLphL2DeltaR   = deltaR(t._pl_lEta[n.PLl2], t._pl_phEta[n.PLph], t._pl_lPhi[n.PLl2], t._pl_phPhi[n.PLph]) if len(t.PLphotons) > 0 and len(t.PLleptons) > 1 else -1
  # TODO turn this back on when the time for systematics has come
  # TODO NEED PLj1JECUP ETS variations then too?  don't think JER variations etc exist for PL but check
  # for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
  for var in ['']:
    setattr(n, 'PLphJetDeltaR'+var,  min([deltaR(t._pl_jetEta[j], t._pl_phEta[n.PLph], t._pl_jetPhi[j], t._pl_phPhi[n.PLph]) for j in getattr(t, 'PLjets'+var)] + [999])   if len(t.PLphotons) > 0 else -1)
    setattr(n, 'PLphBJetDeltaR'+var, min([deltaR(t._pl_jetEta[j], t._pl_phEta[n.PLph], t._pl_jetPhi[j], t._pl_phPhi[n.PLph]) for j in getattr(t, 'PLdbjets'+var)] + [999]) if len(t.PLphotons) > 0 else -1)
    setattr(n, 'PLl1JetDeltaR'+var,  min([deltaR(t._pl_jetEta[j], t._pl_lEta[n.PLl1], t._pl_jetPhi[j], t._pl_lPhi[n.PLl1]) for j in getattr(t, 'PLjets'+var)] + [999])     if len(t.PLleptons) > 0 else -1)
    setattr(n, 'PLl2JetDeltaR'+var,  min([deltaR(t._pl_jetEta[j], t._pl_lEta[n.PLl2], t._pl_jetPhi[j], t._pl_lPhi[n.PLl2]) for j in getattr(t, 'PLjets'+var)] + [999])     if len(t.PLleptons) > 1 else -1)
    setattr(n, 'PLjjDeltaR'+var,     min([deltaR(t._pl_jetEta[getattr(n, 'PLj1'+var)], t._pl_jetEta[getattr(n, 'PLj2'+var)], t._pl_jetPhi[getattr(n, 'PLj1'+var)], t._pl_jetPhi[getattr(n, 'PLj2'+var)])]) if getattr(n, 'PLnjets'+var) > 1 else -1) # pylint: disable=C0301


# def checkPLMatches(t, n):
#   if deltaR(t._phEta[n.ph], t._pl_phEta[n.PLph], t._phPhi[n.ph], t._pl_phPhi[n.PLph]) > 0.1: 
#     log.info('failed ph match')
#     return False
#   if not any([deltaR(t._lEta[n.l1], t._pl_lEta[i], t._lPhi[n.l1], t._pl_lPhi[i]) > 0.1 for i in [n.PLl1, n.PLl2]]):
#     log.info('failed l1 match')
#     return False
#   if not any([deltaR(t._lEta[n.l2], t._pl_lEta[i], t._lPhi[n.l2], t._pl_lPhi[i]) > 0.1 for i in [n.PLl1, n.PLl2]]):
#     log.info('failed l2 match')
#     return False
#   # for i in t.dbjets:
#   #   if not any([deltaR(t._jetEta[i], t._pl_jetEta[j], t._jetPhi[i], t._pl_jetPhi[j]) > 0.1 for j in t.PLdbjets]):
#   #     log.info('failed bjet match')
#   #     return False
#   # for i in (jet for jet in t.jets if not jet in t.dbjets):
#   #   if not any([deltaR(t._jetEta[i], t._pl_jetEta[j], t._jetPhi[i], t._pl_jetPhi[j]) > 0.1 for j in (pljet for pljet in t.PLjets if not pljet in t.PLdbjets)]):
#   #     log.info('failed light jet match')
#   #     return False
#   return True



# _pl_met         = 61.5389
#  _pl_metPhi      = -0.978004
#  _pl_nPh         = 1
#  _pl_phPt        = 19.3656
#  _pl_phEta       = 1.34456
#  _pl_phPhi       = -2.89655
#  _pl_phE         = 39.6717
#  _pl_nL          = 2
#  _pl_lPt         = 70.2148, 
#                   16.7655
#  _pl_lEta        = -0.659435, 
#                   1.04436
#  _pl_lPhi        = 1.85767, 
#                   -3.12054
#  _pl_lE          = 86.0427, 
#                   26.7703
#  _pl_lFlavor     = 0, 
#                   0
#  _pl_lCharge     = 1, 
#                   -1
#  _pl_nJets       = 4
#  _pl_jetPt       = 193.956, 
#                   138.688, 90.6483, 30.2881
#  _pl_jetEta      = 0.472771, 
#                   -0.804818, -0.146903, -1.54542
#  _pl_jetPhi      = -2.17362, 
#                   0.725882, 0.739704, 2.99427
#  _pl_jetE        = 216.368, 
#                   187.581, 93.1615, 74.3374
#  _pl_jetHadronFlavor = 5, 
#                   0, 0, 5