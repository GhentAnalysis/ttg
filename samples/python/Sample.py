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

import glob, os, copy, ROOT, uuid

from ttg.tools.progressBar import progressbar
from ttg.tools.helpers import reducedTupleDir
import ttg.tools.style as styles

#
# Sample class
#
class Sample:                                                                                # pylint: disable=R0902

  def __init__(self, name, path, productionLabel, splitJobs, xsec):
    self.name            = name
    self.path            = path
    self.productionLabel = productionLabel
    self.splitJobs       = splitJobs
    self.isData          = (xsec == 'data')
    self.xsec            = eval(xsec) if not self.isData else None
    self.year            = productionLabel.split('-')[0]
    self.texName         = None
    self.style           = None 
    self.listOfFiles     = None
    self.selectionString = None
    self.addSamples      = [(name, self.productionLabel)]
    self.chain           = None

  def addStyle(self, texName, style):
    self.texName = texName
    self.style   = style

  def addSample(self, name, productionLabel):
    self.addSamples += [(name, productionLabel)]

  def addSelectionString(self, selectionString):
    self.selectionString = selectionString

  def getTotalWeights(self):
    maxVar = None
    for f in self.listOfFiles:
      f = ROOT.TFile(f)
      if not maxVar:
        maxVar = f.Get('blackJackAndHookers/lheCounter').GetNbinsX()
        totals = [0 for i in range(maxVar)]
      for i in range(maxVar):
        if i == 0: totals[i] += f.Get('blackJackAndHookers/hCounter').GetBinContent(i+1)    # should be no difference, but more precise
        else:      totals[i] += f.Get('blackJackAndHookers/lheCounter').GetBinContent(i+1)
    totals = [(t if t > 0 else totals[0]) for t in totals]
    return totals

  def getTrueInteractions(self, reduced=False):
    trueInteractions = None
    for f in self.listOfFiles:
      f = ROOT.TFile(f)
      if not trueInteractions: trueInteractions   = f.Get('nTrue' if reduced else 'blackJackAndHookers/nTrue')
      else:                    trueInteractions.Add(f.Get('nTrue' if reduced else 'blackJackAndHookers/nTrue'))
      trueInteractions.SetDirectory(0)
    return trueInteractions

  # returns list of files for production with most recent time-tag
  def getListOfFiles(self, splitData):
    if splitData: runDirs = os.path.join(self.path, 'crab_Run' + self.year + splitData + '*' + self.productionLabel)
    else:         runDirs = os.path.join(self.path, '*' + self.productionLabel)
    listOfFiles = []
    for runDir in glob.glob(runDirs):
      timeTagDirs = glob.glob(os.path.join(runDir, '*'))
      if len(timeTagDirs) > 1:
        log.warning('Multiple production time-tags found for ' + runDir + '(' + ','.join(i.split('/')[-1] for i in timeTagDirs) + '), taking the most recent one')
      listOfFiles += glob.glob(os.path.join(sorted(timeTagDirs)[-1], '*', '*.root'))  # files are typically at **/YYMMDD_HHMMSS/0000/*.root
    return listOfFiles

  # init the chain and return it
  def initTree(self, shortDebug=False, reducedType=None, splitData=None):
    if reducedType:
      self.chain        = ROOT.TChain('blackJackAndHookersTree')
      self.listOfFiles  = []
      for sample, productionLabel in self.addSamples:
        self.listOfFiles += glob.glob(os.path.join(reducedTupleDir, productionLabel, reducedType, sample, '*.root'))
    else:
      self.chain = ROOT.TChain('blackJackAndHookers/blackJackAndHookersTree')
      self.listOfFiles = self.getListOfFiles(splitData)
    if shortDebug: self.listOfFiles = self.listOfFiles[:3]
    if not len(self.listOfFiles): log.error('No tuples to run over for ' + self.name)
    for i in self.listOfFiles:
      if i.count('pnfs'): path = 'dcap://maite.iihe.ac.be/' + i                         # Speed up read from pnfs
      else:               path = i
      log.debug("Adding " + path)
      self.chain.Add(path)
    return self.chain

  # Helper function when sample is split in subjobs
  def getEventRange(self, entries, totalJobs, subJob):                                                                # pylint: disable=R0201
    thresholds = [i*entries/totalJobs for i in range(totalJobs)]+[entries]
    return xrange(thresholds[subJob], thresholds[subJob+1])

  # Make eventlist for selectionstring
  def getEventList(self, selectionString, totalJobs, subJob):
    tmp = str(uuid.uuid4())
    log.info("Making event list for sample %s and selectionString %s", self.name, selectionString)
    self.chain.Draw('>>'+tmp, selectionString)
    eventList = ROOT.gDirectory.Get(tmp)
    return [eventList.GetEntry(i) for i in self.getEventRange(eventList.GetN(), totalJobs, subJob)]

  # Get iterator over entries
  def eventLoop(self, selectionString = None, totalJobs=1, subJob = 0):
    if self.selectionString and selectionString: selectionString += "&&" + self.selectionString
    elif self.selectionString:                   selectionString  = self.selectionString
    if selectionString: entries = self.getEventList(selectionString, totalJobs, subJob)
    else:               entries = self.getEventRange(self.chain.GetEntries(), totalJobs, subJob)
    return progressbar(entries, self.name, 100)


