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

def phoMvaClosure(CRT, CRL, SRT, SRL, outName, plotName): 
  crt = sumHists(CRT, plotName)
  crl = sumHists(CRL, plotName)
  srt = sumHists(SRT, plotName)
  srl = sumHists(SRL, plotName)
  crt.Divide(crl)
  srt.Divide(srl)
  nbins = crt.GetNbinsX()
  binmax = 1.4 * max([crt.GetBinContent(bin) for bin in range(1, nbins)] + [srt.GetBinContent(bin) for bin in range(1, nbins)])
  c1 = ROOT.TCanvas("c1")
  srt.SetLineColor(632)
  crt.GetYaxis().SetRangeUser(0.,binmax)
  if plotName.count('photon_pt'):
    crt.GetXaxis().SetTitle("p_{T} (#gamma) [ GeV ]")
  if plotName.count('photon_eta'):
    crt.GetXaxis().SetTitle("#eta (#gamma)")  
  if plotName.count('njet'):
    crt.GetXaxis().SetTitle("number of jets")
  crt.GetYaxis().SetTitle("N mva cut / N mva sideband")
  crt.SetTitle(" ")
  crt.Draw("E1")
  srt.Draw("E1 SAME")
  c1.RedrawAxis()
  legend = ROOT.TLegend(0.7,0.74,0.9,0.9)
  legend.AddEntry(crt,"Measurement Region","E")
  legend.AddEntry(srt,"Application region","E")
  # legend->SetMargin(0.4);
  # legend->SetHeader("process","C");
  legend.Draw()
  c1.SaveAs(outName)

def phoCBClosure(CRT, CRL, SRT, SRL, outName, plotName): 
  crt = sumHists(CRT, plotName)
  crl = sumHists(CRL, plotName)
  srt = sumHists(SRT, plotName)
  srl = sumHists(SRL, plotName)
  crt.Divide(crl)
  srt.Divide(srl)
  c1 = ROOT.TCanvas("c1")
  srt.SetLineColor(632)
  nbins = crt.GetNbinsX()
  binmax = 1.4 * max([crt.GetBinContent(bin) for bin in range(1, nbins)] + [srt.GetBinContent(bin) for bin in range(1, nbins)])
  crt.GetYaxis().SetRangeUser(0., binmax)
  # if outName.count('sigma'):
  #   crt.GetYaxis().SetRangeUser(0.,1.)
  # else:
  #   crt.GetYaxis().SetRangeUser(0.,0.5)
  if plotName.count('photon_pt'):
    crt.GetXaxis().SetTitle("p_{T} (#gamma) [ GeV ]")
  if plotName.count('njet'):
    crt.GetXaxis().SetTitle("number of jets")
  if plotName.count('photon_eta'):
    crt.GetXaxis().SetTitle("#eta (#gamma)")  
  crt.GetYaxis().SetTitle("pass/fail")
  crt.SetTitle(" ")
  crt.Draw("E1")
  srt.Draw("E1 SAME")
  c1.RedrawAxis()
  legend = ROOT.TLegend(0.7,0.74,0.9,0.9)
  if outName.count('DYSB') or outName.count('failOrSide'):
    legend.AddEntry(crt,"Measurement Region: on-Z","E")
    legend.AddEntry(srt,"Application region: off-Z","E")
  else:
    legend.AddEntry(crt,"sigma sideband","E")
    legend.AddEntry(srt,"sigma pass","E")
  # legend->SetMargin(0.4);
  # legend->SetHeader("process","C");
  legend.Draw()
  c1.SaveAs(outName)


# CR = 'llg-mll40-onZ-llgNoZ-deepbtag0-photonPt20'
# ['llg-mll40-onZ-llgNoZ-njet1p-photonPt20-','llg-mll40-offZ-llgNoZ-njet1p-photonPt20-']
CR = 'llg-mll40-onZ-llgNoZ-njet1p-photonPt20'
SR = 'llg-mll40-offZ-llgNoZ-njet1p-photonPt20'

# CR = 'llg-mll40-onZ-llgNoZ-deepbtag0-photonPt20'
# SR = 'llg-mll40-offZ-llgNoZ-njet2p-deepbtag1p-photonPt20'
ranges = [ 
  '-phMVANEG0.6to0.20',
  '-phMVANEG0.4to0.20',
  # '-phMVANEG0.3to0.20',
  # '-phMVANEG0.2to0.20',
  # '-phMVANEG0.1to0.20',
  '-phMVANEG0.6to0.10',
  '-phMVANEG0.4to0.10',
  # '-phMVANEG0.3to0.10',
  # '-phMVANEG0.3to0.10',
  # '-phMVANEG0.2to0.10',
]

for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions', 'njets']:  
# for plot in ['phLepDeltaR']:  
  for photype in ['Fake','Had','NP']:
    for ran in ranges:
#       try: phoMvaClosure(basePath + 'phomvasb-onlyDY' + photype + '/noData/'+ CR +'-phMVA0.20/' + plot + '.pkl',
#                     basePath + 'phomvasb-onlyDY' + photype + '/noData/'+ CR + ran + '/' + plot + '.pkl',
#                     basePath + 'phomvasb-onlyTT' + photype + '/noData/'+ SR +'-phMVA0.20/' + plot + '.pkl',                
#                     basePath + 'phomvasb-onlyTT' + photype + '/noData/'+ SR + ran + '/' + plot + '.pkl',
#                     'TTDYplotsMVA/' + ran +  plot + photype + '.pdf',
#                     plot
#                     )
#       except Exception as e:
#         print(e)

# for plot in ['photon_pt_large','photon_eta_large','yield', 'signalRegions', 'njets']:
#   for photype in ['Fake','Had','NP']:
#     try: phoCBClosure(basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-failChgIso-passSigmaIetaIeta-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-failChgIso-passSigmaIetaIeta-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                   'TTDYplotsCB/CB' + photype +  plot + 'DYSBChIso.pdf',
#                   plot
#                   )
#     except Exception as e:
#       print(e)
#     try: phoCBClosure(basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                       basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
#                   'TTDYplotsCB/CB' + photype +  plot + 'DYSBsigma.pdf',
#                   plot
#                   )
#     except Exception as e:
#       print(e)
      try: phoCBClosure(basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-failOrSide-onlyDY' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-failOrSide-onlyTT' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                    'TTDYplotsCB/CB' + photype +  plot + 'failOrSide.pdf',
                    plot
                    )
      except Exception as e:
        print(e)
      try: phoCBClosure(basePath + 'phoCB-passChgIso-passSigmaIetaIeta-ALL' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-failOrSide-ALL' + photype + '/noData/llg-mll40-onZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-passChgIso-passSigmaIetaIeta-ALL' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                        basePath + 'phoCB-failOrSide-ALL' + photype + '/noData/llg-mll40-offZ-llgNoZ-njet1p-photonPt20/'+ plot + '.pkl',
                    'plotsCB/CB' + photype +  plot + 'ALLfailOrSide.pdf',
                    plot
                    )
      except Exception as e:
        print(e)