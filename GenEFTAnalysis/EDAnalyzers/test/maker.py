import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

readFiles = cms.untracked.vstring()
secFiles = cms.untracked.vstring() 
source = cms.Source ("PoolSource",fileNames = readFiles, secondaryFileNames = secFiles)
readFiles.extend( [
#'/store/user/llechner/ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt/ttGamma_Dilept_restrict_ctZ_ctZI_ctW_ctWI_rwgt/200217_094137/0000/GEN_LO_0j_93X_99.root'
'file:GEN_LO_0j_93X_1.root'
#'/store/mc/RunIISummer16MiniAODv3/TTGamma_Dilept_TuneCP5_PSweights_13TeV-madgraph-pythia8/MINIAODSIM/PUMoriond17_94X_mcRun2_asymptotic_v3-v1/30000/0C738535-ABB1-E911-874F-AC1F6BAC7C0A.root'
#'/store/user/llechner/ttGamma_Dilept_Herwigpp_v2/ttGamma_Dilept_Herwigpp_v2/210311_125358/0000/GEN_LO_0j_93X_1.root'
#'file:HNL_GEN_2l.root'
]);

# /TTGamma_Dilept_TuneCP5_PSweights_13TeV-madgraph-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM

secFiles.extend([ ]);

process = cms.Process("GenTreeMaker")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport = cms.untracked.PSet( reportEvery = cms.untracked.int32(1000) )

process.load('PhysicsTools.PatAlgos.slimming.genParticles_cff')
process.load('PhysicsTools.PatAlgos.slimming.prunedGenParticles_cfi')
process.load('PhysicsTools.PatAlgos.slimming.packedGenParticles_cfi')

process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("GeneratorInterface.RivetInterface.mergedGenParticles_cfi")
process.load("GeneratorInterface.RivetInterface.genParticles2HepMC_cfi")
process.genParticles2HepMC.genParticles = cms.InputTag("mergedGenParticles")
process.genParticles2HepMC.signalParticlePdgIds = cms.vint32(6,-6)
process.load("GenEFTAnalysis.EDAnalyzers.particleLevelTTG_cfi")

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )
#process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(100) )

process.source = source

process.load('GenEFTAnalysis.EDAnalyzers.maker_cfi')

process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string("output.root"),
                                   closeFileFast = cms.untracked.bool(True)
                                   )

process.options = cms.untracked.PSet( wantSummary = cms.untracked.bool(False) )

process.p = cms.Path(
    process.prunedGenParticlesWithStatusOne*process.prunedGenParticles*process.packedGenParticles*process.mergedGenParticles*process.genParticles2HepMC*process.particleLevel*
    process.maker
)
#process.p = cms.Path(
#    process.mergedGenParticles*process.genParticles2HepMC*process.particleLevel*
#    process.maker
#)
