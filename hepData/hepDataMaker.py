from hepdata_lib import RootFileReader, Submission, Variable, Table, Uncertainty
import pdb
import os
import glob
import numpy


dataMCList = [
  # figure 2
  # 'njets',
  # 'nbtag',
  # 'unfReco_phPt',
  # 'unfReco_phAbsEta',
  # figure 3
  # 'unfReco_l1l2_ptsum',
  # 'unfReco_ll_deltaPhi',
  # 'unfReco_jetLepDeltaR',
  # 'unfReco_phLepDeltaR',
  # figure 4: Zg stuff
  # 'dlg_mass_zoom',
  # 'dl_mass_small',
  # 'photon_pt',
  # 'signalRegionsZoom',
  # figure 5: NP
  # figure 6: ph pt in 3 channels, postfit
  'unfReco_phPt_mm_post',
  'unfReco_phPt_em_post',
  'unfReco_phPt_ee_post',
  ]

unfdistList = [
  'unfReco_phPt',
  'unfReco_phAbsEta',
  'unfReco_phLepDeltaR',
  'unfReco_phLep1DeltaR',
  'unfReco_phLep2DeltaR',
  'unfReco_phBJetDeltaR',
  'unfReco_jetLepDeltaR',
  'unfReco_ll_absDeltaEta',
  'unfReco_ll_deltaPhi',
  'unfReco_Z_pt',
  'unfReco_l1l2_ptsum',
  'unfReco_jetPt',
  ]


NPdistList = [
  # NOTE WARNING we're replacing this plot probably
  'PBVDphoton_pt',
  'PByield',
  ]


# processes = { 'data', 'nonp', 'ttg', 'zg', 'ST', 'other'}

labels = {
          'unfReco_phPt' :          '$p_{T}(\gamma)$ [GeV]',
          'unfReco_phLepDeltaR' :   '$\Delta R(\gamma, l)$',
          'unfReco_ll_deltaPhi' :   '$\Delta \phi(ll)$',
          'unfReco_jetLepDeltaR' :  '$\Delta R(l, j)$',
          'unfReco_jetPt' :         '$p_{T}(j1)$ [GeV]',
          'unfReco_ll_absDeltaEta' :'$|\Delta\eta(ll)|$',
          'unfReco_phBJetDeltaR' :  '$\Delta R(\gamma, b)$',
          'unfReco_phAbsEta' :      '$|\eta |(\gamma)$',
          'unfReco_phLep1DeltaR' :  '$\Delta R(\gamma, l1)$',
          'unfReco_phLep2DeltaR' :  '$\Delta R(\gamma, l2)$',
          'unfReco_Z_pt' :          '$p_{T}(ll) [GeV]$',
          'unfReco_l1l2_ptsum' :    '$p_{T}(l1)+p_{T}(l2)$ [GeV]',
          'njets':                  'Number of jets',
          'nbtag':                  'Number of b-tagged jets',
          'dlg_mass_zoom':          '$m(ll\gamma)$  [GeV]',
          'dl_mass_small':          '$m(ll)$  [GeV]',
          'photon_pt':              '$p_{T}(\gamma)$ [GeV]',
          'signalRegionsZoom':      '',
          'PBVDphoton_pt':          '$p_{T}(\gamma)$ [GeV]',
          'PByield':                '',
          'unfReco_phPt_mm_post' :  '$p_{T}(\gamma)$ [GeV]',
          'unfReco_phPt_em_post' :  '$p_{T}(\gamma)$ [GeV]',
          'unfReco_phPt_ee_post' :  '$p_{T}(\gamma)$ [GeV]'
          }

metadata = {}

