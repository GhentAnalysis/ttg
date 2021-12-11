import pdb
from os.path import exists
from shutil import copyfile

f = open("output/submission.yaml" , 'r')
lines = f.readlines()
f.close()

naming = {
'$p_{T}(\\gamma)$'.lower() : 'phPt',
'$\\Delta_R(\\gamma,_l)$'.lower() : 'phLepDeltaR',
'$\\Delta_\\phi(ll)$'.lower() : 'll_deltaPhi',
'$\\Delta_R(l,_j)$'.lower() : 'jetLepDeltaR',
'$p_{T}(j1)$'.lower() : 'jetPt',
'$|\\Delta\\eta(ll)|$'.lower() : 'll_absDeltaEta',
'$\\Delta_R(\\gamma,_b)$'.lower() : 'phBJetDeltaR',
'$|\\eta_|(\\gamma)$'.lower() : 'phAbsEta',
'$\\Delta_R(\\gamma,_l1)$'.lower() : 'phLep1DeltaR',
'$\\Delta_R(\\gamma,_l2)$'.lower() : 'phLep2DeltaR',
'$p_{T}(ll)$'.lower() : 'Z_pt',
'$p_{T}(l1)+p_{T}(l2)$'.lower() : 'l1l2_ptsum'
}


outLines = []


for i, line in enumerate(lines):
  if line.count('data_file:'):
    name = line.replace('data_file: ', '').replace('.yaml\n', '')
    if name.count('correlation') or name.count('covariance'):
      name = naming[name.split('_for_')[1].split('_(')[0]] + ('correl' if name.count('correlation') else '')  + name[:4]  + 'Cov' + ('_norm' if name.count('(normalized)') else '')
    if exists('addPlots/' + name + '.png') and exists('addPlots/thumb_' + name + '.png'):
      outLines.append('additional_resources:\n')
      outLines.append('- description: Image file\n')
      outLines.append('  location: ' + name + '.png\n')
      outLines.append('- description: Thumbnail image file\n')
      outLines.append('  location: thumb_' + name + '.png\n')
      copyfile('addPlots/' + name + '.png', 'output/' + name + '.png')
      copyfile('addPlots/thumb_' + name + '.png',    'output/thumb_' + name + '.png')
    outLines.append(line)
  else:
    outLines.append(line)



f = open("output/submission.yaml" , 'w')
f.writelines(outLines)