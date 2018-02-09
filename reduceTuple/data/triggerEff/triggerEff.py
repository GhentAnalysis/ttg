#! /usr/bin/env python

#
# !!!
# Warning: script is possibly not working anymore
# !!!
#

import os, argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--mode',           action='store',      default='muEle',     choices=['doubleMu', 'doubleEle',  'muEle'])
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

#
# Create sample list
#
from ttg.samples.Sample import createSampleList,getSampleFromList
sampleList = createSampleList(os.path.expandvars('$CMSSW_BASE/src/ttg/samples/data/tuplesMET.conf')))
sample     = getSampleFromList(sampleList, 'MET')
c          = sample.initTree(skimType='dilepton')

pt_thresholds            = range(0,30,2)+range(30,50,5)+range(50,210,10)
eta_thresholds           = [x/10. for x in range(-25,26,1) ]
pt_thresholds_coarse     = range(5,25,10)+range(25,130,15)+range(130,330,50)
pt_thresholds_veryCoarse = [20,25,35] + range(50,200,50)+[250]
eta_thresholds_coarse    = [x/10. for x in range(-25,26,5) ]

eff_pt1 = ROOT.TProfile("eff_pt1","eff_pt1", len(pt_thresholds)-1, array.array('d',pt_thresholds), 0,1)
eff_pt1.GetYaxis().SetTitle(triggerName)
eff_pt1.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1.style = styles.errorStyle( ROOT.kBlack )

eff_pt2 = ROOT.TProfile("eff_pt2","eff_pt2", len(pt_thresholds)-1, array.array('d',pt_thresholds), 0,1)
eff_pt2.GetYaxis().SetTitle(triggerName)
eff_pt2.GetXaxis().SetTitle("p_{T} of trailing lepton")
eff_pt2.style = styles.errorStyle( ROOT.kBlack )

eff_eta1 = ROOT.TProfile("eff_eta1","eff_eta1", len(eta_thresholds)-1, array.array('d',eta_thresholds), 0,1)
eff_eta1.GetYaxis().SetTitle(triggerName)
eff_eta1.GetXaxis().SetTitle("#eta of leading lepton")
eff_eta1.style = styles.errorStyle( ROOT.kBlack )

eff_eta2 = ROOT.TProfile("eff_eta2","eff_eta2", len(eta_thresholds)-1, array.array('d',eta_thresholds), 0,1)
eff_eta2.GetYaxis().SetTitle(triggerName)
eff_eta2.GetXaxis().SetTitle("#eta of trailing lepton")
eff_eta2.style = styles.errorStyle( ROOT.kBlack )

ht = ROOT.TH1D("ht","ht", 2000/50,0,2000)
ht.GetYaxis().SetTitle("Number of events")
ht.GetXaxis().SetTitle("H_{T} (GeV)")
ht.style = styles.errorStyle( ROOT.kBlack )

eff_pt1_pt2 = ROOT.TProfile2D("eff_pt1_pt2","eff_pt1_pt2", len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse), len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse))
eff_pt1_pt2.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1_pt2.GetYaxis().SetTitle("p_{T} of trailing lepton")
eff_pt1_pt2.style = styles.errorStyle( ROOT.kBlack )

eff_pt1_pt2_veryCoarse = ROOT.TProfile2D("eff_pt1_pt2_veryCoarse","eff_pt1_pt2_veryCoarse", len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse), len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse))
eff_pt1_pt2_veryCoarse.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1_pt2_veryCoarse.GetYaxis().SetTitle("p_{T} of trailing lepton")
eff_pt1_pt2_veryCoarse.style = styles.errorStyle( ROOT.kBlack )

eff_pt1_pt2_highEta1_veryCoarse = ROOT.TProfile2D("eff_pt1_pt2_highEta1_veryCoarse","eff_pt1_pt2_highEta1_veryCoarse", len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse), len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse))
eff_pt1_pt2_highEta1_veryCoarse.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1_pt2_highEta1_veryCoarse.GetYaxis().SetTitle("p_{T} of trailing lepton")
eff_pt1_pt2_highEta1_veryCoarse.style = styles.errorStyle( ROOT.kBlack )

eff_pt1_pt2_lowEta1_veryCoarse = ROOT.TProfile2D("eff_pt1_pt2_lowEta1_veryCoarse","eff_pt1_pt2_lowEta1_veryCoarse", len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse), len(pt_thresholds_veryCoarse)-1, array.array('d',pt_thresholds_veryCoarse))
eff_pt1_pt2_lowEta1_veryCoarse.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1_pt2_lowEta1_veryCoarse.GetYaxis().SetTitle("p_{T} of trailing lepton")
eff_pt1_pt2_lowEta1_veryCoarse.style = styles.errorStyle( ROOT.kBlack )