metadata['dataMC' + 'njets'                 ] = ('Figure 2a', 'Data corresponding to figure 2a (upper left)' ,   'Distribution of $N_j$ in the signal region.')
metadata['dataMC' + 'nbtag'                 ] = ('Figure 2b', 'Data corresponding to figure 2b (upper right)' ,  'Distribution of $N_b$ in the signal region.')
metadata['dataMC' + 'unfReco_phPt'          ] = ('Figure 2c', 'Data corresponding to figure 2c (lower left)' ,   'Distribution of $p_{T}(\gamma)$ in the signal region.')
metadata['dataMC' + 'unfReco_phAbsEta'      ] = ('Figure 2d', 'Data corresponding to figure 2d (lower right)' ,  'Distribution of $|\eta |(\gamma)$ in the signal region.')
metadata['dataMC' + 'unfReco_l1l2_ptsum'    ] = ('Figure 3a', 'Data corresponding to figure 3a (upper left)' ,   'Distribution of $p_{T}(l1)+p_{T}(l2)$ in the signal region.')
metadata['dataMC' + 'unfReco_ll_deltaPhi'   ] = ('Figure 3b', 'Data corresponding to figure 3b (upper right)' ,  'Distribution of $\Delta \phi(ll)$ in the signal region.')
metadata['dataMC' + 'unfReco_jetLepDeltaR'  ] = ('Figure 3c', 'Data corresponding to figure 3c (lower left)' ,   'Distribution of $\Delta R(l, j)$ in the signal region.')
metadata['dataMC' + 'unfReco_phLepDeltaR'   ] = ('Figure 3d', 'Data corresponding to figure 3d (lower right)' ,  'Distribution of $\Delta R(\gamma, l)$ in the signal region.')
metadata['dataMC' + 'dlg_mass_zoom'         ] = ('Figure 4a', 'Data corresponding to figure 4a (upper left)' ,   'Distribution of $m(ll\gamma)$ in the $Z\gamma$ control region.')
metadata['dataMC' + 'dl_mass_small'         ] = ('Figure 4b', 'Data corresponding to figure 4b (upper right)' ,  'Distribution of $m(ll)$ in the $Z\gamma$ control region.')
metadata['dataMC' + 'photon_pt'             ] = ('Figure 4c', 'Data corresponding to figure 4c (lower left)' ,   'Distribution of $p_{T}(\gamma)$ in the $Z\gamma$ control region.')
metadata['dataMC' + 'signalRegionsZoom'     ] = ('Figure 4d', 'Data corresponding to figure 4d (lower right)' ,  'Distribution of jet multiplicity in the $Z\gamma$ control region.')
metadata['dataMC' + 'PBVDphoton_pt'         ] = ('Figure 5a', 'Data corresponding to figure 5a (left) ' ,        'Closure test of the nonprompt photon estimation as a function of $p_{T}(\gamma)$.')
metadata['dataMC' + 'PByield'               ] = ('Figure 5b', 'Data corresponding to figure 5b (right) ' ,       'Closure test of the nonprompt photon estimation as a function of the lepton flavours.')
metadata['dataMC' + 'unfReco_phPt_mm_post'  ] = ('Figure 6a', 'Data corresponding to figure 6a (upper left) ' ,  'Observed and predicted event yields as a function of $p_{T}(\gamma)$ in the $\mu\mu$ channel, after the fit to the data.')
metadata['dataMC' + 'unfReco_phPt_em_post'  ] = ('Figure 6b', 'Data corresponding to figure 6b (upper right) ' , 'Observed and predicted event yields as a function of $p_{T}(\gamma)$ in the $e\mu$ channel, after the fit to the data.')
metadata['dataMC' + 'unfReco_phPt_ee_post'  ] = ('Figure 6c', 'Data corresponding to figure 6c (lower) ' ,       'Observed and predicted event yields as a function of $p_{T}(\gamma)$ in the $ee$ channel, after the fit to the data.')



metadata['diff' + 'unfReco_phPt'          ]  = ('Figure 8a', 'Data corresponding to figure 8a (upper left)' ,    'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phPt'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phAbsEta'      ]  = ('Figure 8b', 'Data corresponding to figure 8b (upper right)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phAbsEta'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLepDeltaR'   ]  = ('Figure 8c', 'Data corresponding to figure 8c (middle left)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phLepDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLep1DeltaR'  ]  = ('Figure 8d', 'Data corresponding to figure 8d (middle right)' ,  'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phLep1DeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLep2DeltaR'  ]  = ('Figure 8e', 'Data corresponding to figure 8e (lower left)' ,    'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phLep2DeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phBJetDeltaR'  ]  = ('Figure 8f', 'Data corresponding to figure 8f (lower right)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_phBJetDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_jetLepDeltaR'  ]  = ('Figure 9a', 'Data corresponding to figure 9a (upper left)' ,    'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_jetLepDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_ll_absDeltaEta']  = ('Figure 9b', 'Data corresponding to figure 9b (upper right)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_ll_absDeltaEta'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_ll_deltaPhi'   ]  = ('Figure 9c', 'Data corresponding to figure 9c (middle left)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_ll_deltaPhi'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_Z_pt'          ]  = ('Figure 9d', 'Data corresponding to figure 9d (middle right)' ,  'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_Z_pt'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_l1l2_ptsum'    ]  = ('Figure 9e', 'Data corresponding to figure 9e (lower left)' ,    'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_l1l2_ptsum'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_jetPt'         ]  = ('Figure 9f', 'Data corresponding to figure 9f (lower right)' ,   'Absolute differential $tt\gamma$ production cross section as a function of ' + labels['unfReco_jetPt'].replace('[GeV]','') + '.')

