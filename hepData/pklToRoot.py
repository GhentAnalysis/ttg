import ROOT
import pickle
import pdb


def sumHists(names, hists, outName):
  sum = None
  for name in names:
    if not sum:
      sum = hists[name].Clone(outName)
    else:
      sum.Add(hists[name])
  return sum


sigDistList = [
  'nbtag',
  'njets',
  'unfReco_jetLepDeltaR',
  'unfReco_l1l2_ptsum',
  'unfReco_ll_deltaPhi',
  'unfReco_phAbsEta',
  'unfReco_phLepDeltaR',
  'unfReco_phPt'
  ]

NPdistList = [
  'PByield',
  'PBVDphoton_pt',
  ]

zgdistList = [
  'signalRegionsZoom',
  'dl_mass_small',
  'dlg_mass_zoom',
  'photon_pt'
]

postDistList = [
  'unfReco_phPt_ee_post',
  'unfReco_phPt_em_post',
  'unfReco_phPt_mm_post'
]



processes = { 'data':     ['DoubleMuondata', 'DoubleEG_datadata', 'MuonEGdata'],
              'dataee':   ['DoubleEG_data (2e)data (2e)'],
              'dataem':   ['MuonEGdata (1e, 1#mu)'],
              'datamm':   ['DoubleMuondata (2#mu)'],
              'nonp':     ['NPME_nonprompt-estimatenonprompt-estimate', 'NPEl_nonprompt-estimatenonprompt-estimate', 'NPMu_nonprompt-estimatenonprompt-estimate'],
              'nonpee':   ['NPEl_nonprompt-estimatenonprompt-estimate'],
              'nonpem':   ['NPME_nonprompt-estimatenonprompt-estimate'],
              'nonpmm':   ['NPMu_nonprompt-estimatenonprompt-estimate'],
              'nonpMC':   ['TTGamma_DilPCUT_nonpromptnonprompt', 'singleTop_nonpromptnonprompt', 'DY_M50nonprompt', 'TT_Dilnonprompt', 'ZG_nonpromptnonprompt', 'other_nonpromptnonprompt'],
              'ttg':      ['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'],
              'zg':       ['ZG_Z#gamma (genuine)Z#gamma (genuine)'],
              'ST':       ['singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)'],
              'other':    ['other_Other+#gamma (genuine)Other+#gamma (genuine)'],
              'ttMC':     ['TT_Dilt#bar{t} (nonprompt)'],
              'ttEst':    ['TT_Dil_nonprompt-estimate_(MC)nonprompt-estimate (MC)']
              }






for dist in sigDistList:
  hists = pickle.load(open('picklesNormal/' + dist + '.pkl','r'))
  systs = pickle.load(open('picklesNormal/' + dist + 'totalSys.pkl','r'))
  data = sumHists(processes['data'], hists[dist], 'data')
  ttg = sumHists(processes['ttg'], hists[dist], 'ttg')
  nonp = sumHists(processes['nonp'], hists[dist], 'nonp')
  zg = sumHists(processes['zg'], hists[dist], 'zg')
  ST = sumHists(processes['ST'], hists[dist], 'ST')
  other = sumHists(processes['other'], hists[dist], 'other')

  totalMC = ttg.Clone('totalMC')
  totalMC.Add(nonp)
  totalMC.Add(zg)
  totalMC.Add(ST)
  totalMC.Add(other)

  systup = totalMC.Clone('systup')
  systdown = totalMC.Clone('systdown')
  systup.Multiply(systs[0])
  systdown.Multiply(systs[1])

  # Note, averaging this for now

  systup.Add(systdown)
  systup.Scale(0.5)

  data.SaveAs('inputNormal/data' + dist + '.root')
  ttg.SaveAs('inputNormal/ttg' + dist + '.root')
  nonp.SaveAs('inputNormal/nonp' + dist + '.root')
  zg.SaveAs('inputNormal/zg' + dist + '.root')
  ST.SaveAs('inputNormal/ST' + dist + '.root')
  other.SaveAs('inputNormal/other' + dist + '.root')
  totalMC.SaveAs('inputNormal/totalMC' + dist + '.root')
  systup.SaveAs('inputNormal/systup' + dist + '.root')


