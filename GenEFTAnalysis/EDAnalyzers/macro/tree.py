import os
import sys
import math
from array import array
import utils
import ROOT

class tree():

    def __init__(self, name):
        
        self.weight_SM, \
        self.weight_ctZ_2_ctZI_0_ctW_0_ctWI_0, \
        self.weight_ctZ_0_ctZI_2_ctW_0_ctWI_0, \
        self.weight_ctZ_0_ctZI_0_ctW_2_ctWI_0, \
        self.weight_ctZ_0_ctZI_0_ctW_0_ctWI_2 \
        = (array( 'f', [ -777 ] ) for _ in range(5))
        
        self.pid, self.lhepid, self.mid = (ROOT.vector('int')() for _ in range(3))
        self.pt, self.eta, self.phi, self.E, self.coeff = (ROOT.vector('float')() for _ in range(5))
        self.lhept, self.lheeta, self.lhephi, self.lheE = (ROOT.vector('float')() for _ in range(4))

        self.t = ROOT.TTree( name, 'Validation tree' )

        self.t.Branch( 'weight_SM', self.weight_SM, 'weight_SM/F' )
        self.t.Branch( 'weight_ctZ_2_ctZI_0_ctW_0_ctWI_0', self.weight_ctZ_2_ctZI_0_ctW_0_ctWI_0, 'weight_ctZ_2_ctZI_0_ctW_0_ctWI_0/F' )
        self.t.Branch( 'weight_ctZ_0_ctZI_2_ctW_0_ctWI_0', self.weight_ctZ_0_ctZI_2_ctW_0_ctWI_0, 'weight_ctZ_0_ctZI_2_ctW_0_ctWI_0/F' )
        self.t.Branch( 'weight_ctZ_0_ctZI_0_ctW_2_ctWI_0', self.weight_ctZ_0_ctZI_0_ctW_2_ctWI_0, 'weight_ctZ_0_ctZI_0_ctW_2_ctWI_0/F' )
        self.t.Branch( 'weight_ctZ_0_ctZI_0_ctW_0_ctWI_2', self.weight_ctZ_0_ctZI_0_ctW_0_ctWI_2, 'weight_ctZ_0_ctZI_0_ctW_0_ctWI_2/F' )

        self.t.Branch( 'pid', 'std::vector<int>', self.pid )
        self.t.Branch( 'pt', 'std::vector<float>', self.pt )
        self.t.Branch( 'eta', 'std::vector<float>', self.eta )
        self.t.Branch( 'phi', 'std::vector<float>', self.phi )
        self.t.Branch( 'E', 'std::vector<float>', self.E )
        self.t.Branch( 'mid', 'std::vector<int>', self.mid )

        self.t.Branch( 'lhepid', 'std::vector<int>', self.lhepid )
        self.t.Branch( 'lhept', 'std::vector<float>', self.lhept )
        self.t.Branch( 'lheeta', 'std::vector<float>', self.lheeta )
        self.t.Branch( 'lhephi', 'std::vector<float>', self.lhephi )
        self.t.Branch( 'lheE', 'std::vector<float>', self.lheE )
        
        self.t.Branch( 'coeff', 'std::vector<float>', self.coeff )
        
    def clear(self):

        self.pid.clear()
        self.pt.clear()
        self.eta.clear()
        self.phi.clear()
        self.E.clear()
        self.mid.clear()

        self.lhepid.clear()
        self.lhept.clear()
        self.lheeta.clear()
        self.lhephi.clear()
        self.lheE.clear()
        
        self.coeff.clear()
        
    def fill(self):

        self.t.Fill()
        
