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

def phoClosure(CRTF, CRLF, SRTF, SRLF, outName, plotName): 
  crtf = sumHists(CRTF, plotName)
  crlf = sumHists(CRLF, plotName)
  srtf = sumHists(SRTF, plotName)
  srlf = sumHists(SRLF, plotName)
  crtf.Divide(crlf)
  srtf.Divide(srlf)
  c1 = ROOT.TCanvas("c1")
  crtf.SetLineColor(861)
  srtf.SetLineColor(602)
  # set y range based on histogram max
  scaling = ""
  # if max([srth.Integral(), srth.Integral()]) > 2. * max([srtf.Integral(), srtf.Integral()]):
  if srtf.Integral() + srtf.Integral() > 2.5 * (srtf.Integral() + srtf.Integral()):
    scaling = round(0.5 * (srtf.Integral() + srtf.Integral())/ (srtf.Integral() + srtf.Integral()))
    crtf.Scale(scaling)
    srtf.Scale(scaling)
    scaling = "x " + str(scaling) + " "
  nbins = crtf.GetNbinsX() + 1
  binmax = 1.5 * max([crtf.GetBinContent(bin) for bin in range(1, nbins)] + [srtf.GetBinContent(bin) for bin in range(1, nbins)] + [crtf.GetBinContent(bin) for bin in range(1, nbins)] + [srtf.GetBinContent(bin) for bin in range(1, nbins)])
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
  c1.RedrawAxis()
  legend = ROOT.TLegend(0.7,0.74,0.9,0.9)
  legend.AddEntry(crtf,"NP | Measurement Region " + scaling,"E")
  legend.AddEntry(srtf,"NP | Application Region " + scaling,"E")
  legend.Draw()
  c1.SaveAs(outName)

ranges = None

for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions', 'njets']:  
    try: phoClosure(basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-signalRegion-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-signalRegion-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-signalRegion-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-signalRegion-photonPt20/'+ plot + '.pkl',
                      'newPlotsNP/' + plot + '_signalRegion.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlotsNP/' + plot + '_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)