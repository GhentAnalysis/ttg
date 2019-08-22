# combines tuple files into tubles_comb.conf putting the sample year in front of each sample name 
import os

outFile = open(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_comb.conf'),"w")
outFile.write('%WARNING: This file gets overwritten by combSamples.py, edit the tuples_year files instead')
for year in ['2016', '2017', '2018']:
  outFile.write('\n\n%----------------- ' + year + ' samples -----------------\n\n')
  inFile = open(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuples_' + year + '.conf'), 'r')
  for line in (line.lstrip() for line in inFile.readlines()):
    if not len(line) > 1: 
      outFile.write('\n')
      continue
    if line.startswith('%'):
      outFile.write(line)
    else:
      outFile.write(year+line)