metadata['diff' + 'unfReco_phPt'           + '_norm']  = ('Figure 10a', 'Data corresponding to figure 10a (upper left)' ,    'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phPt'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phAbsEta'       + '_norm']  = ('Figure 10b', 'Data corresponding to figure 10b (upper right)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phAbsEta'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLepDeltaR'    + '_norm']  = ('Figure 10c', 'Data corresponding to figure 10c (middle left)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phLepDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLep1DeltaR'   + '_norm']  = ('Figure 10d', 'Data corresponding to figure 10d (middle right)' ,  'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phLep1DeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phLep2DeltaR'   + '_norm']  = ('Figure 10e', 'Data corresponding to figure 10e (lower left)' ,    'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phLep2DeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_phBJetDeltaR'   + '_norm']  = ('Figure 10f', 'Data corresponding to figure 10f (lower right)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_phBJetDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_jetLepDeltaR'   + '_norm']  = ('Figure 11a', 'Data corresponding to figure 11a (upper left)' ,    'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_jetLepDeltaR'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_ll_absDeltaEta' + '_norm']  = ('Figure 11b', 'Data corresponding to figure 11b (upper right)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_ll_absDeltaEta'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_ll_deltaPhi'    + '_norm']  = ('Figure 11c', 'Data corresponding to figure 11c (middle left)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_ll_deltaPhi'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_Z_pt'           + '_norm']  = ('Figure 11d', 'Data corresponding to figure 11d (middle right)' ,  'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_Z_pt'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_l1l2_ptsum'     + '_norm']  = ('Figure 11e', 'Data corresponding to figure 11e (lower left)' ,    'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_l1l2_ptsum'].replace('[GeV]','') + '.')
metadata['diff' + 'unfReco_jetPt'          + '_norm']  = ('Figure 11f', 'Data corresponding to figure 11f (lower right)' ,   'Normalized differential $tt\gamma$ production cross section as a function of  ' + labels['unfReco_jetPt'].replace('[GeV]','') + '.')


metadata['dilctZ']  =  ('Figure 12a', 'Data corresponding to figure 12a (upper left)' ,  'Negative log-likelihood difference with respect to the best fit value as a function of the Wilson coefficient $c_{tZ}$, using the photon pT distribution from the dilepton analysis.')
metadata['comctZ']  =  ('Figure 12b', 'Data corresponding to figure 12b (upper right)' , 'Negative log-likelihood difference with respect to the best fit value as a function of the Wilson coefficient $c_{tZ}$, using the combination of photon pT distributions from the dilepton and lepton+jets analyses.')
metadata['dilctZI']  = ('Figure 12c', 'Data corresponding to figure 12c (lower left)' ,  'Negative log-likelihood difference with respect to the best fit value as a function of the Wilson coefficient $c^{I}_{tZ}$, using the photon pT distribution from the dilepton analysis.')
metadata['comctZI']  = ('Figure 12d', 'Data corresponding to figure 12d (lower right)' , 'Negative log-likelihood difference with respect to the best fit value as a function of the Wilson coefficient $c^{I}_{tZ}$, using the combination of photon pT distributions from the dilepton and lepton+jets analyses.')


metadata['eft2dDil']  = ('Figure 13a', 'Data corresponding to figure 13a (left)' , 'Negative log-likelihood ratio with respect to the best fit value as a function of Wilson coefficients $c_{tZ}$ and $c^{I}_{tZ}$ from the interpretation of the dilepton measurement.')
metadata['eft2dCom']  = ('Figure 13b', 'Data corresponding to figure 13b (right)' , 'Negative log-likelihood ratio with respect to the best fit value as a function of Wilson coefficients $c_{tZ}$ and $c^{I}_{tZ}$ from the interpretation of the dilepton and lepton+jets measurements combined.')




