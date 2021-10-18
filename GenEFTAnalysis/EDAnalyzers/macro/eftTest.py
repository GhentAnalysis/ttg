#!/usr/bin/env python

import os, sys
import ROOT
import WeightInfo as wi
import HyperPoly as hp

ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

def interpret_weight(weight_id):    
    str_s = weight_id.split('_')
    res={}
    for i in range(len(str_s)/2):
        res[str_s[2*i]] = float(str_s[2*i+1].replace('m','-').replace('p','.'))
    return res

def main(argv = None):

    if argv == None:
        argv = sys.argv[1:]

    usage = "usage: %prog [options]\n EFT study"

    parser = OptionParser(usage)
    parser.add_option("--order", type=int, default=2, help="interpolation order [default: %default]")

    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':

    options = main()

    pklFile = 'config/ttGamma_Dilept_restrict_rwgt_slc6_amd64_gcc630_CMSSW_9_3_16_tarball.pkl'

    weightInfo = wi.WeightInfo( pklFile )
    hyperPoly = hp.HyperPoly( options.order )
    
    wvar = [\
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

    f = ROOT.TFile('../test/output.root', 'READ')
    tr = f.Get('maker/tree')

    for ev in tr:
        
        weights = []
        param_points = []

        print '----'
        for w in wvar:    
            pos = weightInfo.data[w]
            interpreted_weight = interpret_weight(w)
            weights += [ getattr(ev, "weight_"+w) ]

            if not hyperPoly.initialized:
                param_points += [ tuple( interpreted_weight[var] for var in weightInfo.variables ) ]
            
        ref_point_coordinates = [ weightInfo.ref_point_coordinates[var] for var in weightInfo.variables ]
        
        if not hyperPoly.initialized:
            hyperPoly.initialize( param_points, ref_point_coordinates )
            
        coeff = hyperPoly.get_parametrization( weights )
        np = hyperPoly.ndof
        chi2_ndof = hyperPoly.chi2_ndof( coeff, weights )
            
        ref_weight = getattr(ev, "weight") / coeff[0]

        func = hyperPoly.root_func_string(coeff)
        func = func.replace('x0','x[0]').replace('x1','x[1]').replace('x2','x[2]').replace('x3','x[3]')
        rfunc = ROOT.TFormula("", func)
#        print "%0.6f" % coeff[0], \
#        "%0.6f" % coeff[1], \
#        "%0.6f" % coeff[2], \
#        "%0.6f" % coeff[3], \
#        "%0.6f" % coeff[4], \
#        "%0.6f" % coeff[5], \
#        "%0.6f" % coeff[6], \
#        "%0.6f" % coeff[7], \
#        "%0.6f" % coeff[8], \
#        "%0.6f" % coeff[9], \
#        "%0.6f" % coeff[10], \
#        "%0.6f" % coeff[11], \
#        "%0.6f" % coeff[12], \
#        "%0.6f" % coeff[13], \
#        "%0.6f" % coeff[14]
        rfunc.Print()
        print 'ref=', coeff[0], rfunc.Eval(4.,4.,4.,4.)
        print 'sm=', ev.weight, rfunc.Eval(0.,0.,0.,0.)/rfunc.Eval(4.,4.,4.,4.)
        print 'eft=', ev.weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p, rfunc.Eval(0.,0.,1.,1.)
            
