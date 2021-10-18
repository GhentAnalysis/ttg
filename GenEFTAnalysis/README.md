# GenEFTAnalysis

Study of gen-level observables for EFT study of the ttgamma process

Install:
```
cmsrel CMSSW_10_5_0_pre2
cd CMSSW_10_5_0_pre2/src
cmsenv

git cms-init

git clone git@github.com:kskovpen/GenEFTAnalysis.git

scram b -j 8
```

Submit jobs with CRAB:
```
source /cvmfs/cms.cern.ch/crab3/crab.sh
cd crab/
./submit.zsh
```