for dist in unfdistList:
  metadata['systCov' + dist ] = ('Syst. covariance for ' + labels[dist] + ' (non-normalized)',   'Additional material related to ' + metadata['diff' + dist][0].lower() + '.' , 'The covariance matrix of the systematic uncertainties and MC statistical uncertainties for the differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')
  metadata['statCov' + dist ] = ('Stat. covariance for ' + labels[dist] + ' (non-normalized)',   'Additional material related to ' + metadata['diff' + dist][0].lower() + '.' , 'The covariance matrix of the data statistical uncertainties for the differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')
  metadata['systCorr' + dist] = ('Syst. correlation for ' + labels[dist], 'Additional material related to ' + metadata['diff' + dist][0].lower() + '.' , 'Correlation matrix of the systematic uncertainty in the absolute differential cross section as a function of ' + labels[dist].replace('[GeV]', '') + '.')
  metadata['statCorr' + dist] = ('Stat. correlation for ' + labels[dist], 'Additional material related to ' + metadata['diff' + dist][0].lower() + '.' , 'Correlation matrix of the statistical uncertainty in the absolute differential cross section as a function of ' + labels[dist].replace('[GeV]', '') + '.')

  metadata['systCov' + dist  + '_norm'] = ('Syst. covariance for ' + labels[dist] + ' (normalized)',   'Additional material related to ' + metadata['diff' + dist + '_norm'][0].lower() + '.' , 'The covariance matrix of the systematic uncertainties and MC statistical uncertainties for the normalized differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')
  metadata['statCov' + dist  + '_norm'] = ('Stat. covariance for ' + labels[dist] + ' (normalized)',   'Additional material related to ' + metadata['diff' + dist + '_norm'][0].lower() + '.' , 'The covariance matrix of the data statistical uncertainties for the normalized differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')
  metadata['systCorr' + dist + '_norm'] = ('Syst. correlation for ' + labels[dist] + ' (normalized)',  'Additional material related to ' + metadata['diff' + dist + '_norm'][0].lower() + '.' , 'The correlation matrix of the systematic uncertainties and MC statistical uncertainties for the normalized differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')
  metadata['statCorr' + dist + '_norm'] = ('Stat. correlation for ' + labels[dist] + ' (normalized)',  'Additional material related to ' + metadata['diff' + dist + '_norm'][0].lower() + '.' , 'The correlation matrix of the data statistical uncertainties for the normalized differential ' + labels[dist].replace('[GeV]', '') + ' distribution.')









# clear output folder first
files = glob.glob('output/*')
for f in files:
  # print(f)
  os.remove(f)


# round all elements of a list
def roundList(list, dec):
  list = [round(i, dec) for i in list]
  return list




sub = Submission()


# TODO 
# might want to round the stat and syst uncertainties
# add proper labeling, titles, etc
# make for unfolding results
# adding images is a problem but can always do it manually



# for normal data vs mc plots


#######################################################
# DATA - MC PLOTS
#######################################################

for dist in dataMCList:
  dataR = RootFileReader('inputNormal/data' + dist + '.root' )
  nonpR = RootFileReader('inputNormal/nonp' + dist + '.root' )
  ttgR = RootFileReader('inputNormal/ttg' + dist + '.root' )
  zgR = RootFileReader('inputNormal/zg' + dist + '.root' )
  STR = RootFileReader('inputNormal/ST' + dist + '.root' )
  otherR = RootFileReader('inputNormal/other' + dist + '.root' )
  totalMCR = RootFileReader('inputNormal/totalMC' + dist + '.root' )
  systupR = RootFileReader('inputNormal/systup' + dist + '.root' )
  


  data = dataR.read_hist_1d('data')
  nonp = nonpR.read_hist_1d('nonp')
  ttg = ttgR.read_hist_1d('ttg')
  zg = zgR.read_hist_1d('zg')
  ST = STR.read_hist_1d('ST')
  other = otherR.read_hist_1d('other')
  totalMC = totalMCR.read_hist_1d('totalMC')
  systup = systupR.read_hist_1d('systup')
  

  # pdb.set_trace()

  # Create variable objects
  x = Variable(labels[dist], is_independent=True, is_binned=True)
  x.values = data["x_edges"]

  

  datavar = Variable("Observed", is_independent=False, is_binned=False)
  datavar.values = data["y"]
  
  datastat = Uncertainty('stat')
  datastat.values = roundList(data['dy'], 2)

  datavar.add_uncertainty(datastat)

  nonpvar =     Variable("nonprompt $\gamma$", is_independent=False, is_binned=False)
  ttgvar =      Variable("$tt \gamma$", is_independent=False, is_binned=False)
  zgvar =       Variable("$Z\gamma$", is_independent=False, is_binned=False)
  STvar =       Variable("Single-t+$\gamma$", is_independent=False, is_binned=False)
  othervar =    Variable("Other+$\gamma$", is_independent=False, is_binned=False)
  totalMCvar =  Variable("Total prediction", is_independent=False, is_binned=False)
  
  nonpvar.values = nonp["y"]
  ttgvar.values = ttg["y"]
  zgvar.values = zg["y"]
  STvar.values = ST["y"]
  othervar.values = other["y"]
  totalMCvar.values = totalMC["y"]

  systupvar =  Uncertainty('syst')
  systupvar.values = roundList(systup['y'], 2)
  totalMCvar.add_uncertainty(systupvar)

  datavar.add_qualifier("SQRT(S)" , 13, 'TeV')
  datavar.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')



  table = Table(metadata['dataMC' + dist][0])
  for var in [x,datavar,totalMCvar, ttgvar, zgvar, STvar, othervar, nonpvar]:
    table.add_variable(var)

  table.location = metadata['dataMC' + dist][1]
  table.description = metadata['dataMC' + dist][2]

  table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
  table.keywords["cmenergies"] = [13000.0]
  table.keywords["observables"] = ["N"]
  table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]



  # table.add_image("plots/" + dist + ".png")

  sub.add_table(table)

