#!/bin/bash

year="Run2"
#year="2016"
typ="photon_pt" # inclusive, photon_pt
dir="eft"
#dir="eftComb"
opt="--cluster"
#opt="--multicore"
#npoi=1
npoi=7
toy=-1
#toy=19

#./fit.py --ws ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy}
#./fit.py --ws ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --obs
#./fit.py --ws ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --dim 2d
#./fit.py --ws ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --dim 2d --obs

#./fit.py --fit ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy}
#./fit.py --fit ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --obs
./fit.py --fit ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --dim 2d
./fit.py --fit ${opt} --type=${typ} --year=${year} --output=${dir} --npoi=${npoi} --toy=${toy} --dim 2d --obs
