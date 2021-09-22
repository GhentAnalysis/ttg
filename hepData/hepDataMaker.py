from hepdata_lib import RootFileReader, Submission, Variable, Table, Uncertainty
import pdb


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
          'unfReco_l1l2_ptsum' :    '$p_{T}(l1)+p_{T}(l2)$ [GeV]'
          }


# Create a reader for the input file
reader = RootFileReader("inputUnfolding/unfReco_phPtsystCov.root")
data = reader.read_hist_2d("covarHist")

# Create variable objects
x = Variable("First Bin", is_independent=True, is_binned=False)
x.values = data["x"]

y = Variable("Second Bin", is_independent=True, is_binned=False)
y.values = data["y"]

correlation = Variable("Covariance coefficient", is_independent=False, is_binned=False)
correlation.values = data["z"]

table = Table("Covariance test")
for var in [x,y,correlation]:
  table.add_variable(var)

# Create the submission object and write output
sub = Submission()
sub.add_table(table)
sub.create_files("./output/")


# TODO 
# might want to round the stat and syst uncertainties
# automate for all response matrices as well
# add proper labeling, titles, etc
# make for unfolding results
# adding images is a problem but can always do it manually


for dist in distList:
  dataR = RootFileReader('inputUnfolding/data' + dist + '.root' )
  nonpR = RootFileReader('inputUnfolding/nonp' + dist + '.root' )
  ttgR = RootFileReader('inputUnfolding/ttg' + dist + '.root' )
  zgR = RootFileReader('inputUnfolding/zg' + dist + '.root' )
  STR = RootFileReader('inputUnfolding/ST' + dist + '.root' )
  otherR = RootFileReader('inputUnfolding/other' + dist + '.root' )
  totalMCR = RootFileReader('inputUnfolding/totalMC' + dist + '.root' )
  systupR = RootFileReader('inputUnfolding/systup' + dist + '.root' )
  


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
  x = Variable(labels[dist], is_independent=True, is_binned=False)
  x.values = data["x"]

  datavar = Variable("Observed", is_independent=False, is_binned=False)
  datavar.values = data["y"]
  
  datastat = Uncertainty('stat')
  datastat.values = data['dy']

  datavar.add_uncertainty(datastat)

  nonpvar =     Variable("nonprompt $\gamma$", is_independent=False, is_binned=False)
  ttgvar =      Variable("$t \bar{t} \gamma$", is_independent=False, is_binned=False)
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
  systupvar.values = systup['y']
  totalMCvar.add_uncertainty(systupvar)




  table = Table("Title test")
  for var in [x,datavar,totalMCvar, ttgvar, zgvar, STvar, othervar, nonpvar]:
    table.add_variable(var)

  # table.add_image("plots/" + dist + ".png")

  # Create the submission object and write output
  # sub = Submission()
  sub.add_table(table)
  sub.create_files("./output/")

# Data = reader_data.read_hist_1d("h_bprimemass_SRlm")

# signal = reader_signal.read_hist_1d("h_bprimemass_SRlm")

