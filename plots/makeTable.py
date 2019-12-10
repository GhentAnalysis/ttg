#! /usr/bin/env python

import argparse, json, os, sys, math

argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store', default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
argParser.add_argument('--run', action='store', default='combine', help="custom run name")
argParser.add_argument('--chan', action='store', default='ee', help="dilepton channel name", choices=['ee', 'mumu', 'emu', 'll'])
argParser.add_argument('--template', action='store', default='./data/r_sysTemplate.tex', help="table template name")
argParser.add_argument('--year', action='store', default='2016', help="year")
argParser.add_argument('--card', action='store', default='srFit', help="datacard name")
argParser.add_argument('--asimov', action='store_true', help="use asimov results")
argParser.add_argument('--mode', action='store', default='impacts_r', help="table type")
args = argParser.parse_args()

from ttg.tools.helpers import plotDir, plotCombineDir
from ttg.tools.logger import getLogger
log = getLogger(args.logLevel)

inputDir = args.run + args.chan
outDir = 'tables/'
mode = args.mode
asimov = args.asimov

def getImpact(param):
    
    fname = './' + inputDir + '/' + args.card + '_' + mode
    if asimov: fname += '_asimov'
    fname += '.json'
    if mode == 'impacts_r' or mode == 'impacts_TT_Dil_norm': res = 'impact_r'
    else: 
        print 'mode ' + mode + ' is not known'
        sys.exit()
    
    with open(fname) as f:
        impacts = json.load(f)
        for p in impacts['POIs']:
            if p['name'] == mode.replace('impacts_',''): r = p['fit'][1]
        for p in impacts['params']:
            if p['name'] == param:
                return '%.2f \\%%' % (p[res]/r*100)
        if param == 'MCSTAT':
            mcimp = 0
            for pp in impacts['params']:
                if 'bin' in pp['name']:
                    mcimp += (pp[res]*pp[res])
            mcimp = math.sqrt(mcimp)/r*100
            return '%.2f \\%%' % (mcimp)
        log.error('Param ' + param + 'not found')
        return ''

def insertPreambule(start=True):
    
    if start == True:
        line = '\\documentclass[11pt,titlepage]{article}\n'
        line += '\\usepackage{tabularx}\n'
        line += '\\usepackage{graphicx}\n'
        line += '\\begin{document}\n'
    else:
        line = '\\end{document}'
    
    return line
    
def insertImpact(line):
    
    if 'IMPACT' in line:
        for i in line.split():
            if 'IMPACT' in i:
                 param = i.split(':')[-1]
                 return line.replace(i, getImpact(param))
    else:
        return line

def compileTable(name):
    
    os.chdir(os.getcwd() + '/tables/')
    command = 'pdflatex -interaction=batchmode -halt-on-error ' + name
    os.system(command)
    command = 'convert ' + name.replace('.tex','.pdf') + ' ' + name.replace('.tex','.png')
    os.system(command)
    os.chdir(os.getcwd() + '/../')
    
os.system('mkdir -p ' + outDir)

fname = 'tab_' + args.card + '_' + mode
if asimov: fname += '_asimov'
fname += '.tex'

with open(outDir + fname, 'w') as out:
    
    out.write(insertPreambule(True))
    
    with open(args.template) as template:
        for line in template:
            out.write(insertImpact(line))
            
    out.write(insertPreambule(False))
    
compileTable(fname)
os.system('cp tables/*.{pdf,png} ' + os.path.join(plotCombineDir, args.year, inputDir))
