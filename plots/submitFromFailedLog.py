#! /usr/bin/env python

#
# This little script scans the logs and will resubmit failed jobs
# (i.e. those not containing 'finished' or 'Finished' in their log)
#
import argparse, os
from datetime import datetime
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--runLocal', action='store_true', default=False,  help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='do not launch subjobs')
argParser.add_argument('--select',   nargs='*', type=str, default=None,   help='resubmit only commands containing all strings given here')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

def getLogs(logDir):
  for topDir, subDirs, files in os.walk(logDir):
    if not len(files) and not len(subDirs):
      os.rmdir(topDir)
    else:
      for f in files:
        yield os.path.join(topDir, f)

jobsToSubmit = []
for logfile in getLogs('./log'):
  finished  = False
  rootError = False
  command   = None
  with open(logfile) as f:
    for line in f:
      if 'SysError in <TFile::ReadBuffer>' in line: rootError = True
      if 'Error in <TChain::LoadTree>' in line:     rootError = True
      if 'Finished' in line or 'finished' in line:  finished  = True
      if 'Command:' in line:                        command   = line.split('Command: ')[-1].rstrip()
  if (not finished or rootError) and command: jobsToSubmit.append((command, logfile))

from ttg.tools.helpers import updateGitInfo
updateGitInfo()

from ttg.tools.jobSubmitter import launchLocal, launchCream02
for i, (command, logfile) in enumerate(jobsToSubmit):
  if not all((command.count(sel) for sel in args.select) or not args.select) : continue
  if args.dryRun:
    log.info('Dry-run: ' + command)
  else:
    os.remove(logfile)
    if args.runLocal: launchLocal(command, logfile)
    else:             
      jobName = 'RE' + datetime.now().strftime("%d_%H%M%S.%f")[:12]
      launchCream02(command, logfile, checkQueue=(i%100==0), wallTime= '30' if logfile.count("base") else "15", jobName = jobName)
  