#!/usr/bin/env python
'''
Created on Feb 16, 2015

@author: Rob
'''
import os, sys, argparse, shutil
from byond.basetypes import Atom, Proc, BYONDValue, BYONDList
from byond.script.dmscript import ParseDreamList
from byond import objtree, GetFilesFromDME

'''
/datum/chemical_reaction/honk
    name = "honk"
    id  = "honk"
    result = "honk"
    result_amount = 5
    secondary_results = list("slip"=100)        //additional reagents produced by the reaction
    
TO

/datum/chemical_reaction/honk
    name = "honk"
    id  = "honk"
    results = list("honk" = 5, "slip" = 100)
'''

def fixReactions(tree):
    removeIfPresent=['result','result_amount','secondary_results','secondary']
    atom = tree.GetAtom('/datum/chemical_reaction') # :type atom Atom:
    for rpath in atom.children:
        catom = atom.children[rpath]
        if not isinstance(catom,Proc):
            if catom.path == '/datum/chemical_reaction':
                continue
            
            fixes = []
            
            if 'required_temp' in catom.properties:
                temp = catom.properties['required_temp']
                if not temp.inherited:
                    catom.properties['min_temperature']=temp
                    del catom.properties['required_temp']
                    fixes.append('required_temp -> min_temperature')
            
            results = {}
            if 'result' in catom.properties and 'result_amount' in catom.properties:
                result = catom.properties['result']
                amount = catom.properties['result_amount']
                if not result.inherited:
                    if result is not None and result.value is not None:
                        results[result] = amount
                    fixes.append('result + result_amount -> results')
                del catom.properties['result_amount']
                del catom.properties['result']
                    
            if 'secondary_results' in catom.properties:
                print(catom.properties['secondary_results'].value)
                secondary_results = ParseDreamList(catom.properties['secondary_results'].value)
                print(secondary_results)
                if not secondary_results.inherited:
                    if secondary_results is not None:
                        results = dict(results, **secondary_results) # Merge
                    del catom.properties['secondary_results']
                    fixes.append('secondary_results -> results')
                    
            for key in removeIfPresent:
                if key in catom.properties:
                    del catom.properties[key]
                    fixes.append('Removed %s' % key)
                    
            if len(results) > 0:
                catom.properties['results'] = BYONDList(results)
            
            if len(fixes) > 0:
                logging.info('Fixed %s:' % catom.path)
                for fix in fixes:
                    logging.info(' - %s' % fix)

def postProcessFile(filename):
    with open(filename,'r') as inp:
        with open(filename+'.cleaned','w') as outp:
            consecutive_newlines = 0
            for line in inp:
                line = line.rstrip()
                if line == '':
                    consecutive_newlines += 1
                    if consecutive_newlines > 2:
                        continue
                else:
                    consecutive_newlines=0
                outp.write(line+'\n')
    if os.path.isfile(filename):
        os.remove(filename)
    shutil.move(filename+'.cleaned',filename)

def processFile(tree, origin, destination, args):
    atomsWritten=[]
    origin = os.path.relpath(os.path.normpath(origin))
    with open(destination, 'w') as f:
        logging('Checking {0}...'.format(destination))
        if False: #args.reorganize:
            for ak in sorted(tree.Atoms.keys()):
                atom = tree.Atoms[ak]
                for a in atomsWritten:
                    if atom.path.startswith(a): continue
                #if atom.filename.replace(os.sep,'/') == sys.argv[2]:
                if atom.filename == origin:
                    f.write(atom.DumpCode()+"\n")
                    atomsWritten+=[atom.path]
        else:
            if origin not in tree.fileLayouts:
                logging.warn('  Unknown origin %r' % origin)
                return
            for thing in tree.fileLayouts[origin]:
                ttype = thing[0]
                if ttype == 'ATOMDEF':
                    f.write(thing[1] + '\n')
                    
                    atom = tree.GetAtom(thing[1])
                    for name, prop in atom.properties.items():
                        if prop.inherited: continue
                        f.write('\t{}\n'.format(prop.DumpCode(name)))
                    f.write('\n')
                elif ttype == 'PROCDEF':
                    proc = tree.GetAtom(thing[1])
                    f.write(proc.DumpCode() + '\n')
                elif ttype == 'VAR':
                    #atom = tree.GetAtom(thing[1])
                    #var = atom.properties[thing[2]]
                    #f.write('\t{}\n'.format(var.DumpCode(thing[2])))
                    continue
                elif ttype == 'DEFINE':
                    name = thing[1]
                    value = thing[2]
                    f.write('#define {} {}\n'.format(name, value))
                elif ttype == 'UNDEF':
                    name = thing[1]
                    f.write('#undef {}\n'.format(name))
                elif ttype == 'COMMENT':
                    continue
                else: 
                    logging.warn('Unknown token %r',ttype)
    postProcessFile(destination)
if __name__ == '__main__':
    
    opt = argparse.ArgumentParser()
    opt.add_argument('project', metavar="project.dme")
    opt.add_argument('file', metavar="file.dm", default=None, nargs='?')
    opt.add_argument('--in-place',default=False, action='store_true')
    #opt.add_argument('--reorganize', dest='reorganize', default=False, action='store_true', help="Reorganize the file's contents, instead of keeping current structure.")
    opt.add_argument('--output','-o', dest='output', default='', help="Where to put the output (default: <file>.fixed)")
    
    args = opt.parse_args()
        
    tree = objtree.ObjectTree(preprocessor_directives=True)
    tree.skip_otr=True
    tree.ProcessFilesFromDME(args.project)
    
    fixReactions(tree)
    
    atomsWritten = []
        
    prefix = None
    if args.file is not None:
        if os.path.isdir(args.file):
            prefix = os.path.relpath(os.path.abspath(args.file), os.path.dirname(args.project))
        else:
            output=args.output
            if output=='':
                output=args.file+'.fixed'
            processFile(tree, args.file, output, args)
            sys.exit(0)
    for filename in GetFilesFromDME(args.project):
        relfilename=os.path.relpath(os.path.abspath(filename), os.path.dirname(args.project))
        if prefix and not relfilename.startswith(prefix):
            continue
        filechunks = relfilename.split(os.sep)
        filechunks[0]+='-fixed'
        fixpath = os.sep.join(filechunks)
        #fixpath = filename.replace('code' + os.sep, 'code-indented' + os.sep)
        #fixpath = fixpath.replace('interface' + os.sep, 'interface-indented' + os.sep)
        #fixpath = fixpath.replace('RandomZLevels' + os.sep, 'RandomZLevels-indented' + os.sep)
        fixdir = os.path.dirname(fixpath)
        if not os.path.isdir(fixdir):
            os.makedirs(fixdir)
        fixpath = fixpath.replace('/', os.sep)
        processFile(tree, filename, fixpath, args)
