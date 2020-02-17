#!/bin/env bash

export LD_LIBRARY_PATH=../../:$LD_LIBRARY_PATH

inputPath="srm://maite.iihe.ac.be//pnfs/iihe/cms/store/user/gmestdac/heavyNeutrino/TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8/localSubmission_2016-magic9/20200109_120946/0000/"

inputFile="${inputPath}dilep_534.root,${inputPath}dilep_535.root,${inputPath}dilep_536.root"

python kinfit.py \
--max=2000 \
--toys=1000 \
--input=${inputFile}
