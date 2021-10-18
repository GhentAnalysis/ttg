from WMCore.Configuration import Configuration
config = Configuration()

config.section_('General')
config.General.requestName = 'REQUESTNAME'
config.General.transferLogs = True
config.section_('JobType')
config.JobType.psetName = '../test/maker.py'
config.JobType.pluginName = 'Analysis'
config.JobType.pyCfgParams = []
config.JobType.allowUndistributedCMSSW = True

config.section_('Data')
config.Data.splitting='FileBased'
config.Data.totalUnits = -1
config.Data.unitsPerJob = 1
##config.Data.inputDBS = 'phys03'
config.Data.publication = False
config.Data.userInputFiles = open('INPUTFILE.txt').readlines()
config.Data.outputPrimaryDataset = 'INPUTFILE'
#config.Data.inputDataset = 'INPUTDATASET'
config.Data.outputDatasetTag = 'PUBLISHDATANAME'
config.Data.outLFNDirBase = 'OUTLFN'

config.section_('User')
config.User.voGroup = 'becms'
config.section_('Site')
config.Site.storageSite = 'T2_BE_IIHE'
###config.Site.whitelist = ['T2_BE_IIHE']
#config.Site.whitelist = ['T2_AT_Vienna']
