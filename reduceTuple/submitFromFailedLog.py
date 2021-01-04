#! /usr/bin/env python

#
# This little script scans the logs and will resubmit failed jobs
# (i.e. those not containing 'finished' or 'Finished' in their log)
#
import argparse, os
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--runLocal', action='store_true', default=False,  help='Use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='Do not launch subjobs')
argParser.add_argument('--select',   nargs='*', type=str, default=[],     help='Resubmit only commands containing all strings given here')
argParser.add_argument('--tolerant', action='store_true', default=False,  help='don not consider e.g. a missing tuple file a reason for resubmit')
argParser.add_argument('--cleanFolders',   action='store_true', default=False,  help='Remove empty folders')
args = argParser.parse_args()

from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


# Get paths to all logs and analyze the files
def getLogs(logDir):
  for topDir, subDirs, files in os.walk(logDir):
    if not len(files) and not len(subDirs):
      if args.cleanFolders:
        os.rmdir(topDir)
    else:
      for f in files:
        yield os.path.join(topDir, f)

jobsToSubmit = []
for logfile in getLogs('./log'):
  finished  = False
  rootError = False
  command   = None
  miscProblem = False
  with open(logfile) as logf:
    for line in logf:
      if 'Finished transferring output files' in line: continue # condor uses the word Finished as well, ignore that...
      if 'SysError in <TFile::ReadBuffer>' in line: rootError = True
      if 'Error in <TChain::LoadTree>' in line:     rootError = True
      if 'Finished' in line or 'finished' in line:  finished  = True
      if 'Could not produce all plots' in line:     
        finished = True
        miscProblem = True
      if 'Command:' in line:                        command   = line.split('Command: ')[-1].rstrip()
  if not command: 
    log.info('no valid command??')
    log.info(logfile)
    continue
  if args.select and not all(command.count(sel) for sel in args.select): continue
  if (not finished or ((rootError or miscProblem) and not args.tolerant)) and command: jobsToSubmit.append((command, logfile))


# Update latest git status before resubmitting
from ttg.tools.helpers import updateGitInfo
updateGitInfo()


# Resubmit the failed jobs
from ttg.tools.jobSubmitter import launchLocal, launchCream02, launchCondor
from datetime import datetime
for i, (command, logfile) in enumerate(jobsToSubmit):
  if args.dryRun:
    log.info('Dry-run: ' + command)
  else:
    os.remove(logfile)
    if args.runLocal: launchLocal(command, logfile)
    else:
      # launchCream02(command, logfile, checkQueue=(i%100==0), wallTime='168', jobLabel='RE', cores=8 if logfile.count("calcTriggerEff") else 1) # TODO: ideally extract walltime, cores,... from the motherscript
      launchCondor(command, logfile, checkQueue=(i%100==0), wallTime='168', jobLabel='RE', cores=8 if logfile.count("calcTriggerEff") else 1) # TODO: ideally extract walltime, cores,... from the motherscript
