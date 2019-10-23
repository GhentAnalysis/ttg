from ttg.tools.logger import getLogger
log = getLogger()

import os, time, subprocess
from datetime import datetime

def system(command):
  return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)

# Check the cream02 queue, do not submit new jobs when over 2000 (limit is 2500)
def checkQueueOnCream02():
  try:
    queue = int(system('qstat -u $USER | wc -l'))
    if queue > 2000:
      log.info('Too much jobs in queue (' + str(queue) + '), sleeping')
      time.sleep(500)
      checkQueueOnCream02()
  except:
    checkQueueOnCream02()

# Cream02 running
def launchCream02(command, logfile, checkQueue=False, wallTime='15', queue='localgrid', cores=1, jobLabel=None):
  jobName = jobLabel + datetime.now().strftime("%d_%H%M%S.%f")[:12]
  if checkQueue: checkQueueOnCream02()
  log.info('Launching %s on %s (%s)' % (command, queue, jobName))
  qsubOptions = ['-v dir=' + os.getcwd() + ',command="' + command + '"',
                 '-q ' + queue + '@cream02',
                 '-o ' + logfile,
                 '-e ' + logfile,
                 '-l walltime=' + wallTime + ':00:00',
                 '-N ' + jobName,
                 '-l nodes=1:ppn=' + str(cores)]
  try:    out = system('qsub ' + ' '.join(qsubOptions) + ' $CMSSW_BASE/src/ttg/tools/scripts/runOnCream02.sh')
  except: out = 'failed'
  if not out.count('.cream02.iihe.ac.be'):
    time.sleep(10)
    launchCream02(command, logfile, wallTime=wallTime, queue=queue, cores=cores, jobLabel=jobLabel)

# Local running: limit to 8 jobs running simultaneously
def launchLocal(command, logfile):
  while(int(system('ps uaxw | grep python | grep $USER |grep -c -v grep')) > 8): time.sleep(20)
  log.info('Launching ' + command + ' on local machine')
  system(command + ' &> ' + logfile + ' &')

#
# Job submitter for T2_BE_IIHE
#   script:     script to be called
#   subJobArgs: argument or tuple of arguments to be varied
#   subJobList: possible values/tuples for the argument
#   argParser:  the argParser from the mother script
#   dropArgs:   if some args need to be ignored
#   subLog:     subdirectory for the logs
#   jobLabel:   used as base to build an job name (i.e. jobLabel + time stamp)
#
def submitJobs(script, subJobArgs, subJobList, argParser, dropArgs=None, subLog=None, wallTime='15', queue='localgrid', cores=1, jobLabel=''):
  args         = argParser.parse_args()
  args.isChild = True
  changedArgs  = [arg for arg in vars(args) if getattr(args, arg) and argParser.get_default(arg) != getattr(args, arg)]
  submitArgs   = {arg: getattr(args, arg) for arg in changedArgs if (not dropArgs or arg not in dropArgs)}

  for i, subJob in enumerate(subJobList):
    for arg, value in zip(subJobArgs, subJob):
      if value: submitArgs[arg] = str(value)
      else:
        try:    submitArgs.pop(arg)
        except: pass

    command = script + ' ' + ' '.join(['--' + arg + '=' + str(value) for arg, value in submitArgs.iteritems() if value != False])
    command = command.replace('=True','')
    logdir  = os.path.join('log', os.path.basename(script).split('.')[0]+(('-'+subLog) if subLog else ''), *(str(s) for s in subJob[:-1]))
    logfile = os.path.join(logdir, str(subJob[-1]) + ".log")

    try:    os.makedirs(logdir)
    except: pass
    
    if args.dryRun:     log.info('Dry-run: ' + command)
    elif args.runLocal: launchLocal(command, logfile)
    else:               launchCream02(command, logfile, checkQueue=(i%100==0), wallTime=wallTime, queue=queue, cores=cores, jobLabel=jobLabel)
