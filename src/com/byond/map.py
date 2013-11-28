import os, itertools, sys
from com.byond.DMI import DMI
from com.byond.directions import NORTH, SOUTH, IMAGE_INDICES
from com.byond.basetypes import Atom, BYONDString, BYONDValue, BYONDFileRef
from com.byond.objtree import ObjectTree
from PIL import Image, PngImagePlugin

ID_ENCODING_TABLE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
def chunker(iterable, chunksize):
    """
    Return elements from the iterable in `chunksize`-ed lists. The last returned
    chunk may be smaller (if length of collection is not divisible by `chunksize`).

    >>> print list(chunker(xrange(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """
    i = iter(iterable)
    while True:
        wrapped_chunk = [list(itertools.islice(i, int(chunksize)))]
        if not wrapped_chunk[0]:
            break
        yield wrapped_chunk.pop()

class Tile:
    FLAG_USE_OLD_ID = 1
    FLAG_INHERITED_PROPERTIES = 2
    
    def __init__(self):
        self.origID = ''
        self.ID = 0
        self.data = []
        self.frame = None
    
    def ID2String(self, pad=0):
        o = ''
        id = self.ID
        IET_SIZE = len(ID_ENCODING_TABLE)
        while(id >= len(ID_ENCODING_TABLE)):
            i = id % IET_SIZE
            o = ID_ENCODING_TABLE[i] + o
            id -= i
            id /= IET_SIZE
        o = ID_ENCODING_TABLE[id] + o
        if pad > len(o):
            o = o.rjust(pad, ID_ENCODING_TABLE[0])
        return o
    
    def __str__(self):
        return self.MapSerialize(Tile.FLAG_USE_OLD_ID)
        
    def MapSerialize(self, flags=0):
        # "aat" = (/obj/structure/grille,/obj/structure/window/reinforced{dir = 8},/obj/structure/window/reinforced{dir = 1},/obj/structure/window/reinforced,/obj/structure/cable{d1 = 2; d2 = 4; icon_state = "2-4"; tag = ""},/turf/simulated/floor/plating,/area/security/prison)
        atoms = []
        atomFlags = 0
        if flags & Tile.FLAG_INHERITED_PROPERTIES:
            atomFlags |= Atom.FLAG_INHERITED_PROPERTIES
        for i in xrange(len(self.data)):
            atom = self.data[i]
            if atom.path != '':
                atoms += [atom.MapSerialize(atomFlags)]
        if not (flags & Tile.FLAG_USE_OLD_ID):
            return '"{ID}" = ({atoms})'.format(ID=self.ID2String(), atoms=','.join(atoms))
        else:
            return '"{ID}" = ({atoms})'.format(ID=self.origID, atoms=','.join(atoms))
    
    def __eq__(self, other):
        if len(self.data) != len(other.data):
            return False
        else:
            return all(self.data[i] == other.data[i] for i in range(len(self.data)))
    
class MapLayer:
    def __init__(self, map, height=255, width=255):
        self.map = map
        self.min = (1, 1)
        self.max = (height, width)
        self.height = height
        self.width = width
        self.tiles = [[0 for _ in xrange(self.width)] for _ in xrange(self.height)]
        
    def SetTileAt(self, x, y, tile):
        grow = False
        if y >= self.height:
            self.height = y - 1
            grow = True
        if x >= self.width:
            self.width = x - 1
            grow = True
        if grow:
            self.grow()
        
        self.tiles[y][x] = tile.ID
    
    def grow(self):
        gamt = self.height - len(self.tiles)
        print('y+=' + str(gamt))
        self.tiles += [[0] for _ in xrange(gamt)]
        for y in range(len(self.tiles)):
            gamt = self.width - len(self.tiles[y])
            print('x[{}]+={}'.format(y, gamt))
            self.tiles[y] += [0 for _ in xrange(self.width - len(self.tiles[y]))]
        
    def GetTileAt(self, x, y):
        # print(repr(self.tiles))
        return self.map.tileTypes[self.tiles[y][x]]
    
