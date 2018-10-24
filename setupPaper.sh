svn co -N svn+ssh://svn.cern.ch/reps/tdr2 paper
cd paper
svn update utils
svn update -N papers
cd papers
git clone https://gitlab.cern.ch/tomc/TTGammaPaper.git TOP-18-010
eval `papers/tdr runtime -sh`
cd TOP-18-010/trunk
tdr --style=paper b TOP-18-010
