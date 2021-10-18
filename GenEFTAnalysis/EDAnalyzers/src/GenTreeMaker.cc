// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "MagneticField/Engine/interface/MagneticField.h" 
#include "MagneticField/Records/interface/IdealMagneticFieldRecord.h" 

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/Common/interface/RefToPtr.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"
#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/JetReco/interface/GenJet.h"
#include "DataFormats/METReco/interface/METCollection.h"
#include "DataFormats/METReco/interface/MET.h"

#include "GenEFTAnalysis/EDAnalyzers/interface/GenTools.h"

#include "TROOT.h"
#include "TH1F.h"
#include "TTree.h"
#include "TRandom3.h"
#include "TLorentzVector.h"
#include "Compression.h"

#include "GenEFTAnalysis/EDAnalyzers/interface/Tree.h"

class GenTreeMaker : public edm::EDAnalyzer
{  
   
 public:
   explicit GenTreeMaker(const edm::ParameterSet& pset);
   ~GenTreeMaker();
    
 private:
   virtual void beginRun(const edm::Run&, const edm::EventSetup&);
   virtual void analyze(const edm::Event&, const edm::EventSetup&);
   virtual void endRun();
   
   unsigned overlapEventType(const std::vector<reco::GenParticle>& genParticles, double ptCut, double etaCut, double genCone) const;

   // ----------member data ---------------------------
   edm::EDGetTokenT<GenEventInfoProduct> genEventInfoToken_;
   edm::EDGetTokenT<reco::GenParticleCollection> genParticleToken_;
   edm::EDGetTokenT<LHEEventProduct> lheInfoToken_;
   
   edm::EDGetTokenT<reco::GenParticleCollection> particleLevelPhotonsToken_;
   edm::EDGetTokenT<reco::GenJetCollection> particleLevelLeptonsToken_;
   edm::EDGetTokenT<reco::GenJetCollection> particleLevelJetsToken_;
   edm::EDGetTokenT<std::vector<reco::MET> > particleLevelMetsToken_;

   const edm::Service<TFileService> fs;
   GenTree* ftree;
};

unsigned GenTreeMaker::overlapEventType(const std::vector<reco::GenParticle>& genParticles, double ptCut, double etaCut, double genCone) const
{   
   int type = 0;
   for(auto p = genParticles.cbegin(); p != genParticles.cend(); ++p)
     {	
	if(p->status()<0)         continue;
	if(p->pdgId()!=22)        continue;
	type = std::max(type, 1);                                                            // Type 1: final state photon found in genparticles with generator level cuts
	if(p->pt()<ptCut)         continue;
	if(fabs(p->eta())>etaCut) continue;
	type = std::max(type, 2);                                                            // Type 2: photon from pion or other meson
	
	if(GenTools::getMinDeltaRTTG(*p, genParticles) < genCone) continue;
	if(not GenTools::noMesonsInChain(*p, genParticles))  continue;
	
	// Everything below is *signal*
	std::set<int> decayChain;
	GenTools::setDecayChain(*p, genParticles, decayChain);
	const reco::GenParticle* mom = GenTools::getMother(*p, genParticles);
	if(std::any_of(decayChain.cbegin(), decayChain.cend(), [](const int entry){return abs(entry) == 24;}))
	  {	     
	     if(abs(mom->pdgId()) == 24)     type = std::max(type, 6);      // Type 6: photon directly from W or decay products which are part of ME
	     else if(abs(mom->pdgId()) <= 6) type = std::max(type, 4);      // Type 4: photon from quark from W (photon from pythia, rarely)
	     else                            type = std::max(type, 5);      // Type 5: photon from lepton from W (photon from pythia)
	  }
	else 
	  {	     
	     if(abs(mom->pdgId()) == 6)      type = std::max(type, 7);      // Type 7: photon from top
	     else if(abs(mom->pdgId()) == 5) type = std::max(type, 3);      // Type 3: photon from b
	     else                            type = std::max(type, 8);      // Type 8: photon from ME
	  }	
     }
      
   return type;
}

