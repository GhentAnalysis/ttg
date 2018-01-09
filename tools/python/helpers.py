#
# Get plot directory
#
import socket, os
plotDir = os.path.expandvars('/eos/user/t/tomc/www/ttG/' if 'lxp' in socket.gethostname() else '/user/$USER/www/ttG/')
def getResultsFile(*args):
  return os.path.join(*((plotDir,)+args+('results.pkl',)))

#
# Get object (e.g. hist) from file using key
#
def getObjFromFile(fname, hname):
    import ROOT
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
def copyIndexPHP(directory):
  import os, shutil
  index_php = os.path.join(directory, 'index.php' )
  if not os.path.exists(directory): os.makedirs(directory)
  if not directory[-1] == '/': directory = directory+'/'
  subdirs = directory.split('/')
  for i in range(1,len(subdirs)):
    p = '/'.join(subdirs[:-i])
    if not (p.count('plots') or p.count('ttG')): continue
    index_php = os.path.join(p, 'index.php')
    shutil.copyfile(os.path.expandvars( '$CMSSW_BASE/src/ttg/tools/php/index.php'), index_php)

#
# Update the latest git information
#
def updateGitInfo():
  import os
  os.system('(git log -n 1;git diff) &> git.txt')

#
# Copy git info for plot
#
def copyGitInfo(path):
  import shutil
  if os.path.isfile('git.txt'):
    shutil.copyfile('git.txt', path)


#
# Edit the info file in a given path
#
def editInfo(path):
  import subprocess,os
  editor = os.getenv('EDITOR', 'vi')
  subprocess.call('%s %s' % (editor, os.path.join(path, 'info.txt')), shell=True)
