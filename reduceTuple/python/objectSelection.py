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
# Set ID options on chain using type string
#
def setIDSelection(c, reducedTupleType):
  c.doPhotonCut         = reducedTupleType.count('pho')
  c.photonCutBased      = reducedTupleType.count('phoCB')
  c.noPixelSeedVeto     = reducedTupleType.count('noPixelSeedVeto')
  c.jetPtCut            = 25 if reducedTupleType.count('jetPt25') else 30

#
# Helper functions
#
def getLorentzVector(pt, eta, phi, e):
  vector = ROOT.TLorentzVector()
  vector.SetPtEtaPhiE(pt, eta, phi, e)
  return vector

#
# Individual lepton selector
#
def leptonPt(tree, index):
  if tree._lFlavor[index]: return getattr(tree, '_lPt'+tree.muvar)[index]
  else:                    return getattr(tree, '_lPt'+tree.egvar)[index]

def leptonE(tree, index):
  if tree._lFlavor[index]: return getattr(tree, '_lE'+tree.muvar)[index]
  else:                    return getattr(tree, '_lE'+tree.egvar)[index]

def photonPt(tree, index): return getattr(tree, '_phPt'+tree.egvar)[index]
def photonE(tree, index):  return getattr(tree, '_phE'+tree.egvar)[index]



def baseElectronSelector(tree, index):
  if not abs(tree._dxy[index]) < 0.05:                  return False
  if not abs(tree._dz[index]) < 0.1:                    return False
  if not abs(tree._3dIPSig[index]) < 8:                 return False
  if not tree._lElectronMissingHits[index] < 2:         return False
  if not tree._miniIso[index] < 0.4:                    return False
  if not tree._lElectronPassConvVeto[index]:            return False
  return True

def baseMuonSelector(tree, index):
  if not tree._lPOGMedium[index]:                       return False
  if not abs(tree._dxy[index]) < 0.05:                  return False
  if not abs(tree._dz[index]) < 0.1:                    return False
  if not abs(tree._3dIPSig[index]) < 8:                 return False
  if not tree._miniIso[index] < 0.4:                    return False
  return True

def electronSelector(tree, index):
  if not baseElectronSelector(tree, index):             return False
  for i in xrange(tree._nMu): # cleaning electrons around muons
    if not (tree._lFlavor[i] == 1 and baseMuonSelector(tree, i)): continue
    if deltaR(tree._lEta[i], tree._lEta[index], tree._lPhi[i], tree._lPhi[index]) < 0.02: return False
  if 1.4442 < abs(tree._lEtaSC[index]) < 1.566:         return False
  return tree._leptonMvaTOP[index] > -.55

def muonSelector(tree, index):
  if not baseMuonSelector(tree, index):                 return False
  return tree._leptonMvaTOP[index] > -0.45

def leptonSelector(tree, index):
  if leptonPt(tree, index) < 15:       return False
  if abs(tree._lEta[index]) > 2.4:     return False
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
  return leptonPt(t, n.l1) > 25 and n.isOS


def select1l(t, n):
  ptAndIndex        = [(leptonPt(t, i), i) for i in t.leptons]
  if len(ptAndIndex) < 1: return False

  ptAndIndex.sort(reverse=True, key=getSortKey)
  n.l1              = ptAndIndex[0][1]
  n.l1_pt           = ptAndIndex[0][0]
  n.isE             = (t._lFlavor[n.l1] == 0)
  n.isMu            = (t._lFlavor[n.l1] == 1)
  return True

def selectLeptons(t, n, minLeptons):
  t.leptons = [i for i in xrange(t._nLight) if leptonSelector(t, i)]
  if   minLeptons == 2: return select2l(t, n)
  elif minLeptons == 1: return select1l(t, n)
  elif minLeptons == 0: return True

#
# Photon selector with reduced cut based ID Fall17V2 (i.e. leaving out chgIso and sigmaIetaIeta cuts)
#
def photonCutBasedReduced(c, index):
  # always use nominal here, since the full id used later on uses nominal pt
  pt = c._phPtCorr[index]
  if abs(c._phEtaSC[index]) < 1.479:
    if c._phHadTowOverEm[index] > 0.02197:                                         return False
    if c._phNeutralHadronIsolation[index] > 1.189 + 0.01512*pt + 0.00002259*pt*pt: return False
    if c._phPhotonIsolation[index] > 2.08 + 0.004017*pt:                           return False
  else:
    if c._phHadTowOverEm[index] > 0.0326:                                          return False
    if c._phNeutralHadronIsolation[index] > 2.718 + 0.0117*pt + 0.000023*pt*pt:    return False
    if c._phPhotonIsolation[index] > 3.867 + 0.0037*pt:                            return False
  return True


