import os
import sys
import math
import operator
import numpy as np
import utils as ut
import ROOT

import common as c
import functions as fun

import WeightInfo as wi
import HyperPoly as hp

class event():

    def __init__(self):
        
        pklFile = '/user/kskovpen/analysis/KinFit/CMSSW_10_5_0_pre2/src/GenEFTAnalysis/EDAnalyzers/macro/config/ttGamma_Dilept_restrict_rwgt_slc6_amd64_gcc630_CMSSW_9_3_16_tarball.pkl'

        self.weightInfo = wi.WeightInfo( pklFile )
        self.hyperPoly = hp.HyperPoly( 2 )

        self.wvar = [\
        'ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p',\
        'ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p',\
        'ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p',\
        'ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p',\
        'ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p',\
        'ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p',\
        'ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p',\
        'ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p',\
        'ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p',\
        'ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p',\
        'ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p',\
        'ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p',\
        'ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p',\
        'ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p',\
        'ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p'\
        ]

    def interpret_weight(self, weight_id):    
        str_s = weight_id.split('_')
        res={}
        for i in range(len(str_s)/2):
            res[str_s[2*i]] = float(str_s[2*i+1].replace('m','-').replace('p','.'))
        return res
        
    def fill(self, ev):

        weights = []
        param_points = []

        for w in self.wvar:    
            pos = self.weightInfo.data[w]
            interpreted_weight = self.interpret_weight(w)
            weights += [ getattr(ev, "weight_"+w) ]

            if not self.hyperPoly.initialized:
                param_points += [ tuple( interpreted_weight[var] for var in self.weightInfo.variables ) ]
            
        ref_point_coordinates = [ self.weightInfo.ref_point_coordinates[var] for var in self.weightInfo.variables ]
        
        if not self.hyperPoly.initialized:
            self.hyperPoly.initialize( param_points, ref_point_coordinates )
            
        coeff = self.hyperPoly.get_parametrization( weights )
        np = self.hyperPoly.ndof
        chi2_ndof = self.hyperPoly.chi2_ndof( coeff, weights )
            
        ref_weight = getattr(ev, "weight") / coeff[0]

        func = self.hyperPoly.root_func_string(coeff)
        func = func.replace('x0','x[0]').replace('x1','x[1]').replace('x2','x[2]').replace('x3','x[3]')
        rfunc = ROOT.TFormula("ParamFunc", func)
        
        self.weight_SM = ref_weight * rfunc.Eval(0.,0.,0.,0.)
        self.weight_ctZ_2_ctZI_0_ctW_0_ctWI_0 = ref_weight * rfunc.Eval(2.,0.,0.,0.)
        self.weight_ctZ_0_ctZI_2_ctW_0_ctWI_0 = ref_weight * rfunc.Eval(0.,2.,0.,0.)
        self.weight_ctZ_0_ctZI_0_ctW_2_ctWI_0 = ref_weight * rfunc.Eval(0.,0.,2.,0.)
        self.weight_ctZ_0_ctZI_0_ctW_0_ctWI_2 = ref_weight * rfunc.Eval(0.,0.,0.,2.)
        
#        print rfunc.Eval(1.,0.,1.,0.), ev.weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p
        
        self.coeff = coeff
        
class particle():
    
    def __init__(self, name, pid, status, daun, mid, pt, eta, phi, E):

        self.name = name
        self.pid = pid
        self.status = status
        self.daun = daun
        self.mid = mid
        
        self.pt = pt
        self.eta = eta
        self.phi = phi
        self.E = E
        
        if abs(self.eta) > 100: return None
        
        self.px = self.pt*math.cos(self.phi)
        self.py = self.pt*math.sin(self.phi)
        self.pz = self.pt*math.sinh(self.eta)
        
    def findDecayed(self, genN, pdgidBr, statusBr, dauNBr, ptBr, etaBr, phiBr, EBr):
        
        pout = None
        
        for i in range(genN):

            pdgid = pdgidBr[i]
            status = statusBr[i]
            dauN = dauNBr[i]
                        
            if self.pid != pdgid: continue
            if dauN < 2: continue
            
            pout = particle(self.name, pdgid, status, dauN, self.mid, ptBr[i], etaBr[i], phiBr[i], EBr[i])
            break
            
        if pout is None: pout = self
            
        return pout
        
