Repository for tt+gamma analysis in the dilepton channel - version for full RunII data

# Setup
The ttg repository is typically checked out within CMSSW, as there are a few little dependencies (e.g. pileup distributions).
Checkout commands:
```
cd $CMSSW_BASE/src;
git clone https://github.com/GhentAnalysis/ttg;
git checkout RunII
```

# Analysis to do list
## In progress
 * Generalize plotting code

## TODO
 * Find/produce samples,SF, etc for 17 and 18
 * Produce plotting code to combine histograms from the three separate years
 * Checking validity of MET/JetHT reference triggers (e.g. correlation ratio as discussed in Section 3 of AN-17-197)
 * Reproducing AN-17-197 step by step for full Run II

## Recently finished
 * Basic generalization of the reduceTuple code
 * Implement changes to match new heavyneutrino code/ntuples

# Input tuples
Tuples are produced in the heavyNeutrino framework (https://github.com/GhentAnalysis/heavyNeutrino)
using option 'dilep' (basic skim of 2 leptons without additional requirements). Currently the master branch is used.

# Structure of the repository

## tools
Small helper functions and scripts.

## samples
Contains the Sample object class and several configuration files (x-sec, styles, how to stack histograms,...)
to handle them.

## reduceTuple
The reduceTuple.py script skims the heavyNeutrino tuples based on a given lepton and photon id
Some usuful variables like m(ll), m(llg), deltaR,... are added to the tuples, such that they can be
fastly accessed by second-level (i.e. plotting) scripts.

## plots
This directory contains the plotting scripts as well as the scripts to do the fits. The plotting script is called 
ttgPlots.py and runs over reduced tuples (as produced by the reduceTuple/reduceTuple.py scripts) which are based
on the original heavyNeutrino tuples but skimmed for lepton and photon id requirements.
The ttgPlots.py script creates plots in .png, .pdf, .root,.C and .pkl formats. The .pkl format is used as an
input to the fitting script.

Histograms will be made per year, and can then be combined for final analysis
