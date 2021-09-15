import pickle
import ROOT
import pdb


def sumHists(sourceHists, plot):
  nHist = None
  gHist = None
  dHist = None
  for file in sourceHists:
    hists = pickle.load(open(file))[plot]
    # pdb.set_trace()
    for name, hist in hists.iteritems():
      if 'nonprompt' in name:
        if not nHist: nHist = hist.Clone()
        else: nHist.Add(hist)
      elif 'genuine' in name:
        if not gHist: gHist = hist.Clone()
        else: gHist.Add(hist)
      elif 'data' in name:
        if not dHist: dHist = hist.Clone()
        else: dHist.Add(hist)
      else:
        print 'warning ' + name
  return (nHist, gHist, dHist)

vars = {}
base = '/storage_mnt/storage/user/gmestdac/public_html/ttG/2016/phoCB-failChgIso-passSigmaIetaIeta-forNPest/all/llg-mll20-llgNoZ-photonPt20-chIso0to15-signalRegionEstA-offZ/photon_pt.pkl'
vars['base'] = base
vars['p1u'] = base.replace('-passSigmaIetaIeta','').replace('-offZ','-offZ-phSigma0to0.01040')
vars['p1d'] = base.replace('-passSigmaIetaIeta','').replace('-offZ','-offZ-phSigma0to0.00990')
for key in vars.keys():
  vars[key] = [vars[key].replace('2016', y) for y in ['2016', '2017', '2018']]

for key in vars.keys():
  np, genu, data = sumHists(vars[key], 'photon_pt')
  np = np.Integral()
  genu = genu.Integral()
  data = data.Integral()


  print genu/(np+genu)
  print genu/data
  print('-----------------------')