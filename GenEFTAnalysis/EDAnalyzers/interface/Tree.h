#ifndef TREE_H
#define TREE_H

#include <TTree.h>
#include <string>
#include <iostream>
#include <vector>

#define null -777

class GenTree
{ 
   
 public:
   
   GenTree(TTree *_tree);
   
   TTree *tree;
   
   void Init();
   void CreateBranches(int buff);

   float weight;
   float weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_0p;
   float weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_0p;
   float weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_0p;
   float weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_0p;
   float weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_1p;
   float weight_ctZ_2p_ctZI_0p_ctW_0p_ctWI_0p;
   float weight_ctZ_1p_ctZI_1p_ctW_0p_ctWI_0p;
   float weight_ctZ_1p_ctZI_0p_ctW_1p_ctWI_0p;
   float weight_ctZ_1p_ctZI_0p_ctW_0p_ctWI_1p;
   float weight_ctZ_0p_ctZI_2p_ctW_0p_ctWI_0p;
   float weight_ctZ_0p_ctZI_1p_ctW_1p_ctWI_0p;
   float weight_ctZ_0p_ctZI_1p_ctW_0p_ctWI_1p;
   float weight_ctZ_0p_ctZI_0p_ctW_2p_ctWI_0p;
   float weight_ctZ_0p_ctZI_0p_ctW_1p_ctWI_1p;
   float weight_ctZ_0p_ctZI_0p_ctW_0p_ctWI_2p;
   
   int gen_n;
   
   std::vector<int> gen_daughter_n;
   std::vector<std::vector<int> > gen_daughterIndex;
   std::vector<float> gen_pt;
   std::vector<float> gen_eta;
   std::vector<float> gen_phi;
   std::vector<float> gen_E;
   std::vector<int> gen_pdgId;
   std::vector<int> gen_charge;
   std::vector<int> gen_status;
   std::vector<bool> gen_isPromptFinalState;
   std::vector<bool> gen_isDirectPromptTauDecayProductFinalState;
   std::vector<bool> gen_isLastCopy;
   std::vector<int> gen_index;
   std::vector<int> gen_motherIndex;

   int lhe_n;
   
   std::vector<float> lhe_E;
   std::vector<float> lhe_pt;
   std::vector<float> lhe_eta;
   std::vector<float> lhe_phi;
   std::vector<int> lhe_pdgId;
   std::vector<int> lhe_status;
   std::vector<int> lhe_index;
   std::vector<int> lhe_mother1Index;
   std::vector<int> lhe_mother2Index;

   float pl_met;
   float pl_metPhi;
   
   int pl_nPh;
   std::vector<float> pl_phPt;
   std::vector<float> pl_phEta;
   std::vector<float> pl_phPhi;
   std::vector<float> pl_phE;

   int pl_nL;
   std::vector<float> pl_lPt;
   std::vector<float> pl_lEta;
   std::vector<float> pl_lPhi;
   std::vector<float> pl_lE;
   std::vector<int> pl_lCharge;
   std::vector<int> pl_lFlavor;

   int pl_nJets;
   std::vector<float> pl_jetPt;
   std::vector<float> pl_jetEta;
   std::vector<float> pl_jetPhi;
   std::vector<float> pl_jetE;
   std::vector<int> pl_jetHadronFlavor;
   
   unsigned ttgEventType;
   unsigned zgEventType;
};

#endif
