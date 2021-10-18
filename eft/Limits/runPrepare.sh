#!/bin/bash

# run on SL6

#weights="fine"
#weights="comb"
weights="1l"
#weights="fine"
ver="Oct7"

# fit to photon pt using total cross section
#./prepare.py --input=EFTinput${ver}/2016 --type=inclusive --year=2016 --weights=${weights} --ncores=10
#./prepare.py --input=EFTinput${ver}/2017 --type=inclusive --year=2017 --weights=${weights} --ncores=10
#./prepare.py --input=EFTinput${ver}/2018 --type=inclusive --year=2018 --weights=${weights} --ncores=10
#./prepare.py --input=EFTinput${ver}/RunII --type=inclusive --year=Run2 --weights=${weights} --ncores=10

# fit to photon pt using differential cross section
#./prepare.py --input=EFTinput${ver}/2016 --type=photon_pt --year=2016 --weights=${weights} --ncores=10
#./prepare.py --input=EFTinput${ver}/2017 --type=photon_pt --year=2017 --weights=${weights} --ncores=10
#./prepare.py --input=EFTinput${ver}/2018 --type=photon_pt --year=2018 --weights=${weights} --ncores=10
./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10

# Run toys
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=0
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=1
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=2
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=3
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=4
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=5
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=6
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=7
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=8
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=9
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=10
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=11
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=12
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=13
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=14
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=15
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=16
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=17
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=18
#./prepare.py --input=EFTinput${ver}/RunII --type=photon_pt --year=Run2 --weights=${weights} --ncores=10 --toy=19
