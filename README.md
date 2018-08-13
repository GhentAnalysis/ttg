Repository for tt+gamma analysis in the dilepton channel

# Analysis to do list
## In progress
Implemented, but not yet propagated to plots and/or final results
 * Muon SF systematic uncertainties
 * Make systematic band assymetric (already assymetric for the combine fit, but not in the plots)
 * SF and OF separate measurements

## To do
 * AN systematic table + input range
 * AN overlap removal discussion
 * Review of trigger strategy
 * Post-fit signal region plot
 * Separate stat and sys errors (need combine expert)
 * Check ISR and FSR


# Input tuples
Tuples are produced in the heavyNeutrino framework (https://github.com/GhentAnalysis/heavyNeutrino)
using option 'dilep' (basic skim of 2 leptons without additional requirements). The branch used is
currently CMSSW\_8\_0\_X

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


