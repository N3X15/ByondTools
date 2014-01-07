'''
Created on Jan 5, 2014

@author: Rob
'''
import os, sys
from com.byond.basetypes import Atom, Proc
from com.byond import objtree
if __name__ == '__main__':
    if os.path.isfile(sys.argv[1]):
        selectedDMEs = []
        tree = objtree.ObjectTree(preprocessor_directives=True)
        tree.ProcessFilesFromDME(sys.argv[1])
        
        atomsWritten = []
        with open(sys.argv[2] + '.fixed', 'w') as f:
            """
            for ak in sorted(tree.Atoms.keys()):
                atom = tree.Atoms[ak]
                for a in atomsWritten:
                    if atom.path.startswith(a): continue
                if atom.filename.replace(os.sep,'/') == sys.argv[2]:
                    f.write(atom.DumpCode())
                    atomsWritten+=[atom.path]
            """
            for thing in tree.fileLayouts[sys.argv[2].replace('/', os.sep)]:
                ttype = thing[0]
                if ttype == 'ATOMDEF':
                    f.write(thing[1] + '\n')
                elif ttype == 'PROCDEF':
                    proc = tree.GetAtom(thing[1])
                    f.write(proc.DumpCode() + '\n')
                elif ttype == 'VAR':
                    atom = tree.GetAtom(thing[1])
                    var = atom.properties[thing[2]]
                    f.write('\t{}\n'.format(var.DumpCode(thing[2])))
                else: print('wot is ' + ttype + '?')
