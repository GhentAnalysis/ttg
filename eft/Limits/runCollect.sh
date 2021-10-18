#!/bin/bash

typ="photon_pt" # inclusive, photon_pt

ddir="eft"

#./collect.py --type=${typ} --year=2016 --dim=1d --input=${ddir} --mode=expected --toy=0
#./collect.py --type=${typ} --year=2016 --dim=1d --input=${ddir} --mode=all --toy=1

#./collect.py --type=${typ} --year=2016 --dim=1d --input=${ddir} --mode=all
#./collect.py --type=${typ} --year=2016 --dim=2d --input=${ddir} --mode=all

#./collect.py --type=${typ} --year=2017 --dim=1d --input=${ddir} --mode=all
#./collect.py --type=${typ} --year=2017 --dim=2d --input=${ddir} --mode=all

#./collect.py --type=${typ} --year=2018 --dim=1d --input=${ddir} --mode=all
#./collect.py --type=${typ} --year=2018 --dim=2d --input=${ddir} --mode=all

#for it in 10 11 12 13 14 15 16 17 18 19
#for it in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
#for it in 14 15 16 17 18 19
#do
#  mv eft_fit_photon_pt_Run2_Toy${it}/ctZ_1d/observed eft_fit_photon_pt_Run2_Toy${it}/ctZ_1d/expected
#  mv eft_fit_photon_pt_Run2_Toy${it}/ctZI_1d/observed eft_fit_photon_pt_Run2_Toy${it}/ctZI_1d/expected
#  ./collect.py --type=${typ} --year=Run2 --dim=1d --input=${ddir} --mode=expected --toy=${it}
#done

./collect.py --type=${typ} --year=Run2 --dim=1d --input=${ddir} --mode=all
./collect.py --type=${typ} --year=Run2 --dim=2d --input=${ddir} --mode=all

ddir="eftComb"

#./collect.py --type=${typ} --year=Run2 --dim=1d --input=${ddir} --mode=all
#./collect.py --type=${typ} --year=Run2 --dim=2d --input=${ddir} --mode=all
