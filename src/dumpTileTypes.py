
"""
Usage:
    $ python dumpTileTypes.py path/to/your.dme path/to/yourmap.dmm

dumpTileTypes.py - Dump all tiles and instances used on a map. 

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
import os, sys
from com.byond.objtree import ObjectTree
from com.byond.map import Map, MapRenderFlags

tmpl_head = '''
<html>
    <head>
        <title>OpenBYOND Map Analysis :: {TITLE}</title>
    </head>
    <body>
        <h1>{TITLE}</h1>
        <ul>
            <li><a href="{ROOT}/instances/index.html">Instances</a></li>
            <li><a href="{ROOT}/index.html">Tiles</a></li>
        </ul>
'''
tmpl_footer = '''
    </body>
</html>
'''

presentable_attributes=[
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

if os.path.isfile(sys.argv[1]):
    selectedDMEs = []
    tree = ObjectTree()
    tree.ProcessFilesFromDME(sys.argv[1])
    dmm = Map(tree)
    dmm.readMap(sys.argv[2])
    
    basedir = os.path.join(os.path.dirname(sys.argv[1]), 'analysis', os.path.basename(sys.argv[2]))
    
    if not os.path.isdir(basedir):
        os.makedirs(os.path.join(basedir,'instances'))
        os.makedirs(os.path.join(basedir,'tiles'))
    
    # Dump instances
    instance_info = {}
    for atom in dmm.instances:
        if atom.path not in instance_info:
            instance_info[atom.path] = []
        instance_info[atom.path] += [atom.id]
        
        with open(os.path.join(basedir, 'instances', str(atom.id) + '.html'), 'w') as f:
            body = '<h2>Atom Data:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>'
            for attr in presentable_attributes: 
                body += '<tr><th>{0}</th><td>{1}</td></tr>'.format(attr, getattr(atom, attr, None))
            body += '</tbody></table>'
            
            body += '<h2>Map-Specified Properties:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>'
            for attr_name in atom.mapSpecified:
                body += '<tr><th>{0}</th><td>{1}</td></tr>'.format(attr_name, atom.getProperty(attr_name, None))
            body += '</tbody></table>'
            
            body += '<h2>All Properties:</h2><table class="prettytable"><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>'
            for attr_name in sorted(atom.properties.keys()):
                body += '<tr><th>{0}</th><td>{1}</td></tr>'.format(attr_name, atom.getProperty(attr_name, None))
            body += '</tbody></table>'
            f.write(MakePage(title='Instance #{0}'.format(atom.id), depth=1, body=body))
    with open(os.path.join(basedir, 'instances', 'index.html'), 'w') as idx:
        body = '<ul>'
        for atype, instances in instance_info.items():
            body += '<li><b>{0}</b><ul>'.format(atype)
            for iid in instances:
                body += '<li><a href="{{ROOT}}/instances/{0}.html">#{0}</a></li>'.format(iid)
            body += '</ul></li>'
        body += "</ul>"
        idx.write(MakePage(title='Instance Index'.format(atom.id), depth=1, body=body))
        
    # Tiles
    with open(os.path.join(basedir, 'index.html'), 'w') as f:
        body = '<table class="prettytable"><thead><tr><th>Icon</th><th>ID</th><th>Instances</th></tr></thead><tbody>'
        for tile in dmm.tileTypes:
            body += '<tr><td><img src="tiles/{0}.png" height="96" width="96" /></td><th>{0}</th><td><ul>'.format(tile.ID)
            for atom in tile.SortAtoms():
                body += '<li><a href="{{ROOT}}/instances/{0}.html">#{0}</a> - {1}</li>'.format(atom.id,atom.path)
            body += '</ul></td></tr>'
            img = tile.RenderToMapTile(0, os.path.dirname(sys.argv[1]), MapRenderFlags.RENDER_STARS)
            if img is None: continue
            pass_2 = tile.RenderToMapTile(1, os.path.dirname(sys.argv[1]), 0)
            if pass_2 is not None:
                img.paste(pass_2,(0,0,96,96),pass_2)
            img.save(os.path.join(basedir, 'tiles', '{0}.png'.format(tile.ID)), 'PNG')
        body += '</tbody></table>'
        f.write(MakePage(title='Tile Index'.format(atom.id), depth=0, body=body))
            
