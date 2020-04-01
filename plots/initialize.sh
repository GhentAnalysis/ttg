#!/bin/bash

#  Zg enriched plots needed for Zg estimation/correction
# ./ttgPlots.py --year 2016 --channel all --selection llg-mll40-offZ-llgOnZ-photonPt20 --tag phoCBfull-forZgest --noZgCorr --runLocal
# ./ttgPlots.py --year 2017 --channel all --selection llg-mll40-offZ-llgOnZ-photonPt20 --tag phoCBfull-forZgest --noZgCorr --runLocal
# ./ttgPlots.py --year 2018 --channel all --selection llg-mll40-offZ-llgOnZ-photonPt20 --tag phoCBfull-forZgest --noZgCorr --runLocal


# # for nonprompt estimation, uses the default stack (without estimation)
# ./ttgPlots.py --year 2016 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2016 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest
# ./ttgPlots.py --year 2016 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2016 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest


# ./ttgPlots.py --year 2017 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2017 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest
# ./ttgPlots.py --year 2017 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2017 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest


# ./ttgPlots.py --year 2018 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2018 --channel all --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20     --tag phoCB-passChgIso-sidebandSigmaIetaIeta-forNPest
# ./ttgPlots.py --year 2018 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-passSigmaIetaIeta-forNPest    
# ./ttgPlots.py --year 2018 --channel all --selection llg-mll40-njet1p-onZ-llgNoZ-photonPt20-chIso0to10 --tag phoCB-failChgIso-sidebandSigmaIetaIeta-forNPest



# # # for closure checking in MC, needed for NP systematic
# ./ttgPlots.py --year 2016 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribMC-forNPclosure
# ./ttgPlots.py --year 2017 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribMC-forNPclosure
# ./ttgPlots.py --year 2018 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribMC-forNPclosure


# # # not strictly needed, DD estimate vs MC, alternative closure check
# ./ttgPlots.py --year 2016 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribDD-forNPclosure
# ./ttgPlots.py --year 2017 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribDD-forNPclosure
# ./ttgPlots.py --year 2018 --channel noData --selection llg-mll40-signalRegion-offZ-llgNoZ-photonPt20 --tag phoCBfull-compRewContribDD-forNPclosure


