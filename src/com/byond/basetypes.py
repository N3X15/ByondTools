'''
Created on Nov 6, 2013

@author: Rob
'''
# import logging
AREA_LAYER = 1
TURF_LAYER = 2
OBJ_LAYER = 3
MOB_LAYER = 4
FLY_LAYER = 5


class BYONDValue:
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0):
        self.value = string
        self.filename = filename
        self.line = line
        
    def __str__(self):
        return '{0}'.format(self.value)
        
    def __repr__(self):
        return '<BYONDValue value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)

class BYONDFileRef(BYONDValue):
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0):
        BYONDValue.__init__(self, string, filename, line)
        
    def __str__(self):
        return "'{0}'".format(self.value)
        
    def __repr__(self):
        return '<BYONDFileRef value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)

class BYONDString(BYONDValue):
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0):
        BYONDValue.__init__(self, string, filename, line)
        
    def __str__(self):
        return '"{0}"'.format(self.value)
        
    def __repr__(self):
        return '<BYONDString value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)
    
class PropertyFlags:
    MAP_SPECIFIED = 1
    STRING  = 2
    FILEREF = 4
    VALUE   = 8
class Atom:
    FLAG_INHERITED_PROPERTIES = 1
    def __init__(self, path, filename='', line=0):
        global TURF_LAYER, AREA_LAYER, OBJ_LAYER, MOB_LAYER
        
        self.path = path
        self.properties = {}
        self.mapSpecified = []
        self.children = {}
        self.parent = None
        self.filename = filename
        self.line = line
        
    def copy(self):
        new_node = Atom(self.path)
        new_node.properties = self.properties.copy()
        new_node.mapSpecified = self.mapSpecified
        # new_node.parent = self.parent
        return new_node
    
    def getProperty(self,index,default=None):
        prop = self.properties.get(index,None)
        if prop == None:
            return default
        return prop.value
    
    def setProperty(self,index,value,flags=0):
        if flags & PropertyFlags.MAP_SPECIFIED:
            if index not in self.mapSpecified:
                self.mapSpecified += [index]
        if flags & PropertyFlags.VALUE:
            self.properties[index]=BYONDValue(value)
        elif isinstance(value,str) or flags & PropertyFlags.STRING:
            if flags & PropertyFlags.STRING:
                value=str(value)
            self.properties[index]=BYONDString(value)
        elif flags & PropertyFlags.FILEREF:
            if flags & PropertyFlags.RILEREF:
                value=str(value)
            self.properties[index]=BYONDFileRef(value)
        else:
            self.properties[index]=BYONDValue(value)

    def InheritProperties(self):
        if self.parent:
            for key, value in self.parent.properties.items():
                if key not in self.properties:
                    self.properties[key] = value
        for k in self.children.iterkeys():
            self.children[k].InheritProperties()
    
    def __ne__(self, atom):
        return not self.__eq__(atom)
    
    def __eq__(self, atom):
        if atom == None:
            return False
        if self.mapSpecified != atom.mapSpecified:
            return False
        if self.path != atom.path:
            return False
        return self.properties == atom.properties  
        
    def __lt__(self, other):
        if 'layer' not in self.properties or 'layer' not in other.properties:
            return False
        myLayer = float(self.properties['layer'].value)
        otherLayer = float(other.properties['layer'].value)
        return myLayer > otherLayer
        
    def __gt__(self, other):
        if 'layer' not in self.properties or 'layer' not in other.properties: 
            return False
        myLayer = float(self.properties['layer'].value)
        otherLayer = float(other.properties['layer'].value)
        return myLayer < otherLayer
    
    def MapSerialize(self, flags=0):
        atomContents = []
        # print(repr(self.mapSpecified))
        if (flags & Atom.FLAG_INHERITED_PROPERTIES):
            for key, val in self.properties.items():
                atomContents += ['{0} = {1}'.format(key, val)]
        else:
            for i in range(len(self.mapSpecified)):
                key = self.mapSpecified[i]
                if key in self.properties:
                    val = self.properties[key]
                    atomContents += ['{0} = {1}'.format(key, val)]
        if len(atomContents) > 0:
            return self.path + '{' + '; '.join(atomContents) + '}'
        else:
            return self.path
        
    def dumpPropInfo(self, name):
        o = '{0}: '.format(name)
        if name not in self.properties:
            return o + 'None'
        return o + repr(self.properties[name])


class Proc(Atom):
    def __init__(self, path, arguments, filename='', line=0):
        Atom.__init__(self, path, filename, line)
        self.arguments = arguments
        
    def MapSerialize(self, flags=0):
        return None
    
    def InheritProperties(self):
        return
