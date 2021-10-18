#!/bin/sh

proxy=${proxy}
arch=${arch}
dout=${dout}
sample=${sample}
tag=${tag}
xml=${xml}
output=${output}
nmax=${nmax}

export X509_USER_PROXY=${proxy}

source /cvmfs/cms.cern.ch/cmsset_default.sh
cd ${dout}/../../
export SCRAM_ARCH=${arch}
eval `scramv1 runtime -sh`
cd -

echo "Executing python makeTree.py --sample ${sample} --tag ${tag} --xml ${xml} --output ${output} --nmax ${nmax}"
time python ${dout}/./makeTree.py --sample "${sample}" --tag "${tag}" --xml "${xml}" --output "${output}" --nmax "${nmax}"