GenTreeMaker::GenTreeMaker(const edm::ParameterSet& pset)
{
   genEventInfoToken_ = consumes<GenEventInfoProduct>(pset.getParameter<edm::InputTag>("genEventInfo"));
   genParticleToken_ = consumes<reco::GenParticleCollection>(pset.getParameter<edm::InputTag>("genParticles"));
   lheInfoToken_ = consumes<LHEEventProduct>(pset.getParameter<edm::InputTag>("lheInfo"));
   
   particleLevelPhotonsToken_ = consumes<reco::GenParticleCollection>(pset.getParameter<edm::InputTag>("particleLevelPhotons"));
   particleLevelLeptonsToken_ = consumes<reco::GenJetCollection>(pset.getParameter<edm::InputTag>("particleLevelLeptons"));
   particleLevelJetsToken_ = consumes<reco::GenJetCollection>(pset.getParameter<edm::InputTag>("particleLevelJets"));
   particleLevelMetsToken_ = consumes<reco::METCollection>(pset.getParameter<edm::InputTag>("particleLevelMets"));
   
   TFile& f = fs->file();
   f.SetCompressionAlgorithm(ROOT::kZLIB);
   f.SetCompressionLevel(9);
   
   ftree = new GenTree(fs->make<TTree>("tree","tree"));   
   ftree->CreateBranches(32000);
}

GenTreeMaker::~GenTreeMaker()
{
}

