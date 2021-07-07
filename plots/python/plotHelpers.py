#! /usr/bin/env python

from ttg.tools.helpers import deltaR, deltaPhi
import ROOT
import numpy

def rawLep1JetDeltaR(tree):
  return min(deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) for j in range(tree._nJets))

def rawLep2JetDeltaR(tree):
  return min(deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) for j in range(tree._nJets))

def rawLepJetDeltaR(tree):
  return min([rawLep1JetDeltaR(tree), rawLep2JetDeltaR(tree)])

def closestRawJetLep1(tree):
  dist = [deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) for j in range(tree._nJets)]
  return dist.index(min(dist))

def closestRawJetLep2(tree):
  dist = [deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) for j in range(tree._nJets)]
  return dist.index(min(dist))

def genLep1RawJetDeltaR(tree):
  j = closestRawJetLep1(tree)
  if tree._lIsPrompt[tree.l1]: return deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1])
  else: return -1.

def genLep2RawJetDeltaR(tree):
  j = closestRawJetLep2(tree)
  if tree._lIsPrompt[tree.l2]: return deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2])
  else: return -1.

def genLepRawJetDeltaR(tree):
  # NOTE this means both leptons are required to be prompt
  return min([genLep1RawJetDeltaR(tree), genLep2RawJetDeltaR(tree)])

def genLepRawJetNearPhDeltaR(tree):
  j = closestRawJet(tree) #jet closest to photon
  distl1 = deltaR(tree._jetEta[j], tree._lEta[tree.l1], tree._jetPhi[j], tree._lPhi[tree.l1]) if tree._lIsPrompt[tree.l1] else -1.
  distl2 = deltaR(tree._jetEta[j], tree._lEta[tree.l2], tree._jetPhi[j], tree._lPhi[tree.l2]) if tree._lIsPrompt[tree.l2] else -1.
  return min([distl1, distl1])

def channelNumbering(t):
  return (1 if t.isMuMu else (2 if t.isEMu else 3))

def channelNumberingPB(t):
  return (1 if t.isEMu else (2 if t.isEE else 3))

def createSignalRegions(t):
  if t.ndbjets == 0:
    if t.njets == 0: return 0
    if t.njets == 1: return 1
    if t.njets == 2: return 2
    if t.njets >= 3: return 3
  elif t.ndbjets == 1:
    if t.njets == 1: return 4
    if t.njets == 2: return 5
    if t.njets >= 3: return 6
  elif t.ndbjets == 2:
    if t.njets == 2: return 7
    if t.njets >= 3: return 8
  elif t.ndbjets >= 3 and t.njets >= 3: return 9
  return -1



def createSignalRegionsZoom(t):
  if t.ndbjets == 1:
    if t.njets == 1: return 0
    if t.njets == 2: return 1
    if t.njets >= 3: return 2
  elif t.ndbjets == 2:
    if t.njets == 2: return 3
    if t.njets >= 3: return 4
  elif t.ndbjets >= 3 and t.njets >= 3: return 5
  return -1

def createSignalRegionsZoomCap(t):
  if t.ndbjets == 1:
    if t.njets == 1: return 0
    if t.njets >= 2: return 1
  elif t.ndbjets >= 2: return 2
  return -1


def createSignalRegionsCap(t):
  if t.ndbjets == 0:
    if t.njets == 0: return 0
    if t.njets == 1: return 1
    if t.njets >= 2: return 2
  elif t.ndbjets == 1:
    if t.njets == 1: return 3
    if t.njets >= 2: return 4
  elif t.ndbjets >= 2: return 5
  return -1