def photonSelector(tree, index, n, minLeptons):
  if abs(tree._phEta[index]) > 1.4442 and abs(tree._phEta[index]) < 1.566:      return False
  if abs(tree._phEta[index]) > 2.5:                                             return False
  if photonPt(tree, index) < 20:                                                return False
  if tree._phHasPixelSeed[index] and not tree.noPixelSeedVeto:                  return False
  for i in ([] if minLeptons == 0 else ([n.l1] if minLeptons==1 else [n.l1, n.l2])):
    if deltaR(tree._lEta[i], tree._phEta[index], tree._lPhi[i], tree._phPhi[index]) < 0.4: return False
  if tree.photonCutBased:       return photonCutBasedReduced(tree, index)
  return True

def addGenPhotonInfo(t, n, index):
  n.genPhDeltaR        = 99
  n.genPhMinDeltaR     = 99
  n.genPhPassParentage = False
  n.genPhPt            = -1
  n.genPhEta           = 99
  n.genPhMomPdg        = -9999
  for i in range(t._gen_nPh):
    myDeltaR = deltaR(t._phEta[index], t._gen_phEta[i], t._phPhi[index], t._gen_phPhi[i])
    if myDeltaR < n.genPhDeltaR:
      n.genPhDeltaR        = myDeltaR
      n.genPhPassParentage = t._gen_phPassParentage[i]
      n.genPhMinDeltaR     = t._gen_phMinDeltaR[i]
      n.genPhRelPt         = (t._gen_phPt[i]-photonPt(t, n.ph))/t._gen_phPt[i]
      n.genPhPt            = t._gen_phPt[i]
      n.genPhEta           = t._gen_phEta[i]
      n.genPhMomPdg        = t._gen_phMomPdg[i]

  try:
    n.lhePhPt = t._lhePt[[i for i in t._lhePdgId].index(22)]
  except:
    n.lhePhPt = 0.

def selectPhotons(t, n, minLeptons, isData):
  t.photons  = [p for p in range(t._nPh) if photonSelector(t, p, n, minLeptons)]
  n.nphotons = sum([t._phCutBasedMedium[i] for i in t.photons])
  # NOTE maybe keep saving this value or just stor bot nloose and ntight?
  # n.nphotons = len(t.photons)
  if len(t.photons):
    n.ph    = t.photons[0]
    n.ph_pt = photonPt(t, n.ph)
    if not isData: addGenPhotonInfo(t, n, n.ph)
  # NOTE point of dispute: exact way to require 1 photon
  return (len(t.photons) == 1 or not t.doPhotonCut)
  # return len(t.photons) > 0
  # return ((len(t.photons) > 0 and not n.nphotons > 1) or not t.doPhotonCut)


#
# Add invariant masses to the tree
#
def makeInvariantMasses(t, n):
  first  = getLorentzVector(leptonPt(t, n.l1), t._lEta[n.l1], t._lPhi[n.l1], leptonE(t, n.l1))   if len(t.leptons) > 0 else None
  second = getLorentzVector(leptonPt(t, n.l2), t._lEta[n.l2], t._lPhi[n.l2], leptonE(t, n.l2))   if len(t.leptons) > 1 else None
  photon = getLorentzVector(photonPt(t, n.ph), t._phEta[n.ph], t._phPhi[n.ph], photonE(t, n.ph)) if len(t.photons) > 0 else None

  n.mll  = (first+second).M()        if first and second else -1
  n.mllg = (first+second+photon).M() if first and second and photon else -1
  n.ml1g = (first+photon).M()        if first and photon else -1
  n.ml2g = (second+photon).M()       if second and photon else -1


#
# Jets (filter those within 0.4 from lepton or 0.1 from photon)
#
def isGoodJet(tree, n, index):
  if not tree._jetIsTight[index]:        return False
  if not abs(tree._jetEta[index]) < 2.4: return False
  if len(tree.photons) > 0 and tree.photonCutBased: #selected photon is necessarily CB (but not always CBfull)
    if deltaR(tree._jetEta[index], tree._phEta[n.ph], tree._jetPhi[index], tree._phPhi[n.ph]) < 0.1: return False
  
  for lep in tree.leptons:
    if deltaR(tree._jetEta[index], tree._lEta[lep], tree._jetPhi[index], tree._lPhi[lep]) < 0.4: return False
  return True

# Note that all cleared jet variables are smearedJet based, not sure if the should be renamed
def goodJets(t, n):
  allGoodJets = [i for i in xrange(t._nJets) if isGoodJet(t, n, i)]
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'jets'+var,  [i for i in allGoodJets if getattr(t, '_jetSmearedPt'+var)[i] > t.jetPtCut])
    setattr(n, 'njets'+var, len(getattr(t, 'jets'+var)))
    setattr(n, 'j1'+var, getattr(t, 'jets'+var)[0] if getattr(n, 'njets'+var) > 0 else -1)
    setattr(n, 'j2'+var, getattr(t, 'jets'+var)[1] if getattr(n, 'njets'+var) > 1 else -1)

