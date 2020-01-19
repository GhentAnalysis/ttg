import numpy as np
import importlib
import math
import sys, os
import style
import ROOT

sys.path.append('../../')
from kfit import *

from optparse import OptionParser

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n Application of the TopKinFit reconstruction"

    parser = OptionParser(usage)
    parser.add_option("-i","--input",default="output.root",help="input data [default: %default]")
    parser.add_option("-m","--max",type=int,default=100,help="max number of events to process [default: %default]")
    parser.add_option("-t","--toys",type=int,default=100,help="number of toys [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

def deltaR2( e1, p1, e2, p2 ):
    de = e1 - e2
    dp = deltaPhi(p1, p2)
    return de*de + dp*dp
                        
def deltaR( *args ):
    return math.sqrt( deltaR2(*args) )

def deltaPhi( p1, p2):
    res = p1 - p2
    while res > math.pi:
        res -= 2*math.pi
    while res < -math.pi:
        res += 2*math.pi
    return res

if __name__ == '__main__':

    options = main()

    ROOT.gROOT.SetBatch()
    
    pstyle = style.SetPlotStyle(1)
    
    fName = options.input.split(',')
    tr = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
    for f in fName:        
        tr.Add(f)
    nEvents = tr.GetEntries()

    print '-----'
    print 'Initialize TopKinFit'
    
    kf = kfit()

    kf.Init(TOPTOPLEPLEP)

    pdfFileName = "../GenAnalysis/TopLep/pdf.root"
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
    
    kf.SetNToy(options.toys)

    print 'Create histograms'
    
    h_disc = ROOT.TH1F('h_disc','h_disc',20,0.,30.)
    
    print 'Loop through events ('+str(nEvents)+')'

    iev = 0
    for ev in tr:
        
        if iev > options.max and options.max >= 0: break
        
        genTop1WLepPt, genTop1WLepEta, genTop1WLepPhi, genTop1WLepE, genTop1WLepPdgId = -1, -1, -1, -1, -1
        genTop1WNuPt, genTop1WNuEta, genTop1WNuPhi, genTop1WNuE, genTop1WNuPdgId = -1, -1, -1, -1, -1
        genTop1WPt, genTop1WEta, genTop1WPhi, genTop1WE, genTop1WIdx = -1, -1, -1, -1, -1
        genTop1BPt, genTop1BEta, genTop1BPhi, genTop1BE = -1, -1, -1, -1
        genTop1Pt, genTop1Eta, genTop1Phi, genTop1E, genTop1Idx = -1, -1, -1, -1, -1

        genTop2WLepPt, genTop2WLepEta, genTop2WLepPhi, genTop2WLepE, genTop2WLepPdgId = -1, -1, -1, -1, -1
        genTop2WNuPt, genTop2WNuEta, genTop2WNuPhi, genTop2WNuE, genTop2WNuPdgId = -1, -1, -1, -1, -1
        genTop2WPt, genTop2WEta, genTop2WPhi, genTop2WE, genTop2WIdx = -1, -1, -1, -1, -1
        genTop2BPt, genTop2BEta, genTop2BPhi, genTop2BE = -1, -1, -1, -1
        genTop2Pt, genTop2Eta, genTop2Phi, genTop2E, genTop2Idx = -1, -1, -1, -1, -1
                
        nPart = ev._nLheParticles

        # find top quarks
        for p in range(nPart):
            
            pdgId = ev._lhePdgId[p]
            pt = ev._lhePt[p]
            eta = ev._lheEta[p]
            phi = ev._lhePhi[p]
            E = ev._lheE[p]

            if abs(pdgId) == 6:
                if genTop1Pt == -1: 
                    genTop1Pt = pt
                    genTop1Eta = eta
                    genTop1Phi = phi
                    genTop1E = E
                    genTop1Idx = p
                else:
                    genTop2Pt = pt
                    genTop2Eta = eta
                    genTop2Phi = phi
                    genTop2E = E
                    genTop2Idx = p

        # find b quarks and W bosons
        for p in range(nPart):
            
            pdgId = ev._lhePdgId[p]
            pt = ev._lhePt[p]
            eta = ev._lheEta[p]
            phi = ev._lhePhi[p]
            E = ev._lheE[p]
            mom = ev._lheMother1[p]

            if abs(pdgId) == 5:
                if mom == genTop1Idx:
                    genTop1BPt = pt
                    genTop1BEta = eta
                    genTop1BPhi = phi
                    genTop1BE = E
                else:
                    genTop2BPt = pt
                    genTop2BEta = eta
                    genTop2BPhi = phi
                    genTop2BE = E

            if abs(pdgId) == 24:
                if mom == genTop1Idx:
                    genTop1WPt = pt
                    genTop1WEta = eta
                    genTop1WPhi = phi
                    genTop1WE = E
                    genTop1WIdx = p
                else:
                    genTop2WPt = pt
                    genTop2WEta = eta
                    genTop2WPhi = phi
                    genTop2WE = E
                    genTop2WIdx = p

        # find leptons and neutrinos
        for p in range(nPart):
            
            pdgId = ev._lhePdgId[p]
            pt = ev._lhePt[p]
            eta = ev._lheEta[p]
            phi = ev._lhePhi[p]
            E = ev._lheE[p]
            mom = ev._lheMother1[p]

            if abs(pdgId) == 11 or abs(pdgId) == 13 or abs(pdgId) == 15:
                if mom == genTop1WIdx:
                    genTop1WLepPdgId = pdgId
                    genTop1WLepPt = pt
                    genTop1WLepEta = eta
                    genTop1WLepPhi = phi
                    genTop1WLepE = E
                else:
                    genTop2WLepPdgId = pdgId
                    genTop2WLepPt = pt
                    genTop2WLepEta = eta
                    genTop2WLepPhi = phi
                    genTop2WLepE = E

            if abs(pdgId) == 12 or abs(pdgId) == 14 or abs(pdgId) == 16:
                if mom == genTop1WIdx:
                    genTop1WNuPdgId = pdgId
                    genTop1WNuPt = pt
                    genTop1WNuEta = eta
                    genTop1WNuPhi = phi
                    genTop1WNuE = E
                else:
                    genTop2WNuPdgId = pdgId
                    genTop2WNuPt = pt
                    genTop2WNuEta = eta
                    genTop2WNuPhi = phi
                    genTop2WNuE = E

        recTop1WLepPt, recTop1WLepEta, recTop1WLepPhi, recTop1WLepE, recTop1WLepIdx, recTop1WLepPdgId = -1, -1, -1, -1, -1, -1
        recTop1BPt, recTop1BEta, recTop1BPhi, recTop1BE, recTop1BIdx = -1, -1, -1, -1, -1

        recTop2WLepPt, recTop2WLepEta, recTop2WLepPhi, recTop2WLepE, recTop2WLepIdx, recTop2WLepPdgId = -1, -1, -1, -1, -1, -1
        recTop2BPt, recTop2BEta, recTop2BPhi, recTop2BE, recTop2BIdx = -1, -1, -1, -1, -1

        recMetPx, recMetPy = ev._met*math.cos(ev._metPhi), ev._met*math.sin(ev._metPhi)
                    
        # find reco match for l1
        drMin = 10E+10
        for l in range(ev._nL):
            pt = ev._lPt[l]
            eta = ev._lEta[l]
            phi = ev._lPhi[l]
            E = ev._lE[l]
            flav = ev._lFlavor[l]
            if flav == 0 and abs(genTop1WLepPdgId) != 11: continue
            if flav == 1 and abs(genTop1WLepPdgId) != 13: continue
            if abs(genTop1WLepPdgId) == 15: continue
            dr = deltaR(eta, phi, genTop1WLepEta, genTop1WLepPhi)
            if dr < drMin:
                drMin = dr
                recTop1WLepPt = pt
                recTop1WLepEta = eta
                recTop1WLepPhi = phi
                recTop1WLepE = E
                recTop1WLepIdx = l
                recTop1WLepPdgId = genTop1WLepPdgId
            
        # find reco match for l2
        drMin = 10E+10
        for l in range(ev._nL):
            pt = ev._lPt[l]
            eta = ev._lEta[l]
            phi = ev._lPhi[l]
            E = ev._lE[l]
            flav = ev._lFlavor[l]
            if l == recTop1WLepIdx: continue
            if flav == 0 and abs(genTop2WLepPdgId) != 11: continue
            if flav == 1 and abs(genTop2WLepPdgId) != 13: continue
            if abs(genTop2WLepPdgId) == 15: continue
            dr = deltaR(eta, phi, genTop2WLepEta, genTop2WLepPhi)
            if dr < drMin:
                drMin = dr
                recTop2WLepPt = pt
                recTop2WLepEta = eta
                recTop2WLepPhi = phi
                recTop2WLepE = E
                recTop2WLepIdx = l
                recTop2WLepPdgId = genTop2WLepPdgId

        # find reco match for b1
        drMin = 10E+10
        for j in range(ev._nJets):
            pt = ev._jetPt[j]
            eta = ev._jetEta[j]
            phi = ev._jetPhi[j]
            E = ev._jetE[j]
            dr = deltaR(eta, phi, genTop1BEta, genTop1BPhi)
            if dr < drMin:
                drMin = dr
                recTop1BPt = pt
                recTop1BEta = eta
                recTop1BPhi = phi
                recTop1BE = E
                recTop1BIdx = j

        # find reco match for b2
        drMin = 10E+10
        for j in range(ev._nJets):
            pt = ev._jetPt[j]
            eta = ev._jetEta[j]
            phi = ev._jetPhi[j]
            E = ev._jetE[j]
            if j == recTop1BIdx: continue
            dr = deltaR(eta, phi, genTop2BEta, genTop2BPhi)
            if dr < drMin:
                drMin = dr
                recTop2BPt = pt
                recTop2BEta = eta
                recTop2BPhi = phi
                recTop2BE = E
                recTop2BIdx = j

        if recTop1WLepIdx < 0 or recTop1BIdx < 0 or recTop2WLepIdx < 0 or recTop2BIdx < 0: continue
                
        BJetPt = FloatVector()
        BJetEta = FloatVector()
        BJetPhi = FloatVector()
        BJetE = FloatVector()

        ElectronPt = FloatVector()
        ElectronEta = FloatVector()
        ElectronPhi = FloatVector()
        ElectronE = FloatVector()

        MuonPt = FloatVector()
        MuonEta = FloatVector()
        MuonPhi = FloatVector()
        MuonE = FloatVector()
        
        for v in [recTop1BPt,recTop2BPt]: BJetPt.push_back(v)
        for v in [recTop1BEta,recTop2BEta]: BJetEta.push_back(v)
        for v in [recTop1BPhi,recTop2BPhi]: BJetPhi.push_back(v)
        for v in [recTop1BE,recTop2BE]: BJetE.push_back(v)

        if abs(recTop1WLepPdgId) == 11:
            ElectronPt.push_back(recTop1WLepPt)
            ElectronEta.push_back(recTop1WLepEta)
            ElectronPhi.push_back(recTop1WLepPhi)
            ElectronE.push_back(recTop1WLepE)
        else:
            MuonPt.push_back(recTop1WLepPt)
            MuonEta.push_back(recTop1WLepEta)
            MuonPhi.push_back(recTop1WLepPhi)
            MuonE.push_back(recTop1WLepE)
        
        if abs(recTop2WLepPdgId) == 11:
            ElectronPt.push_back(recTop2WLepPt)
            ElectronEta.push_back(recTop2WLepEta)
            ElectronPhi.push_back(recTop2WLepPhi)
            ElectronE.push_back(recTop2WLepE)
        else:
            MuonPt.push_back(recTop2WLepPt)
            MuonEta.push_back(recTop2WLepEta)
            MuonPhi.push_back(recTop2WLepPhi)
            MuonE.push_back(recTop2WLepE)
            
        kf.SetBJet(BJetPt,BJetEta,BJetPhi,BJetE)
        kf.SetElectron(ElectronPt,ElectronEta,ElectronPhi,ElectronE)
        kf.SetMuon(MuonPt,MuonEta,MuonPhi,MuonE)
        kf.SetMet(recMetPx,recMetPy)

        kf.Run()
        
        NPerm = kf.GetNPerm()
        
        disc = kf.GetDisc(0)
        print iev, disc
        h_disc.Fill(disc)
        
        iev += 1
            
    print 'Produce plots'

    if not os.path.exists('pics'):
        os.makedirs('pics')
    
    c1 = ROOT.TCanvas()
    h_disc.GetXaxis().SetTitle('D')
    h_disc.GetYaxis().SetTitle('Number of events')
    h_disc.Draw('hist e1')
    c1.Print('pics/disc.eps')
    
    print 'Done'
