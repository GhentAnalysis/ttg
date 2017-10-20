from ttg.tools.logger import getLogger
log = getLogger()

import os, time

#
# Job submitter for T2_BE_IIHE
#   script:     script to be called
#   subJobArg:  argument to be varied
#   subJobList: possible values for the argument
#   args:       other args
#   dropArgs:   if some args need to be ignored
#   subLog:     subdirectory for the logs
#

def launch(command, logfile, runLocal):
    if runLocal: os.system(command + ' &> ' + logfile + ' &')
    else:        os.system("qsub -v dir=" + os.getcwd() + ",command=\"" + command + "\" -q localgrid@cream02 -o " + logfile + " -e " + logfile + " -l walltime=10:00:00 $CMSSW_BASE/src/ttg/tools/scripts/runOnCream02.sh &> .qsub.log")
    with open('.qsub.log','r') as qsublog:
      for l in qsublog:
        if 'Invalid credential' in l:
          time.sleep(10)
          launch(command, logfile, runLocal)

def submitJobs(script, subJobArg, subJobList, args, dropArgs = [], subLog=''):
  os.system("mkdir -p log")

  submitArgs = {arg: getattr(args, arg) for arg in vars(args) if arg not in dropArgs and arg!=subJobArg}
  for subJob in subJobList:
    submitArgs[subJobArg] = str(subJob)
    submitArgs['isChild'] = True

    command = script + ' ' + ' '.join(['--' + arg + '=' + str(value) for arg, value in submitArgs.iteritems() if value != False])
    command = command.replace('=True','')
    logdir  = os.path.join('log', os.path.basename(script).split('.')[0], subLog)
    logfile = os.path.join(logdir, str(subJob) + ".log")

    try:    os.makedirs(logdir)
    except: pass

    log.info('Launching ' + command)
    if not args.dryRun: launch(command, logfile, args.runLocal)
