svn co -N svn+ssh://svn.cern.ch/reps/tdr2 analysisNote
cd analysisNote
svn update utils
svn update -N notes
svn update notes/AN-17-197
eval `notes/tdr runtime -sh`
cd notes/AN-17-197/trunk
tdr --style=pas b AN-17-197
