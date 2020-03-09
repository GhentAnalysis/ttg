#! /usr/bin/env python

with open('sysMappingsTemplate.json', 'r') as template:
  with open('sysMappings.json', 'w') as mapping:
    for line in template:
      if line.count('STATERRORS'):
        for sample, sampleTex in [('TTGamma', 't#bar{t}#gamma'), ('TT_Dil', 't#bar{t}'), ('ZG', 'Z#gamma'), ('DY', 'Drell-Yan'), ('VVTo2L2Nu', 'Other'), ('singleTop', 'singleTop')]:
          for signs in ['emu', 'ee', 'mumu']:
            for i, mult in [('3', '2j,0b'), ('4', '#geq3j,0b'), ('5', '1j,1b'), ('6', '2j1b'), ('7', '#geq3j,1b'), ('8', '2j2b'), ('9', '#geq3j,2b'), ('10', '#geq3j,#geq3b')]:
              mapping.write('  "sr_' + signs + sample + 'Stat' + i + '" : "Stats ' + sampleTex + ' ' + mult + ' (' + signs + ')",\n')
            for signs in ['ee', 'mumu']:
              mapping.write('  "zg_' + signs + sample + 'Stat' + i + '" : "Stats ' + sampleTex + ' ' + mult + ' (Z#gammaCR ' + signs + ')",\n')
        for i, mult in [('2', '2j,0b'), ('3', '#geq3j,0b'), ('4', '1j,1b'), ('5', '2j1b'), ('6', '#geq3j,1b'), ('7', '2j2b'), ('8', '#geq3j,2b'), ('9', '#geq3j,#geq3b')]:   # AutoMCStats, bin numbering starts at 0!
          mapping.write('  "prop_binsr_emu_bin' + i + '" : "Stats ' + mult + ' (emu SR)",\n')
          mapping.write('  "prop_binsr_ee_bin' + i + '" : "Stats ' + mult + ' (ee SR)",\n')
          mapping.write('  "prop_binsr_mumu_bin' + i + '" : "Stats ' + mult + ' (mumu SR)",\n')
          mapping.write('  "prop_binzg_ee_bin' + i + '" : "Stats ' + mult + ' (ee Zg CR)",\n')
          mapping.write('  "prop_binzg_mumu_bin' + i + '" : "Stats ' + mult + ' (mumu Zg CR)",\n')
        for year in ["2016", "2017", "2018"]:
          for i, mult in [('2', '2j,0b'), ('3', '#geq3j,0b'), ('4', '1j,1b'), ('5', '2j1b'), ('6', '#geq3j,1b'), ('7', '2j2b'), ('8', '#geq3j,2b'), ('9', '#geq3j,#geq3b')]:   # AutoMCStats, bin numbering starts at 0!
            mapping.write('  "prop_biny' + year + '_sr_emu_bin' + i + '" : "Stats ' + mult + ' (emu SR) ' + year + '",\n')
            mapping.write('  "prop_biny' + year + '_sr_ee_bin' + i + '" : "Stats ' + mult + ' (ee SR) ' + year + '",\n')
            mapping.write('  "prop_biny' + year + '_sr_mumu_bin' + i + '" : "Stats ' + mult + ' (mumu SR) ' + year + '",\n')
            mapping.write('  "prop_biny' + year + '_zg_ee_bin' + i + '" : "Stats ' + mult + ' (ee Zg CR) ' + year + '",\n')
            mapping.write('  "prop_biny' + year + '_zg_mumu_bin' + i + '" : "Stats ' + mult + ' (mumu Zg CR) ' + year + '",\n')
      else:
        mapping.write(line)