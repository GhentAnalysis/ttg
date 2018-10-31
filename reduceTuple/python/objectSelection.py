from ttg.tools.logger  import getLogger
from ttg.tools.helpers import deltaR
import ROOT
log = getLogger()

#
# All functions to select objects, as well as some functions which add new variables based on the selected objects to the tree
#

#
# Set ID options on chain using type string
#
def setIDSelection(c, reducedTupleType):
  c.doPhotonCut         = reducedTupleType.count('pho')
  c.photonCutBased      = reducedTupleType.count('phoCB')
  c.photonMva           = reducedTupleType.count('photonMva')
  c.eleMva              = reducedTupleType.count('eleMva')
  c.cbLoose             = reducedTupleType.count('eleCBLoose')
  c.cbMedium            = reducedTupleType.count('eleCBMedium')
  c.cbVeto              = reducedTupleType.count('eleCBVeto')
  c.susyLoose           = reducedTupleType.count('eleSusyLoose')
  c.noPixelSeedVeto     = reducedTupleType.count('noPixelSeedVeto')
  c.jetPtCut            = 40 if reducedTupleType.count('jetPt40') else 30


#
# Helper functions
#
def slidingCut(pt, low, high):
  slope = (high - low)/10.
  return min(low, max(high, low + slope*(pt-15)))

def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  return vector

#
# Individual lepton selector
#
def leptonPt(tree, index):
  if tree._lFlavor[index]: return tree._lPt[index]
  else:                    return tree._lPtCorr[index]

def leptonE(tree, index):
  if tree._lFlavor[index]: return tree._lE[index]
  else:                    return tree._lECorr[index]


def looseLeptonSelector(tree, index):
  if tree._lFlavor[index] == 2:        return False
  if tree._relIso[index] > 0.4:        return False
  if leptonPt(tree, index) < 15:       return False
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
  if(abs(tree._lEta[index]) < 0.8):     return tree._lElectronMva[index] > slidingCut(tree._lPtCorr[index], -0.48, -0.85)
  elif(abs(tree._lEta[index]) < 1.479): return tree._lElectronMva[index] > slidingCut(tree._lPtCorr[index], -0.67, -0.91)
  else:                                 return tree._lElectronMva[index] > slidingCut(tree._lPtCorr[index], -0.49, -0.83)

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
  if leptonPt(tree, index) < 15:       return False
  if tree._relIso[index] > 0.12:       return False
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
  ptAndIndex        = [(leptonPt(t, i), i) for i in t.leptons]
  if len(ptAndIndex) < 2: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.l2              = ptAndIndex[1][1]
  n.l1_pt           = ptAndIndex[0][0]
  n.l2_pt           = ptAndIndex[1][0]
  n.isEE            = (t._lFlavor[n.l1]==0 and t._lFlavor[n.l2]==0)
  n.isEMu           = (t._lFlavor[n.l1]==0 and t._lFlavor[n.l2]==1) or (t._lFlavor[n.l1]==1 and t._lFlavor[n.l2]==0)
  n.isMuMu          = (t._lFlavor[n.l1]==1 and t._lFlavor[n.l2]==1)
  n.isOS            = t._lCharge[n.l1] != t._lCharge[n.l2]
  n.looseLeptonVeto = len([i for i in xrange(ord(t._nLight)) if looseLeptonSelector(t, i)]) <= 2
  return leptonPt(t, n.l1) > 25 and n.isOS


def select1l(t, n):
  ptAndIndex        = [(leptonPt(t, i), i) for i in t.leptons]
  if len(ptAndIndex) < 1: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.l1_pt           = ptAndIndex[0][0]
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
  pt = c._phPtCorr[index]
  if abs(c._phEtaSC[index]) < 1.479:
    if c._phHadronicOverEm[index] >  0.0396:                                return False
    if c._phNeutralHadronIsolation[index] > 2.725+0.0148*pt+0.000017*pt*pt: return False
    if c._phPhotonIsolation[index] >  2.571+0.0047*pt :                     return False
  else:
    if c._phHadronicOverEm[index] > 0.0219:                                   return False
    if c._phNeutralHadronIsolation[index] >  1.715+0.0163*pt+0.000014*pt*pt : return False
    if c._phPhotonIsolation[index] >  3.863+0.0034*pt:                        return False
  return True


