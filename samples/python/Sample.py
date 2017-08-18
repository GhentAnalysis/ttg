#
# Use a sample class and some helper functions to initalize sample informtion
# Hides most of the dirty programming stuff from the main scripts
# Important functions
#   createSampleList:   imports a tuple file like ../data/tuples.conf with sample name, path, version, jobSplitting and x-sec 
#   createStack:        imports both a tuple and style file like ../data/stack.conf, returns as [[data1, data2,...], [mc1, mc2, mc3,..],...]
#   getSampleFromList:  access sample instance using its name 
#   getSampleFromStack: access sample instance using its name
#   sample.initTree:    get chain
#   sample.eventLoop:   loops over events from the chain (given selection string, job splitting)
#

from ttg.tools.logger import getLogger
log = getLogger()

import glob, os, copy, ROOT, uuid, socket

from ttg.tools.progressBar import progressbar
import ttg.tools.style as styles

#
# Sample class
#
class Sample:

  def __init__(self, name, path, productionLabel, splitJobs, xsec):
    self.name            = name
    self.path            = path
    self.isData          = (xsec == 'data')
    self.xsec            = eval(xsec) if not self.isData else None
    self.productionLabel = productionLabel
    self.splitJobs       = splitJobs
    self.texName         = None
    self.style           = None 
    self.listOfFiles     = None
    self.selectionString = None
    self.addSamples      = [name]

  def addStyle(self, texName, style):
    self.texName = texName
    self.style   = style

  def addSample(self, name):
    self.addSamples += [name]

  def addSelectionString(self, selectionString):
    self.selectionString = selectionString

  def getTotalEvents(self):
    total = 0
    for f in self.listOfFiles:
      f      = ROOT.TFile(f)
      total += f.Get('blackJackAndHookers/hCounter').GetBinContent(1)
    return total

  # init the chain and return it
  def initTree(self, skimType='dilep', shortDebug=False, reducedType=None):
    if reducedType:
      self.chain        = ROOT.TChain('blackJackAndHookersTree')
      self.listOfFiles  = []
      baseDir           = '/afs/cern.ch/work/t/tomc/public/reducedTuples/' if 'lxp' in socket.gethostname() else '/user/tomc/public/TTG/reducedTuples/'
      for s in self.addSamples:
        self.listOfFiles += glob.glob(os.path.join(baseDir, self.productionLabel, reducedType, s, '*.root'))
    else:
      self.chain        = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
      self.listOfFiles  = glob.glob(os.path.join(self.path, '*' + self.productionLabel, '*.root'))
      self.listOfFiles += glob.glob(os.path.join(self.path, '*' + self.productionLabel, '*', '*', '*.root'))
    if shortDebug: self.listOfFiles = self.listOfFiles[:3]
    if not len(self.listOfFiles): log.error('No tuples to run over for ' + self.name)
    for i in self.listOfFiles:
      if i.count('pnfs'): path = 'dcap://maite.iihe.ac.be/' + i                         # Speed up read from pnfs
      else:               path = i
      log.debug("Adding " + path)
      self.chain.Add(path)
    return self.chain

  # Helper function when sample is split in subjobs
  def getEventRange(self, entries, totalJobs, subJob):
    thresholds = [i*entries/totalJobs for i in range(totalJobs)]+[entries]
    return xrange(thresholds[subJob], thresholds[subJob+1])

  # Make eventlist for selectionstring
  def getEventList(self, chain, selectionString, totalJobs, subJob):
    tmp=str(uuid.uuid4())
    log.info("Making event list for sample %s and selectionString %s", self.name, selectionString)
    self.chain.Draw('>>'+tmp, selectionString)
    eventList = ROOT.gDirectory.Get(tmp)
    return [eventList.GetEntry(i) for i in self.getEventRange(eventList.GetN(), totalJobs, subJob)]

  # Get iterator over entries
  def eventLoop(self, selectionString = None, totalJobs=1, subJob = 0):
    if self.selectionString and selectionString: selectionString += "&&" + self.selectionString
    elif self.selectionString:                   selectionString  = self.selectionString
    if selectionString: entries = self.getEventList(self.chain, selectionString, totalJobs, subJob)
    else:               entries = self.getEventRange(self.chain.GetEntries(), totalJobs, subJob)
    return progressbar(entries, self.name, 100)


#
# Create basic sample (without style options)
#
def createSampleList(file):
  sampleInfos = [line.split('%')[0].strip() for line in open(file)]                         # Strip % comments and \n charachters
  sampleInfos = [line.split() for line in sampleInfos if line]                              # Get lines into tuples
  for name, path, productionLabel, splitJobs, xsec in sampleInfos:
    yield Sample(name, path, productionLabel, int(splitJobs), xsec)

#
# Create stack from configuration file
#
def createStack(tuplesFile, styleFile, channel):
  sampleList  = [s for s in createSampleList(tuplesFile)]
  sampleInfos = [line.split('%')[0].strip() for line in open(styleFile)]                    # Strip % comments and \n charachters
  sampleInfos = [line.split() for line in sampleInfos if line]                              # Get lines into tuples
  allStacks   = []
  stack       = []
  skip        = False
  for info in sampleInfos:
    if '--' in info:
      if len(stack):                                                                        # When "--", start a new stack
        allStacks.append(stack)
        stack = []
    else:
      if info[0].startswith('+'):                                                           # Add more subsamples to legend item (unless we skip the dataset)
        if not skip: stack[-1].addSample(info[0].strip('+'))
      else:
        selectionString = None
        try:    name, texName, style, color, selectionString = info
        except: name, texName, style, color = info

        try:    color = int(color)                                                          # Create style element for this sample
        except: color = getattr(ROOT, color)
        if style == 'fillStyle':    style = styles.fillStyle(color)
        elif style == 'errorStyle': style = styles.errorStyle(color)
        elif style == 'lineStyle':  style = styles.lineStyle(color)
        else:                       raise('Unkown style')

        if texName.count('data'):                                                           # If data, skip if not needed for this channel, fix texName
          if not texName.count(channel):
            skip = True
            continue
          texName = texName.split(':')[0]
          if channel == 'SF':   texName += ' (SF)'
          if channel == 'ee':   texName += ' (2e)'
          if channel == 'mumu': texName += ' (2#mu)'
          if channel == 'emu':  texName += ' (1e, 1#mu)'

        sample = getSampleFromList(stack, name)                                             # Check if sample with same name already exists in this stack
        if not sample: sample = getSampleFromStack(allStacks, name)                         # or other stack
        if sample:                                                                          # if yes, take it from there and make a deepcopy with different name
          sample = copy.deepcopy(sample)
          sample.addSamples = [sample.name]
          sample.name += '_' + texName
        else:                                   
          sample = getSampleFromList(sampleList, name)
        if not sample: log.error('Could not load sample ' + name + ' from ' + styleFile)
        sample.addSelectionString(selectionString)
        texName = texName.replace('_{','lower{').replace('_',' ').replace('lower{','_{')
        sample.addStyle(texName, style)
        stack.append(sample)
  if len(stack): allStacks.append(stack)
  return allStacks


#
# Get sample from list or stack using its name
#
def getSampleFromList(list, name):
  return next((s for s in list if s.name==name), None)

def getSampleFromStack(stack, name):
  return next((s for s in sum(stack, []) if s.name==name), None)