# you can remove items from momList, but keep momRef 
momRef = {1: 'd', 2: 'u', 3: 's', 4: 'c', 5: 'b', 6: 't', 11: 'e', 13: '#mu', 15: '#tau', 21: 'g', 24: 'W', 111: '#pi^{0}', 221: '#pi^{+/-}', 223: '#rho^{+}', 331: '#rho `', 333: '#phi', 413: 'D^{*+}', 423: 'D^{*0}', 433: 'D_{s}^{*+}', 445: '445', 513: 'B^{*0}', 523: 'B^{*+}', 533: 'B_{s}^{*0}', 543: 'B_{c}^{*+}', 2212: 'p', 4312:'4312', 4314: '4314', 4322: '4322', 4324: '4324', 4334: '4334', 5324: '5324', 20443: '20443', 100443: '#psi'}
# momList = [1, 2, 3, 4, 5, 6, 11, 13, 15, 21, 24, 111, 221, 223, 331, 333, 413, 423, 433, 445, 513, 523, 533, 543, 2212, 4312, 4314, 4322, 4324, 4334, 5324, 20443, 100443]
momList = [1, 2, 3, 4, 5, 6, 11, 13, 15, 21, 24, 111, 221, 223, 331, 333, 413, 423, 433, 513, 523, 533, 543, 2212, 100443]
nameList = [momRef[mom] for mom in momList] + ['other']
momDict = {entry: num for num, entry in enumerate(momList)}

# NOTE WARNING this is wrong, t.ph needs to be replaced by id (in gen list of matched photon)
def momDictFunc(t):
  try: momId = abs(t._gen_phMomPdg[t.ph])
  except: momId = -1
  try: return momDict[momId]
  except: return len(momList)

def closestRawJet(tree):
  dist = [deltaR(tree._jetEta[j], tree._phEta[tree.ph], tree._jetPhi[j], tree._phPhi[tree.ph]) for j in range(tree._nJets)]
  return dist.index(min(dist))

def rawJetDeltaR(tree):
  return min(deltaR(tree._jetEta[j], tree._phEta[tree.ph], tree._jetPhi[j], tree._phPhi[tree.ph]) for j in range(tree._nJets))

def jetNeutralHadronFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetNeutralHadronFraction[ind]

def jetChargedHadronFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetChargedHadronFraction[ind]

def jetNeutralEmFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetNeutralEmFraction[ind]

def jetChargedEmFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetChargedEmFraction[ind]

def jetHFHadronFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetHFHadronFraction[ind]

def jetHFEmFraction(c, ind):
  if ind < 0: return -9999.
  else: return c._jetHFEmFraction[ind]

def NoverCha(c):
  if c._phChargedIsolation[c.ph] > 0:
    return c._phNeutralHadronIsolation[c.ph]/c._phChargedIsolation[c.ph]
  else:
    return -0.9

def ChaOverN(c):
  if c._phNeutralHadronIsolation[c.ph] > 0:
    return c._phChargedIsolation[c.ph]/c._phNeutralHadronIsolation[c.ph]
  else:
    return -0.9

def leptonPt(tree, index):
  return tree._lPtCorr[index]

def leptonE(tree, index):
  return tree._lECorr[index]

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  # log.info("got vect")
  return vector


# NOTE temp
def nearestZ(tree):
  distmll  = abs(91.1876 - tree.mll)
  distmllg = abs(91.1876 - tree.mllg)
  if distmll < distmllg:
    return 0.
  else:
    return 1.

# NOTE always nominal values
def leptonPt(tree, index):
  return tree._lPtCorr[index]

def leptonE(tree, index):
  return tree._lECorr[index]

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  # log.info("got vect")
  return vector

def plphpt(tree):
  try: return c._pl_phPt[0]
  except: return -99.


def kickUnder(under, threshold, val):
  if val > threshold: return under - 1.
  else:               return val

def theta(eta):
  return 2.*numpy.arctan(numpy.e**(-1* eta))

def angle(theta1, theta2, phi1, phi2):
  return ((theta1-theta2)**2. + deltaPhi(phi1,phi2)**2.)**0.5

def Zpt(c):
  first  = getLorentzVector(leptonPt(c, c.l1), c._lEta[c.l1], c._lPhi[c.l1], leptonE(c, c.l1))
  second = getLorentzVector(leptonPt(c, c.l2), c._lEta[c.l2], c._lPhi[c.l2], leptonE(c, c.l2))
  return (first+second).Pt()

def plZpt(c):
  first  = getLorentzVector(c.PLl1_pt, c._pl_lEta[c.PLl1], c._pl_lPhi[c.PLl1], c._pl_lE[c.PLl1])
  second = getLorentzVector(c.PLl2_pt, c._pl_lEta[c.PLl2], c._pl_lPhi[c.PLl2], c._pl_lE[c.PLl2])
  return (first+second).Pt()
