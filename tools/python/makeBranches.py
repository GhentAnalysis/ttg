#
# Create new branches (as ['var1/F','var2/I',...]) on the given tree
# Returns struct with the new variables
#
import ROOT

cType = {
    'b': 'UChar_t',
    'S': 'Short_t',
    's': 'UShort_t',
    'I': 'Int_t',
    'i': 'UInt_t',
    'F': 'Float_t',
    'D': 'Double_t',
    'L': 'Long64_t',
    'l': 'ULong64_t',
    'O': 'Bool_t',
}

def makeBranches(tree, branches):
  branches = [tuple(branch.split('/')) for branch in branches]
  ROOT.gROOT.ProcessLine('struct newVars {' + ';'.join([cType[type] + ' ' + name for name, type in branches]) + ';};')
  from ROOT import newVars
  newVars = newVars()

  for name, type in branches:
    tree.Branch(name, ROOT.AddressOf(newVars, name), name+ '/' + type)
    from ctypes import py_object
  return newVars
