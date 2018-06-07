#! /usr/bin/env python

#
# This little script scans the logs and will resubmit failed jobs
# (i.e. those not containing 'finished' or 'Finished' in their log)
#
import argparse, os
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', help='Log level for logging', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'])
argParser.add_argument('--runLocal', action='store_true', default=False,  help='use local resources instead of Cream02')
argParser.add_argument('--dryRun',   action='store_true', default=False,  help='do not launch subjobs')
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
  finished = False
  with open(logfile) as f:
    for line in f:
      if 'Finished' in line or 'finished' in line: finished = True
      if 'Command:' in line:                       command  = line.split('Command: ')[-1].rstrip()
  if not finished:  jobsToSubmit.append((command, logfile))

from ttg.tools.helpers import updateGitInfo
updateGitInfo()

from ttg.tools.jobSubmitter import launchLocal, launchCream02
for command, logfile in jobsToSubmit:
  if args.dryRun:     log.info('Dry-run: ' + command)
  elif args.runLocal: launchLocal(command, logfile)
  else:               launchCream02(command, logfile, checkQueue=(i%100==0))
