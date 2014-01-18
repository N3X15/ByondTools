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

import re
REGEX_TABS = re.compile('^(?P<tabs>\t*)') 
class BYONDValue:
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0, typepath='/', **kwargs):
        self.value = string
        self.filename = filename
        self.line = line
        self.type = typepath
        self.inherited = kwargs.get('inherited', False)
        self.declaration = kwargs.get('declaration', False)
        self.special = kwargs.get('special', None)
        self.size = kwargs.get('size', None)
        
    def copy(self):
        return BYONDValue(self.value, self.filename, self.line, self.type, declaration=self.declaration, inherited=self.inherited, special=self.special)
    
    def __str__(self):
        return '{0}'.format(self.value)
        
    def __repr__(self):
        return '<BYONDValue value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)
    
    def DumpCode(self, name):
        decl = []
        if self.declaration:
            decl += ['var']
        if self.type != '/' and self.declaration:
            decl += self.type.split('/')[1:]
        decl += [name]
        constructed = '/'.join(decl)
        if self.value is not None:
            constructed += ' = {0}'.format(str(self))
        return constructed

class BYONDFileRef(BYONDValue):
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0, **kwargs):
        BYONDValue.__init__(self, string, filename, line, '/icon', **kwargs)
        
    def copy(self):
        return BYONDFileRef(self.value, self.filename, self.line, declaration=self.declaration, inherited=self.inherited, special=self.special)
        
    def __str__(self):
        return "'{0}'".format(self.value)
        
    def __repr__(self):
        return '<BYONDFileRef value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)

class BYONDString(BYONDValue):
    """
    Just to format file references differently.
    """
    def __init__(self, string, filename='', line=0, **kwargs):
        BYONDValue.__init__(self, string, filename, line, '/', **kwargs)
        
    def copy(self):
        return BYONDString(self.value, self.filename, self.line, declaration=self.declaration, inherited=self.inherited, special=self.special)
        
    def __str__(self):
        return '"{0}"'.format(self.value)
        
    def __repr__(self):
        return '<BYONDString value="{}" filename="{}" line={}>'.format(self.value, self.filename, self.line)
    
class PropertyFlags:
    MAP_SPECIFIED = 1
    STRING = 2
    FILEREF = 4
    VALUE = 8
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
    
    def getProperty(self, index, default=None):
        prop = self.properties.get(index, None)
        if prop == None:
            return default
        return prop.value
    
    def setProperty(self, index, value, flags=0):
        if flags & PropertyFlags.MAP_SPECIFIED:
            if index not in self.mapSpecified:
                self.mapSpecified += [index]
        if flags & PropertyFlags.VALUE:
            self.properties[index] = BYONDValue(value)
        elif isinstance(value, str) or flags & PropertyFlags.STRING:
            if flags & PropertyFlags.STRING:
                value = str(value)
            self.properties[index] = BYONDString(value)
        elif flags & PropertyFlags.FILEREF:
            if flags & PropertyFlags.RILEREF:
                value = str(value)
            self.properties[index] = BYONDFileRef(value)
        else:
            self.properties[index] = BYONDValue(value)

    def InheritProperties(self):
        if self.parent:
            for key, value in self.parent.properties.items():
                value = value.copy()
                if key not in self.properties:
                    self.properties[key] = value
                    self.properties[key].inherited = True
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
        myLayer=0
        otherLayer=0
        try:
            myLayer = float(self.properties['layer'].value)
            otherLayer = float(other.properties['layer'].value)
        except ValueError:
            pass
        return myLayer > otherLayer
        
    def __gt__(self, other):
        if 'layer' not in self.properties or 'layer' not in other.properties: 
            return False
        myLayer=0
        otherLayer=0
        try:
            myLayer = float(self.properties['layer'].value)
            otherLayer = float(other.properties['layer'].value)
        except ValueError:
            pass
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
    
    def _DumpCode(self):
        divider = '//' + ((len(self.path) + 2) * '/') + '\n'
        o = divider
        o += '// ' + self.path + '\n'
        o += divider
        o += self.path + '\n'
        # o += '\t//{0} properties total\n'.format(len(self.properties))
        for name in sorted(self.properties.keys()):
            prop = self.properties[name]
            if prop.inherited: continue
            _type = prop.type
            if not _type.endswith('/'):
                _type += '/'
            prefix = ''
            if prop.declaration:
                prefix = 'var'
            if not prop.declaration and _type == '/':
                _type = ''
            o += '\t{prefix}{type}{name}'.format(prefix=prefix, type=_type, name=name)
            if prop.value is not None:
                o += ' = {value}'.format(value=str(prop))
            o += '\n'
        
        # o += '\n'
        # o += '\t//{0} children total\n'.format(len(self.children))
        procs = ''
        children = ''
        for ck in sorted(self.children.keys()):
            co = '\n'
            co += self.children[ck]._DumpCode()
            if isinstance(self.children[ck], Proc):
                procs += co
            else:
                children += co
        o += procs + children
        return o
    
    def DumpCode(self):
        return self._DumpCode()
    
class Proc(Atom):
    def __init__(self, path, arguments, filename='', line=0):
        Atom.__init__(self, path, filename, line)
        self.arguments = arguments
        self.code = []  # (indent, line)
        
    def CountTabs(self, line):
        m = REGEX_TABS.match(line)
        if m is not None:
            return len(m.group('tabs'))
        return 0
        
    def AddCode(self, indentLevel, line):
        self.code += [(indentLevel, line)]
        
    def AddBlankLine(self):
        if len(self.code) > 0 and self.code[-1][1] == '':
            return
        self.code += [(0, '')]
        
    def MapSerialize(self, flags=0):
        return None
    
    def InheritProperties(self):
        return
    
    def _DumpCode(self):
        o = '\n' + self.path + '\n'
        min_indent = 0
        # Find minimum indent level
        for i in range(len(self.code)):
            indent, _ = self.code[i]
            if indent == 0: continue
            min_indent = indent
            break
        # Should be 1, so find the difference.
        indent_delta = 1 - min_indent
        # o += '\t// min_indent = {0}\n'.format(min_indent)
        # o += '\t// indent_delta = {0}\n'.format(indent_delta)
        for i in range(len(self.code)):
            indent, code = self.code[i]
            indent = max(1, indent + indent_delta)
            if code == '' and i == len(self.code) - 1:
                continue
            if code.strip() == '':
                o += '\n'
            else:
                o += (indent * '\t') + code.strip() + '\n'
        return o
