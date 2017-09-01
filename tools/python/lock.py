from ttg.tools.logger import getLogger
log = getLogger()

import os, errno, time

#
# Wait until multithread process could acquire lock
#
def waitForLock(filename):
  lockAcquired = False
  firstAttempt = True
  while not lockAcquired:
    try:
      f = os.open(filename + "_lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
      os.close(f)
      lockAcquired = True
    except OSError as e:
      if e.errno == errno.EEXIST:  # Failed as the file already exists.
        time.sleep(1)
        if firstAttempt: log.warning('Waiting for lock on ' + filename)
        firstAttempt = False
      else:  # Something unexpected went wrong
        log.error("Problem acquiring a lock on file " + filename)
        exit(1)

def removeLock(filename):
  os.system("rm " + filename + "_lock")