class Map:
    WRITE_OLD_IDS = 1
    def __init__(self, tree=None):
        self.tileTypes = []
        self.zLevels = {}
        self.oldID2NewID = {}
        self.DMIs = {}
        self.width = 0
        self.height = 0
        self.idlen = 0
        self.tree = tree
        
    def readMap(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            print('--- Reading tile types...')
            self.consumeTiles(f)
            print('--- Reading tile positions...')
            self.consumeTileMap(f)
        
    def writeMap(self, filename, flags=0):
        self.filename = filename
        tileFlags = 0
        if flags & Map.WRITE_OLD_IDS:
            tileFlags |= Tile.FLAG_USE_OLD_ID
        with open(filename, 'w') as f:
            for tile in self.tileTypes:
                f.write('{0}\n'.format(tile.MapSerialize(tileFlags)))
            for z in self.zLevels.keys():
                f.write('\n(1,1,{0}) = {{"\n'.format(z))
                zlevel = self.zLevels[z]
                for y in xrange(zlevel.height):
                    for x in xrange(zlevel.width):
                        tile = zlevel.GetTileAt(x, y)
                        if flags & Map.WRITE_OLD_IDS:
                            f.write(tile.origID)
                        else:
                            f.write(tile.ID2String(self.idlen))
                    f.write("\n")
                f.write('"}\n')
                
            
    def GetTileAt(self, x, y, z):
        if z < len(self.zLevels):
            return self.zLevels[z].GetTileAt(x, y)
        
    def consumeTileMap(self, f):
        zLevel = []
        y = 0
        z = 0
        inZLevel = False
        width = 0
        height = 0
        while True:
            line = f.readline()
            if line == '':
                return
            # (1,1,1) = {"
            if line.startswith('('):
                coordChunk = line[1:line.index(')')].split(',')
                # print(repr(coordChunk))
                z = int(coordChunk[2])
                zLevel = MapLayer(self, 255, 255)
                inZLevel = True
                y = 0
                width = 0
                height = 0
                continue
            if line.strip() == '"}':
                inZLevel = False
                if height == 0:
                    height = y
                # self.zLevels[z] = MapLayer(self, height, width)
                # self.zLevels[z].tiles = zLevel
                self.zLevels[z] = zLevel
                print('Added map layer {0} ({1}x{2})'.format(z, height, width))
                continue
            if inZLevel:
                if width == 0:
                    width = len(line) / self.idlen
                # self.zLevels[currentZLevel] += [self.oldID2NewID[line[i:i + self.idlen]] for i in range(0, len(line), self.idlen)]
                x = 0
                for chunk in chunker(line.strip(), self.idlen):
                    chunk = ''.join(chunk)
                    tid = self.oldID2NewID[chunk]
                    # print('{0} => {1}'.format(chunk,tid))
                    zLevel.SetTileAt(x, y, self.tileTypes[tid])
                    x += 1
                y += 1
                
            
    def generateImage(self, filename_tpl, basedir='.'):
        icons = {}
        print('--- Generating texture atlas...')
        for tid in xrange(len(self.tileTypes)):
            self.tileTypes[tid].frame = Image.new('RGBA', (96, 96))
            self.tileTypes[tid].offset = (32, 32)
            for atom in sorted(self.tileTypes[tid].data, reverse=True):
                
                # Ignore /areas.  They look like ass.
                if atom.path.startswith('/area'):
                    continue
                
                if atom.path == '/turf/space':
                    # We're going to turn space black for smaller images.
                    atom.properties['icon_state'].value = 'black'
                    
                if 'icon' not in atom.properties:
                    continue
                
                dmi_file = atom.properties['icon'].value
                
                if 'icon_state' not in atom.properties:
                    # Grab default icon_state ('') if we can't find the one defined.
                    atom.properties['icon_state'] = BYONDString("")
                
                state = atom.properties['icon_state'].value
                
                direction = SOUTH
                if 'dir' in atom.properties:
                    try:
                        direction = int(atom.properties['dir'].value)
                    except ValueError:
                        print('FAILED TO READ dir = ' + repr(atom.properties['dir'].value))
                        continue
                
                icon_key = '{0}:{1}[{2}]'.format(dmi_file, state, direction)
                if icon_key not in icons:
                    dmi = None
                    try:
                        dmi = self.loadDMI(os.path.join(basedir, dmi_file))
                    except Exception:
                        for prop in ['icon', 'icon_state', 'dir']:
                            print('\t{0}'.format(atom.dumpPropInfo(prop)))
                        pass
                    
                    if dmi.img.mode not in ('RGBA', 'P'):
                        print('WARNING: {} is mode {}!'.format(dmi_file, dmi.img.mode))
                        
                    if direction not in IMAGE_INDICES:
                        print('WARNING: Unrecognized direction {} on atom {} in tile {}!'.format(direction, atom.MapSerialize(), self.tileTypes[tid].origID))
                        direction = SOUTH  # DreamMaker property editor shows dir = 2.  WTF?
                        
                    frame = dmi.getFrame(state, direction, 0)
                    if frame == None:
                        # Get the error/default state.
                        frame = dmi.getFrame("", direction, 0)
                        # varState=atom.properties['icon_state']
                        # varDir=None
                        # if 'dir' in atom.properties:
                        #    varDir=atom.properties['dir']
                        # print('state:{} dir:{} == None'.format(state, direction))
                        # print('icon_state in {}:{}'.format(varState.filename,varState.line))
                    
                    if frame == None:
                        continue
                    # print(repr(frame))
                    frame = frame.convert("RGBA")
                    pixel_x = 0
                    if 'pixel_x' in atom.properties:
                        pixel_x = int(atom.properties['pixel_x'].value)
                    pixel_y = 0
                    if 'pixel_y' in atom.properties:
                        pixel_y = int(atom.properties['pixel_y'].value)
                    self.tileTypes[tid].frame.paste(frame, (32 + pixel_x, 32 + pixel_y), frame)  # Add to the top of the stack.
        print('--- Creating maps...')
        for z in self.zLevels.keys():
            filename = filename_tpl.replace('{z}', str(z))
            print(' -> {} ({}x{})'.format(filename, (self.zLevels[z].height + 2) * 32, (self.zLevels[z].width + 2) * 32))
            zpic = Image.new('RGBA', ((self.zLevels[z].width + 2) * 32, (self.zLevels[z].height + 2) * 32), "black")
            for y in xrange(self.zLevels[z].height):
                for x in xrange(self.zLevels[z].width):
                    tile = self.zLevels[z].GetTileAt(x, y)
                    if tile is not None:
                        x_o = 0
                        y_o = 32 - tile.frame.size[1]  # BYOND uses LOWER left as origin for some fucking reason
                        zpic.paste(tile.frame, ((x * 32) + x_o + tile.offset[0], (y * 32) + y_o + tile.offset[1], (x * 32) + tile.frame.size[0] + x_o + tile.offset[0], (y * 32) + tile.frame.size[0] + y_o + tile.offset[1]), tile.frame)
            zpic.save(filename, 'PNG')
        
            
    def loadDMI(self, filename):
        if filename not in self.DMIs:
            self.DMIs[filename] = DMI(filename)
            self.DMIs[filename].loadAll()
        return self.DMIs[filename]
    
    def cleanTile(self, t):
        for i in xrange(len(t.data)):
            if t.data[i] and 'tag' in t.data[i].properties:
                del t.data[i].properties['tag']
        return t
            
    # TODO: THIS IS GODAWFULLY SLOW
    def consumeTiles(self, f):
        index = 0
        duplicates = 0
        # self.tileTypes = [Tile() for _ in xrange(10000)]
        lineNumber = 0
        while True:
            line = f.readline()
            lineNumber += 1
            if line.startswith('"'):
                t = Tile()
                t.origID = self.consumeTileID(line)
                t.data = self.consumeTileTypes(line[line.index('(') + 1:], lineNumber)
                t.ID = index
                # if line.startswith('"aav"'):
                #    print(t.__str__(True))
                # t = self.cleanTile(t)
                tid = self.getTileTypeID(t)
                # if line.startswith('"aav"'):
                #    print(repr(tid))
                if tid == None:
                    self.tileTypes += [t]
                    self.idlen = max(self.idlen, len(t.ID2String()))
                    self.oldID2NewID[t.origID] = t.ID
                    # if line.startswith('"aav"'):
                    #    print(t.origID)
                    index += 1
                    if((index % 100) == 0):
                        print(index)
                else:
                    print('{} duplicate of {}! Installing redirect...'.format(t.origID, tid))
                    self.oldID2NewID[t.origID] = tid
                    print(t)
                    print(self.tileTypes[tid])
                    duplicates += 1
            else:
                print('-- {} tiles loaded, {} duplicates discarded'.format(index, duplicates))
                return 
    def getTileTypeID(self, t):
        for tile in self.tileTypes:
            if tile == t:
                return tile.ID
        return None
    def consumeTileID(self, line):
        e = line.index('"', 1)
        return line[1:e]
    
    # So we can read a map without parsing the tree.
    def GetAtom(self, path):
        if self.tree is not None:
            return self.tree.GetAtom(path)
        return Atom(path)
    
    def consumeTileTypes2(self, line, lineNumber):
        return
        
    def consumeTileTypes(self, line, lineNumber):
        types = []
        inString = False
        stringQuote = ''
        _buffer = ''
        inProperties = False
        index = -1
        currentAtom = Atom('')
        key = ''
        debug = False
        while(True):
            index += 1
            c = line[index]
            if not inProperties:
                if c == '{':
                    currentAtom = self.GetAtom(_buffer)
                    assert currentAtom != None
                    currentAtom = currentAtom.copy()
                    if debug:
                        print('NEW_ATOM({})'.format(currentAtom.path))
                        print('PROPERTIES_START')
                    _buffer = ''
                    inProperties = True
                    continue
                elif c == ',':
                    if currentAtom == None or currentAtom.path == '':
                        currentAtom = self.GetAtom(_buffer)
                        assert currentAtom != None
                        currentAtom = currentAtom.copy()
                        if debug: print('NEW_ATOM({})'.format(currentAtom.path))
                    # print 'buffer was '+_buffer
                    _buffer = ''
                        
                    # Compare to base
                    currentAtom.SetLayer()
                    # currentAtom.mapSpecified = []
                    base_atom = self.GetAtom(currentAtom.path)
                    assert base_atom != None
                    for key in base_atom.properties.keys():
                        val = base_atom.properties[key]
                        if key not in currentAtom.properties:
                            currentAtom.properties[key] = val
                    for key in currentAtom.properties.iterkeys():
                        val = currentAtom.properties[key].value
                        """
                        if key not in base_atom.properties or val != base_atom.properties[key].value:
                            if key not in currentAtom.mapSpecified:
                                currentAtom.mapSpecified.append(key)
                        """
                        if key in base_atom.properties and val == base_atom.properties[key].value:
                            if key in currentAtom.mapSpecified:
                                currentAtom.mapSpecified.remove(key)
                    
                    types += [currentAtom]
                    currentAtom = Atom('')
                    continue
                elif c == ')':
                    if currentAtom.path == '':
                        currentAtom = self.GetAtom(_buffer)
                        assert currentAtom != None
                        currentAtom = currentAtom.copy()
                        # currentAtom.parent=tmp_atom.parent
                        # currentAtom.children=tmp_atom.children
                    # print 'buffer was '+_buffer
                        
                    # Compare to base
                    currentAtom.SetLayer()
                    # currentAtom.mapSpecified = []
                    base_atom = self.GetAtom(currentAtom.path)
                    assert base_atom != None
                    for key in base_atom.properties.keys():
                        val = base_atom.properties[key]
                        if key not in currentAtom.properties:
                            currentAtom.properties[key] = val
                    for key in currentAtom.properties.iterkeys():
                        val = currentAtom.properties[key].value
                        """
                        if key not in base_atom.properties or val != base_atom.properties[key].value:
                            if key not in currentAtom.mapSpecified:
                                currentAtom.mapSpecified.append(key)
                        """
                        if key in base_atom.properties and val == base_atom.properties[key].value:
                            if key in currentAtom.mapSpecified:
                                currentAtom.mapSpecified.remove(key)
                                
                    if debug: print('NEW_ATOM({})'.format(currentAtom.path))
                    _buffer = ''
                    types += [currentAtom]
                    currentAtom = Atom('')
                    return types
            else:
                if not inString:
                    if c == '}':
                        # print 'buffer was '+_buffer
                        if stringQuote == '"':
                            currentAtom.properties[key] = BYONDString(_buffer.strip(), self.filename, lineNumber)
                        elif stringQuote == "'":
                            currentAtom.properties[key] = BYONDFileRef(_buffer.strip(), self.filename, lineNumber)
                        elif stringQuote == ')':
                            currentAtom.properties[key] = BYONDValue(_buffer.strip() + ')', self.filename, lineNumber)
                        else:
                            currentAtom.properties[key] = BYONDValue(_buffer.strip(), self.filename, lineNumber)
                        if key not in currentAtom.mapSpecified:
                            currentAtom.mapSpecified += [key]
                        if debug: print('PROPERTY({},{})'.format(key, currentAtom.properties[key]))
                        
                        _buffer = ''
                        stringQuote = None
                        inProperties = False
                        
                        if debug: print('PROPERTIES_END({})'.format(repr(currentAtom.properties)))
                        continue
                    elif c == ';':
                        # print currentAtom.type+': ['+key+'] buffer was '+_buffer
                        if stringQuote == '"':
                            currentAtom.properties[key] = BYONDString(_buffer.strip(), self.filename, lineNumber)
                        elif stringQuote == "'":
                            currentAtom.properties[key] = BYONDFileRef(_buffer.strip(), self.filename, lineNumber)
                        elif stringQuote == ')':
                            currentAtom.properties[key] = BYONDValue(_buffer.strip() + ')', self.filename, lineNumber)
                        else:
                            currentAtom.properties[key] = BYONDValue(_buffer.strip(), self.filename, lineNumber)
                        if key not in currentAtom.mapSpecified:
                            currentAtom.mapSpecified += [key]
                        if debug: print('PROPERTY({},{})'.format(key, currentAtom.properties[key]))
                        _buffer = ''
                        stringQuote = None
                        continue
                    elif c == '=':
                        key = _buffer.strip()
                        _buffer = ''
                        continue
                    elif c in ['"', "'"]:
                        inString = True
                        stringQuote = c
                        continue
                    elif c == '(':
                        inString = True
                        stringQuote = ')'
                else:
                    if c == stringQuote and line[index - 1] != '\\':
                        inString = False
                        continue
            _buffer += c
