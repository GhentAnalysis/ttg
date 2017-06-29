# ttg
Repository for tt+gamma analysis in the dilepton channel

# tuples
Tuples are produced in the heavyNeutrino framework (https://github.com/GhentAnalysis/heavyNeutrino)
using option 'TTG' (basic skim of 2 leptons and 1 photon without additional requirements)

# postprocessing of tuples
Using ttg/reduceTuple/reduceTuple.py the tuples are futher skimmed for a given lepton and photon id
Some usuful variables like m(ll), m(llg), deltaR,... are added to the tuples

# plotting script
See ttg/plots/ttgPlots.py
