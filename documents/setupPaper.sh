note=TOP-18-010
if [ ! -d "$note" ]; then
  git clone --recursive https://gitlab.cern.ch/tdr/papers/$note.git 
fi
cd $note
eval `./utils/tdr runtime -sh`
tdr --temp_dir=$PWD/tmp --style=paper b