# for unfolding results NOTE: norm and non-norm
# can load directly from unfoldedRoots folder



#######################################################
# CHANNEL PLOT
#######################################################



table = Table('Figure 7')

c = Variable('Channel', is_independent=True, is_binned=False)


c.values = [
'Combined',
'$ee$',
'$e\mu$',
'$\mu\mu$',
]

t = Variable('Fiducial cross section [fb]', is_independent=False, is_binned=False)

t.values = [
173.5,
172.6,
173.9,
177.6
]

ccstat =  Uncertainty('stat')
ccstat.values = [
2.5,
5.6,
3.1,
6.3
]


ccsyst =  Uncertainty('syst')
ccsyst.values = [
6.3,
7.8,
6.3,
9.7
]



t.add_uncertainty(ccstat)
t.add_uncertainty(ccsyst)


t.add_qualifier("SQRT(S)" , 13, 'TeV')
t.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

table.add_variable(c)
table.add_variable(t)

table.location = 'Data corresponding to figure 7'
table.description = 'Fiducial $tt\gamma$ production cross section in the dilepton final state measured for different lepton flavour channels, and the combined result.'


table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
table.keywords["cmenergies"] = [13000.0]
table.keywords["observables"] = ["N"]
table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]
table.keywords["phrases"] += ['lepton+jets']

sub.add_table(table)







#######################################################
# UNFOLDING PLOTS
#######################################################

for normCase in ['', '_norm']:
  for dist in unfdistList:
    dataR = RootFileReader('../unfolding/unfoldedRoots/' + dist + 'obsTotUnc' + normCase + '.root')
    HW7R  = RootFileReader('../unfolding/unfoldedRoots/' + dist + 'HW7' + normCase + '.root')
    statR = RootFileReader('../unfolding/unfoldedRoots/' + dist + 'obsStatUnc' + normCase + '.root')
    systR = RootFileReader('../unfolding/unfoldedRoots/' + dist + 'obsSystUnc' + normCase + '.root')
    theoR = RootFileReader('../unfolding/unfoldedRoots/' + dist + 'theo' + normCase + '.root')

    data = dataR.read_hist_1d('dummyName')
    HW7  = HW7R.read_hist_1d('dummyName')
    stat = statR.read_hist_1d('dummyName')
    syst = systR.read_hist_1d('dummyName')
    theo = theoR.read_hist_1d('dummyName')
    

    # Create variable objects
    x = Variable(labels[dist], is_independent=True, is_binned=True)
    x.values = data["x_edges"]

    datavar = Variable("Observed", is_independent=False, is_binned=False)
    datavar.values = roundList(data["y"], (4 if normCase else 2))
    
    statunc = Uncertainty('stat')
    statunc.values = roundList(stat['dy'], (4 if normCase else 2))
    datavar.add_uncertainty(statunc)

    systunc =  Uncertainty('syst')
    systunc.values = roundList(syst['dy'], (4 if normCase else 2))
    datavar.add_uncertainty(systunc)

    HW7var = Variable("Theory Herwig", is_independent=False, is_binned=False)
    HW7var.values = roundList(HW7["y"], (4 if normCase else 2))

    theovar = Variable("Theory Pythia8", is_independent=False, is_binned=False)
    theovar.values = roundList(theo["y"], (4 if normCase else 2))

    theounc = Uncertainty('theory unc.')
    theounc.values = roundList(theo['dy'], (4 if normCase else 2))
    theovar.add_uncertainty(theounc)

    datavar.add_qualifier("SQRT(S)" , 13, 'TeV')
    datavar.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')
    theovar.add_qualifier("SQRT(S)" , 13, 'TeV')
    theovar.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')
    HW7var.add_qualifier("SQRT(S)" , 13, 'TeV')
    HW7var.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')


    table = Table(metadata['diff' + dist + normCase][0])
    for var in [x, datavar, theovar, HW7var]:
      table.add_variable(var)

    table.location = metadata['diff' + dist + normCase][1]
    table.description = metadata['diff' + dist + normCase][2]

    table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
    table.keywords["cmenergies"] = [13000.0]
    table.keywords["observables"] = ["N"]
    table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]

    # table.add_image("plots/" + dist + ".png")

    sub.add_table(table)



