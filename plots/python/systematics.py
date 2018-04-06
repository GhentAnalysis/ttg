#
# Defining shape systematics as "name : ([var, sysVar], [var2, sysVar2],...)"
#
systematics = {}
for i in ('Up', 'Down'):
  systematics['isr'+i]      = []
  systematics['fsr'+i]      = []
  systematics['eScale'+i]   = []
  systematics['eRes'+i]     = []
  systematics['phScale'+i]  = []
  systematics['phRes'+i]    = []
  systematics['pu'+i]       = [('puWeight',      'puWeight'+i)]
  systematics['phSF'+i]     = [('phWeight',      'phWeight'+i)]
  systematics['lSF'+i]      = [('lWeight',       'lWeight'+i)]
  systematics['trigger'+i]  = [('triggerWeight', 'triggerWeight'+i)]
  systematics['bTagl'+i]    = [('bTagWeight',    'bTagWeightl'+i)]
  systematics['bTagb'+i]    = [('bTagWeight',    'bTagWeightb'+i)]
  systematics['pdf'+i]      = [('genWeight',     'weight_pdf'+i)]
  systematics['q2'+i]       = [('genWeight',     'weight_q2'+i)]
  systematics['JEC'+i]      = [('njets',         'njets_JEC'+i),     ('ndbjets',    'ndbjets_JEC'+i), ('j1', 'j1_JEC'+i), ('j2', 'j2_JEC'+i), ('_jetPt', '_jetPt_JEC'+i)]
  systematics['JER'+i]      = [('njets',         'njets_JER'+i),     ('ndbjets',    'ndbjets_JER'+i), ('j1', 'j1_JER'+i), ('j2', 'j2_JER'+i), ('_jetPt', '_jetPt_JER'+i)]


#
# Defining linear systematics as "name : (sampleList, %)"
#
linearSystematics = {}
linearSystematics['lumi'] = (None, 2.5)
#linearSystematics['TTGamma'] = (['TTGamma'], 2.5)]


#
# Function to apply the systematic to the cutstring or tree
#
def applySysToString(sys, string):
  for i in systematics[sys]:
    var, sysVar = i
    string = string.replace(var, sysVar)
  return string

def applySysToTree(sys, tree):
  for i in systematics[sys]:
    var, sysVar = i
    setattr(tree, var, getattr(tree, sysVar))
