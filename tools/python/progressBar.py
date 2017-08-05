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
      sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix.ljust(25), "#"*x, "."*(size-x), i, total))
      sys.stdout.flush()

  if sys.stdout.isatty():
    show(0)
    for i, item in enumerate(it):
      yield item
      if i and i%(int(total/size/10)+1)==0: show(i)
    show(total)
    sys.stdout.write("\n")
    sys.stdout.flush()
  else:
    for item in it: yield item
    log.info(prefix + ': ' + str(total) + ' events processed')