eff_pt1_eta1 = ROOT.TProfile2D("eff_pt1_eta1","eff_pt1_eta1", len(pt_thresholds_coarse)-1, array.array('d',pt_thresholds_coarse), len(eta_thresholds_coarse)-1, array.array('d',eta_thresholds_coarse))
eff_pt1_eta1.GetXaxis().SetTitle("p_{T} of leading lepton")
eff_pt1_eta1.GetYaxis().SetTitle("#eta of leading lepton")
eff_pt1_eta1.style = styles.errorStyle( ROOT.kBlack )

eff_pt2_eta2 = ROOT.TProfile2D("eff_pt2_eta2","eff_pt2_eta2", len(pt_thresholds_coarse)-1, array.array('d',pt_thresholds_coarse), len(eta_thresholds_coarse)-1, array.array('d',eta_thresholds_coarse))
eff_pt2_eta2.GetXaxis().SetTitle("p_{T} of trailing lepton")
eff_pt2_eta2.GetYaxis().SetTitle("#eta of trailing lepton")
eff_pt2_eta2.style = styles.errorStyle( ROOT.kBlack )




from ttg.reduceTuple.objectSelection import select2l
for i in sample.eventLoop(totalJobs=1, subJob=0, selectionString=None):
  c.GetEntry(i)
  if not (select2l(c, c)): continue

    if sample.name.count('DoubleMuon') and not c._passTTG_mm:                              continue
    if sample.name.count('DoubleEG')   and not c._passTTG_ee:                              continue
    if sample.name.count('MuonEG')     and not c._passTTG_em:                              continue
    if sample.name.count('SingleMuon'):
      if newVars.isMuMu and not (not c._passTTG_mm and c._passTTG_m):                      continue
      if newVars.isEMu  and not (not c._passTTG_em and c._passTTG_m):                      continue
    if sample.name.count('SingleElectron'):
      if newVars.isEE   and not (not c._passTTG_ee and c._passTTG_e):                      continue
      if newVars.isEMu  and not (not c._passTTG_em and c._passTTG_e and not c._passTTG_m): continue


plot_string_pt1      = args.dileptonTrigger+":MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1"
plot_string_pt2      = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt2"

logger.info( "Plot string: %s" % plot_string_pt1 )
logger.info( "Selection:   %s" % selection_string )
 
data.chain.Draw(plot_string_pt1, selection_string, 'goff')
data.chain.Draw(plot_string_pt2, selection_string, 'goff')

data.chain.Draw("Sum$(Jet_pt*(Jet_pt>30&&abs(Jet_eta)<2.4&&Jet_id))>>ht", selection_string, 'goff')

