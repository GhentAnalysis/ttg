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
  if tree._lEta[index] < 0.8: return tree._lElectronMva[index] > (0.941 if tree.eleMvaTight else 0.837)
  else:                       return tree._lElectronMva[index] > (0.899 if tree.eleMvaTight else 0.715)

def electronSelector(tree, index):
  for i in xrange(ord(tree._nMu)): # cleaning electrons around muons
    if not looseLeptonSelector(tree, i): continue
    if deltaR(tree._lEta[i], tree._lEta[index], tree._lPhi[i], tree._lPhi[index]) < 0.02: return False
  if tree.eleMva: return electronMva(tree, index)
  else:           return tree._lPOGTight[index]

def muonSelector(tree, index):
  return tree._lPOGMedium[index]

def leptonSelector(tree, index):
  if tree._relIso[index] > 0.12:       return False
  if tree._lPt[index] < 20:            return False
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
  t.leptons         = [i for i in xrange(ord(t._nLight)) if leptonSelector(t, i)]
  ptAndIndex        = [(t._lPt[i], i) for i in t.leptons]
  if len(ptAndIndex) < 2: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.l2              = ptAndIndex[1][1]
  n.isEE            = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 0
  n.isEMu           = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 1
  n.isMuMu          = (t._lFlavor[n.l1] + t._lFlavor[n.l2]) == 2 # note: assuming to taus are kept
  n.isOS            = t._lCharge[n.l1] != t._lCharge[n.l2]
  n.looseLeptonVeto = len([i for i in xrange(ord(t._nLight)) if looseLeptonSelector(t, i)]) <= 2
  return t._lPt[n.l1] > 25 and n.isOS


def photonCutBasedReduced(c, index):
  pt = c._phPt[index]
  if abs(c._phEtaSC[index]) < 1.479:
    if c._phHadronicOverEm[index] >  0.0396: return False
    if c._phNeutralHadronIsolation[index] > 2.725+0.0148*pt+0.000017*pt*pt: return False
    if c._phPhotonIsolation[index] >  2.571+0.0047*pt : return False
  else:
    if c._phHadronicOverEm[index] > 0.0219: return False
    if c._phNeutralHadronIsolation[index] >  1.715+0.0163*pt+0.000014*pt*pt : return False
    if c._phPhotonIsolation[index] >  3.863+0.0034*pt: return False
  return True




#
# Select photon with pt > 20
#
def photonSelector(tree, index, n):
  if abs(tree._phEta[index]) > 2.5:                   return False
  if tree._phPt[index] < 15:                          return False
  if tree._phHasPixelSeed[index]:                     return False  # actually only one of the two recommended
  if not tree._phPassElectronVeto[index]:             return False
  for i in [n.l1, n.l2]:
    if deltaR(tree._lEta[i], tree._phEta[index], tree._lPhi[i], tree._phPhi[index]) < 0.1: return False
  if tree.photonCutBasedTight:  return tree._phCutBasedTight[index]
  if tree.photonCutBased:       return photonCutBasedReduced(tree, index)
  if tree.photonMva:            return tree._phMva[index] > 0.20
  return True

def selectPhoton(t, n):
  t.photons = [p for p in range(ord(t._nPh)) if photonSelector(t, p, n)]
  if not len(t.photons): return False
  n.ph = t.photons[0]
  return True


#
# Find matched photon, similar as described in AN-2015/165 (but not perfectly, the text is a bit confusing, and we do not have all gen particles stored)
#
def matchPhoton(t, n):
  match = None
  for i in range(ord(t._gen_nPh)):
    if deltaR(t._gen_phEta[i], t._phEta[n.ph], t._gen_phPhi[i], t._phPhi[n.ph]) > 0.01: continue
    if abs(t._gen_phEta[i] - t._phEta[n.ph]) > 0.005: continue
    if abs(t._gen_phPt[i]-t._phPt[n.ph]) > 0.1*t._gen_phPt[i]: continue
    match = i
    break
  n.matchedGenPh = i if match else -1

  match = None
  for i in range(ord(t._gen_nL)):
    if t._gen_lFlavor[i] > 0: continue
    if deltaR(t._gen_lEta[i], t._phEta[n.ph], t._gen_lPhi[i], t._phPhi[n.ph]) > 0.04: continue
    if abs(t._gen_lEta[i] - t._phEta[n.ph]) > 0.005: continue
    if abs(t._gen_lPt[i]-t._phPt[n.ph]) > 0.1*t._gen_lPt[i]: continue
    match = i
    break
  n.matchedGenEle = i if match else -1



