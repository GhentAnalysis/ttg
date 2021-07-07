import ROOT, socket, os, shutil, subprocess
from math import pi, sqrt
from operator import mul

#
# Get some fixed paths
#
userGroup       = os.path.expandvars('$USER')[0:1]
plotDir         = os.path.expandvars(('/afs/cern.ch/user/' + userGroup + '/$USER/www/ttG/')       if 'lxp' in socket.gethostname() else '/user/$USER/public_html/ttG/')
plotCombineDir         = os.path.expandvars(('/afs/cern.ch/user/' + userGroup + '/$USER/www/ttG/')       if 'lxp' in socket.gethostname() else '/user/$USER/public_html/ttG/')
# plotCombineDir  = os.path.expandvars(('/afs/cern.ch/user/' + userGroup + '/$USER/combineplots/')       if 'lxp' in socket.gethostname() else '/user/$USER/combineplots/')
# reducedTupleDir = os.path.expandvars(('/afs/cern.ch/user/' + userGroup + '/$USER/reducedTuples/') if 'lxp' in socket.gethostname() else '/user/$USER/public/reducedTuples/') 
reducedTupleDir = os.path.expandvars('/pnfs/iihe/cms/store/user/$USER/ttgTuples/')


lumiScales = {'2016':36.33,
              '2017':41.53,
              '2018':59.74,
              'RunII':137.56
              }

lumiScalesRounded = {'2016':36, '2017':42, '2018':60, 'RunII':138}

#
# Check if valid ROOT file exists
#
def isValidRootFile(fname):
  if not os.path.exists(os.path.expandvars(fname)): return False
  f = ROOT.TFile(fname)
  if not f: return False
  try:
    return not (f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered) or f.GetListOfKeys().IsEmpty())
  finally:
    f.Close()

#
# Get object (e.g. hist) from file using key, and keep in memory after closing
#
def getObjFromFile(fname, hname):
  assert isValidRootFile(fname)
  try:
    f = ROOT.TFile(fname)
    f.cd()
    htmp = f.Get(hname)
    if not htmp: return None
    ROOT.gDirectory.cd('PyROOT:/')
    res = htmp.Clone()
    return res
  finally:
    f.Close()

#
# Copy the index.php file to plotting directory and all mother directories within the plotDir
#
def copyIndexPHP(directory):
  if not os.path.exists(directory): os.makedirs(directory)
  subdirs = directory.split('/') + ['']
  for i in range(1, len(subdirs)):
    p = '/'.join(subdirs[:-i])
    if not plotDir in p: continue
    index_php = os.path.join(p, 'index.php')
    if os.path.exists(index_php): continue
    shutil.copyfile(os.path.expandvars('$CMSSW_BASE/src/ttg/tools/php/index.php'), index_php)

#
# Update the latest git information
#
def updateGitInfo():
  os.system('(git log -n 1;git diff) &> git.txt')

#
# Copy git info for plot
#
def copyGitInfo(path):
  if os.path.isfile('git.txt'):
    shutil.copyfile('git.txt', path)


#
# Edit the info file in a given path
#
def editInfo(path):
  try:    os.makedirs(path)
  except: pass
  editor = os.getenv('EDITOR', 'vi')
  subprocess.call('%s %s' % (editor, os.path.join(path, 'info.txt')), shell=True)


#
# Delta phi and R function
#
def deltaPhi(phi1, phi2):
  dphi = phi2-phi1
  if dphi > pi:   dphi -= 2.0*pi
  if dphi <= -pi: dphi += 2.0*pi
  return abs(dphi)

def deltaR(eta1, eta2, phi1, phi2):
  return sqrt(deltaPhi(phi1, phi2)**2 + (eta1-eta2)**2)

#
# Safe hist add
#
def addHist(first, second):
  if first and second: first.Add(second)
  elif second:         first = second.Clone()
  return first

def addHists(histList):
  total = None
  for h in histList:
    total = addHist(total, h)
  return total


#
# multiply all elements in list
#
def multiply(mylist):
  return reduce(mul, mylist, 1.)

#
# Output a canvas to directory/name with following extensions
#
def printCanvas(canvas, directory, name, extensions):
  try:    os.makedirs(directory)
  except: pass
  copyIndexPHP(directory)
  for ext in extensions:
    canvas.Print(os.path.join(directory, name + '.' + ext))