plot_string_eta1     = args.dileptonTrigger+":LepGood_eta>>eff_eta1"
data.chain.Draw(plot_string_eta1, selection_string+"&&LepGood_pt==MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+')', 'goff') 

plot_string_eta2     = args.dileptonTrigger+":LepGood_eta>>eff_eta2"
data.chain.Draw(plot_string_eta2, selection_string+"&&LepGood_pt==MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+')', 'goff') 

plot_string_pt1_pt2    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2"
data.chain.Draw(plot_string_pt1_pt2, selection_string, 'goff')
plot_string_pt1_pt2_veryCoarse    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2_veryCoarse"
data.chain.Draw(plot_string_pt1_pt2_veryCoarse, selection_string, 'goff')

if args.mode=='muEle':
    # split high/low wrt muon
    plot_string_pt1_pt2_highEta1_veryCoarse    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2_highEta1_veryCoarse"
    data.chain.Draw(plot_string_pt1_pt2_highEta1_veryCoarse, selection_string+"&&Sum$(abs(LepGood_pdgId)==13&&abs(LepGood_eta)>1.5&&"+selString(index=None,ptCut=0)+')==1', 'goff')

    plot_string_pt1_pt2_lowEta1_veryCoarse    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2_lowEta1_veryCoarse"
    data.chain.Draw(plot_string_pt1_pt2_lowEta1_veryCoarse, selection_string+"&&Sum$(abs(LepGood_pdgId)==13&&abs(LepGood_eta)<=1.5&&"+selString(index=None,ptCut=0)+')==1', 'goff')
else:
    # split high/low wrt leading lepton
    plot_string_pt1_pt2_highEta1_veryCoarse    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2_highEta1_veryCoarse"
    data.chain.Draw(plot_string_pt1_pt2_highEta1_veryCoarse, selection_string+"&&Sum$(abs(LepGood_eta)>1.5&&LepGood_pt==MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+'))==1', 'goff')

    plot_string_pt1_pt2_lowEta1_veryCoarse    = args.dileptonTrigger+":MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+"):MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_pt2_lowEta1_veryCoarse"
    data.chain.Draw(plot_string_pt1_pt2_lowEta1_veryCoarse, selection_string+"&&Sum$(abs(LepGood_eta)<=1.5&&LepGood_pt==MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+'))==1', 'goff')

plot_string_pt1_eta1   = args.dileptonTrigger+":LepGood_eta:MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt1_eta1"
data.chain.Draw(plot_string_pt1_eta1, selection_string+"&&LepGood_pt==MaxIf$(LepGood_pt,"+selString(index=None,ptCut=0)+')', 'goff')

plot_string_pt2_eta2   = args.dileptonTrigger+":LepGood_eta:MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+")>>eff_pt2_eta2"
data.chain.Draw(plot_string_pt2_eta2, selection_string+"&&LepGood_pt==MinIf$(LepGood_pt,"+selString(index=None,ptCut=0)+')', 'goff')


prefix = preprefix+"_%s_%s_measuredIn%s_minLeadLepPt%i" % ( triggerName, 'baseTrigger_METhadronic', args.sample, args.minLeadingLeptonPt)
if args.small: prefix = "small_" + prefix

from StopsDilepton.tools.user import plot_directory
plot_path = os.path.join(plot_directory, args.plot_directory, prefix)

plotting.draw(
    Plot.fromHisto(name = 'pt1_'+triggerName, histos = [[ eff_pt1 ]], texX = "p_{T} of leading lepton", texY = triggerName),
    plot_directory = plot_path, #ratio = ratio, 
    logX = False, logY = False, sorting = False,
     yRange = (0,1), legend = None ,
    # scaling = {0:1},
    # drawObjects = drawObjects( dataMCScale )
)
plotting.draw(
    Plot.fromHisto(name = 'pt2_'+triggerName, histos = [[ eff_pt2 ]], texX = "p_{T} of trailing lepton", texY = triggerName),
    plot_directory = plot_path, #ratio = ratio, 
    logX = False, logY = False, sorting = False,
     yRange = (0,1), legend = None ,
    # scaling = {0:1},
    # drawObjects = drawObjects( dataMCScale )
)
plotting.draw(
    Plot.fromHisto(name = 'eta1_'+triggerName, histos = [[ eff_eta1 ]], texX = "#eta of leading lepton", texY = triggerName),
    plot_directory = plot_path, #ratio = ratio, 
    logX = False, logY = False, sorting = False,
     yRange = (0,1), legend = None ,
    # scaling = {0:1},
    # drawObjects = drawObjects( dataMCScale )
)
plotting.draw(
    Plot.fromHisto(name = 'eta2_'+triggerName, histos = [[ eff_eta2 ]], texX = "#eta of trailing lepton", texY = triggerName),
    plot_directory = plot_path, #ratio = ratio, 
    logX = False, logY = False, sorting = False,
     yRange = (0,1), legend = None ,
    # scaling = {0:1},
    # drawObjects = drawObjects( dataMCScale )
)
plotting.draw(
    Plot.fromHisto(name = "ht_"+triggerName, histos = [[ ht ]], texX = "H_{T} (GeV)", texY = "Number of events"),
    plot_directory = plot_path, #ratio = ratio, 
    logX = False, logY = True, sorting = False,
     yRange = (0.3,"auto"), legend = None ,
    # scaling = {0:1},
    # drawObjects = drawObjects( dataMCScale )
)

ROOT.gStyle.SetPadRightMargin(0.15)
ROOT.gStyle.SetPaintTextFormat("2.2f")
for name, plot in [
    ["pt1_pt2", eff_pt1_pt2],
    ["pt1_pt2_veryCoarse", eff_pt1_pt2_veryCoarse],
    ["pt1_pt2_lowEta1_veryCoarse", eff_pt1_pt2_lowEta1_veryCoarse],
    ["pt1_pt2_highEta1_veryCoarse", eff_pt1_pt2_highEta1_veryCoarse],
    ["pt1_eta1", eff_pt1_eta1],
    ["pt2_eta2", eff_pt2_eta2],
    ]:
    c1 = ROOT.TCanvas()
    if 'veryCoarse' in name:
        plot.SetMarkerSize(0.8)
        #plot.Draw("COLZTextE")
        plot.Draw("COLZText")
    else:
        plot.Draw("COLZ" )

    plot.GetZaxis().SetRangeUser(0,1)
    c1.Print(os.path.join(plot_path, triggerName+'_'+name+'.png') )
    c1.Print(os.path.join(plot_path, triggerName+'_'+name+'.pdf') )
    c1.Print(os.path.join(plot_path, triggerName+'_'+name+'.root') )
    del c1

ofile = ROOT.TFile.Open(os.path.join(plot_path, prefix+'.root'), 'recreate')
eff_pt1.Write()
eff_pt2.Write()
eff_eta1.Write()
eff_eta2.Write()
eff_pt1_pt2.Write()
eff_pt1_pt2_highEta1_veryCoarse.Write()
eff_pt1_pt2_lowEta1_veryCoarse.Write()
eff_pt1_eta1.Write()
eff_pt2_eta2.Write()
ht.Write()
ofile.Close()
