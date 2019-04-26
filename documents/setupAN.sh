note=AN-19-086
if [ ! -d "$note" ]; then
  git clone --recursive https://gitlab.cern.ch/tdr/notes/$note.git 
fi
cd $note
eval `./utils/tdr runtime -sh`
tdr --temp_dir=$PWD/tmp --style=an b