#######################################################
# COVARIANCE AND RESPONSE MATRICES
#######################################################

# note done: add stat, correl, and refine/label etc

# for normCase in ['', '_norm']:
for normCase in ['']:
  for dist in unfdistList:
    # for plotType in ['systCov', 'statCov', 'systCorr', 'statCorr']:
    for plotType in ['systCorr', 'statCorr']:
      # Create a reader for the input file
      reader = RootFileReader("../unfolding/unfoldedRoots/" + dist + plotType + normCase + ".root")
      data = reader.read_hist_2d("dummyName")

      # Create variable objects
      x = Variable(labels[dist], is_independent=True, is_binned=True)
      x.values = data["x_edges"]

      y = Variable(labels[dist] + ' ' , is_independent=True, is_binned=True)
      y.values = data["y_edges"]

      correlation = Variable(("correlation" if plotType.count('Corr') else "covariance"), is_independent=False, is_binned=False, units= ('%' if plotType.count('Corr') else 'fb$^{2}$'))
      if plotType.count('Corr'):
        zval = [i * 100. for i in data["z"]] 
      else:
        zval = data["z"] 
      correlation.values = roundList(zval, (7 if (normCase and not plotType.count('Corr')) else 3))

      table = Table(metadata[plotType + dist + normCase][0].replace(' [GeV]',''))
      for var in [x,y,correlation]:
        table.add_variable(var)

      table.location = metadata[plotType + dist + normCase][1]
      table.description = metadata[plotType + dist + normCase][2]
      correlation.add_qualifier("SQRT(S)" , 13, 'TeV')
      correlation.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

      table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
      table.keywords["cmenergies"] = [13000.0]
      table.keywords["observables"] = ["N"]
      table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]


      sub.add_table(table)


# EFT



for plot in ['dilctZ', 'comctZ', 'dilctZI', 'comctZI']:

  table = Table(metadata[plot][0])

  c = Variable('$C_{tZ}$', is_independent=True, is_binned=False, units='$(\Lambda/TeV)^{2}$')
  c.values = numpy.loadtxt( 'inputEFT/' + plot + 'exp.txt')[:,0]

  nllexp = Variable("$-2\Delta lnN$ (expected)", is_independent=False, is_binned=False)
  nllexp.values = numpy.loadtxt( 'inputEFT/' + plot + 'exp.txt')[:,1]

  nllobs = Variable("$-2\Delta lnN$ (observed)", is_independent=False, is_binned=False)
  nllobs.values = numpy.loadtxt( 'inputEFT/' + plot + 'obs.txt')[:,1]


  nllexp.add_qualifier("SQRT(S)" , 13, 'TeV')
  nllexp.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

  nllobs.add_qualifier("SQRT(S)" , 13, 'TeV')
  nllobs.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')



  table.add_variable(c)
  table.add_variable(nllobs)
  table.add_variable(nllexp)


  table.location = metadata[plot][1]
  table.description = metadata[plot][2]

  # TODO maybe adjust keywords for combined plots ?

  table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
  table.keywords["cmenergies"] = [13000.0]
  table.keywords["observables"] = ["CLS", "CL"]
  table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]
  if plot.count('com'):
    table.keywords["phrases"] += ['lepton+jets']

  sub.add_table(table)



table = Table(metadata['eft2dDil'][0])

c1 = Variable('$C_{tZ}$', is_independent=True, is_binned=False, units='$(\Lambda/TeV)^{2}$')
c1.values = numpy.loadtxt( 'inputEFT/dil2d.txt')[:,0]

c2 = Variable('$C^{I}_{tZ}$', is_independent=True, is_binned=False, units='$(\Lambda/TeV)^{2}$')
c2.values = numpy.loadtxt( 'inputEFT/dil2d.txt')[:,1]


nll = Variable("$-2\Delta lnN$", is_independent=False, is_binned=False)
nll.values = numpy.loadtxt( 'inputEFT/dil2d.txt')[:,2]
nll.add_qualifier("SQRT(S)" , 13, 'TeV')
nll.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

table.add_variable(c1)
table.add_variable(c2)
table.add_variable(nll)


table.location = metadata['eft2dDil'][1]
table.description = metadata['eft2dDil'][2]

table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
table.keywords["cmenergies"] = [13000.0]
table.keywords["observables"] = ["N"]
table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]

sub.add_table(table)



table = Table(metadata['eft2dCom'][0])

c1 = Variable('$C_{tZ}$', is_independent=True, is_binned=False, units='$(\Lambda/TeV)^{2}$')
c1.values = numpy.loadtxt( 'inputEFT/com2d.txt')[:,0]

