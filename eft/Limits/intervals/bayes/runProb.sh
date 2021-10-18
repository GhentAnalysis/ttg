#!/bin/bash

typ="photon_pt" # inclusive, photon_pt

coup=('ctZ' 'ctZ_obs' 'ctZI' 'ctZI_obs')
year=(2016 2017 2018 Run2 Run2_Comb)
#year=(2018)

maxRun2=(10. 10. 10. 10.)
max=(10. 10. 10. 10.)
step=(0.01 0.01 0.01 0.01)

for y in ${year[@]}
do
  for i in ${!coup[@]}
  do
    echo ${coup[$i]} ${y} ${step[$i]}
    if [[ ${y} == 2016 || ${y} == 2017 || ${y} == 2018 ]]; then
      ./prob.py --type=${typ} --nll=${coup[$i]} --year=${y} --max=${max[$i]} --step=${step[$i]} --dim="1d"
    else
      ./prob.py --type=${typ} --nll=${coup[$i]} --year=${y} --max=${maxRun2[$i]} --step=${step[$i]} --dim="1d"
    fi
  done
done

maxRun2=(10. 10. 10. 10.)
max=(10. 10. 10. 10.)
coup=('ctZ_ctZI' 'ctZ_ctZI_obs')
#coup=('ctZ_ctZI')
step=(0.05 0.05)

for y in ${year[@]}
do
  for i in ${!coup[@]}
  do
    echo ${coup[$i]} ${y} ${step[$i]}
    if [[ ${y} == 2016 || ${y} == 2017 || ${y} == 2018 ]]; then
      ./prob.py --type=${typ} --nll=${coup[$i]} --year=${y} --max=${max[$i]} --step=${step[$i]} --dim="2d"
    else
      ./prob.py --type=${typ} --nll=${coup[$i]} --year=${y} --max=${maxRun2[$i]} --step=${step[$i]} --dim="2d"
    fi
  done
done