void GenTreeMaker::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
   using namespace edm;
   using namespace std;

   ftree->Init();

   edm::Handle<GenEventInfoProduct> genEventInfo;
   iEvent.getByToken(genEventInfoToken_, genEventInfo);
   
   edm::Handle<reco::GenParticleCollection> genParticles;
   iEvent.getByToken(genParticleToken_, genParticles);

   edm::Handle<LHEEventProduct> lheInfo;
   iEvent.getByToken(lheInfoToken_, lheInfo);

   edm::Handle<reco::GenParticleCollection> particleLevelPhotons;
   iEvent.getByToken(particleLevelPhotonsToken_, particleLevelPhotons);

   edm::Handle<reco::GenJetCollection> particleLevelLeptons;
   iEvent.getByToken(particleLevelLeptonsToken_, particleLevelLeptons);

   edm::Handle<reco::GenJetCollection> particleLevelJets;
   iEvent.getByToken(particleLevelJetsToken_, particleLevelJets);

   edm::Handle<std::vector<reco::MET> > particleLevelMets;
   iEvent.getByToken(particleLevelMetsToken_, particleLevelMets);
   
   ftree->weight = genEventInfo->weight();
   
   // Save LHE weights
   int nWeights = lheInfo->weights().size();
   for( int i=0;i<nWeights;i++ )
     {
	std::string wid = lheInfo->weights()[i].id;
	float wgt = lheInfo->weights()[i].wgt;
	
	if( wid == "ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p = wgt;
	else if( wid == "ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p" ) ftree->weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p = wgt;
	else if( wid == "ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p" ) ftree->weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p = wgt;
	else if( wid == "ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p" ) ftree->weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p = wgt;
	else if( wid == "ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p = wgt;
	else if( wid == "ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p = wgt;
	else if( wid == "ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p" ) ftree->weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p = wgt;
     }
   
   // Save LHE particles
   unsigned int _lhe_n = lheInfo->hepeup().NUP;
   std::vector<float> _lhe_pt;
   std::vector<float> _lhe_eta;
   std::vector<float> _lhe_phi;
   std::vector<float> _lhe_E;
   std::vector<int> _lhe_pdgId;
   std::vector<int> _lhe_status;
   std::vector<int> _lhe_index;
   std::vector<int> _lhe_mother1Index;
   std::vector<int> _lhe_mother2Index;
   for( unsigned i=0;i<_lhe_n;++i )
     {
	float px = lheInfo->hepeup().PUP[i][0];
	float py = lheInfo->hepeup().PUP[i][1];
	float pz = lheInfo->hepeup().PUP[i][2];
	_lhe_E.push_back(lheInfo->hepeup().PUP[i][3]);
	TLorentzVector pv  = TLorentzVector(px, py, pz, _lhe_E[i]);
	_lhe_pt.push_back(pv.Et());
	_lhe_eta.push_back(pv.Eta());
	_lhe_phi.push_back(pv.Phi());
	_lhe_pdgId.push_back(lheInfo->hepeup().IDUP[i]);
	_lhe_status.push_back(lheInfo->hepeup().ISTUP[i]);
	_lhe_index.push_back(i);
	_lhe_mother1Index.push_back(lheInfo->hepeup().MOTHUP[i].first-1);
	_lhe_mother2Index.push_back(lheInfo->hepeup().MOTHUP[i].second-1);
     }
   
   ftree->lhe_n = _lhe_n;
   ftree->lhe_pt = _lhe_pt;
   ftree->lhe_eta = _lhe_eta;
   ftree->lhe_phi = _lhe_phi;
   ftree->lhe_E = _lhe_E;
   ftree->lhe_pdgId = _lhe_pdgId;
   ftree->lhe_status = _lhe_status;
   ftree->lhe_index = _lhe_index;
   ftree->lhe_mother1Index = _lhe_mother1Index;
   ftree->lhe_mother2Index = _lhe_mother2Index;
   
   // Save all gen particles
   int _gen_n = 0;
   std::vector<int> _gen_daughter_n;
   std::vector<std::vector<int> > _gen_daughterIndex;
   std::vector<float> _gen_pt;
   std::vector<float> _gen_eta;
   std::vector<float> _gen_phi;
   std::vector<float> _gen_E;
   std::vector<int> _gen_pdgId;
   std::vector<int> _gen_charge;
   std::vector<int> _gen_status;
   std::vector<bool> _gen_isPromptFinalState;
   std::vector<bool> _gen_isDirectPromptTauDecayProductFinalState;
   std::vector<bool> _gen_isLastCopy;
   std::vector<int> _gen_index;
   std::vector<int> _gen_motherIndex;
   
   for(const reco::GenParticle& p : *genParticles)
     {
	int indexGen = _gen_n;
	
	int nDaughters = p.numberOfDaughters();
	
	_gen_daughter_n.push_back(nDaughters);

	std::vector<int> daug;
	for(int d=0;d<nDaughters;++d)
	  {	     
	     daug.push_back(p.daughterRef(d).key());
	  }
	_gen_daughterIndex.push_back(daug);
	
	_gen_pt.push_back(p.pt());
	_gen_eta.push_back(p.eta());
	_gen_phi.push_back(p.phi());
	_gen_E.push_back(p.energy());
	_gen_pdgId.push_back(p.pdgId());
	_gen_charge.push_back(p.charge());
	_gen_status.push_back(p.status());
	_gen_isPromptFinalState.push_back(p.isPromptFinalState());
	_gen_isDirectPromptTauDecayProductFinalState.push_back(p.isDirectPromptTauDecayProductFinalState());
	_gen_isLastCopy.push_back(p.isLastCopy());
	_gen_index.push_back(indexGen);
	_gen_motherIndex.push_back((p.numberOfMothers() == 0) ? -1 : p.motherRef(0).key());
	
	++_gen_n;
     }
   
   ftree->gen_n = _gen_n;
   ftree->gen_daughter_n = _gen_daughter_n;
   ftree->gen_daughterIndex = _gen_daughterIndex;
   ftree->gen_pt = _gen_pt;
   ftree->gen_eta = _gen_eta;
   ftree->gen_phi = _gen_phi;
   ftree->gen_E = _gen_E;
   ftree->gen_pdgId = _gen_pdgId;
   ftree->gen_charge = _gen_charge;
   ftree->gen_status = _gen_status;
   ftree->gen_isPromptFinalState = _gen_isPromptFinalState;
   ftree->gen_isDirectPromptTauDecayProductFinalState = _gen_isDirectPromptTauDecayProductFinalState;
   ftree->gen_isLastCopy = _gen_isLastCopy;
   ftree->gen_index = _gen_index;
   ftree->gen_motherIndex = _gen_motherIndex;

   float _pl_met = -1.;
   float _pl_metPhi = -1.;
   
   int _pl_nPh = 0;
   std::vector<float> _pl_phPt;
   std::vector<float> _pl_phEta;
   std::vector<float> _pl_phPhi;
   std::vector<float> _pl_phE;
   
   int _pl_nL = 0;
   std::vector<float> _pl_lPt;
   std::vector<float> _pl_lEta;
   std::vector<float> _pl_lPhi;
   std::vector<float> _pl_lE;
   std::vector<int> _pl_lCharge;
   std::vector<int> _pl_lFlavor;
   
   int _pl_nJets = 0;
   std::vector<float> _pl_jetPt;
   std::vector<float> _pl_jetEta;
   std::vector<float> _pl_jetPhi;
   std::vector<float> _pl_jetE;
   std::vector<int> _pl_jetHadronFlavor;
   
   const reco::MET &metv = particleLevelMets->front();
   _pl_met    = metv.pt();
   _pl_metPhi = metv.phi();
   
   for( const reco::GenParticle& p : *particleLevelPhotons )
     {
	_pl_phPt.push_back(p.pt());
	_pl_phEta.push_back(p.eta());
	_pl_phPhi.push_back(p.phi());
	_pl_phE.push_back(p.energy());
     }
   _pl_nPh = _pl_phPt.size();

   for( const reco::GenJet& p : *particleLevelLeptons )
     {
	_pl_lPt.push_back(p.pt());
	_pl_lEta.push_back(p.eta());
	_pl_lPhi.push_back(p.phi());
	_pl_lE.push_back(p.energy());
	_pl_lCharge.push_back(p.charge());

	if( abs(p.pdgId()) == 11 ) _pl_lFlavor.push_back(0);
	else if( abs(p.pdgId()) == 13 ) _pl_lFlavor.push_back(1);
	else _pl_lFlavor.push_back(2);
     }
   _pl_nL = _pl_lPt.size();
   
   for( const reco::GenJet& p : *particleLevelJets )
     {	
	_pl_jetPt.push_back(p.pt());
	_pl_jetEta.push_back(p.eta());
	_pl_jetPhi.push_back(p.phi());
	_pl_jetE.push_back(p.energy());
	_pl_jetHadronFlavor.push_back(p.pdgId());
     }   
   _pl_nJets = _pl_jetPt.size();

   ftree->pl_met = _pl_met;
   ftree->pl_metPhi = _pl_metPhi;
   
   ftree->pl_nPh = _pl_nPh;
   ftree->pl_phPt = _pl_phPt;
   ftree->pl_phEta = _pl_phEta;
   ftree->pl_phPhi = _pl_phPhi;
   ftree->pl_phE = _pl_phE;

   ftree->pl_nL = _pl_nL;
   ftree->pl_lPt = _pl_lPt;
   ftree->pl_lEta = _pl_lEta;
   ftree->pl_lPhi = _pl_lPhi;
   ftree->pl_lE = _pl_lE;
   ftree->pl_lCharge = _pl_lCharge;
   ftree->pl_lFlavor = _pl_lFlavor;

   ftree->pl_nJets = _pl_nJets;
   ftree->pl_jetPt = _pl_jetPt;
   ftree->pl_jetEta = _pl_jetEta;
   ftree->pl_jetPhi = _pl_jetPhi;
   ftree->pl_jetE = _pl_jetE;
   ftree->pl_jetHadronFlavor = _pl_jetHadronFlavor;
   
   unsigned _ttgEventType = overlapEventType(*genParticles, 10., 5.0, 0.1);
   unsigned _zgEventType  = overlapEventType(*genParticles, 15., 2.6, 0.05);

   ftree->ttgEventType = _ttgEventType;
   ftree->zgEventType = _zgEventType;
   
   ftree->tree->Fill();
}

void GenTreeMaker::beginRun(const edm::Run& iRun, const edm::EventSetup& iSetup)
{
}

void GenTreeMaker::endRun() 
{
}

//define this as a plug-in
DEFINE_FWK_MODULE(GenTreeMaker);
