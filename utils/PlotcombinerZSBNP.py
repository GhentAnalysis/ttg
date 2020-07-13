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
# CL ALL 
# clfullcb chiso Z
    try: phoClosure(basePath +   'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSBChiso_njet1p_nar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clallcb sigma Z
    try: phoClosure(basePath +   'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSBSigma_njet1p_nar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clallcb OR Z
    try: phoClosure(basePath +   'phoCBfull-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNP/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNPM/noData/llg-njet1p-onZnar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSboth_njet1p_nar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)



# CL ALL 
    try: phoClosure(basePath +   'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-passChgIso-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passSigmaIetaIeta-failChgIso-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSBChiso_njet1p_Vnar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clallcb sigma Z
    try: phoClosure(basePath +   'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-passSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-passChgIso-sidebandSigmaIetaIeta-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSBSigma_njet1p_Vnar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)

# clallcb OR Z
    try: phoClosure(basePath +   'phoCBfull-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNP/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNP/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNPM/noData/llg-njet1p-onZverynar-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCBfull-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      basePath + 'phoCB-failOrSide-onlyTTDYNPM/noData/llg-njet1p-offZ-llgNoZ-photonPt20/'+ plot + '.pkl',
                      'ZSBplots/' + plot + '_ZSboth_njet1p_Vnar_NP.pdf',
                  plot
                  )
    except Exception as e:
      print(e)
