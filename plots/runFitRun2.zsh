#!/bin/env zsh

run='combine'
chan='ll' # ee, mumu, emu or ll
#blind='--blind'
#tab='--tab'
#ratio='--ratio'

./createFitRun2.py --chan=${chan} --run=${run} ${ratio} ${tab} ${blind}
#./createFitRun2.py --chan=${chan} --run=${run} ${ratio} ${tab} ${blind}
