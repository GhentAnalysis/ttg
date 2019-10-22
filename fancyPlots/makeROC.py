#!/usr/bin/env python

#
# Argument parser and logging
#
import os, argparse, sys
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',         nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--tag',            action='store',      default='rocCurve2016', help='Tag to take the flatLeptonTrees from')
argParser.add_argument('--flavor',         action='store',      default=None,           help='Select electrons, muons or both', choices=[None, 'e', 'mu'])
argParser.add_argument('--ptMin',          action='store',      default=None,           help='Select minimum lepton pt')
argParser.add_argument('--ptMax',          action='store',      default=None,           help='Select maximum lepton pt')
argParser.add_argument('--editInfo',       action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,          help='do not launch subjobs')
args = argParser.parse_args()


from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)


#
# Check git and edit the info file
#
from ttg.tools.helpers import editInfo, plotDir, updateGitInfo
plotDir = plotDir.replace('ttG', 'mvaRoc')
if args.editInfo:
  try:    os.makedirs(os.path.join(plotDir, args.tag))
  except: pass
  editInfo(os.path.join(plotDir, args.tag))

#
# Directory name
#
def getPlotDir(baseName, flavor=None, ptMin=None, ptMax=None):
  flavorString = ('_' + flavor) if flavor else ''
  if ptMin and ptMax: ptString = '_pt%sto%s' % (ptMin, ptMax)
  elif ptMax:         ptString = '_pt0to%s' % ptMax
  elif ptMin:         ptString = '_pt%s' % ptMin
  else:               ptString = ''
  return baseName + flavorString + ptString


#
# Submit subjobs
#
if not args.isChild:
  updateGitInfo()

  jobs = []
  for ptRange in [(None, None), (0, 10), (10, 20), (20, 30), (30, 50), (50, None), (0, 25), (25, None)]:
    for flavor in [None, 'e', 'mu']:
      jobs.append((args.tag, flavor, ptRange[0], ptRange[1]))

  from ttg.tools.jobSubmitter import submitJobs
  # Setup the virtual environment before running the job
  # since 21/10/2019, this script needs to be run with ipython instead of python for unknown reasons
  submitJobs('source setupVirtEnv.sh; ipython -- ' + __file__, ('tag', 'flavor', 'ptMin', 'ptMax'), jobs, argParser, jobLabel = "ROC", wallTime="5")
  sys.exit(0)





import glob, ROOT, os
from ttg.tools.progressBar import progressbar

