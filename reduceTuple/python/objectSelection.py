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
  if   tree.eleMva:  return electronMva(tree, index)
  elif tree.hnTight: return tree._lHNTight[index]
  else:              return tree._lPOGTight[index]

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
  if abs(tree._phEta[index]) > 2.5:                    return False
  if tree._phPt[index] < 15:                           return False
  if not n.isMuMu and tree._phHasPixelSeed[index]:     return False # For dimuon channel
  if n.isMuMu and not tree._phPassElectronVeto[index]: return False # For other channels
  for i in ([] if tree.QCD else [n.l1, n.l2]):
    if deltaR(tree._lEta[i], tree._phEta[index], tree._lPhi[i], tree._phPhi[index]) < 0.1: return False
  if tree.photonCutBased:       return photonCutBasedReduced(tree, index)
  if tree.photonMva:            return tree._phMva[index] > 0.20
  return True

def selectPhoton(t, n, doCut):
  t.photons = [p for p in range(ord(t._nPh)) if photonSelector(t, p, n)]
  if len(t.photons): n.ph = t.photons[0]
  return (len(t.photons) > 0 or not doCut)


#
# Add invariant masses to the tree
#
def makeInvariantMasses(t, n):
  first  = ROOT.TLorentzVector()
  second = ROOT.TLorentzVector()
  first.SetPtEtaPhiE( t._lPt[n.l1], t._lEta[n.l1], t._lPhi[n.l1], t._lE[n.l1])
  second.SetPtEtaPhiE(t._lPt[n.l2], t._lEta[n.l2], t._lPhi[n.l2], t._lE[n.l2])
  n.mll = (first+second).M()

  if len(t.photons) > 0:
    photon = ROOT.TLorentzVector()
    photon.SetPtEtaPhiE(t._phPt[n.ph], t._phEta[n.ph], t._phPhi[n.ph], t._phE[n.ph])
    n.mllg = (first+second+photon).M()
    n.ml1g = (first+photon).M()
    n.ml2g = (second+photon).M()
  else :
    n.mllg = -1
    n.ml1g = -1
    n.ml2g = -1


#
# Jets (filter those within 0.4 from lepton or photon)
#
def isGoodJet(tree, index):
  if not tree._jetId[index]: return False
  for ph in tree.photons:
    if deltaR(tree._jetEta[index], tree._phEta[ph], tree._jetPhi[index], tree._phPhi[ph]) < 0.1: return False
  for lep in ([] if tree.QCD else tree.leptons):
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
  t.bjets          = [i for i in t.jets         if t._jetCsvV2[i] > btagWP]
  bjets_JECUp      = [i for i in t.jets_JECUp   if t._jetCsvV2[i] > btagWP]
  bjets_JECDown    = [i for i in t.jets_JECDown if t._jetCsvV2[i] > btagWP]
  bjets_JERUp      = [i for i in t.jets_JERUp   if t._jetCsvV2[i] > btagWP]
  bjets_JERDown    = [i for i in t.jets_JERDown if t._jetCsvV2[i] > btagWP]
  n.nbjets         = len(t.bjets)
  n.nbjets_JECUp   = len(bjets_JECUp)
  n.nbjets_JECDown = len(bjets_JECDown)
  n.nbjets_JERUp   = len(bjets_JERUp)
  n.nbjets_JERDown = len(bjets_JERDown)
  btagWP = 0.6324
  t.dbjets         = [i for i in t.jets         if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > btagWP]
  dbjets_JECUp     = [i for i in t.jets_JECUp   if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > btagWP]
  dbjets_JECDown   = [i for i in t.jets_JECDown if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > btagWP]
  dbjets_JERUp     = [i for i in t.jets_JERUp   if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > btagWP]
  dbjets_JERDown   = [i for i in t.jets_JERDown if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > btagWP]
  n.dbjets         = len(t.dbjets)
  n.dbjets_JECUp   = len(dbjets_JECUp)
  n.dbjets_JECDown = len(dbjets_JECDown)
  n.dbjets_JERUp   = len(dbjets_JERUp)
  n.dbjets_JERDown = len(dbjets_JERDown)



#
# delta R
#
def makeDeltaR(t, n):
  if len(t.photons) > 0:
    n.phL1DeltaR  = deltaR(t._lEta[n.l1], t._phEta[n.ph], t._lPhi[n.l1], t._phPhi[n.ph])
    n.phL2DeltaR  = deltaR(t._lEta[n.l2], t._phEta[n.ph], t._lPhi[n.l2], t._phPhi[n.ph])
    n.phJetDeltaR = min([deltaR(t._jetEta[j], t._phEta[n.ph], t._jetPhi[j], t._phPhi[n.ph]) for j in t.jets] + [999])
  else:
    n.phL1DeltaR  = -1
    n.phL2DeltaR  = -1
    n.phJetDeltaR = -1
