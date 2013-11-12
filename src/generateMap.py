import os, sys, re
from com.byond.objtree import *
import com.byond.map as byond_map
from com.byond import GetFilesFromDME
"""
Usage:
    $ python calculateMaxTechLevels.py path/to/your.dme .dm

calculateMaxTechLevels.py - Get techlevels of all objects and generate reports. 

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

if os.path.isfile(sys.argv[1]):
    selectedDMEs = []
    tree = ObjectTree()
    tree.ProcessFilesFromDME(sys.argv[1])
    path2name={}
    dmm = byond_map.Map(tree)
    dmm.readMap(sys.argv[2])
    dmm.generateImage(sys.argv[2]+'.{z}.png',os.path.dirname(sys.argv[1]))
    with open(sys.argv[2]+'.opt','w') as f:
        for tile in dmm.tileTypes:
            f.write(tile.MapSerialize(byond_map.Tile.FLAG_INHERITED_PROPERTIES|byond_map.Tile.FLAG_USE_OLD_ID)+'\n')