def makeRocCurves(baseName, directory, flavor=None, ptMin=None, ptMax=None):
  plotDir = getPlotDir(baseName, flavor=flavor, ptMin=ptMin, ptMax=ptMax)
  topDir  = '/user/tomc/public_html/mvaRoc/'
  try:    os.makedirs(os.path.join(topDir, plotDir))
  except: pass
  print('Making roc curves for %s (%s)' % (baseName, plotDir))

  title = 'ROC curve (2016) for %s' % ('electrons' if flavor=='e' else ('muons' if flavor=='mu' else 'electrons and muons'))
  if ptMin or ptMax:
    if ptMax: title += ' (%s < $p_{T}$ < %s GeV)' % (ptMin if ptMin else 0, ptMax)
    else:     title += ' (%s < $p_{T}$)' % (ptMin if ptMin else 0)
    if ptMin: ptMin = int(ptMin)
    if ptMax: ptMax = int(ptMax)


  def analyzeTree(sample, mvas):
    prompt = ('tZq' in sample or 'ttZ' in sample)
    tree = ROOT.TChain('flatLeptonTree')
    files = []
    for i in glob.glob(os.path.join(directory, sample, '*.root')):
      tree.Add(i)
      files.append(i)
    assert len(files)

    hists = {}
    for mva in mvas:
      hists[mva] = ROOT.TH1F(sample+mva, sample+mva, 100000, -1., 1.)
    for i in progressbar(xrange(tree.GetEntries()), sample, 100):
      tree.GetEntry(i)
      if prompt!=tree.isPrompt: continue
      if flavor=='e'  and tree.flavor!=0: continue
      if flavor=='mu' and tree.flavor!=1: continue
      if ptMin and tree.pt<ptMin: continue
      if ptMax and tree.pt>ptMax: continue
      for mva in mvas:
        hists[mva].Fill(getattr(tree, mva))
    return hists

  def makeRoc(signalHist, backgroundHist):
    effPoints = []
    totSig = signalHist.Integral()
    totBkg = backgroundHist.Integral()
    for i in range(1, signalHist.GetNbinsX()+1):
        effSig = signalHist.Integral(i, -1)/totSig
        effBkg = backgroundHist.Integral(i, -1)/totBkg
        effPoints.append((signalHist.GetBinLowEdge(i), effSig, effBkg))
    return effPoints

  mvaValues = {}
  for sample in ['tZq', 'TT_Sem']:
    mvaValues[sample] = analyzeTree(sample, ['mvaTTH', 'mvaTZQ'])

  rocTTH = makeRoc(mvaValues['tZq']['mvaTTH'], mvaValues['TT_Sem']['mvaTTH'])
  rocTZQ = makeRoc(mvaValues['tZq']['mvaTZQ'], mvaValues['TT_Sem']['mvaTZQ'])

  def getWorkingPoint(roc, cut):
    for i in roc:
      if i[0] > cut:
        return i[1], i[2]

  #
  # Plotting with plotly
  #
  import plotly.offline
  import plotly.graph_objs as go

  def getXaxis():
    return {
        "title": "background efficiency",
        "titlefont": {"color": "#673ab7"},
        "rangemode": "nonnegative",
        "range": [0., 1.],
        "type": "linear",
        "zeroline": False,
        "showgrid": True,
      }

  def getYaxis():
    return {
        "title": "signal effiency",
        "anchor": "x",
        "rangemode": "nonnegative",
        "range": [0., 1.],
        "linecolor": "#673ab7",
        "side": "left",
        "tickfont": {"color": "#673ab7"},
        "tickmode": "auto",
        "ticks": "",
        "titlefont": {"color": "#673ab7"},
        "type": "linear",
        "showgrid": True,
        "zeroline": False
      }

  def rocToScatter(roc, name, color):
    text   = ['Cut: %s<br>Sig eff.: %s<br>Bkg rej: %s' % i for i in roc]
    sigEff = [i[1] for i in roc]
    bkgEff = [i[2] for i in roc]
    scat = go.Scatter(x=bkgEff, y=sigEff, name=name, yaxis= "y", text=text, line_color=color, marker_color=color)
    scat.update({"hoverinfo": "name+text",
                 "line": {"width": 1., "color": color},
                 "marker": {"size": 8},
                 "mode": "lines",
                 "showlegend": True})
    return scat

  def addWorkingpoints(roc, name, color):
    workingpoints = [-0.4, 0.4, 0.6, 0.8]
    names         = ['ttZ 4L', 'ttZ 3l', 'ttW', 'tZq']
    return go.Scatter(
      x=[getWorkingPoint(roc, wpCut)[1] for wpCut in workingpoints],
      y=[getWorkingPoint(roc, wpCut)[0] for wpCut in workingpoints],
      mode="markers",
      name="Workingpoints " + name,
      marker_color=color,
      text=names,
      textposition="bottom right"
    )

  def getRocPlot():
    layout = {
      "title": title.replace('$p_{T}$', 'p<sub>T</sub>'),
      "dragmode": "zoom",
      "hovermode": "x",
      "hoverlabel": {"font": {"size" : 7}, "namelength" : -1},
      "legend": {"traceorder": "normal", "font": {"size" : 8}, "tracegroupgap" : 5},
      "margin": {"t": 100, "b": 100},
      "xaxis": getXaxis(),
      "yaxis": getYaxis(),
    }
    mvas  = [(rocTZQ, 'ghent lepton MVA', '#1f77b4'), (rocTTH, 'ttH lepton MVA', '#ff7f0e')]
    data  = [rocToScatter(roc, name, color) for roc, name, color in mvas]
    data += [addWorkingpoints(roc, name, color) for roc, name, color in mvas]
    fig   = go.Figure(data=data, layout=layout)
    div   = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
    div  += plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
    return div

  with open('index.php') as template:
    with open(os.path.join(topDir, plotDir, 'index.php'), 'w') as f:
      for line in template:
        if 'DIV' in line:
          f.write(getRocPlot() + '\n')
        elif 'SHOWIFEXISTS' in line:
          f.write("  showIfExists('../%s', 'both');"      % getPlotDir(baseName, flavor=None, ptMin=ptMin, ptMax=ptMax))
          f.write("  showIfExists('../%s', 'electrons');" % getPlotDir(baseName, flavor='e', ptMin=ptMin, ptMax=ptMax))
          f.write("  showIfExists('../%s', 'muons');"     % getPlotDir(baseName, flavor='mu', ptMin=ptMin, ptMax=ptMax))
          f.write("  showIfExists('roc.pdf', 'pdf (linear)');")
          f.write("  showIfExists('roc_log.pdf', 'pdf (log)');")
          f.write("  showIfExists('roc_IlliaStyle.pdf', 'pdf (Illia style)');")
        else:
          f.write(line)

  #
  # Plotting with matplotlib
  #
  import matplotlib.pyplot as pyplot

  def makePyplot(name, logX=False, logY=False, minX=0, minY=0, annotate=False):
    fig, ax = pyplot.subplots()

    if not minY:
      minY = min([i[1] for roc in [rocTZQ, rocTTH] for i in roc if i[2]>minX])

    ax.set_xlim(minX, 1)
    ax.set_ylim(minY, 1)
    if logX: ax.set_xscale('log')
    if logY: ax.set_yscale('log')

    for label, roc, color in [('ghent lepton MVA', rocTZQ, 'blue'), ('ttH lepton MVA', rocTTH, 'red')]:
      sigEff = [i[1] for i in roc]
      bkgEff = [i[2] for i in roc]
      ax.plot(bkgEff, sigEff, label=label, color=color)

      for wpName, wp, marker in [('ttZ 4l', -.4, 'o'), ('ttZ 3l', .4, '^'), ('ttW', .6, 's'), ('tZq', .8, 'h')]:
        y, x = getWorkingPoint(roc, wp)
        if x<minX: continue
        ax.scatter([x], [y], c=color, marker=marker, label=(label + ' ' + wpName), linewidth='0')

    legend = ax.legend(loc='lower right', fontsize=8, scatterpoints=1)
    legend.get_frame().set_linewidth(0.0)
    ax.set(xlabel='background efficiency', ylabel='signal efficiency', title=title)
    ax.grid()

    fig.savefig(os.path.join(topDir, plotDir, name + ".pdf"))
    pyplot.close()

  makePyplot('roc')
  makePyplot('roc_log', logX=True, logY=True, minX=0.001, minY=0.001)
  makePyplot('roc_IlliaStyle', logX=True, minX=0.0008, minY=None)
  makePyplot('roc_IlliaStyle2', logX=True, minX=0.008, minY=None)
  makePyplot('roc_IlliaStyle3', logX=True, minX=0.00008, minY=None)
  makePyplot('roc_IlliaStyle4', logX=True, minX=0.000008, minY=None)

makeRocCurves(args.tag, '/user/tomc/public/reducedTuples/dilepton_MC_2016_v5/' + args.tag, flavor=args.flavor, ptMin=args.ptMin, ptMax=args.ptMax)
log.info('Finished')
