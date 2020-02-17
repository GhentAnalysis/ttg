import pickle
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
# tdr.setTDRStyle()
# ROOT.gStyle.SetPaintTextFormat(paintformat)
ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")


basePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/'
oldBasePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016HadCategBug'

def sumHists(picklePath, plot):
  hists = pickle.load(open(picklePath))[plot]
  sumHist = None
  for name, hist in hists.iteritems():
    if not sumHist: sumHist = hist
    else: sumHist.Add(hist)
  return sumHist

def phoClosure(CRTF, CRLF, SRTF, SRLF, CRTH, CRLH, SRTH, SRLH, outName, plotName): 
  crtf = sumHists(CRTF, plotName)
  crlf = sumHists(CRLF, plotName)
  srtf = sumHists(SRTF, plotName)
  srlf = sumHists(SRLF, plotName)
  crth = sumHists(CRTH, plotName)
  crlh = sumHists(CRLH, plotName)
  srth = sumHists(SRTH, plotName)
  srlh = sumHists(SRLH, plotName)
  crtf.Divide(crlf)
  srtf.Divide(srlf)
  crth.Divide(crlh)
  srth.Divide(srlh)
  c1 = ROOT.TCanvas("c1")
  crtf.SetLineColor(861)
  srtf.SetLineColor(602)
  crth.SetLineColor(632)
  srth.SetLineColor(633)
  # set y range based on histogram max
  scaling = ""
  # if max([srth.Integral(), srth.Integral()]) > 2. * max([srtf.Integral(), srtf.Integral()]):
  if srth.Integral() + srth.Integral() > 2.5 * (srtf.Integral() + srtf.Integral()):
    scaling = round(0.5 * (srth.Integral() + srth.Integral())/ (srtf.Integral() + srtf.Integral()))
    crtf.Scale(scaling)
    srtf.Scale(scaling)
    scaling = "x " + str(scaling) + " "
  nbins = crtf.GetNbinsX() + 1
  binmax = 2. * max([crtf.GetBinContent(bin) for bin in range(1, nbins)] + [srth.GetBinContent(bin) for bin in range(1, nbins)] + [crtf.GetBinContent(bin) for bin in range(1, nbins)] + [srth.GetBinContent(bin) for bin in range(1, nbins)])
  crtf.GetYaxis().SetRangeUser(0., binmax)
  #label x-axis based on plot name
  if plotName.count('photon_pt'):
    crtf.GetXaxis().SetTitle("p_{T} (#gamma) [ GeV ]")
  if plotName.count('photon_eta'):
    crtf.GetXaxis().SetRangeUser(0., 1.5)
    crtf.GetXaxis().SetTitle("#eta (#gamma)")  
  if plotName.count('njet'):
    crtf.GetXaxis().SetTitle("number of jets")
  if plotName.count('signalRegions'):
    labels = ['0j,0b', '1j,0b', '2j,0b', '#geq3j,0b', '1j,1b', '2j,1b', '#geq3j,1b', '2j,2b', '#geq3j,2b', '#geq3j,#geq3b']
    for i, l in enumerate(labels):
      crtf.GetXaxis().SetBinLabel(i+1, l)
  if plotName.count('yield'):
    crtf.GetXaxis().SetTitle("yield")
    labels = ['#mu #mu', 'e #mu', 'ee']
    for i, l in enumerate(labels):
      crtf.GetXaxis().SetBinLabel(i+1, l)

  crtf.SetTitle(" ")

  crtf.GetYaxis().SetTitle("signal/sideband")
  crtf.Draw("E1")
  srtf.Draw("E1 SAME")
  crth.Draw("E1 SAME")
  srth.Draw("E1 SAME")
  c1.RedrawAxis()
  legend = ROOT.TLegend(0.7,0.74,0.9,0.9)
  legend.AddEntry(crtf,"Fake | Measurement Region " + scaling,"E")
  legend.AddEntry(srtf,"Fake | Application Region " + scaling,"E")
  legend.AddEntry(crth,"Hadr | Measurement Region ","E")
  legend.AddEntry(srth,"Hadr | Application Region ","E")
  legend.Draw()
  c1.SaveAs(outName)


for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions',
  'njets','phBJetDeltaR','phJetDeltaR_small','phRawJetDeltaR_WIDE', 'nTrueInt']:  
# clallcb
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      'plotsEta/' + plot + '_clallcb_njet1p_lowEta.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# clfullcb
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0to0.8/'+ plot + '.pkl',
                      'plotsEta/' + plot + '_clfullcb_njet1p_lowEta.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clallcb
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      'plotsEta/' + plot + '_clallcb_njet1p_highEta.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# clfullcb
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20-photonEta0.8to1.6/'+ plot + '.pkl',
                      'plotsEta/' + plot + '_clfullcb_njet1p_highEta.pdf',
                  plot
                  )
    except Exception as e:
      print(e)