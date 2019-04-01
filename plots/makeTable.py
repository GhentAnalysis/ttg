#! /usr/bin/env python
import argparse, json
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE'], help="Log level for logging")
args = argParser.parse_args()

from ttg.tools.logger       import getLogger
log = getLogger(args.logLevel)

def getImpact(param):
  with open('./combine/srFit_impacts.json') as f:
    impacts = json.load(f)
    for p in impacts['POIs']:
      if p['name'] == 'r': r = p['fit'][1]
    for p in impacts['params']:
      if p['name'] == param:
        return '%.2f \\%%' % (p['impact_r']/r*100)
    log.error('Param ' + param + 'not found')
    return ''

def insertImpact(line):
  if 'IMPACT' in line:
    for i in line.split():
      if 'IMPACT' in i:
        param = i.split(':')[-1]
        return line.replace(i, getImpact(param))
  else:
    return line

with open('sysTable.tex', 'w') as out:
  with open('./data/sysTableTemplate.tex') as template:
    for line in template:
      out.write(insertImpact(line))
