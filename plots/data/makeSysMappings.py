#! /usr/bin/env python

with open('sysMappingsTemplate.json', 'r') as template:
  with open('sysMappings.json', 'w') as mapping:
    for line in template:
      if line.count('STATERRORS'):
##        for photonTypeShort, photonType in [('h', 'hadronic photon'), ('g', 'genuine photon'), ('f', 'hadronic fake')]:
##          for i in range(1, 8):
##            mapping.write('  "chgIsoall_' + photonTypeShort + 'Stat' + str(i) + '" : "Stats ' + photonType + ' bin ' + str(i) + '",\n')
        for sample, sampleTex in [('TTGamma', 't#bar{t}#gamma'), ('TT_Dil', 't#bar{t}'), ('ZG', 'Z#gamma'), ('DY', 'Drell-Yan'), ('other', 'Other')]:
          for signs in ['emu', 'ee', 'mumu']:
            for i, mult in [('3', '2j,0b'), ('4', '#geq3j,0b'), ('5', '1j,1b'), ('6', '2j1b'), ('7', '#geq3j,1b'), ('8', '2j2b'), ('9', '#geq3j,2b')]:
              mapping.write('  "sr_' + signs + sample + 'Stat' + i + '" : "Stats ' + sampleTex + ' ' + mult + ' (' + signs + ')",\n')
##              mapping.write('  "zg_' + signs + sample + 'Stat' + i + '" : "Stats ' + sampleTex + ' ' + mult + ' (Z#gamma ' + signs + ')",\n')
        for i, mult in [('2', '2j,0b'), ('3', '#geq3j,0b'), ('4', '1j,1b'), ('5', '2j1b'), ('6', '#geq3j,1b'), ('7', '2j2b'), ('8', '#geq3j,2b')]:   # AutoMCStats, bin numbering starts at 0!
          mapping.write('  "prop_binsr_emu_bin' + i + '" : "Stats ' + mult + ' (emu SR)",\n')
          mapping.write('  "prop_binsr_ee_bin' + i + '" : "Stats ' + mult + ' (ee SR)",\n')
          mapping.write('  "prop_binsr_mumu_bin' + i + '" : "Stats ' + mult + ' (mumu SR)",\n')
##        for i in range(7):
##          mapping.write('  "prop_binchgIso_bin' + str(i) + '" : "Stats bin ' + str(i) + '",\n')
##        for i in range(4):
##          mapping.write('  "prop_binsigEtaEta_bin' + str(i+6) + '" : "#sigma_{i#etai#eta} stats bin ' + str(i) + '",\n')
      else:
        mapping.write(line)
