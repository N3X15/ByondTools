import os, sys, argparse
from com.byond.objtree import ObjectTree
from com.byond.map import Map, Tile, MapRenderFlags
"""
Usage:
    $ python generateMap.py path/to/your/project.dme path/to/your/map.dmm

generateMap.py - Creates an image of a DMM map.

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

opt = argparse.ArgumentParser()
opt.add_argument('project', metavar="project.dme")
opt.add_argument('map', metavar="map.dmm")
opt.add_argument('--render-stars', dest='render_stars', default=False, action='store_true', help="Render space.  Normally off to prevent ballooning the image size.")
opt.add_argument('--render-areas', dest='render_areas', default=False, action='store_true', help="Render area overlays.")
opt.add_argument('--area', dest='area', type=str, default=None, help="Specify an area to restrict rendering to.")
args = opt.parse_args()
if os.path.isfile(args.project):
    tree = ObjectTree()
    tree.ProcessFilesFromDME(args.project)
    dmm = Map(tree)
    dmm.readMap(args.map)
    renderflags = 0
    if args.render_stars:
        renderflags |= MapRenderFlags.RENDER_STARS
    if args.render_areas:
        renderflags |= MapRenderFlags.RENDER_AREAS
    kwargs = {}
    if args.area:
        kwargs['area'] = args.area
    dmm.generateImage(args.map + '.{z}.png', os.path.dirname(args.project), renderflags, **kwargs)
    
    # with open(sys.argv[2]+'.types','w') as f:
    #    for tile in dmm.tileTypes:
    #        f.write(tile.MapSerialize(Tile.FLAG_INHERITED_PROPERTIES|Tile.FLAG_USE_OLD_ID)+'\n')