def bJets(t, n):
  workingPoints = {'2016':0.6321, '2017':0.4941, '2018':0.4184}
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(t, 'dbjets'+var,  [i for i in getattr(t, 'jets'+var) if t._jetDeepCsv_b[i] + t._jetDeepCsv_bb[i] > workingPoints[t.year]])
    setattr(n, 'ndbjets'+var, len(getattr(t, 'dbjets'+var)))
    setattr(n, 'dbj1'+var, getattr(t, 'dbjets'+var)[0] if getattr(n, 'ndbjets'+var) > 0 else -1)
    setattr(n, 'dbj2'+var, getattr(t, 'dbjets'+var)[1] if getattr(n, 'ndbjets'+var) > 1 else -1)


#
# delta R
#
def makeDeltaR(t, n):
  n.phL1DeltaR   = deltaR(t._lEta[n.l1], t._phEta[n.ph], t._lPhi[n.l1], t._phPhi[n.ph]) if len(t.photons) > 0 and len(t.leptons) > 0 else -1
  n.phL2DeltaR   = deltaR(t._lEta[n.l2], t._phEta[n.ph], t._lPhi[n.l2], t._phPhi[n.ph]) if len(t.photons) > 0 and len(t.leptons) > 1 else -1
  for var in ['', '_JECUp', '_JECDown', '_JERUp', '_JERDown']:
    setattr(n, 'phJetDeltaR'+var,  min([deltaR(t._jetEta[j], t._phEta[n.ph], t._jetPhi[j], t._phPhi[n.ph]) for j in getattr(t, 'jets'+var)] + [999])   if len(t.photons) > 0 else -1)
    setattr(n, 'phBJetDeltaR'+var, min([deltaR(t._jetEta[j], t._phEta[n.ph], t._jetPhi[j], t._phPhi[n.ph]) for j in getattr(t, 'dbjets'+var)] + [999]) if len(t.photons) > 0 else -1)
    setattr(n, 'l1JetDeltaR'+var,  min([deltaR(t._jetEta[j], t._lEta[n.l1], t._jetPhi[j], t._lPhi[n.l1]) for j in getattr(t, 'jets'+var)] + [999])     if len(t.leptons) > 0 else -1)
    setattr(n, 'l2JetDeltaR'+var,  min([deltaR(t._jetEta[j], t._lEta[n.l2], t._jetPhi[j], t._lPhi[n.l2]) for j in getattr(t, 'jets'+var)] + [999])     if len(t.leptons) > 1 else -1)
    setattr(n, 'jjDeltaR'+var,     min([deltaR(t._jetEta[getattr(n, 'j1'+var)], t._jetEta[getattr(n, 'j2'+var)], t._jetPhi[getattr(n, 'j1'+var)], t._jetPhi[getattr(n, 'j2'+var)])]) if getattr(n, 'njets'+var) > 1 else -1) # pylint: disable=C0301

def getEta(pt, pz):
  theta = atan(pt/pz)
  if( theta < 0 ): theta += pi
  return -logar(tan(theta/2))


def getTopKinFit():
  from ttg.TopKinFit.kfit import *
  kf = kfit()
  kf.Init(TOPTOPLEPLEP)
  # fitterDir  = "$CMSSW_BASE/src/ttg/TopKinFit/python/test/GenAnalysis/TopTopLepLep/pdf.root"
  pdfFileName = os.path.expandvars("$CMSSW_BASE/src/ttg/TopKinFit/python/test/GenAnalysis/TopTopLepLep/pdf.root")
  kf.SetPDF("TopWMass", pdfFileName, "TopWM_Fit")
  kf.SetPDF("TopMass", pdfFileName, "TopM_Fit")
  kf.SetPDF("MetPx", pdfFileName, "dMetPx_Gaus")
  kf.SetPDF("MetPy", pdfFileName, "dMetPy_Gaus")
  kf.SetPDF("BJetPx", pdfFileName, "dBJetPx_Fit")
  kf.SetPDF("BJetPy", pdfFileName, "dBJetPy_Fit")
  kf.SetPDF("BJetPz", pdfFileName, "dBJetPz_Fit")
  kf.SetPDF("BJetE", pdfFileName, "dBJetE_Fit")
  kf.SetPDF("ElecPx", pdfFileName, "dElecPx_Fit")
  kf.SetPDF("ElecPy", pdfFileName, "dElecPy_Fit")
  kf.SetPDF("ElecPz", pdfFileName, "dElecPz_Fit")
  kf.SetPDF("ElecE", pdfFileName, "dElecE_Fit")
  kf.SetPDF("MuonPx", pdfFileName, "dMuonPx_Fit")
  kf.SetPDF("MuonPy", pdfFileName, "dMuonPy_Fit")
  kf.SetPDF("MuonPz", pdfFileName, "dMuonPz_Fit")
  kf.SetPDF("MuonE", pdfFileName, "dMuonE_Fit")

  kf.SetNToy(50)
  return kf

