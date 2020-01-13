#!/bin/env zsh

run='combine'
chan='ll' # ee, mumu, emu, or ll
year='All' # 2016, 2017, 2018, or All
#year='2016'
#blind='--blind'
#tab='--tab'
#ratio='--ratio'

./createFitRun2.py --chan=${chan} --run=${run} --year=${year} ${ratio} ${tab} ${blind}
