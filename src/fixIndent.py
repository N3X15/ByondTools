'''
Created on Jan 5, 2014

@author: Rob
'''
import os, sys
from com.byond.basetypes import Atom, Proc
from com.byond import objtree, GetFilesFromDME

def processFile(tree, origin, destination):
    with open(destination, 'w') as f:
        """
        for ak in sorted(tree.Atoms.keys()):
            atom = tree.Atoms[ak]
            for a in atomsWritten:
                if atom.path.startswith(a): continue
            if atom.filename.replace(os.sep,'/') == sys.argv[2]:
                f.write(atom.DumpCode())
                atomsWritten+=[atom.path]
        """
        for thing in tree.fileLayouts[origin]:
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
            elif ttype == 'DEFINE':
                name = thing[1]
                value = thing[2]
                f.write('#define {} {}\n'.format(name, value))
            elif ttype == 'UNDEF':
                name = thing[1]
                f.write('#undef {}\n'.format(name))
            else: print('wot is ' + ttype + '?')
if __name__ == '__main__':
    if not os.path.isfile(sys.argv[1]):
        print('{0} baystation12.dme [code/FileToFix.dm]')
        sys.exit(1)
        
    tree = objtree.ObjectTree(preprocessor_directives=True)
    tree.ProcessFilesFromDME(sys.argv[1])
        
    atomsWritten = []
        
    if len(sys.argv)>=3 and os.path.isfile(sys.argv[2]):
        filename = sys.argv[2].replace('/', os.sep)
        processFile(tree, filename, filename + '.fixed')
    else:
        for filename in GetFilesFromDME(sys.argv[1]):
            fixpath = filename.replace('code' + os.sep, 'code-indented' + os.sep)
            fixpath = fixpath.replace('interface' + os.sep, 'interface-indented' + os.sep)
            fixpath = fixpath.replace('RandomZLevels' + os.sep, 'RandomZLevels-indented' + os.sep)
            fixdir = os.path.dirname(fixpath)
            if not os.path.isdir(fixdir):
                os.makedirs(fixdir)
            fixpath = fixpath.replace('/', os.sep)
            processFile(tree, filename, fixpath)
