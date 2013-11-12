
"""
Usage:
    $ python dumpTileTypes.py path/to/your.dme path/to/yourmap.dmm

dumpTileTypes.py - Dump all tiles used on a map. 

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
from com.byond.map import Tile, Map

if os.path.isfile(sys.argv[1]):
    selectedDMEs = []
    tree = ObjectTree()
    tree.ProcessFilesFromDME(sys.argv[1])
    dmm = Map(tree)
    dmm.readMap(sys.argv[2])
    with open(sys.argv[2]+'.opt','w') as f:
        for tile in dmm.tileTypes:
            f.write(tile.MapSerialize(Tile.FLAG_INHERITED_PROPERTIES|Tile.FLAG_USE_OLD_ID))