class truth():

    def __init__(self, ev, verbose = False):

        self.proc = ''

        genN = ev.gen_n
        lheN = ev.lhe_n

        if verbose: print '-----------------'

        self.ps = []
        self.lhe = []
        
        pdgIdBr = ev.gen_pdgId
        statusBr = ev.gen_status
        dauNBr = ev.gen_daughter_n
        ptBr = ev.gen_pt
        etaBr = ev.gen_eta
        phiBr = ev.gen_phi
        EBr = ev.gen_E
        motIdxBr = ev.gen_motherIndex

        lhepdgIdBr = ev.lhe_pdgId
        lhestatusBr = ev.lhe_status
        lheptBr = ev.lhe_pt
        lheetaBr = ev.lhe_eta
        lhephiBr = ev.lhe_phi
        lheEBr = ev.lhe_E
        lheMidBr = ev.lhe_mother1Index

        # LHE
        for i in range(lheN):

            pdgid = lhepdgIdBr[i]
            status = lhestatusBr[i]
            pt = lheptBr[i]
            
            motIdx = lheMidBr[i]
            if motIdx < 0: continue
            motPdgId = lhepdgIdBr[motIdx]
            mid = abs(motPdgId)

            pid = abs(pdgid)

            if pid == 6: pname = 't'
            elif pid == 24: pname = 'w'
            elif pid == 5: pname = 'b'
            elif pid == 22: pname = 'g'
            elif pid in [11,13,15]: pname = 'l'
            else: continue

            p = particle(pname, pdgid, status, -1, motPdgId, lheptBr[i], lheetaBr[i], lhephiBr[i], lheEBr[i])
            
            if p is not None:
                self.lhe.append(p)
                
        phoLheOrigin = -1
        for i, p in enumerate(self.lhe):
            if p.pid == 22:
                phoLheOrigin = p.mid
                break

        # PS
        for i in range(genN):
                                
            pdgid = pdgIdBr[i]
            status = statusBr[i]
            dauN = dauNBr[i]
            pt = ptBr[i]
            
            pid = abs(pdgid)
            
            if pt < 1.0 and pid == 22: continue # remove soft radiation
            
            motIdx = motIdxBr[i]
            if motIdx < 0: continue
            motPdgId = pdgIdBr[motIdx]
            mid = abs(motPdgId)

#            if (pid in [6]) or \            
            if (pid in [6] and dauN > 1 and status in [62]) or \
            (pid in [24] and status in [22]) or \
            (pid in [5] and status in [23]) or \
            (pid in [11,13,15] and mid in [24]) or \
            (pid in [22]):

                if pid == 6: pname = 't'                
                elif pid == 24: pname = 'w'
                elif pid == 5: pname = 'b'
                elif pid == 22: pname = 'g'
                elif pid in [11,13,15]: pname = 'l'
                
                p = particle(pname, pdgid, status, dauN, motPdgId, ptBr[i], etaBr[i], phiBr[i], EBr[i])

                if pid == motPdgId and pid == 22: continue
#                if motPdgId != phoLheOrigin and pid == 22 and phoLheOrigin not in [21]: continue
#                if phoLheOrigin in [21] and motPdgId not in [22, 21] and pid == 22: continue

#                if dauN < 2:
#                    p = p.findDecayed(genN, pdgIdBr, statusBr, dauNBr, ptBr, etaBr, phiBr, EBr)

                if p is not None:
                    self.ps.append(p)
            
        # Analyse selected particles
        self.ps.sort(key=operator.attrgetter('pt'), reverse=True)
        self.lhe.sort(key=operator.attrgetter('pt'), reverse=True)
        
        foundPho = False
#        foundTop = 0

        plist = []
        for i, p in enumerate(self.ps):
            
            if p.pid == 22:
                if foundPho:
                    continue
                else: foundPho = True
                
#            if abs(p.pid) == 6:
#                foundTop += 1
                
            plist.append(p)

        if not foundPho:
            print 'No photon found'
            sys.exit()
            
        self.ps = plist
            
        for i, p in enumerate(self.ps):
            if verbose: print p.name, p.pid, p.status, p.daun, p.mid, p.pt, p.eta, p.phi

#        if foundTop < 2:
#            print 'missing top' # top quarks can still be off-shell according to bwcutoff
#            sys.exit()
            