for dist in zgdistList:
  # only difference is NP photons from MC and DY+ttbar is present etc?
  hists = pickle.load(open('picklesNormal/' + dist + '.pkl','r'))
  systs = pickle.load(open('picklesNormal/' + dist + 'totalSys.pkl','r'))
  data = sumHists(processes['data'], hists[dist], 'data')
  ttg = sumHists(processes['ttg'], hists[dist], 'ttg')
  nonp = sumHists(processes['nonpMC'], hists[dist], 'nonp')
  zg = sumHists(processes['zg'], hists[dist], 'zg')
  ST = sumHists(processes['ST'], hists[dist], 'ST')
  other = sumHists(processes['other'], hists[dist], 'other')

  totalMC = ttg.Clone('totalMC')
  totalMC.Add(nonp)
  totalMC.Add(zg)
  totalMC.Add(ST)
  totalMC.Add(other)

  systup = totalMC.Clone('systup')
  systdown = totalMC.Clone('systdown')
  systup.Multiply(systs[0])
  systdown.Multiply(systs[1])

  # Note, averaging this for now

  systup.Add(systdown)
  systup.Scale(0.5)

  data.SaveAs('inputNormal/data' + dist + '.root')
  ttg.SaveAs('inputNormal/ttg' + dist + '.root')
  nonp.SaveAs('inputNormal/nonp' + dist + '.root')
  zg.SaveAs('inputNormal/zg' + dist + '.root')
  ST.SaveAs('inputNormal/ST' + dist + '.root')
  other.SaveAs('inputNormal/other' + dist + '.root')
  totalMC.SaveAs('inputNormal/totalMC' + dist + '.root')
  systup.SaveAs('inputNormal/systup' + dist + '.root')


for dist in postDistList:
  # only difference is the lack of data (load it from pre-fit) + since it's per channel est histgram for each
  hists = pickle.load(open('picklesNormal/' + dist + '.pkl','r'))
  systs = pickle.load(open('picklesNormal/' + dist + 'totalSys.pkl','r'))

  histspre = pickle.load(open('picklesNormal/' + dist.replace('post','pre') + '.pkl','r'))
  data = sumHists(processes['data'+ dist.split('_')[2]], histspre['unfReco_phPt'], 'data')
  
  ttg = sumHists(processes['ttg'], hists['unfReco_phPt'], 'ttg')
  # only difference is NP photons from MC
  nonp = sumHists(processes['nonp'+ dist.split('_')[2] ], hists['unfReco_phPt'], 'nonp')
  zg = sumHists(processes['zg'], hists['unfReco_phPt'], 'zg')
  ST = sumHists(processes['ST'], hists['unfReco_phPt'], 'ST')
  other = sumHists(processes['other'], hists['unfReco_phPt'], 'other')

  totalMC = ttg.Clone('totalMC')
  totalMC.Add(nonp)
  totalMC.Add(zg)
  totalMC.Add(ST)
  totalMC.Add(other)

  systup = totalMC.Clone('systup')
  systdown = totalMC.Clone('systdown')
  systup.Multiply(systs[0])
  systdown.Multiply(systs[1])

  # Note, averaging this for now

  systup.Add(systdown)
  systup.Scale(0.5)

  data.SaveAs('inputNormal/data' + dist + '.root')
  ttg.SaveAs('inputNormal/ttg' + dist + '.root')
  nonp.SaveAs('inputNormal/nonp' + dist + '.root')
  zg.SaveAs('inputNormal/zg' + dist + '.root')
  ST.SaveAs('inputNormal/ST' + dist + '.root')
  other.SaveAs('inputNormal/other' + dist + '.root')
  totalMC.SaveAs('inputNormal/totalMC' + dist + '.root')
  systup.SaveAs('inputNormal/systup' + dist + '.root')



for dist in NPdistList:
  # only had ttbar from MC and ttbar from estimate (and syst unc)
  hists = pickle.load(open('picklesNormal/' + dist + '.pkl','r'))
  systs = pickle.load(open('picklesNormal/' + dist + 'totalSys.pkl','r'))
  ttMC = sumHists(processes['ttMC'], hists[dist], 'ttMC')
  ttEst = sumHists(processes['ttEst'], hists[dist], 'ttEst')

  # pdb.set_trace()
  systup = ttMC.Clone('systup')
  systdown = ttMC.Clone('systdown')
  systup.Multiply(systs[0])
  systdown.Multiply(systs[1])

  # Note, averaging this for now

  systup.Add(systdown)
  systup.Scale(0.5)

  ttMC.SaveAs('inputNormal/ttMC' + dist + '.root')
  ttEst.SaveAs('inputNormal/ttEst' + dist + '.root')
  systup.SaveAs('inputNormal/systup' + dist + '.root')