c2 = Variable('$C^{I}_{tZ}$', is_independent=True, is_binned=False, units='$(\Lambda/TeV)^{2}$')
c2.values = numpy.loadtxt( 'inputEFT/com2d.txt')[:,1]


nll = Variable("$-2\Delta lnN$", is_independent=False, is_binned=False)
nll.values = numpy.loadtxt( 'inputEFT/com2d.txt')[:,2]
nll.add_qualifier("SQRT(S)" , 13, 'TeV')
nll.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

table.add_variable(c1)
table.add_variable(c2)
table.add_variable(nll)


table.location = metadata['eft2dCom'][1]
table.description = metadata['eft2dCom'][2]

table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
table.keywords["cmenergies"] = [13000.0]
table.keywords["observables"] = ["N"]
table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]
table.keywords["phrases"] += ['lepton+jets']
sub.add_table(table)



# EFT tables (like, actual tables)


table = Table('Table 5')

c = Variable('Wilson coefficient', is_independent=True, is_binned=False)


c.values = [
'$c_{tZ}$',
'$c_{tZ}$',
'$c^{I}_{tZ}$',
'$c^{I}_{tZ}$ ',
'$c_{tZ}$',
'$c_{tZ}$',
'$c^{I}_{tZ}$',
'$c^{I}_{tZ}$ ',
]

t = Variable('fit case', is_independent=True, is_binned=False)

t.values = [
'expected, $c^{I}_{tZ}$=0',
'expected, profiled',
'expected, $c_{tZ}$=0',
'expected, profiled',
'observed, $c^{I}_{tZ}$=0',
'observed, profiled',
'observed, $c_{tZ}$=0',
'observed, profiled',
]



CL6 = Variable("68% CL interval", is_independent=False, is_binned=False, units='$(\Lambda/TeV)^2$')
CL6.values = [
'[-0.28, 0.35]                      ',
'[-0.28, 0.35]                      ',
'[-0.33, 0.30]                      ',
'[-0.33, 0.30]                      ',
'[-0.43, -0.09]                     ',
'[-0.43, 0.17]                      ',
'[-0.47, -0.030] $\cup$ [0.07, 0.38]',
'[-0.43, 0.33]                      '
]

CL9 = Variable("95% CL interval", is_independent=False, is_binned=False, units='$(\Lambda/TeV)^2$')
CL9.values = [
'[-0.42, 0.49]',
'[-0.42, 0.49]',
'[-0.47, 0.45]',
'[-0.47, 0.45]',
'[-0.53, 0.52]',
'[-0.53, 0.51]',
'[-0.58, 0.52]',
'[-0.56, 0.51]'
]



CL6Comb = Variable("68% CL interval", is_independent=False, is_binned=False, units='$(\Lambda/TeV)^2$')
CL6Comb.values = [
'[-0.15, 0.19]                     ',
'[-0.15, 0.19]                     ',
'[-0.17, 0.18]                     ',
'[-0.18, 0.18]                     ',
'[-0.30, -0.13]                    ',
'[-0.30, 0.00]                     ',
'[-0.32, -0.13] $\cup$ [0.16, 0.29]',
'[-0.28, 0.23]                     '
]

CL9Comb = Variable("95% CL interval", is_independent=False, is_binned=False, units='$(\Lambda/TeV)^2$')
CL9Comb.values = [
'[-0.25, 0.29]',
'[-0.25, 0.29]',
'[-0.27, 0.27]',
'[-0.27, 0.27]',
'[-0.36, 0.31]',
'[-0.36, 0.31]',
'[-0.38, 0.36]',
'[-0.36, 0.35]'
]




CL9.add_qualifier("SQRT(S)" , 13, 'TeV')
CL9.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')
CL6.add_qualifier("SQRT(S)" , 13, 'TeV')
CL6.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

# t.add_qualifier("CHANNEL" , "dilepton")
CL9.add_qualifier("CHANNEL" , "dilepton")
CL6.add_qualifier("CHANNEL" , "dilepton")

CL6Comb.add_qualifier("SQRT(S)" , 13, 'TeV')
CL9Comb.add_qualifier("SQRT(S)" , 13, 'TeV')
CL6Comb.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')
CL9Comb.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

CL6Comb.add_qualifier("CHANNEL" , "dilepton & l+jets")
CL9Comb.add_qualifier("CHANNEL" , "dilepton & l+jets")



table.add_variable(c)
table.add_variable(t)
table.add_variable(CL6)
table.add_variable(CL9)
table.add_variable(CL6Comb)
table.add_variable(CL9Comb)

