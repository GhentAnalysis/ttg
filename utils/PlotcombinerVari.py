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

CR = 'llg-mll40-onZ-llgNoZ-njet1p-photonPt20'
SR = 'llg-mll40-offZ-llgNoZ-njet1p-photonPt20'

# ranges = ['-phMVANEG0.6to0.20','-phMVANEG0.4to0.20','-phMVANEG0.6to0.10','-phMVANEG0.4to0.10']
# ranges = ['-phMVANEG0.6to0.20']
ranges = None

for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions',
  'njets','phBJetDeltaR','phJetDeltaR_small','phRawJetDeltaR_WIDE', 'nTrueInt']:  
# clallcb
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clallcb_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clallcb_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clsel
    try: phoClosure(basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clsel_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clsel-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clsel_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# clfullcb
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# nophocl
    try: phoClosure(basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_nophocl_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-nophocl-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_nophocl_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# expcl
    try: phoClosure(basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_expcl_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-expcl-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_expcl_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# clfullcb llveto
    try: phoClosure(basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcbLLVeto_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-looseLeptonVeto-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcbLLVeto_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# sigcla
    try: phoClosure(basePath + 'phoCB-sigcla-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcla_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-sigcla-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcla-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcla_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
# sigclb
    try: phoClosure(basePath + 'phoCB-sigclb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigclb_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-sigclb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigclb_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# sigclc
    try: phoClosure(basePath + 'phoCB-sigclc-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigclc_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-sigclc-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigclc-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigclc_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# sigcld
    try: phoClosure(basePath + 'phoCB-sigcld-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcld_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-sigcld-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcld-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcld_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# sigcle
    try: phoClosure(basePath + 'phoCB-sigcle-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcle_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-sigcle-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-sigcle-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_sigcle_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clfullcb-noPixelSeedVeto
    try: phoClosure(basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb-noPixelSeedVeto_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-noPixelSeedVeto-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_clfullcb-noPixelSeedVeto_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)


    try: phoClosure(basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      'newPlots/' + plot + '_puIsoCut_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      basePath + 'phoCBmagic-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-mll40-offZ-llgNoZ-njet2p-photonPt20-puChargedHadronIso0to18/'+ plot + '.pkl',
                      'newPlots/' + plot + '_puIsoCut_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)



# clallcb
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_anymass_clallcb_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clallcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_anymass_clallcb_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clfullcb
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet1p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_anymass_clfullcb_njet1p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
    try: phoClosure(basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilFake/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-sidebandSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-passChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-clfullcb-failChgIso-passSigmaIetaIeta-onlyTTDilHad/noData/llg-njet2p-photonPt20/'+ plot + '.pkl',
                      'newPlots/' + plot + '_anymass_clfullcb_njet2p.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