def reconstTops(kf, t, n):
  if n.ndbjets > 1: 
    n.topsReconst = True
    # prepare lists to enter into fitter
    nonBJets = [i for i in t.jets if i not in t.dbjets]
    BJetPt  = [t._jetSmearedPt[j] for j in t.dbjets ]
    BJetEta = [t._jetEta[j] for j in t.dbjets ]
    BJetPhi = [t._jetPhi[j] for j in t.dbjets ]
    BJetE   = [t._jetE[j] for j in t.dbjets ]
    nonBJetPt  = [t._jetSmearedPt[j] for j in nonBJets ]
    nonBJetEta = [t._jetEta[j] for j in nonBJets ]
    nonBJetPhi = [t._jetPhi[j] for j in nonBJets ]
    nonBJetE   = [t._jetE[j] for j in nonBJets ]

    ElePt, EleEta, ElePhi, EleE, MuPt, MuEta, MuPhi, MuE = [[] for _ in range(8)]
    for lept in [n.l1, n.l2]:
      if t._lFlavor[lept] == 0:
        ElePt.append(t._lPt[lept])
        EleEta.append(t._lEta[lept])
        ElePhi.append(t._lPhi[lept])
        EleE.append(t._lE[lept])
      else:
        MuPt.append(t._lPt[lept])
        MuEta.append(t._lEta[lept])
        MuPhi.append(t._lPhi[lept])
        MuE.append(t._lE[lept])
    # log.info('-------------------------------------')
    # log.info(nonBJets)
    # log.info(BJetPt)
    # log.info(BJetEta)
    # log.info(BJetPhi)
    # log.info(BJetE)
    # log.info(nonBJetPt)
    # log.info(nonBJetEta)
    # log.info(nonBJetPhi)
    # log.info(nonBJetE)
    # log.info(ElePt)
    # log.info(EleEta)
    # log.info(ElePhi)
    # log.info(EleE)
    # log.info(MuPt)
    # log.info(MuEta)
    # log.info(MuPhi)
    # log.info(MuE)
    # log.info('-------------------------------------')
    # enter lists into fitter
    kf.SetBJet(BJetPt, BJetEta, BJetPhi, BJetE)
    kf.SetNonBJet(nonBJetPt, nonBJetEta, nonBJetPhi, nonBJetE)
    kf.SetElectron(ElePt, EleEta, ElePhi, EleE)
    kf.SetMuon(MuPt, MuEta, MuPhi, MuE)
    # convert met and met phi to px py, independent op E and eta
    metVect = ROOT.Math.PtEtaPhiEVector(t._met ,0.,t._metPhi, 0.)
    kf.SetMet(metVect.px(), metVect.py())
    kf.Run()

    n.top1Pt  = kf.GetTopPt(0,0)
    n.top1Eta = kf.GetTopEta(0,0)
    n.top2Pt  = kf.GetTopPt(0,1)
    n.top2Eta = kf.GetTopEta(0,1)
    n.nu1Pt   = sqrt(kf.GetNuPx(0,0)*kf.GetNuPx(0,0) + kf.GetNuPy(0,0)*kf.GetNuPy(0,0))
    n.nu1Eta  = getEta(n.nu1Pt, kf.GetNuPz(0,0)) if not (kf.GetNuPz(0,0) == 0. or n.nu1Pt == 0 ) else -9999.
    n.nu2Pt   = sqrt(kf.GetNuPx(0,1)*kf.GetNuPx(0,1) + kf.GetNuPy(0,1)*kf.GetNuPy(0,1))
    n.nu2Eta  = getEta(n.nu2Pt, kf.GetNuPz(0,1)) if not (kf.GetNuPz(0,1) == 0. or n.nu2Pt == 0 ) else -9999.
    n.liHo    = kf.GetDisc(0)

  else:
    n.topsReconst = False
    n.top1Pt  = -9999.
    n.top1Eta = -9999.
    n.top2Pt  = -9999.
    n.top2Eta = -9999.
    n.nu1Pt   = -9999.
    n.nu1Eta  = -9999.
    n.nu2Pt   = -9999.
    n.nu2Eta  = -9999.
    n.liHo    = -9999.