table.location = 'Data corresponding to table 5'
table.description = 'One-dimensional CL intervals for the Wilson coefficients  $c_{tZ}$ and $c^{I}_{tZ}$, using the photon $p_{T}$ distribution from the dilepton analysis, or the combination of photon pT distributions from the dilepton and lepton+jets analyses.'



table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
table.keywords["cmenergies"] = [13000.0]
table.keywords["observables"] = ["N"]
table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]
table.keywords["phrases"] += ['lepton+jets']

sub.add_table(table)



#######################################################
# COMPARISON PLOT
#######################################################



table = Table('Figure 14')



w = Variable('Wilson coefficient', is_independent=True, is_binned=False)
w.values = [
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c_{tZ}$',
'$c^{I}_{tZ}$',
'$c^{I}_{tZ}$',
'$c^{I}_{tZ}$',
'$c^{I}_{tZ}$'
]


c = Variable('Dataset & method', is_independent=False, is_binned=False)
c.values = [
'CMS $77.5$ $fb^{-1}$ $ttZ$',
'CMS $138$ $fb^{-1}$ $ttZ$ & $tZq$ individually',
'CMS $138$ $fb^{-1}$ $ttZ$ & $tZq$ marginalized',
'CMS $137$ $fb^{-1}$ $tt\gamma$ (l+jets)',
'CMS $138$ $fb^{-1}$ $tt\gamma$ (dilepton)',
'CMS $138$ $fb^{-1}$ $tt\gamma$ (l+jets + dilepton)',
'Global fit individually',
'Global fit marginalized',
'CMS $77.5$ $fb^{-1}$ $ttZ$',
'CMS $137$ $fb^{-1}$ $tt\gamma$ (l+jets)',
'CMS $138$ $fb^{-1}$ $tt\gamma$ (dilepton)',
'CMS $138$ $fb^{-1}$ $tt\gamma$ (l+jets + dilepton)',
]

ctz = Variable('$95\%$ CL interval', is_independent=False, is_binned=False)

ctz.values = [
'[-1.1, 1.1]',
'[-0.76, 0.71',
'[-0.85, 0.76]',
'[-0.43, 0.38]',
'[-0.53, 0.52]',
'[-0.36, 0.31]',
'[-0.58, 2.16]',
'[-1.20, 2.50]',
'[-1.2, 1.2]',
'[-0.43, 0.43]',
'[-0.58, 0.52]',
'[-0.38, 0.36]'
]


# ctzm = Variable('$c_{tZ}$ marg.', is_independent=False, is_binned=False)

# ctzm.values = [
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]'
# ]

# ctzi = Variable('$c^{I}_{tZ}$', is_independent=False, is_binned=False)

# ctzi.values = [
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]'
# ]



# ctzim = Variable('$c^{I}_{tZ}$ marg.', is_independent=False, is_binned=False)

# ctzim.values = [
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]',
# '[-99,99]'
# ]



# ctz.add_qualifier("SQRT(S)" , 13, 'TeV')
# ctz.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

# ctzi.add_qualifier("SQRT(S)" , 13, 'TeV')
# ctzi.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

# ctzm.add_qualifier("SQRT(S)" , 13, 'TeV')
# ctzm.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

# ctzim.add_qualifier("SQRT(S)" , 13, 'TeV')
# ctzim.add_qualifier("LUMINOSITY" , 138 ,'fb$^{-1}$')

table.add_variable(w)
table.add_variable(c)
table.add_variable(ctz)
# table.add_variable(ctzi)
# table.add_variable(ctzm)
# table.add_variable(ctzim)

table.location = 'Data corresponding to figure 14'
table.description = 'Comparison of observed $95\%$ CL intervals for the Wilson coefficients $c_{tZ}$ and $c^{I}_{tZ}$. Results are shown from a CMS ttZ measurement [JHEP 03 (2020) 056], from a CMS ttZ & tZq interpretation [arXiv:2107.13896], from a CMS ttG (lepton+jets) measurement [arXiv:2107.01508], from this measurement, and from a global fit by J. Ellis et al. [JHEP 04 (2021) 279].'


# table.keywords["reactions"] = ["P P --> TOP TOPBAR X", "P P --> TOP TOPBAR GAMMA"]
# table.keywords["cmenergies"] = [13000.0]
# table.keywords["observables"] = ["N"]
# table.keywords["phrases"] = ["Top", "Quark", "Photon", "dilepton", "dileptonic", "Cross Section", "Proton-Proton Scattering", "Inclusive", "Differential"]
# table.keywords["phrases"] += ['lepton+jets']

sub.add_table(table)




sub.create_files("./output/")
