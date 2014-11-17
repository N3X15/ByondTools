#!/usr/bin/env python
"""
dmm.py - Collection of map tools.

Copyright 2013-2014 Rob "N3X15" Nelson <nexis@7chan.org>

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
import sys, argparse, os, re
from byond import ObjectTree, Map, MapRenderFlags
from byond.basetypes import Atom, PropertyFlags
from byond.map.format.dmm import DMMFormat

def main():
    dmmt = DMMFormat(None)
    opt = argparse.ArgumentParser()  # version='0.1')
    opt.add_argument('--project', default='baystation12.dme', type=str, help='Project file.', metavar='environment.dme')
    
    command = opt.add_subparsers(help='The command you wish to execute', dest='MODE')
    
    _compare = command.add_parser('diff', help='Compare two map files and generate a map patch.')
    _compare.add_argument('-O', '--output', dest='output', type=str, help='The other side.', metavar='mine.dmdiff', nargs='?')
    _compare.add_argument('theirs', type=str, help='One side of the difference', metavar='theirs.dmm')
    _compare.add_argument('mine', type=str, help='The other side.', metavar='mine.dmm')
    
    _patch = command.add_parser('patch', help='Apply a map patch.')
    _patch.add_argument('-O', '--output', dest='output', type=str, help='Where to place the patched map. (Default is to overwrite input map)', metavar='mine.dmdiff', nargs='?')
    _patch.add_argument('--clobber', dest='clobber', action="store_true", help='Overwrite conflicts')
    _patch.add_argument('patches', action='append', nargs='+', help='Patch(es) to apply.', metavar='patch.dmmpatch')
    _patch.add_argument('map', type=str, help='The map to change.', metavar='map.dmm')
    
    _analyze = command.add_parser('analyze', help='Generate a report of each atom on a map.  WARNING: huge')
    _analyze.add_argument('map', type=str, help='Map to analyze.', metavar='map.dmm')
    
    _split = command.add_parser('split', help='Split up a map by z-level.')
    #_split.add_argument('-i','--isolate', help='Isolate a given z-level', metavar='NUM')
    _split.add_argument('map', type=str, help='Map to split.', metavar='map.dmm')
    
    args = opt.parse_args()
    if args.MODE == 'diff':
        compare_dmm(args)
    elif args.MODE == 'analyze':
        analyze_dmm(args)
    elif args.MODE == 'split':
        split_dmm(args)
    elif args.MODE == 'patch':
        patch_dmm(args)
    else:
        print('!!! Error, unknown MODE=%r' % args.MODE)
        
def split_dmm(args):
    if not os.path.isfile(args.map):
        print('File {0} does not exist.'.format(args.mine))
        sys.exit(1)
    if not os.path.isfile(args.project):
        print('DM Environment File {0} does not exist.'.format(args.project))
        sys.exit(1)
    
    dmm = Map(forgiving_atom_lookups=True)
    dmm.Load(args.map, format='dmm')
    
    #fmt = DMMFormat(dmm)
    
    nz = len(dmm.zLevels)
    for z in range(nz):
        basename,ext = os.path.splitext(args.map)
        outfile='{0}-{1}{2}'.format(basename,z+1,ext)
        print('>>> Splitting z={}/{} to {}'.format(z+1,nz,outfile))
        output = Map(forgiving_atom_lookups=True)
        currentZLevel = dmm.zLevels[z]
        newZLevel = output.CreateZLevel(currentZLevel.height, currentZLevel.width)
        #newZLevel.initial_load=True
        for y in range(currentZLevel.width):
            for x in range(currentZLevel.height):
                newTile = newZLevel.GetTile(x, y)
                for atom in currentZLevel.GetTile(x,y).GetAtoms():
                    newTile.AppendAtom(atom.copy(toNewMap=True))
        #newZLevel.initial_load=False
        output.Save(outfile, format='dmm')

def patch_dmm(args):
    print(repr(args.patches))
    for i in range(len(args.patches[0])):
        patch=args.patches[0][i]
        if not os.path.isfile(patch):
            print('File {0} does not exist.'.format(patch))
            sys.exit(1)
    if not os.path.isfile(args.map):
        print('File {0} does not exist.'.format(args.mine))
        sys.exit(1)
    if not os.path.isfile(args.project):
        print('DM Environment File {0} does not exist.'.format(args.project))
        sys.exit(1)
        
    dmm = Map(forgiving_atom_lookups=True)
    dmm.Load(args.map, format='dmm')
    
    fmt = DMMFormat(dmm)

    context = None
    added = 0
    removed = 0
    
    currentpatch = ''
    
    def changeMarker(ln):
        a = Atom('/obj/effect/byondtools/changed')
        a.setProperty('tag','{}:{}'.format(currentpatch,ln),flags=PropertyFlags.MAP_SPECIFIED)
        return a
    
    def printReport(context, added, removed):
        if context is not None:
            x, y, z = context
            print(' Z={} +{} -{}'.format(z, added, removed))
    
    REG_INSTRUCTION = re.compile(r'^(?P<change>[\+\-])(?P<amount>[0-9\*]+)?\s+(?P<atom>/.*)')
    
    for i in range(len(args.patches[0])):
        patch=args.patches[0][i]
        print('* Applying {}...'.format(patch))
        currentpatch=patch
        with open(patch) as f:
            ln = 0
            lz = -1
            skip_block = False
            for line in f:
                ln += 1
                line = line.strip()
                if line == '': continue
                if line.startswith('#'): continue
                if line.startswith('<') and line.endswith('>'):
                    strcoords = line.strip('<>').split(',')
                    newcoords = []
                    for coord in strcoords:
                        newcoords += [int(coord)]
                    if context is not None and lz != context[2]:
                        printReport(context, added, removed)
                        lz = context[2]
                        added = removed = 0
                    context = newcoords
                    skip_block = False
                    continue
                if line.startswith('@') and not skip_block:
                    # @CHECK before-hash after-hash atoms-block
    
                    x, y, z = context
                    
                    if line.startswith('@CHECK'):
                        _, beforehash, afterhash, serdata = line.split(' ', 3)
                        
                        if args.clobber:
                            #print('WARNING: <{},{},{}> has changed and will be overwritten. (--clobber)'.format(x, y, z))
                            t=fmt.consumeTileChunk(serdata, cache=False)
                            t.AppendAtom(changeMarker(ln))
                            dmm.SetTileAt(x, y, z, t)
                            skip_block = True
                            continue
                        curhash = dmm.GetTileAt(x, y, z).GetHash()
                        if afterhash == curhash:
                            print('Skipping <{},{},{}> (already what we expected)'.format(x, y, z))
                            skip_block = True
                            continue
                        #else: print('PRE {} != {}: OK'.format(curhash,afterhash))
                        if beforehash != curhash:
                            print('WARNING: <{},{},{}> has changed.  Operations on this tile may not be accurate!'.format(x, y, z))
                            continue
                        #else: print('OLD {} == {}: OK'.format(curhash,beforehash))
                              
                if not skip_block and (line.startswith('+') or line.startswith('-')):
                    if line == '-ALL':
                        dmm.SetTileAt(x, y, z, dmm.CreateTile())
                        continue
                    m = REG_INSTRUCTION.match(line)
                    if m is None:
                        print('{}:{}: MALFORMED INSTRUCTION: {}'.format(args.patch, ln, line))
                        sys.exit(1)
                    amount = m.group('amount')
                    if amount == '*':
                        amount = 9999
                    else:
                        amount = int(m.group('amount') or 1)
                    change = m.group('change')
                    
                    atom = fmt.consumeAtom(m.group('atom'), ln)
                    atom.filename = args.patch
                    atom.line = ln
                    if atom is None:
                        print('{}:{}: WARNING: Unable to parse instance specified by chunk {}'.format(args.patch, ln, m.group('atom')))
                        continue
    
                    x, y, z = context
                    if x == 0 and y == 0 and z == 0:
                        print('WE AT <0,0,0> SOMEFIN WRONG')
                        
                    if z >= len(dmm.zLevels): continue
                    
                    tile = dmm.GetTileAt(x, y, z)
                    if change == '-':
                        for _ in range(amount):
                            if tile.CountAtom(atom) > 0:
                                tile.RemoveAtom(atom, hash=False)
                                removed += 1
                            else: break
                    elif change == '+':
                        for _ in range(amount):
                            tile.AppendAtom(atom, hash=False)
                        added += amount
                    tile.UpdateHash()
                    # dmm.SetTileAt(x, y, z, tile)
                    # print('{} - {}'.format((x,y,z),tile))
            printReport(context, added, removed)
    
    print('Saving...')
    dmm.Save(args.output if args.output else args.map)
    
def compare_dmm(args):
    if not os.path.isfile(args.theirs):
        print('File {0} does not exist.'.format(args.theirs))
        sys.exit(1)
    if not os.path.isfile(args.mine):
        print('File {0} does not exist.'.format(args.mine))
        sys.exit(1)
    if not os.path.isfile(args.project):
        print('DM Environment File {0} does not exist.'.format(args.project))
        sys.exit(1)
        
    theirs_dmm = Map(forgiving_atom_lookups=True)
    theirs_dmm.Load(args.theirs, format='dmm')
    
    mine_dmm = Map(forgiving_atom_lookups=True)
    mine_dmm.Load(args.mine, format='dmm')
    
    ttitle, _ = os.path.splitext(os.path.basename(args.theirs))
    mtitle, _ = os.path.splitext(os.path.basename(args.mine))
    
    format = DMMFormat(theirs_dmm)
    
    output = '{} - {}.dmmpatch'.format(ttitle, mtitle)
    
    if args.output:
        output = args.output
    with open(output, 'w') as f:
        stats = {
            'diffs':0,
            'tilediffs':0,
            'tiles':0,
            'atoms':0
        }
        print('Comparing maps...')
        for z in xrange(len(theirs_dmm.zLevels)):
            t_zlev = theirs_dmm.zLevels[z]
            m_zlev = mine_dmm.zLevels[z]
            if t_zlev.height != m_zlev.height or t_zlev.width != m_zlev.width:
                print('!!! ZLEVEL {} HEIGHT/WIDTH MISMATCH: ({},{}) != ({},{})'.format(z, t_zlev.height, t_zlev.width, m_zlev.height, m_zlev.width))
                continue
            print(" Scanning z-level {} ({}x{})...".format(z, t_zlev.height, t_zlev.width))
            for y in range(t_zlev.height):
                for x in range(t_zlev.width):
                    CHANGES = {}
                    
                    tTile = theirs_dmm.GetTileAt(x, y, z)
                    # if tTile is None:
                    #    print('!!! THEIRS <{},{},{}>: Tile object is None!'.format(x, y, z))
                    #    #return
                    mTile = mine_dmm.GetTileAt(x, y, z)
                    # if tTile is None:
                    #    print('!!! MINE <{},{},{}>: Tile object is None!'.format(x, y, z))
                    #    #return
                    
                    theirs = {}
                    mine = {}
                    all_keys = set()
                    
                    if tTile:
                        for A in tTile.GetAtoms():
                            key = format.SerializeAtom(A)
                            all_keys.add(key)
                            if key not in theirs:
                                theirs[key] = [A, 0]
                            theirs[key][1] += 1
                    if mTile:
                        for A in mTile.GetAtoms():
                            key = format.SerializeAtom(A)
                            all_keys.add(key)
                            if key not in mine:
                                mine[key] = [A, 0]
                            mine[key][1] += 1

                    removals = set()
                    additions = set()
                    kept = {}
                    
                    for key in all_keys:
                        change = None
                        minecount = 0
                        if key in mine:
                            minecount = mine[key][1]
                        theircount = 0
                        if key in theirs:
                            theircount = theirs[key][1]
                        delta = minecount - theircount
                        if delta < 0:
                            change = '-'
                            removals.add(key)
                        elif delta > 0:
                            change = '+'
                            additions.add(key)
                        if minecount > 0 and delta <= 0:
                            kept[key] = minecount
                        if change is not None:
                            CHANGES[key] = [change, abs(delta), minecount, theircount]
                        stats['tiles'] += 1
                    
                    def writeChanges(f, source, CHANGES):
                        for key in source:
                            change, amount, mc, tc = CHANGES[key]
                            # change, amount, _, _ = changedat
                            # f.write(' # {} vs {}\n'.format(mc, tc))
                            abs_amt = abs(amount)
                            if abs_amt > 1:
                                f.write(' {}{} {}\n'.format(change, abs_amt if mc > 0 else '*', key))
                            else:
                                f.write(' {} {}\n'.format(change, key))
                            stats['diffs'] += abs_amt
                            
                    if len(CHANGES) > 0:
                        f.write('<{},{},{}>\n'.format(x, y, z))
                        stats['tilediffs'] += 1
                        f.write(' @CHECK {before} {after} {tiledat}\n'.format(before=tTile.GetHash(), after=mTile.GetHash(), tiledat=format.SerializeTile(mTile)))
                        if len(kept) == 0:
                            f.write(' -ALL\n')
                        else:
                            writeChanges(f, removals, CHANGES)
                        """
                        for key,count in kept.items():
                            if count > 1:
                                f.write(' ={} {}\n'.format(count, key))
                            else:
                                f.write(' = {}\n'.format(key))
                        """
                        writeChanges(f, additions, CHANGES)
        print('Compared maps: {} differences in {} tiles.'.format(stats['diffs'], stats['tilediffs']))
        print('Total: {} atoms, {} tiles.'.format(stats['diffs'], stats['tilediffs']))


def analyze_dmm(args):
    tmpl_head = '''
<html>
    <head>
        <title>BYONDTools Map Analysis :: {TITLE}</title>
    </head>
    <body>
        <h1>{TITLE}</h1>
        <ul>
            <li><a href="{ROOT}/instances/index.html">Instances</a></li>
            <li><a href="{ROOT}/index.html">Tiles</a></li>
        </ul>'''
    tmpl_footer = '''
    </body>
</html>
    '''
    
    presentable_attributes = [
        'path',
        'id',
        'filename',
        'line'
    ]

    def MakePage(**kwargs):
        rewt = '.'
        depth = kwargs.get('depth', 0)
        if depth > 0:
            rewt = '/'.join(['..'] * depth)
        title = kwargs.get('title', 'LOL NO TITLE')
        body = kwargs.get('body', '')
        return (tmpl_head + body + tmpl_footer).replace('{TITLE}', title).replace('{ROOT}', rewt)

    if not os.path.isfile(args.project):
        print('DM Environment file {0} does not exist.'.format(args.theirs))
        sys.exit(1)

    if not os.path.isfile(args.map):
        print('Map {0} does not exist.'.format(args.theirs))
        sys.exit(1)

    tree = ObjectTree()
    tree.ProcessFilesFromDME(args.project)
    dmm = Map(tree)
    dmm.readMap(args.map)
    
    basedir = os.path.join(os.path.dirname(args.project), 'analysis', os.path.basename(args.map))
    
    if not os.path.isdir(basedir):
        os.makedirs(os.path.join(basedir, 'instances'))
        os.makedirs(os.path.join(basedir, 'tiles'))
    
    # Dump instances
    instance_info = {}
    for atom in dmm.instances:
        if atom.path not in instance_info:
            instance_info[atom.path] = []
        instance_info[atom.path] += [atom.ID]
        
        with open(os.path.join(basedir, 'instances', str(atom.ID) + '.html'), 'w') as f:
            body = '<h2>Atom Data:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>'
            for attr in presentable_attributes: 
                body += '<tr><th>{0}</th><td>{1}</td></tr>'.format(attr, getattr(atom, attr, None))
            body += '</tbody></table>'
            
            body += '<h2>Map-Specified Properties:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>'
            for attr_name in atom.mapSpecified:
                body += '<tr><th>{0}</th><td>{1}</td></tr>'.format(attr_name, atom.getProperty(attr_name, None))
            body += '</tbody></table>'
            
            body += '<h2>All Properties:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th><th>File/Line</th></tr></thead><tbody>'
            for attr_name in sorted(atom.properties.keys()):
                attr = atom.properties[attr_name]
                body += '<tr><th>{0}</th><td>{1}</td><td>{2}:{3}</td></tr>'.format(attr_name, attr.value, attr.filename, attr.line)
            body += '</tbody></table>'
            f.write(MakePage(title='Instance #{0}'.format(atom.ID), depth=1, body=body))
    with open(os.path.join(basedir, 'instances', 'index.html'), 'w') as idx:
        body = '<ul>'
        for atype, instances in instance_info.items():
            body += '<li><b>{0}</b><ul>'.format(atype)
            for iid in instances:
                body += '<li><a href="{{ROOT}}/instances/{0}.html">#{0}</a></li>'.format(iid)
            body += '</ul></li>'
        body += "</ul>"
        idx.write(MakePage(title='Instance Index'.format(atom.ID), depth=1, body=body))
        
    # Tiles
    with open(os.path.join(basedir, 'index.html'), 'w') as f:
        body = '<table class="prettytable"><thead><tr><th>Icon</th><th>ID</th><th>Instances</th></tr></thead><tbody>'
        for tile in dmm.tileTypes:
            body += '<tr><td><img src="tiles/{0}.png" height="96" width="96" /></td><th>{0}</th><td><ul>'.format(tile.ID)
            for atom in tile.SortAtoms():
                body += '<li><a href="{{ROOT}}/instances/{0}.html">#{0}</a> - {1}</li>'.format(atom.ID, atom.path)
            body += '</ul></td></tr>'
            img = tile.RenderToMapTile(0, os.path.dirname(sys.argv[1]), MapRenderFlags.RENDER_STARS)
            if img is None: continue
            pass_2 = tile.RenderToMapTile(1, os.path.dirname(sys.argv[1]), 0)
            if pass_2 is not None:
                img.paste(pass_2, (0, 0, 96, 96), pass_2)
            img.save(os.path.join(basedir, 'tiles', '{0}.png'.format(tile.ID)), 'PNG')
        body += '</tbody></table>'
        f.write(MakePage(title='Tile Index'.format(atom.ID), depth=0, body=body))
            
if __name__ == '__main__':
    main()
