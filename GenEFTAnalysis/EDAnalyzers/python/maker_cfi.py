import FWCore.ParameterSet.Config as cms

maker = cms.EDAnalyzer("GenTreeMaker",

                       genEventInfo                  = cms.InputTag("generator"),
#                       genParticles                  = cms.InputTag("genParticles"),
                       genParticles                  = cms.InputTag("prunedGenParticles"),
                       lheInfo                       = cms.InputTag("externalLHEProducer"),
                       particleLevelLeptons          = cms.InputTag("particleLevel:leptons"),
                       particleLevelPhotons          = cms.InputTag("particleLevel:photons"),
                       particleLevelJets             = cms.InputTag("particleLevel:jets"),
                       particleLevelMets             = cms.InputTag("particleLevel:mets")

)
