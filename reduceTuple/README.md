# ttg/reduceTuple 

## reduceTuple.py
Script to transform the heavyNeutrino tuples into reducedTuples which only retain events which are triggered, fulfill the object ID requirements and/or some basic selection.
Also adds additional often-used kinematic variables and calculates/stores the needed weights for systematic variations. This makes the reducedTuples perfectly suited to perform
the analysis and make plots.

The reduceTuple.py script uses following helper codes
 * python/objectSelection.py defines the used lepton, photon and jet object selections as well as the calculation of some higher level variables based on them
 * python/btagEfficiency.py provides the class to return b-tagging efficiencies and uncertainties 
 * python/leptonSF.py provides the class to return lepton scale factors and uncertainties
 * python/leptonTrackingEfficiency.py does similar as the above for the lepton tracking efficiencies
 * python/photonSF.py provides the class for photon scale factors and uncertainties
 * python/puReweighting.py returns the pile-up reweighting function
 * python/triggerEfficiency.py provides the class to return trigger scale factors and uncertainties

## calcTriggerEff.py
Calculates the trigger efficiency (in 2D histograms) for the lepton triggers using unbiased MET triggers.

## makeTriggerSF.py
Creates 2D histograms with data/MC scale factors, based on the trigger efficiencies calculated using calcTriggerEff.py.

## calcMCBTagEfficiency.py
Calculates the MC b-tagging efficiencies needed for the b-tagging scale factors using method 1a (see python/btagEfficiency.py).

## submitFromFailedLog.py
Resubmits jobs which returned with a failed log.
