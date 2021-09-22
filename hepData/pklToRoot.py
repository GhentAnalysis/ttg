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


distList = [
  'unfReco_phPt',
  # 'unfReco_phLepDeltaR',
  # 'unfReco_jetLepDeltaR',
  # 'unfReco_jetPt',
  # 'unfReco_ll_absDeltaEta',
  # 'unfReco_ll_deltaPhi',
  # 'unfReco_phAbsEta',
  # 'unfReco_phBJetDeltaR',
  # 'unfReco_phLep1DeltaR',
  # 'unfReco_phLep2DeltaR',
  # 'unfReco_Z_pt',
  # 'unfReco_l1l2_ptsum'
  ]

processes = { 'data': ['DoubleMuondata', 'DoubleEG_datadata', 'MuonEGdata'],
              'nonp': ['NPME_nonprompt-estimatenonprompt-estimate', 'NPEl_nonprompt-estimatenonprompt-estimate', 'NPMu_nonprompt-estimatenonprompt-estimate'],
              'ttg':  ['TTGamma_DilPCUTt#bar{t}#gamma (genuine)'],
              'zg':   ['ZG_Z#gamma (genuine)Z#gamma (genuine)'],
              'ST':   ['singleTop_Single-t+#gamma (genuine)Single-t+#gamma (genuine)'],
              'other': ['other_Other+#gamma (genuine)Other+#gamma (genuine)']}

for dist in distList:
  hists = pickle.load(open('pickles/' + dist + '.pkl','r'))
  systs = pickle.load(open('pickles/' + dist + 'totalSys.pkl','r'))
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

  data.SaveAs('inputUnfolding/data' + dist + '.root')
  ttg.SaveAs('inputUnfolding/ttg' + dist + '.root')
  nonp.SaveAs('inputUnfolding/nonp' + dist + '.root')
  zg.SaveAs('inputUnfolding/zg' + dist + '.root')
  ST.SaveAs('inputUnfolding/ST' + dist + '.root')
  other.SaveAs('inputUnfolding/other' + dist + '.root')
  totalMC.SaveAs('inputUnfolding/totalMC' + dist + '.root')
  systup.SaveAs('inputUnfolding/systup' + dist + '.root')

  # sftp://gmestdac@m6.iihe.ac.be/storage_mnt/storage/user/gmestdac/TTG/CMSSW_10_2_10/src/ttg/hepData/inputUnfolding
  # pdb.set_trace()

# fun fact: dit script moet ge nog schrijven lad