#
# Add invariant masses to the tree
# 
def makeInvariantMasses(t, n):
  first  = ROOT.TLorentzVector()
  second = ROOT.TLorentzVector()
  first.SetPtEtaPhiE( t._lPt[n.l1], t._lEta[n.l1], t._lPhi[n.l1], t._lE[n.l1])
  second.SetPtEtaPhiE(t._lPt[n.l2], t._lEta[n.l2], t._lPhi[n.l2], t._lE[n.l2])
  n.mll = (first+second).M()
  photon = ROOT.TLorentzVector()
  photon.SetPtEtaPhiE(t._phPt[n.ph], t._phEta[n.ph], t._phPhi[n.ph], t._phE[n.ph])
  n.mllg = (first+second+photon).M()
  n.ml1g = (first+photon).M()
  n.ml2g = (second+photon).M()


#
# Jets (filter those within 0.4 from lepton or photon)
#
def isGoodJet(tree, index):
  if not tree._jetId[index]: return False
  for ph in tree.photons:
    if deltaR(tree._jetEta[index], tree._phEta[ph], tree._jetPhi[index], tree._phPhi[ph]) < 0.1: return False
  for lep in tree.leptons:
    if deltaR(tree._jetEta[index], tree._lEta[lep], tree._jetPhi[index], tree._lPhi[lep]) < 0.4: return False
  return True

def goodJets(t, n):
  allGoodJets    = [i for i in xrange(ord(t._nJets)) if isGoodJet(t, i)]
  t.jets         = [i for i in allGoodJets if t._jetPt[i] > 30]
  t.jets_JECUp   = [i for i in allGoodJets if t._jetPt_JECUp[i] > 30]
  t.jets_JECDown = [i for i in allGoodJets if t._jetPt_JECDown[i] > 30]
  t.jets_JERUp   = [i for i in allGoodJets if t._jetPt_JERUp[i] > 30]
  t.jets_JERDown = [i for i in allGoodJets if t._jetPt_JERDown[i] > 30]
  n.njets         = len(t.jets)
  n.njets_JECUp   = len(t.jets_JECUp)
  n.njets_JECDown = len(t.jets_JECDown)
  n.njets_JERUp   = len(t.jets_JERUp)
  n.njets_JERDown = len(t.jets_JERDown)
  n.j1    = t.jets[0] if n.njets > 0 else -1
  n.j2    = t.jets[1] if n.njets > 1 else -1
      
def bJets(t, n):
  btagWP = 0.8484
  bjets            = [i for i in t.jets         if t._jetCsvV2[i] > btagWP]
  bjets_JECUp      = [i for i in t.jets_JECUp   if t._jetCsvV2[i] > btagWP]
  bjets_JECDown    = [i for i in t.jets_JECDown if t._jetCsvV2[i] > btagWP]
  bjets_JERUp      = [i for i in t.jets_JECUp   if t._jetCsvV2[i] > btagWP]
  bjets_JERDown    = [i for i in t.jets_JECDown if t._jetCsvV2[i] > btagWP]
  n.nbjets         = len(bjets)
  n.nbjets_JECUp   = len(bjets_JECUp)
  n.nbjets_JECDown = len(bjets_JECDown)
  n.nbjets_JERUp   = len(bjets_JERUp)
  n.nbjets_JERDown = len(bjets_JERDown)


#
# delta R
#
def makeDeltaR(t, n):
  n.phL1DeltaR  = deltaR(t._lEta[n.l1], t._phEta[n.ph], t._lPhi[n.l1], t._phPhi[n.ph])
  n.phL2DeltaR  = deltaR(t._lEta[n.l2], t._phEta[n.ph], t._lPhi[n.l2], t._phPhi[n.ph])
  n.phJetDeltaR = min([deltaR(t._jetEta[j], t._phEta[n.ph], t._jetPhi[j], t._phPhi[n.ph]) for j in t.jets] + [999])
