#!/usr/bin/env python

import os, sys, glob, json
from optparse import OptionParser

def getOpLabel(name):

    if name == 'ctZ': lab = '$C_{tZ}$'
    elif name == 'ctZI': lab = '$C_{tZ}^{[Im]}$'
    else:
        print 'Unknown operator'
        sys.exit()
    
    return lab

def getInterval(data):
    
    return '['+str(round(data[0], 2))+', '+str(round(data[1], 2))+']' if len(data) == 2 else '['+str(round(data[0], 2))+', '+str(round(data[1], 2))+'], '+'['+str(round(data[2], 2))+', '+str(round(data[3], 2))+']'

def main(argv = None):
    
    if argv == None:
        argv = sys.argv[1:]
                                
    usage = "usage: %prog [options]\n Create tables"
    
    parser = OptionParser(usage)
    
    parser.add_option("--input", type=str, default='pics', help="Input directory name [default: %default]")
    parser.add_option("--op", type=str, default='ctZ,ctZI', help="List of WCs [default: %default]")
    parser.add_option("--year", type=str, default='2016', help="Year of the data taking (2016, 2017, 2018, Run2) [default: %default]")
    parser.add_option("--type", type=str, default='photon_pt', help="Type of input distributions (inclusive, photon_pt, etc.) [default: %default]")
    
    (options, args) = parser.parse_args(sys.argv[1:])

    return options

if __name__ == '__main__':
                                                            
    options = main()
    
    wdir = options.input+'/'+options.type+'/'+options.year

    t = '\\begin{table}[t!]\n'
    t += '\\centering\n'
    t += '\\caption{Summary of the one-dimensional intervals for Wilson coefficients obtained in '+options.year.replace('Run2', 'Run 2')+' data.}\n'
    t += '\\begin{tabular}{l|l|l|l}\n'
    t += '\\hline\n'
    t += 'Wilson coefficients & Measurement & 68\\% CL interval & 95\% CL interval \\\\ \n'
    t += '\\hline\n'
    t += '\\hline\n'
    
    wc = options.op.split(',')
    
    rsingle, rprofiled = {}, {}
    
    for w in wc:
        
        if os.path.isfile(wdir+'/'+w+'_obs.json'): single = wdir+'/'+w+'_obs.json'
        else: single = wdir+'/'+w+'.json'

        if os.path.isfile(wdir+'/'+w+'_prof_obs.json'): profiled = wdir+'/'+w+'_prof_obs.json'
        else: profiled = wdir+'/'+w+'_prof.json'

        with open(single, "r") as read_file:
            rsingle[w] = json.load(read_file)

        with open(profiled, "r") as read_file:
            rprofiled[w] = json.load(read_file)
            
    wc0_i68_exp = getInterval(rsingle[wc[0]]['expected']['68'])
    wc0_i95_exp = getInterval(rsingle[wc[0]]['expected']['95'])

    wc0_i68_prof_exp = getInterval(rprofiled[wc[0]]['expected']['68'])
    wc0_i95_prof_exp = getInterval(rprofiled[wc[0]]['expected']['95'])
    
    wc1_i68_exp = getInterval(rsingle[wc[1]]['expected']['68'])
    wc1_i95_exp = getInterval(rsingle[wc[1]]['expected']['95'])

    wc1_i68_prof_exp = getInterval(rprofiled[wc[1]]['expected']['68'])
    wc1_i95_prof_exp = getInterval(rprofiled[wc[1]]['expected']['95'])
    
    if len(rsingle[wc[0]]) > 1:
        
        wc0_i68_obs = getInterval(rsingle[wc[0]]['observed']['68'])
        wc0_i95_obs = getInterval(rsingle[wc[0]]['observed']['95'])

        wc0_i68_prof_obs = getInterval(rprofiled[wc[0]]['observed']['68'])
        wc0_i95_prof_obs = getInterval(rprofiled[wc[0]]['observed']['95'])
        
        wc1_i68_obs = getInterval(rsingle[wc[1]]['observed']['68'])
        wc1_i95_obs = getInterval(rsingle[wc[1]]['observed']['95'])

        wc1_i68_prof_obs = getInterval(rprofiled[wc[1]]['observed']['68'])
        wc1_i95_prof_obs = getInterval(rprofiled[wc[1]]['observed']['95'])
        
    t += '('+getOpLabel(wc[0])+', '+getOpLabel(wc[1])+' = 0) & Expected & '+wc0_i68_exp+' & '+wc0_i95_exp+' \\\\ \n'
    if len(rsingle[wc[0]]) > 1: t += '('+getOpLabel(wc[0])+', '+getOpLabel(wc[1])+' = 0) & Observed & '+wc0_i68_obs+' & '+wc0_i95_obs+' \\\\ \n'
    t += '('+getOpLabel(wc[1])+', '+getOpLabel(wc[0])+' = 0) & Expected & '+wc1_i68_exp+' & '+wc1_i95_exp+' \\\\ \n'
    if len(rsingle[wc[0]]) > 1: t += '('+getOpLabel(wc[1])+', '+getOpLabel(wc[0])+' = 0) & Observed & '+wc1_i68_obs+' & '+wc1_i95_obs+' \\\\ \n'
    
    t += '\\hline\n'

    t += '('+getOpLabel(wc[0])+', '+getOpLabel(wc[1])+' = profiled) & Expected & '+wc0_i68_prof_exp+' & '+wc0_i95_prof_exp+' \\\\ \n'
    if len(rsingle[wc[0]]) > 1: t += '('+getOpLabel(wc[0])+', '+getOpLabel(wc[1])+' = profiled) & Observed & '+wc0_i68_prof_obs+' & '+wc0_i95_prof_obs+' \\\\ \n'
    t += '('+getOpLabel(wc[1])+', '+getOpLabel(wc[0])+' = profiled) & Expected & '+wc1_i68_prof_exp+' & '+wc1_i95_prof_exp+' \\\\ \n'
    if len(rsingle[wc[0]]) > 1: t += '('+getOpLabel(wc[1])+', '+getOpLabel(wc[0])+' = profiled) & Observed & '+wc1_i68_prof_obs+' & '+wc1_i95_prof_obs+' \\\\ \n'
    
    t += '\\hline\n'
    t += '\\hline\n'
    t += '\\end{tabular}\n'
    t += '\\label{tab:eft'+options.year+'}\n'
    t += '\\end{table}\n'

    print wdir+'/table.tex'
    with open(wdir+'/table.tex', 'w') as fout:
        fout.write(t)
        fout.close()
