#!/usr/bin/env python
"""
dmmfix.py - Apply various fixes to a map. 

Copyright 2013 Rob "N3X15" Nelson <nexis@7chan.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
import sys, argparse, logging
from byond.map import Map, Tile
from byond.objtree import ObjectTree
#from byond.basetypes import BYONDString, BYONDValue, Atom, PropertyFlags
#from byond.directions import *

from byond import mapfixes


logging.basicConfig(
    format='%(asctime)s [%(levelname)-8s]: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO  # ,
    # filename='logs/main.log',
    # filemode='w'
    )

opt = argparse.ArgumentParser()  # version='0.1')
opt.add_argument('-O', '--output', dest='output', type=str, help='Where to place the patched map. (Default is to overwrite input map)', metavar='butts.dmm', nargs='?')
opt.add_argument('-n', '--namespace', dest='namespaces', type=str, nargs='*', default=[], help='MapFix namespace to load (ss13, vgstation).')
opt.add_argument('-N', '--no-deps', dest='no_dependencies', action='store_true', help='Stop loading of namespace dependencies.')
opt.add_argument('-f', '--fix-script', dest='fixscripts', type=str, nargs='*', default=[], help='A script that specifies property and type replacements.')

opt.add_argument('dme', nargs='?', default='baystation12.dme', type=str,help='Project file.', metavar='environment.dme')
opt.add_argument('map', type=str,help='Map to fix.', metavar='map.dmm')

opt.set_defaults(no_dependencies=False)
args = opt.parse_args()

actions = []

mapfixes.Load()
actions += mapfixes.GetFixesForNS(args.namespaces, not args.no_dependencies)

tree = ObjectTree()
tree.ProcessFilesFromDME(args.dme)

for fixscript in args.fixscripts:
    with open(fixscript, 'r') as repl:
        ln = 0
        errors = 0
        for line in repl:
            ln += 1
            if line.startswith('#'):
                continue
            if line.strip() == '':
                continue
            # PROPERTY: step_x > pixel_x
            # TYPE: /obj/item/key > /obj/item/weapon/key/janicart
            subject, action = line.split(':')
            subject = subject.lower()
            if subject == 'property':
                old, new = action.split('>')
                actions += [mapfixes.base.RenameProperty(old.strip(), new.strip())]
            if subject == 'type' or subject == 'type!':
                force = subject == 'type!'
                old, new = action.split('>')
                newtype = new.strip()
                if newtype != "" and not newtype.startswith('/'):
                    logging.error('{0}:{1}: ERROR: Type "{2}" is not absolute. It must start with "/".  Example: /obj/item/book'.format(fixscript, ln,newtype))
                    errors += 1
                elif tree.GetAtom(newtype) is None:
                    logging.error('{0}:{1}: ERROR: Unable to find replacement type "{2}".'.format(fixscript, ln,newtype))
                    errors += 1
                else:
                    actions += [mapfixes.base.ChangeType(old.strip(), newtype, force)]
        if errors > 0:
            logging.critical('Found {0} errors, please fix them.'.format(errors))
            sys.exit(1)
            
dmm = Map(tree, forgiving_atom_lookups=1)
dmm.Load(args.map)
#dmm.Load(args.map.replace('.dmm', '.dmm2'))
logging.info('Changes to make:')
for action in actions:
    logging.info(' * ' + str(action))
logging.info('Iterating tiles...')
hashMap={} # hash => null to remove, hash => True to not remove, hash => Tile to replace with this.
it = dmm.Tiles()
thousandsActivity=0
for tile in it:
    if tile is None: continue
    for atom in tile.GetAtoms(): 
        ': :type atom Atom:'
        changes = []
        tile.RemoveAtom(atom)
        hash = atom.GetHash()
        if hash in hashMap:
            val = hashMap[hash]
            if val is None or type(val) is Tile:
                atom = val
        else:
            atomInfo='{0} #{1} (Tile #{2}/{3}):'.format(atom.path, atom.ID, it.pos, it.max)
            for action in actions:
                action.SetTree(tree)
                if action.Matches(atom):
                    atom = action.Fix(atom)
                    changes += [str(action)]
                    if atom is None: break
            
            '''
            compiled_atom = tree.GetAtom(atom.path)
            if compiled_atom is not None:
                for propname in list(atom.properties.keys()):
                    if propname not in compiled_atom.properties and propname not in ('req_access_txt','req_one_access_txt'):
                        del atom.properties[propname]
                        if propname in atom.mapSpecified:
                            atom.mapSpecified.remove(propname)
                        changes += ['Dropped property {0} (not found in compiled atom)'.format(propname)]
            '''
            if len(changes) > 0:
                thousandsActivity+=1
                logging.info(atomInfo if atom is not None else '{} (DELETED)'.format(atomInfo))
                for change in changes:
                    logging.info(' * ' + change)
        if atom is not None:
            tile.AppendAtom(atom)
        if hash not in hashMap:
            if len(changes) == 0:
                hashMap[hash]=True
            else:
                hashMap[hash]=atom
    if (it.pos % 1000) == 0:
        if thousandsActivity == 0:
            logging.info(it.pos)
        thousandsActivity=0
#for atom, _ in atomsToFix.items():
#    print('Atom {0} needs id_tag.'.format(atom))
with open(args.map + '.missing', 'w') as f:
    for atom in sorted(dmm.missing_atoms):
        f.write(atom + "\n")
print('--- Saving...')
dmm.Save(args.output if args.output else args.map + '.fixed')        
#dmm.writeMap2(args.map.replace('.dmm', '.dmm2') + '.fixed')
