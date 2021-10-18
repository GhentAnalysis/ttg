#!/bin/env zsh

# source /cvmfs/cms.cern.ch/crab3/crab.sh

#slist="samples.txt"
slist="samplesGEN.txt"
#slist="samplesMINIAOD.txt"
pver="1" # production tentative
pset="crabConfigTemplate.py"
#ver="EFT-v20200619"
ver="GEN-v20210712"
prodv="/store/user/kskovpen/TTG/Ntuple/${ver}/"

rm -f crabConfig.py*

samp=()
is=1
cat ${slist} | while read line
do
  if [[ ${line[1]} == '#' ]]; then
    continue
  fi
  samp[${is}]=${line}
  is=$[$is+1]
done

for i in ${samp}
do
#  spl=($(echo $i | tr "/" "\n"))
  spl=${i}
#  pubdn=$(echo "${spl[2]}_${spl[3]}" | sed 's%rwgt-.*%%g' | sed 's%RunIISummer.*%%g')
#  nam=$(echo "${spl[1]}" | sed 's%-%_%g')
  pubdn=${i}
  nam=${i}
  
  pubdn=$(echo $pubdn | sed 's%llechner.*%%g')

  cat ${pset} | sed "s%INPUTDATASET%${i}%g" \
  | sed "s%OUTLFN%${prodv}%g" \
  | sed "s%INPUTFILE%${i}%g" \
  | sed "s%REQUESTNAME%${nam}_${pubdn}_${pver}%g" \
  | sed "s%PUBLISHDATANAME%${pubdn}%g" \
  > crabConfig.py

  echo "${nam} ${pubdn}"
#  crab submit -c crabConfig.py --dryrun
#  crab --debug submit -c crabConfig.py
  crab submit -c crabConfig.py
  
done

rm -f crabConfig.py*
