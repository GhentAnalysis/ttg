import pickle
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
# tdr.setTDRStyle()
# ROOT.gStyle.SetPaintTextFormat(paintformat)
ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")


basePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/'
oldBasePath = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016NPMCategBug'

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
  legend.AddEntry(crtf,"NP | Measurement Region " + scaling,"E")
  legend.AddEntry(srtf,"NP | Application Region " + scaling,"E")
  legend.AddEntry(crth,"NPM | Measurement Region ","E")
  legend.AddEntry(srth,"NPM | Application Region ","E")
  legend.Draw()
  c1.SaveAs(outName)

CR = 'llg-mll40-onZ-llgNoZ-njet1p-photonPt20'
SR = 'llg-mll40-offZ-llgNoZ-njet1p-photonPt20'

# ranges = ['-phMVANEG0.6to0.20','-phMVANEG0.4to0.20','-phMVANEG0.6to0.10','-phMVANEG0.4to0.10']
# ranges = ['-phMVANEG0.6to0.20']
ranges = None

for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions', 'njets','phBJetDeltaR','phJetDeltaR_small','phRawJetDeltaR_WIDE']:  
# clallcb
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clallcb_njet1p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clallcb_njet2p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clsel
    try: phoClosure(basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clsel_njet1p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clsel_njet2p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# clfullcb
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb_njet1p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb_njet2p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# nophocl
    try: phoClosure(basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_nophocl_njet1p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_nophocl_njet2p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# expcl
    try: phoClosure(basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_expcl_njet1p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_expcl_njet2p_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    # try: phoClosure(basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   'newPlots/' + plot + '_puIsoCut_njet1p_NP.pdf',
    #               plot
    #               )
    # except Exception as e:
    #   print(e)
    # try: phoClosure(basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilNP/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilNPM/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedNPMronIso0to18/'+ plot + '.pkl',
    #                   'newPlots/' + plot + '_puIsoCut_njet2p_NP.pdf',
    #               plot
    #               )
    # except Exception as e:
    #   print(e)