from ttg.tools.logger import getLogger
log = getLogger()

#
# All functions to select objects, as well as some functions which add new variables based on the selected objects to the tree
#

from math import sqrt,pi
import ROOT

#
# Helper functions
#
def deltaPhi(phi1, phi2):
  dphi = phi2-phi1
  if dphi > pi:   dphi -= 2.0*pi
  if dphi <= -pi: dphi += 2.0*pi
  return abs(dphi)

def deltaR(eta1, eta2, phi1, phi2):
  return sqrt(deltaPhi(phi1, phi2)**2 + (eta1-eta2)**2)

def slidingCut(pt, low, high):
  slope = (high - low)/10.;
  return min(low, max(high, low + slope*(pt-15)))

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  return vector

#
# Individual lepton selector
#
def looseLeptonSelector(tree, index):
  if tree._lFlavor[index] == 2:        return False
  if tree._relIso[index] > 0.4:        return False
  if tree._lPt[index] < 15:            return False
  if abs(tree._lEta[index]) > 2.4:     return False
  if abs(tree._3dIPSig[index]) > 4:    return False
  if abs(tree._dxy[index]) > 0.05:     return False
  if abs(tree._dz[index]) > 0.1:       return False
  return tree._lPOGVeto[index]


def electronMva(tree, index):
  if not tree._lElectronPassEmu[index]: return False
  if tree._lEta[index] < 0.8: return tree._lElectronMva[index] > (0.941 if tree.eleMvaTight else 0.837)
  else:                       return tree._lElectronMva[index] > (0.899 if tree.eleMvaTight else 0.715)

def electronSusyLoose(tree, index):
  if not tree._lElectronPassEmu[index]: return False
  if(abs(tree._lEta[index]) < 0.8):     return tree._lElectronMva[index] > slidingCut(tree._lPt[index], -0.48, -0.85)
  elif(abs(tree._lEta[index]) < 1.479): return tree._lElectronMva[index] > slidingCut(tree._lPt[index], -0.67, -0.91)
  else:                                 return tree._lElectronMva[index] > slidingCut(tree._lPt[index], -0.49, -0.83)

def electronSelector(tree, index):
  for i in xrange(ord(tree._nMu)): # cleaning electrons around muons
    if not looseLeptonSelector(tree, i): continue
    if deltaR(tree._lEta[i], tree._lEta[index], tree._lPhi[i], tree._lPhi[index]) < 0.02: return False
  if   tree.eleMva:    return electronMva(tree, index)
  elif tree.cbVeto:    return tree._lPOGVeto[index]
  elif tree.cbLoose:   return tree._lPOGLoose[index]
  elif tree.cbMedium:  return tree._lPOGMedium[index]
  elif tree.susyLoose: return electronSusyLoose(tree, index)
  else:                return tree._lPOGTight[index]

def muonSelector(tree, index):
  return tree._lPOGMedium[index]

def leptonSelector(tree, index):
  if tree._relIso[index] > 0.12:       return False
  if tree._lPt[index] < 15:            return False
  if abs(tree._lEta[index]) > 2.4:     return False
  if abs(tree._3dIPSig[index]) > 4:    return False
  if abs(tree._dxy[index]) > 0.05:     return False
  if abs(tree._dz[index]) > 0.1:       return False
  if   tree._lFlavor[index] == 0:      return electronSelector(tree, index)
  elif tree._lFlavor[index] == 1:      return muonSelector(tree, index)
  else:                                return False


#
# Selects leptons passing the id and iso criteria, sorts them, and save their indices
# First lepton needs to pass pt > 25 GeV
#
def getSortKey(item): return item[0]

def select2l(t, n):
  ptAndIndex        = [(t._lPt[i], i) for i in t.leptons]
  if len(ptAndIndex) < 2: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.l2              = ptAndIndex[1][1]
  n.isEE            = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 0
  n.isEMu           = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 1
  n.isMuMu          = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 2 # note: assuming no taus are kept
  n.isOS            = t._lCharge[n.l1] != t._lCharge[n.l2]
  n.looseLeptonVeto = len([i for i in xrange(ord(t._nLight)) if looseLeptonSelector(t, i)]) <= 2
  return t._lPt[n.l1] > 25 and n.isOS


def select1l(t, n):
  ptAndIndex        = [(t._lPt[i], i) for i in t.leptons]
  if len(ptAndIndex) < 1: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.isE             = (t._lFlavor[n.l1] == 0)
  n.isMu            = (t._lFlavor[n.l1] == 1)
  n.looseLeptonVeto = len([i for i in xrange(ord(t._nLight)) if looseLeptonSelector(t, i)]) <= 1
  return True

def selectLeptons(t, n, minLeptons):
  t.leptons = [i for i in xrange(ord(t._nLight)) if leptonSelector(t, i)]
  if   minLeptons == 2: return select2l(t, n)
  elif minLeptons == 1: return select1l(t, n)
  elif minLeptons == 0: return True




