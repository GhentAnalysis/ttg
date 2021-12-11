import pickle
import pdb

dil2dFile = pickle.load(open('ctZ_ctZI_obs.pkl','r'))
com2dFile = pickle.load(open('ctZ_ctZI_obsComb.pkl','r'))

# ['coup2', 'coup1', 'nll']

dil2dDict = {}
for i in range(len(dil2dFile['coup1'])):
  dil2dDict[(round(dil2dFile['coup1'][i], 3), round(dil2dFile['coup2'][i], 3))] = round(dil2dFile['nll'][i], 3)

dilc1 =  list(set(dil2dFile['coup1']))
dilc1.sort()

dilc1 = dilc1[1::3]
dilc1 = [round(i, 3) for i in dilc1]

dilc2 =  list(set(dil2dFile['coup1']))
dilc2.sort()

dilc2 = dilc2[1::3]
dilc2 = [round(i, 3) for i in dilc2]


dil2DOut = open('dil2d.txt', 'w')

for a in dilc1:
  for b in dilc2:
    dil2DOut.write(str(a) + '\t' + str(b) + '\t' + str(dil2dDict[(a,b)]) + '\n')

dil2DOut.close()



com2dDict = {}
for i in range(len(com2dFile['coup1'])):
  com2dDict[(round(com2dFile['coup1'][i], 3), round(com2dFile['coup2'][i], 3))] = round(com2dFile['nll'][i], 3)

comc1 =  list(set(com2dFile['coup1']))
comc1.sort()

comc1 = comc1[1::3]
comc1 = [round(i, 3) for i in comc1]

comc2 =  list(set(com2dFile['coup1']))
comc2.sort()

comc2 = comc2[1::3]
comc2 = [round(i, 3) for i in comc2]


com2DOut = open('com2d.txt', 'w')

for a in comc1:
  for b in comc2:
    com2DOut.write(str(a) + '\t' + str(b) + '\t' + str(com2dDict[(a,b)]) + '\n')

com2DOut.close()


dilctZexpFile = pickle.load(open('ctZ.pkl','r'))
dilctZobsFile = pickle.load(open('ctZ_obs.pkl','r'))
dilctZIexpFile = pickle.load(open('ctZI.pkl','r'))
dilctZIobsFile = pickle.load(open('ctZI_obs.pkl','r'))

comctZexpFile = pickle.load(open('ctZComb.pkl','r'))
comctZobsFile = pickle.load(open('ctZ_obsComb.pkl','r'))
comctZIexpFile = pickle.load(open('ctZIComb.pkl','r'))
comctZIobsFile = pickle.load(open('ctZI_obsComb.pkl','r'))

plots = [
('dilctZexp', dilctZexpFile, (-0.61, 0.61)),
('dilctZobs', dilctZobsFile, (-0.61, 0.61)),
('dilctZIexp', dilctZIexpFile, (-0.61, 0.61)),
('dilctZIobs', dilctZIobsFile, (-0.61, 0.61)),
('comctZexp', comctZexpFile, (-0.41, 0.41)),
('comctZobs', comctZobsFile, (-0.41, 0.41)),
('comctZIexp', comctZIexpFile, (-0.41, 0.41)),
('comctZIobs', comctZIobsFile, (-0.41, 0.41))
]

for plot in plots:
  out1d = open(plot[0] + '.txt', 'w')
  for i in range(len(plot[1]['coup'])):
    if plot[2][0] < plot[1]['coup'][i] < plot[2][1]:
      out1d.write(str(round(plot[1]['coup'][i], 3)) + '\t' + str(round(plot[1]['nll'][i], 3)) + '\n')
  out1d.close()