def photonSelector(tree, index, n, minLeptons):
  if abs(tree._phEta[index]) > 1.4442 and abs(tree._phEta[index]) < 1.566:      return False
  if abs(tree._phEta[index]) > 2.5:                                             return False
  if tree._phPtCorr[index] < 15:                                                return False
  if tree._phHasPixelSeed[index] and not tree.noPixelSeedVeto:                  return False
  if not tree._phPassElectronVeto[index]:                                       return False
  for i in ([] if minLeptons == 0 else ([n.l1] if minLeptons==1 else [n.l1, n.l2])):
    if deltaR(tree._lEta[i], tree._phEta[index], tree._lPhi[i], tree._phPhi[index]) < 0.1: return False
  if tree.photonCutBased:       return photonCutBasedReduced(tree, index)
  if tree.photonMva:            return tree._phMva[index] > 0.20
  return True

def addGenPhotonInfo(t, n, index):
  n.genPhDeltaR        = 99
  n.genPhMinDeltaR     = 99
  n.genPhPassParentage = False
  n.genPhPt            = -1
  n.genPhEta           = 99
  for i in range(ord(t._gen_nPh)):
    myDeltaR = deltaR(t._phEta[index], t._gen_phEta[i], t._phPhi[index], t._gen_phPhi[i])
    if myDeltaR < n.genPhDeltaR:
      n.genPhDeltaR        = myDeltaR
      n.genPhPassParentage = t._gen_phPassParentage[i]
      n.genPhMinDeltaR     = t._gen_phMinDeltaR[i]
      n.genPhRelPt         = (t._gen_phPt[i]-t._phPt[n.ph])/t._gen_phPt[i]
      n.genPhPt            = t._gen_phPt[i]
      n.genPhEta           = t._gen_phEta[i]

def selectPhotons(t, n, minLeptons, isData):
  t.photons  = [p for p in range(ord(t._nPh)) if photonSelector(t, p, n, minLeptons)]
  n.nphotons = sum([t._phCutBasedMedium[i] for i in t.photons])
  if len(t.photons):
    n.ph    = t.photons[0]
    n.ph_pt = t._phPtCorr[n.ph]
    if not isData: addGenPhotonInfo(t, n, n.ph)
  return (len(t.photons) > 0 or not t.doPhotonCut)


#
# Add invariant masses to the tree
#
def makeInvariantMasses(t, n):
  first  = getLorentzVector(leptonPt(t, n.l1), t._lEta[n.l1], t._lPhi[n.l1], leptonE(t, n.l1))   if len(t.leptons) > 0 else None
  second = getLorentzVector(leptonPt(t, n.l2), t._lEta[n.l2], t._lPhi[n.l2], leptonE(t, n.l2))   if len(t.leptons) > 1 else None
  photon = getLorentzVector(t._phPtCorr[n.ph], t._phEta[n.ph], t._phPhi[n.ph], t._phECorr[n.ph]) if len(t.photons) > 0 else None

  n.mll  = (first+second).M()        if first and second else -1
  n.mllg = (first+second+photon).M() if first and second and photon else -1
  n.ml1g = (first+photon).M()        if first and photon else -1
  n.ml2g = (second+photon).M()       if second and photon else -1


#
# Jets (filter those within 0.4 from lepton or 0.1 from photon)
#
def isGoodJet(tree, index):
  if not tree._jetId[index]:             return False
  if not abs(tree._jetEta[index]) < 2.4: return False
  for ph in [ph for ph in tree.photons if tree._phCutBasedMedium[ph]]:
    if deltaR(tree._jetEta[index], tree._phEta[ph], tree._jetPhi[index], tree._phPhi[ph]) < 0.1: return False
  for lep in tree.leptons:
    if deltaR(tree._jetEta[index], tree._lEta[lep], tree._jetPhi[index], tree._lPhi[lep]) < 0.4: return False
  return True

def goodJets(t, n):
  allGoodJets = [i for i in xrange(ord(t._nJets)) if isGoodJet(t, i)]
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'jets'+var,  [i for i in allGoodJets if getattr(t, '_jetPt'+var)[i] > t.jetPtCut])
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
  n.l1JetDeltaR = min([deltaR(t._jetEta[j], t._lEta[n.l1], t._jetPhi[j], t._lPhi[n.l1]) for j in t.jets] + [999])  if len(t.leptons) > 0 else -1
  n.l2JetDeltaR = min([deltaR(t._jetEta[j], t._lEta[n.l2], t._jetPhi[j], t._lPhi[n.l2]) for j in t.jets] + [999])  if len(t.leptons) > 1 else -1
