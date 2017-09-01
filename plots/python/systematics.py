#
# Defining shape systematics as "name : ([var, sysVar], [var2, sysVar2],...)"
#
systematics = {}
for i in ('Up', 'Down'):
  systematics['pu'+i]       = [('puWeight',      'puWeight'+i)]
  systematics['phSF'+i]     = [('phWeight',      'phWeight'+i)]
  systematics['lSF'+i]      = [('lWeight',       'lWeight'+i)]
  systematics['trigger'+i]  = [('triggerWeight', 'triggerWeight'+i)]
  systematics['bTagl'+i]    = [('bTagWeight',    'bTagWeightl'+i)]
  systematics['bTagb'+i]    = [('bTagWeight',    'bTagWeightb'+i)]
  systematics['JEC'+i]      = [('njets',         'njets_JEC'+i),     ('dbjets',    'dbjets_JEC'+i)]
  systematics['JER'+i]      = [('njets',         'njets_JER'+i),     ('dbjets',    'dbjets_JER'+i)]


#
# Defining linear systematics as "name : (sampleList, %)"
#
linearSystematics = {}
linearSystematics['lumi'] = (None, 2.5)
#linearSystematics['TTGamma'] = (['TTGamma'], 2.5)]


#
# Function to apply the systematic to the cutstring or tree
#
def applySysToString(string):
  for i in systematics[args.sys]:
    var, sysVar = i
    string = string.replace(var, sysVar)

def applySysToTree(tree):
  for i in systematics[args.sys]:
    var, sysVar = i
    setattr(tree, var, getattr(tree, sysVar))
