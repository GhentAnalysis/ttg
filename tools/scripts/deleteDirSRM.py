#!/usr/bin/env python
import os
import getpass
import argparse

argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--force',      action='store_true', default=False, help='Do not ask for confirmation')
argParser.add_argument('--onlyFailed', action='store_true', default=False, help='Only those in failed directories')
args, directories = argParser.parse_known_args()

userdir = "srm://maite.iihe.ac.be:8443/pnfs/iihe/cms/store/user/" + getpass.getuser() + "/"

# Function for confirmation
def confirm(prompt, resp=False):
  prompt = '%s %s|%s: ' % (prompt, 'y', 'n')
  while True:
    ans = raw_input(prompt)
    if not ans: return resp
    if ans not in ['y', 'Y', 'n', 'N']:
      print 'please enter y or n.'
      continue
    if ans == 'y' or ans == 'Y': return True
    if ans == 'n' or ans == 'N': return False

# Function to delete
def deleteFile(file):
  print "Delete srm://maite.iihe.ac.be:8443" + file.split()[-1] 
  os.system("srmrm srm://maite.iihe.ac.be:8443" + file.split()[-1])

for dir in directories:
  list = []
  for root, dirs, files in os.walk(dir):
    for f in files:
      list.append(os.path.join(root, f))
  print "Files to delete:"
  for l in list: print l

  dir = dir.replace("/pnfs/iihe/cms/store/user/" + getpass.getuser() + "/", "")
  if not dir.endswith('/'): dir += '/'

  if(args.force or confirm('Delete these files?')):
    from multiprocessing import Pool
    pool = Pool(processes=16)
    results = pool.map(deleteFile, list)
    pool.close()
    pool.join()
    os.system("srmrmdir -recursive=true " + userdir + dir)

  print "DONE"