#
# Create basic sample (without style options)
#  - filename: tuples config as found in ttg/samples/data, e.g. "tuples_16.conf"
#
def createSampleList(*filenames):
  for filename in filenames:
    sampleInfos = [line.split('%')[0].strip() for line in open(filename)]                     # Strip % comments and \n charachters
    sampleInfos = [line.split() for line in sampleInfos if line]                              # Get lines into tuples
    for name, path, productionLabel, splitJobs, xsec in sampleInfos:
      yield Sample(name, path, productionLabel, int(splitJobs), xsec)

#
# Create stack from configuration file
# Refactoring needed
#
def createStack(tuplesFile, styleFile, channel, replacements = None):                       # pylint: disable=R0912,R0914,R0915
  if not replacements: replacements = {}
  sampleList  = [s for s in createSampleList(tuplesFile)]
  sampleInfos = [line.split('%')[0].strip() for line in open(styleFile)]                    # Strip % comments and \n charachters
  sampleInfos = [line.split() for line in sampleInfos if line]                              # Get lines into tuples
  allStacks   = []
  stack       = []
  skip        = False
  alias = None
  for info in sampleInfos:
    if info[0].startswith('$'):
      alias = info[0].strip('$')
      continue
    for i, j in replacements.iteritems():
      if info[0] == i: info[0] = j
    if '--' in info:
      if len(stack):                                                                        # When "--", start a new stack
        allStacks.append(stack)
        stack = []
    else:
      if info[0].startswith('+'):                                                           # Add more subsamples to legend item (unless we skip the dataset)
        if not skip:
          sample = getSampleFromList(sampleList, info[0].strip('+'))
          stack[-1].addSample(sample.name, sample.productionLabel)
      else:
        selectionString = None
        try:    name, texName, style, color, selectionString = info
        except: name, texName, style, color = info

        try:    color = int(color)                                                          # Create style element for this sample
        except: color = getattr(ROOT, color)
        if style == 'fillStyle':       style = styles.fillStyle(color)
        elif style == 'errorStyle':    style = styles.errorStyle(color)
        elif style.count('lineStyle'): style = styles.lineStyle(color, width=2)
        else:                          raise ValueError('Unkown style')

        if texName.count('data'):                                                           # If data, skip if not needed for this channel, fix texName
          if not texName.count(channel):
            skip = True
            continue
          texName = texName.split(':')[0]
          if channel == 'SF':   texName += ' (SF)'
          if channel == 'ee':   texName += ' (2e)'
          if channel == 'mumu': texName += ' (2#mu)'
          if channel == 'emu':  texName += ' (1e, 1#mu)'
        sample = getSampleFromList(stack, name)                         # Check if sample with same name already exists in this stack
        if not sample: sample = getSampleFromStack(allStacks, name)     # or other stack
        if sample:                                                                          # if yes, take it from there and make a deepcopy with different name
          sample = copy.deepcopy(sample)
          sample.addSamples = [(sample.name, sample.productionLabel)]
          sample.name += '_' + texName
        else:                                   
          sample = getSampleFromList(sampleList, name)
        if not sample: log.error('Could not load sample ' + name + ' from ' + styleFile)
        sample.addSelectionString(selectionString)
        texName = texName.replace('_{','lower{').replace('_',' ').replace('lower{','_{')
        sample.addStyle(texName, style)
        if alias:
          sample = copy.deepcopy(sample)
          sample.addSamples = [(sample.name, sample.productionLabel)]
          sample.name = alias
          alias = None
        stack.append(sample)
  if len(stack): allStacks.append(stack)
  for s in sum(allStacks, []):
    s.nameNoSys = s.name
    for i, j in replacements.iteritems():                                                   # Still use original name when using replacement samples like ISR and FSR
      s.nameNoSys = s.nameNoSys.replace(j, i)
  return allStacks


#
# Get sample from list or stack using its name
#
def getSampleFromList(sampleList, name, year=None):
  sample = next((s for s in sampleList if s.name==name and (s.year==year or not year )), None)
  if sample: return sample
  else:      log.warning('No sample ' + name + ' found for year ' + year + '!')

def getSampleFromStack(stack, name):
  sample = next((s for s in sum(stack, []) if s.name==name), None)
  if sample: return sample
  else:      log.warning('No sample ' + name + ' found in stack!')
