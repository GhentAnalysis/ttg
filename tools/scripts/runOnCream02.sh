#!/bin/bash
cd $dir
source $VO_CMS_SW_DIR/cmsset_default.sh
eval `scram runtime -sh`
eval $command