#
# Photon selector
#
def photonCutBasedReduced(c, index):
  pt = c._phPt[index]
  if abs(c._phEtaSC[index]) < 1.479:
    if c._phHadronicOverEm[index] >  0.0396:                                return False
    if c._phNeutralHadronIsolation[index] > 2.725+0.0148*pt+0.000017*pt*pt: return False
    if c._phPhotonIsolation[index] >  2.571+0.0047*pt :                     return False
  else:
    if c._phHadronicOverEm[index] > 0.0219:                                   return False
    if c._phNeutralHadronIsolation[index] >  1.715+0.0163*pt+0.000014*pt*pt : return False
    if c._phPhotonIsolation[index] >  3.863+0.0034*pt:                        return False
  return True


def photonSelector(tree, index, n, pixelSeed, minLeptons):
  if abs(tree._phEta[index]) > 1.4442 and abs(tree._phEta[index]) < 1.566:      return False
  if abs(tree._phEta[index]) > 2.5:                                             return False
  if tree._phPt[index] < 15:                                                    return False
  if pixelSeed and tree._phHasPixelSeed[index]:                                 return False
  if not pixelSeed and not tree._phPassElectronVeto[index]:                     return False
  for i in ([] if minLeptons == 0 else ([n.l1] if minLeptons==1 else [n.l1, n.l2])):
    if deltaR(tree._lEta[i], tree._phEta[index], tree._lPhi[i], tree._phPhi[index]) < 0.1: return False
  if tree.photonCutBased:       return photonCutBasedReduced(tree, index)
  if tree.photonMva:            return tree._phMva[index] > 0.20
  return True

def selectPhotons(t, n, doCut, minLeptons):
  if   minLeptons == 2 and n.isMuMu: pixelSeed = False
  elif minLeptons == 1 and n.isMu:   pixelSeed = False
  else:                              pixelSeed = True
  t.photons  = [p for p in range(ord(t._nPh)) if photonSelector(t, p, n, pixelSeed, minLeptons)]
  n.nphotons = sum([t._phCutBasedMedium[i] for i in t.photons])
  if len(t.photons): n.ph = t.photons[0]
  return (len(t.photons) > 0 or not doCut)


#
# Add invariant masses to the tree
#
def makeInvariantMasses(t, n):
  first  = getLorentzVector(t._lPt[n.l1], t._lEta[n.l1], t._lPhi[n.l1], t._lE[n.l1])     if len(t.leptons) > 0 else None
  second = getLorentzVector(t._lPt[n.l2], t._lEta[n.l2], t._lPhi[n.l2], t._lE[n.l2])     if len(t.leptons) > 1 else None
  photon = getLorentzVector(t._phPt[n.ph], t._phEta[n.ph], t._phPhi[n.ph], t._phE[n.ph]) if len(t.photons) > 0 else None

  n.mll  = (first+second).M()        if first and second else -1
  n.mllg = (first+second+photon).M() if first and second and photon else -1
  n.ml1g = (first+photon).M()        if first and photon else -1
  n.ml2g = (second+photon).M()       if second and photon else -1


#
# Jets (filter those within 0.4 from lepton or 0.1 from photon)
#
def isGoodJet(tree, index):
  if not tree._jetId[index]:        return False
  if not tree._jetEta[index] < 2.4: return False
  for ph in tree.photons:
    if deltaR(tree._jetEta[index], tree._phEta[ph], tree._jetPhi[index], tree._phPhi[ph]) < 0.1: return False
  for lep in tree.leptons:
    if deltaR(tree._jetEta[index], tree._lEta[lep], tree._jetPhi[index], tree._lPhi[lep]) < 0.4: return False
  return True

def goodJets(t, n):
  allGoodJets = [i for i in xrange(ord(t._nJets)) if isGoodJet(t, i)]
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'jets'+var,  [i for i in allGoodJets if getattr(t, '_jetPt'+var)[i] > 30])
    setattr(n, 'njets'+var, len(getattr(t, 'jets'+var)))
    setattr(n, 'j1'+var,    getattr(t, 'jets'+var)[0] if getattr(n, 'njets'+var) > 0 else -1)
    setattr(n, 'j2'+var,    getattr(t, 'jets'+var)[1] if getattr(n, 'njets'+var) > 1 else -1)

def bJets(t, n):
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'bjets'+var,  [i for i in getattr(t, 'jets'+var) if t._jetCsvV2[i] > 0.8484])
    setattr(n, 'nbjets'+var, len(getattr(t, 'bjets'+var)))
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'dbjets'+var,  [i for i in getattr(t, 'jets'+var) if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > 0.6324])
    setattr(n, 'ndbjets'+var, len(getattr(t, 'dbjets'+var)))


#
# delta R
#
def makeDeltaR(t, n):
  n.phL1DeltaR  = deltaR(t._lEta[n.l1], t._phEta[n.ph], t._lPhi[n.l1], t._phPhi[n.ph])                              if len(t.photons) > 0 and len(t.leptons) > 0 else -1
  n.phL2DeltaR  = deltaR(t._lEta[n.l2], t._phEta[n.ph], t._lPhi[n.l2], t._phPhi[n.ph])                              if len(t.photons) > 0 and len(t.leptons) > 1 else -1
  n.phJetDeltaR = min([deltaR(t._jetEta[j], t._phEta[n.ph], t._jetPhi[j], t._phPhi[n.ph]) for j in t.jets] + [999]) if len(t.photons) > 0 else -1
