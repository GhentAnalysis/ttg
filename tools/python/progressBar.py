from ttg.tools.logger import getLogger
log = getLogger()

#
# Shows a progress bar when running interactively
#  it:     collection to run over
#  prefix: text to be shown before progressbar
#  size:   size of the progressbar
#
import sys
def progressbar(it, prefix="", size=60):
  total = len(it)

  def show(i):
      x = int(size*i/total)
      sys.stdout.write("%s\x1b[6;30;42m%s\x1b[0m\x1b[0;30;41m%s\x1b[0m %i/%i %s\r" % (" "*40, " "*x, " "*(size-x), i, total, prefix))
      sys.stdout.flush()

  if sys.stdout.isatty():
    for i, item in enumerate(it):
      yield item
      if i and i%(int(total/size/10)+1)==0: show(i)
    if total > 0: show(total)
    sys.stdout.write("\n")
    sys.stdout.flush()
  else:
    for item in it: yield item
    log.info(prefix + ': ' + str(total) + ' events processed')
