#include "GenEFTAnalysis/EDAnalyzers/interface/Tree.h"

GenTree::GenTree(TTree* _tree)
{
   tree = _tree;
}

void GenTree::Init()
{
   weight = null;
   weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p = null;
   weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p = null;
   weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p = null;
   weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p = null;
   weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p = null;
   weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p = null;
   weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p = null;
   weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p = null;
   weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p = null;
   weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p = null;

   gen_n = 0;
   gen_daughter_n.clear();
   gen_daughterIndex.clear();
   gen_pt.clear();
   gen_eta.clear();
   gen_phi.clear();
   gen_E.clear();
   gen_pdgId.clear();
   gen_charge.clear();
   gen_status.clear();
   gen_isPromptFinalState.clear();
   gen_isDirectPromptTauDecayProductFinalState.clear();
   gen_isLastCopy.clear();
   gen_index.clear();
   gen_motherIndex.clear();

   lhe_n = 0;
   
   lhe_E.clear();
   lhe_pt.clear();
   lhe_eta.clear();
   lhe_phi.clear();
   lhe_pdgId.clear();
   lhe_status.clear();
   lhe_index.clear();
   lhe_mother1Index.clear();
   lhe_mother2Index.clear();

   pl_met = -1;
   pl_metPhi = -1;
   
   pl_nPh = 0;
   pl_phPt.clear();
   pl_phEta.clear();
   pl_phPhi.clear();
   pl_phE.clear();
   
   pl_nL = 0;
   pl_lPt.clear();
   pl_lEta.clear();
   pl_lPhi.clear();
   pl_lE.clear();
   pl_lCharge.clear();
   pl_lFlavor.clear();

   pl_nJets = 0;
   pl_jetPt.clear();
   pl_jetEta.clear();
   pl_jetPhi.clear();
   pl_jetE.clear();
   pl_jetHadronFlavor.clear();
   
   ttgEventType = 777;
   zgEventType = 777;
}

void GenTree::CreateBranches(int buff = 32000)
{
   tree->Branch("weight", &weight, "weight/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p", &weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p, "weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p", &weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p, "weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p", &weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p, "weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p", &weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p, "weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p", &weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p, "weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p/F", buff);
   tree->Branch("weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p", &weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p, "weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p", &weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p, "weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p", &weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p, "weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p", &weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p, "weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p", &weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p, "weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p", &weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p, "weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p", &weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p, "weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p", &weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p, "weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p", &weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p, "weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p/F", buff);
   tree->Branch("weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p", &weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p, "weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p/F", buff);
   
   tree->Branch("gen_n", &gen_n, "gen_n/I", buff);   
   tree->Branch("gen_daughter_n", "std::vector<int>", &gen_daughter_n, buff);
   tree->Branch("gen_daughterIndex", "std::vector<std::vector<int> >", &gen_daughterIndex, buff);
   tree->Branch("gen_pt", "std::vector<float>", &gen_pt, buff);
   tree->Branch("gen_eta", "std::vector<float>", &gen_eta, buff);
   tree->Branch("gen_phi", "std::vector<float>", &gen_phi, buff);
   tree->Branch("gen_E", "std::vector<float>", &gen_E, buff);
   tree->Branch("gen_pdgId", "std::vector<int>", &gen_pdgId, buff);
   tree->Branch("gen_charge", "std::vector<int>", &gen_charge, buff);
   tree->Branch("gen_status", "std::vector<int>", &gen_status, buff);
   tree->Branch("gen_isPromptFinalState", "std::vector<bool>", &gen_isPromptFinalState, buff);
   tree->Branch("gen_isDirectPromptTauDecayProductFinalState", "std::vector<bool>", &gen_isDirectPromptTauDecayProductFinalState, buff);
   tree->Branch("gen_isLastCopy", "std::vector<bool>", &gen_isLastCopy, buff);
   tree->Branch("gen_index", "std::vector<int>", &gen_index, buff);
   tree->Branch("gen_motherIndex", "std::vector<int>", &gen_motherIndex, buff);

   tree->Branch("lhe_n", &lhe_n, "lhe_n/I", buff);
   tree->Branch("lhe_E", "std::vector<float>", &lhe_E, buff);
   tree->Branch("lhe_pt", "std::vector<float>", &lhe_pt, buff);
   tree->Branch("lhe_eta", "std::vector<float>", &lhe_eta, buff);
   tree->Branch("lhe_phi", "std::vector<float>", &lhe_phi, buff);
   tree->Branch("lhe_pdgId", "std::vector<int>", &lhe_pdgId, buff);
   tree->Branch("lhe_status", "std::vector<int>", &lhe_status, buff);
   tree->Branch("lhe_index", "std::vector<int>", &lhe_index, buff);
   tree->Branch("lhe_mother1Index", "std::vector<int>", &lhe_mother1Index, buff);
   tree->Branch("lhe_mother2Index", "std::vector<int>", &lhe_mother2Index, buff);

   tree->Branch("pl_met", &pl_met, "pl_met/F", buff);
   tree->Branch("pl_metPhi", &pl_metPhi, "pl_metPhi/F", buff);
   
   tree->Branch("pl_nPh", &pl_nPh, "pl_nPh/I", buff);
   tree->Branch("pl_phPt", "std::vector<float>", &pl_phPt, buff);
   tree->Branch("pl_phEta", "std::vector<float>", &pl_phEta, buff);
   tree->Branch("pl_phPhi", "std::vector<float>", &pl_phPhi, buff);
   tree->Branch("pl_phE", "std::vector<float>", &pl_phE, buff);
   
   tree->Branch("pl_nL", &pl_nL, "pl_nL/I", buff);
   tree->Branch("pl_lPt", "std::vector<float>", &pl_lPt, buff);
   tree->Branch("pl_lEta", "std::vector<float>", &pl_lEta, buff);
   tree->Branch("pl_lPhi", "std::vector<float>", &pl_lPhi, buff);
   tree->Branch("pl_lE", "std::vector<float>", &pl_lE, buff);
   tree->Branch("pl_lCharge", "std::vector<int>", &pl_lCharge, buff);
   tree->Branch("pl_lFlavor", "std::vector<int>", &pl_lFlavor, buff);

   tree->Branch("pl_nJets", &pl_nJets, "pl_nJets/I", buff);
   tree->Branch("pl_jetPt", "std::vector<float>", &pl_jetPt, buff);
   tree->Branch("pl_jetEta", "std::vector<float>", &pl_jetEta, buff);
   tree->Branch("pl_jetPhi", "std::vector<float>", &pl_jetPhi, buff);
   tree->Branch("pl_jetE", "std::vector<float>", &pl_jetE, buff);
   tree->Branch("pl_jetHadronFlavor", "std::vector<int>", &pl_jetHadronFlavor, buff);

   tree->Branch("ttgEventType", &ttgEventType, "ttgEventType/I", buff);
   tree->Branch("zgEventType", &zgEventType, "zgEventType/I", buff);
}
