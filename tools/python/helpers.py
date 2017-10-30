#
# Get plot directory
#
import socket, os
plotDir = os.path.expandvars('/afs/cern.ch/work/t/$USER/public/ttG/' if 'lxp' in socket.gethostname() else '/user/$USER/TTG/plots')
def getResultsFile(*args):
  return os.path.join(plotDir, args, 'results.pkl')

#
# Get object (e.g. hist) from file using key
#
import ROOT
def getObjFromFile(fname, hname):
    f = ROOT.TFile(fname)
    assert not f.IsZombie()
    f.cd()
    htmp = f.Get(hname)
    if not htmp:  return htmp
    ROOT.gDirectory.cd('PyROOT:/')
    res = htmp.Clone()
    f.Close()
    return res

#
# Copy the index.php file to plotting directory
#
import os, shutil
def copyIndexPHP(directory):
  index_php = os.path.join(directory, 'index.php' )
  if not os.path.exists(directory): os.makedirs(directory)
  if not directory[-1] == '/': directory = directory+'/'
  subdirs = directory.split('/')
  for i in range(1,len(subdirs)):
    p = '/'.join(subdirs[:-i])
    if not (p.count('plots') or p.count('ttG')): continue
    index_php = os.path.join(p, 'index.php')
    shutil.copyfile(os.path.expandvars( '$CMSSW_BASE/src/ttg/tools/php/index.php'), index_php)


