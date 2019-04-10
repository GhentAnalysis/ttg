from ttg.tools.logger import getLogger
from ttg.plots.plot   import getHistFromPkl
log = getLogger()

def replaceShape(hist, shape):
  normalization = hist.Integral("width")/shape.Integral("width")
  hist = shape.Clone()
  hist.Scale(normalization)
  return hist

def replaceShapeForFakes(plot):
  for sample, hist in plot.histos.iteritems():
    name = sample if isinstance(sample, str) else (sample.name + sample.texName)
    if 'hadronic fakes' in name:
      selection     = 'llg-looseLeptonVeto-mll40-offZ-llgNoZ-signalRegion-photonPt20'
      sideBandShape = getHistFromPkl(('eleCBTight-phoCB-sidebandSigmaIetaIeta', 'all', selection), plot.name, '', ['MuonEG'], ['DoubleEG'], ['DoubleMuon'])
      plot.histos[sample] = replaceShape(hist, sideBandShape)
      log.info('Replaced the fakes for ' + name + ' by data from the sigmeIetaIeta sideband')
  return {'hadronic fakes' : 'hadronic fakes from #sigma_{i#eta i#eta} sideband'}
