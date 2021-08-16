Repository for tt+gamma analysis in the dilepton channel - version for full RunII data

# Setup
The ttg repository is typically checked out within CMSSW, as there are a few little dependencies (e.g. pileup distributions).
Checkout commands:
```
cd $CMSSW_BASE/src;
git clone https://github.com/GhentAnalysis/ttg;
cd ttg;
git checkout RunII
```

# Input tuples
Tuples are produced in the heavyNeutrino framework (https://github.com/GhentAnalysis/heavyNeutrino)
using option 'dilep' (basic skim of 2 leptons without additional requirements). Currently the master branch is used.
