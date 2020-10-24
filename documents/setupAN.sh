note=AN-20-186
if [ ! -d "$note" ]; then
  git clone --recursive https://gitlab.cern.ch/tdr/notes/$note.git 
fi
cd $note
if [ ! -d utils ]; then # sometimes there is a connection problem and utils isn't checked out
  git clone --recursive https://gitlab.cern.ch/tdr/utils.git 
fi
eval `./utils/tdr runtime -sh`
tdr --temp_dir=$PWD/tmp --style=an b
