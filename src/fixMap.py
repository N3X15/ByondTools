"""
fixMap.py map.dmm replacements.txt

* Removes step_(x|y)
* Fixes old networking setup.
* Replaces old shit with /vg/ shit.
"""
import sys
from com.byond.map import Map
from com.byond.objtree import ObjectTree
from com.byond.basetypes import BYONDString, BYONDValue, Atom, PropertyFlags
from com.byond.directions import *

class Matcher:
    def Matches(self, atom):
        return False
    
    def Fix(self, atom):
        return atom
    
    def SetTree(self, tree):
        self.tree = tree
    
class RenameProperty(Matcher):
    def __init__(self, old, new):
        self.old = old
        self.new = new
        self.removed = False
        
    def Matches(self, atom):
        if self.old in atom.properties:
            return True
        return False
    
    def Fix(self, atom):
        if self.new not in atom.properties:  # Defer to the correct one if both exist.
            atom.properties[self.new] = atom.properties[self.old]
        if self.old in atom.mapSpecified:
            if self.new not in atom.mapSpecified:
                atom.mapSpecified += [self.new]
            else:
                self.removed = True
            atom.mapSpecified.remove(self.old)
        del atom.properties[self.old]
        return atom
    
    def __str__(self):
        if self.removed:
            return 'Removed {0}'.format(self.old)
        else:
            return 'Renamed {0} to {1}'.format(self.old, self.new)
    
class StandardizeManifolds(Matcher):
    STATE_TO_TYPE = {
        'manifold-b'  :'/obj/machinery/atmospherics/pipe/manifold/supply/visible',
        'manifold-b-f':'/obj/machinery/atmospherics/pipe/manifold/supply/hidden',
        'manifold-r'  :'/obj/machinery/atmospherics/pipe/manifold/scrubbers/visible',
        'manifold-r-f':'/obj/machinery/atmospherics/pipe/manifold/scrubbers/hidden',
        'manifold-c'  :'/obj/machinery/atmospherics/pipe/manifold/cyan/visible',
        'manifold-c-f':'/obj/machinery/atmospherics/pipe/manifold/cyan/hidden',
        'manifold-y'  :'/obj/machinery/atmospherics/pipe/manifold/yellow/visible',
        'manifold-y-f':'/obj/machinery/atmospherics/pipe/manifold/yellow/hidden',
        'manifold-g'  :'/obj/machinery/atmospherics/pipe/manifold/filtering/visible',
        'manifold-g-f':'/obj/machinery/atmospherics/pipe/manifold/filtering/hidden',
        'manifold'    :'/obj/machinery/atmospherics/pipe/manifold/general/visible',
        'manifold-f'  :'/obj/machinery/atmospherics/pipe/manifold/general/hidden',
    }
    def __init__(self):
        return
        
    def Matches(self, atom):
        if atom.path == '/obj/machinery/atmospherics/pipe/manifold' and 'icon_state' in atom.mapSpecified:
            return atom.getProperty('icon_state') in self.STATE_TO_TYPE
        return False
    
    def Fix(self, atom):
        icon_state = atom.properties['icon_state'].value
        new_atom = Atom(self.STATE_TO_TYPE[icon_state])
        if 'dir' in atom.mapSpecified:
            new_atom.setProperty('dir', atom.getProperty('dir'), PropertyFlags.MAP_SPECIFIED)
        return new_atom
    
    def __str__(self):
        return 'Standardized pipe manifold'
    
class StandardizePiping(Matcher):
    TYPE_TRANSLATIONS = {
        '/obj/machinery/atmospherics/pipe/simple': 'simple',
        '/obj/machinery/atmospherics/pipe/manifold': 'manifold',
        '/obj/machinery/atmospherics/pipe/manifold4w': 'manifold4w',
    }
    COLOR_CODES = {
        'b':'supply',
        'r':'scrubbers',
        'g':'filtering',
        'c':'cyan',
        'y':'yellow',
        '': 'general'
    }
    def __init__(self):
        self.before = None
        self.after = None
        return
        
    def trans_simple(self, atom):
        type_tmpl = '/obj/machinery/atmospherics/pipe/simple/{color}/{visibility}'
        color_code, visible = self.parseIconState(atom.getProperty('icon_state', ''))
        return self.getNewType(type_tmpl, color_code, visible)
        
    def trans_manifold(self, atom):
        type_tmpl = '/obj/machinery/atmospherics/pipe/manifold/{color}/{visibility}'
        color_code, visible = self.parseIconState(atom.getProperty('icon_state', ''))
        return self.getNewType(type_tmpl, color_code, visible)
        
    def trans_manifold4w(self, atom):
        type_tmpl = '/obj/machinery/atmospherics/pipe/manifold4w/{color}/{visibility}'
        color_code, visible = self.parseIconState(atom.getProperty('icon_state', ''))
        return self.getNewType(type_tmpl, color_code, visible)
        
    def parseIconState(self, state):
        parts = state.split('-')
        if len(parts) <= 1:
            return ('', True)
        elif len(parts) == 2:
            if parts[1] == 'f':
                return ('', True)
            return (parts[1], True) 
        return (parts[1], parts[2] != 'f')
        
    def getNewType(self, tmpl, color_code, visible, color_wheel=COLOR_CODES):
        visibility = 'visible'
        if not visible:
            visibility = 'hidden'
        color = color_wheel[color_code]
        return Atom(tmpl.format(color=color, visibility=visibility))
        
    def Matches(self, atom):
        return atom.path in self.TYPE_TRANSLATIONS
    
    def Fix(self, atom):
        self.before = atom.MapSerialize()
        old_dir = None
        if 'dir' in atom.mapSpecified:
            old_dir = int(atom.getProperty('dir', 2))
        atom = getattr(self, 'trans_{0}'.format(self.TYPE_TRANSLATIONS[atom.path]))(atom)
        if old_dir is not None and old_dir != 2:
            atom.setProperty('dir', old_dir, PropertyFlags.MAP_SPECIFIED)
        self.after = atom.MapSerialize()
        return atom
    
    def __str__(self):
        if self.before is not None and self.after is not None:
            return 'Standardized pipe: {0} -> {1}'.format(self.before, self.after)
        else:
            return 'Standardize pipes'
    
class StandardizeInsulatedPipes(Matcher):
    STATE_TO_TYPE = {
        'intact'  :'/obj/machinery/atmospherics/pipe/simple/insulated/visible',
        'intact-f':'/obj/machinery/atmospherics/pipe/simple/insulated/hidden'
    }
    def __init__(self):
        return
        
    def Matches(self, atom):
        if atom.path == '/obj/machinery/atmospherics/pipe/simple/insulated':
            return True
        if atom.path.startswith('/obj/machinery/atmospherics/pipe/simple/insulated') and int(atom.getProperty('dir', 0)) in (3, 8, 12):
            # print(atom.MapSerialize())
            return True
        return False
    
    def Fix(self, atom):
        newtype = atom.path
        if atom.path == '/obj/machinery/atmospherics/pipe/simple/insulated':
            icon_state = ''
            if 'icon_state' in atom.properties:
                icon_state = atom.properties['icon_state'].value
            newtype = self.STATE_TO_TYPE.get(icon_state, '/obj/machinery/atmospherics/pipe/simple/insulated/visible')
        new_atom = Atom(newtype)
        if 'dir' in atom.mapSpecified:
            # Normalize dir
            direction = int(atom.getProperty('dir', 2))
            if direction == 3:
                direction = 1
            elif direction == 8:  # Breaks things, for some reason
                direction = 4
            elif direction == 12:
                direction = 4
            new_atom.setProperty('dir', direction, PropertyFlags.MAP_SPECIFIED)
        return new_atom
    
    def __str__(self):
        return 'Standardized insulated pipe'
    
class FixWindows(Matcher):
    def __init__(self):
        return
        
    def Matches(self, atom):
        if atom.path.startswith('/obj/structure/window/full'):
            return False
        if atom.path.startswith('/obj/structure/window') and int(atom.getProperty('dir', SOUTH)) in (NORTH | WEST, SOUTH | WEST, NORTH | EAST, SOUTH | EAST):
            # print(atom.MapSerialize())
            return True
        return False
    
    def Fix(self, atom):
        newtype = atom.path.replace('/obj/structure/window', '/obj/structure/window/full')
        atom.path = newtype
        atom.properties = {}
        atom.mapSpecified = []
        return atom
    
    def __str__(self):
        return 'Standardized full windows'
    
class FixVaultFloors(Matcher):
    """
    Changes flooring icons to use /vg/'s standardized vault icons.
    """
    # state:1
    ICON_STATE_CHANGES = {
        'vault:1' :{'icon_state':'dark-markings', 'dir':2},
        'vault:2' :{'icon_state':'dark vault stripe', 'dir':2},
        'vault:4' :{'icon_state':'dark-markings', 'dir':1},
        'vault:8' :{'icon_state':'dark-markings', 'dir':8},
        'vault:6' :{'icon_state':'dark vault corner', 'dir':2},
        'vault:10':{'icon_state':'dark vault corner', 'dir':8},
        'vault:5' :{'icon_state':'dark vault full', 'dir':2},
        'vault:9' :{'icon_state':'dark loading', 'dir':4},
        
        'vault-border:1' :{'icon_state':'dark vault stripe', 'dir':2},
        'vault-border:2' :{'icon_state':'dark vault stripe', 'dir':1},
        'vault-border:4' :{'icon_state':'dark vault stripe', 'dir':4},
        'vault-border:8' :{'icon_state':'dark vault stripe', 'dir':8},
        'vault-border:6' :{'icon_state':'dark vault corner', 'dir':2},
        'vault-border:10':{'icon_state':'dark vault stripe', 'dir':5},
        'vault-border:5' :{'icon_state':'dark vault stripe', 'dir':5},
        'vault-border:9' :{'icon_state':'dark vault stripe', 'dir':6},
    }
    def __init__(self):
        self.stateKey = ''
        self.changesMade = []
        return
    
    def GetStateKey(self, atom):
        icon_state = ''
        _dir = '2'
        if 'dir' in atom.properties:
            _dir = str(atom.getProperty('dir'))
        if 'icon_state' in atom.properties:
            icon_state = atom.getProperty('icon_state')
        return icon_state + ":" + _dir
        
    def Matches(self, atom):
        if atom.path.startswith('/turf/') and 'icon_state' in atom.mapSpecified:
            sk = self.GetStateKey(atom)
            if sk in self.ICON_STATE_CHANGES:
                self.stateKey = sk
                return True
        return False
    
    def Fix(self, atom):
        self.changesMade = []
        propChanges = self.ICON_STATE_CHANGES[self.stateKey]
        if 'tag' in atom.mapSpecified:
            atom.mapSpecified.remove('tag')
        for key, newval in propChanges.items():
            if key not in atom.mapSpecified:
                atom.mapSpecified += [key]
            oldval = 'NONE'
            if key in atom.properties:
                oldval = str(atom.properties[key])
            if isinstance(newval, str):
                atom.properties[key] = BYONDString(newval)
            elif isinstance(newval, int):
                atom.properties[key] = BYONDValue(newval)
            self.changesMade += ['{0}: {1} -> {2}'.format(key, oldval, atom.properties[key])]
        return atom
    
    def __str__(self):
        return 'Standardized vault flooring (' + ', '.join(self.changesMade) + ')'
    
class ChangeType(Matcher):
    def __init__(self, old, new):
        self.old = old
        self.new = new
        
    def Matches(self, atom):
        if self.old == atom.path:
            return True
        return False
    
    def Fix(self, atom):
        atom.path = self.new
        return atom
    
    def __str__(self):
        return 'Change type from {0} to {1}'.format(self.old, self.new)

class FixNetwork(Matcher):
    def __init__(self):
        pass
    
    def Matches(self, atom):
        if atom.path.startswith('/obj/machinery/camera') and 'network' in atom.properties:
            return isinstance(atom.properties['network'], BYONDString) and not atom.properties['network'].value.startswith('list(')
        return False
    
    def Fix(self, atom):
        fix = atom.properties['network'].value
        atom.properties['network'] = BYONDValue('list("{0}")'.format(fix))
        return atom
    
    def __str__(self):
        return 'Changed network property to list'

class NukeTags(Matcher):
    def __init__(self):
        pass
    
    def Matches(self, atom):
        return 'tag' in atom.properties and 'tag' in atom.mapSpecified
    
    def Fix(self, atom):
        atom.mapSpecified.remove('tag')
        return atom
    
    def __str__(self):
        return 'Removed tag'

class StandardizeAPCs(Matcher):
    ACT_CLEAR_NAME = 1
    ACT_FIX_OFFSET = 2
    def __init__(self):
        self.actions = 0
        self.pixel_x = 0
        self.pixel_y = 0
        
    def Matches(self, atom):
        self.actions = 0
        if atom.path == '/obj/machinery/power/apc':
            # Determine if this APC is pretty close to standard-issue (no weird permissions, etc).
            nonstandard_settings = []
            for setting in atom.mapSpecified:
                if setting not in ('name', 'pixel_x', 'pixel_y', 'tag', 'dir'):
                    nonstandard_settings += [setting]
            if len(nonstandard_settings) > 0:
                print('Non-standard APC: Has strange settings - ' + ', '.join(nonstandard_settings))
            else:
                if 'name' in atom.properties and 'name' in atom.mapSpecified:
                    self.actions |= self.ACT_CLEAR_NAME
                
            direction = int(atom.getProperty('dir', 2))
            self.pixel_x = 0
            self.pixel_y = 0
            c_pixel_x = atom.getProperty('pixel_x', 0)
            c_pixel_y = atom.getProperty('pixel_y', 0)
            if (direction & 3):
                self.pixel_x = 0
                if(direction == 1): 
                    self.pixel_y = 24 
                else:
                    self.pixel_y = -24
            else:
                if(direction == 4): 
                    self.pixel_x = 24 
                else:
                    self.pixel_x = -24
                self.pixel_y = 0
            if self.pixel_x != c_pixel_x or self.pixel_y != c_pixel_y:
                self.actions |= self.ACT_FIX_OFFSET
        return self.actions != 0
    
    def Fix(self, atom):
        if self.actions & self.ACT_CLEAR_NAME:
            atom.mapSpecified.remove('name')
        if self.actions & self.ACT_FIX_OFFSET:
            atom.setProperty('pixel_x', self.pixel_x, PropertyFlags.MAP_SPECIFIED)
            atom.setProperty('pixel_y', self.pixel_y, PropertyFlags.MAP_SPECIFIED)
        return atom
    
    def __str__(self):
        if self.actions == 0:
            return 'APC Standardization'
        descr = []
        if self.actions & self.ACT_CLEAR_NAME:
            descr += ['Cleared name property']
        if self.actions & self.ACT_FIX_OFFSET:
            descr += ['Set pixel offset to {0},{1}'.format(self.pixel_x, self.pixel_y)]
        return 'Standardized APC: ' + ', '.join(descr)

atomsToFix = {}
class FixIDTags(Matcher):
    def __init__(self):
        pass
    
    def Matches(self, atom):
        global atomsToFix
        if 'id_tag' in atom.properties:
            compiled_atom = self.tree.GetAtom(atom.path)
            if compiled_atom is None: return False
            if 'id_tag' not in compiled_atom.properties:
                atomsToFix[atom.path] = True
        return 'id' in atom.properties and 'id' in atom.mapSpecified
        # return False
    
    def Fix(self, atom):
        id = atom.properties['id']
        id_idx = atom.mapSpecified.index('id')
        atom.properties['id_tag'] = id
        del atom.properties['id']
        atom.mapSpecified[id_idx] = 'id_tag'
        return atom
    
    def __str__(self):
        return 'Renamed id to id_tag'
    

actions = [
    # Fix step_x,step_y
    RenameProperty('step_x', 'pixel_x'),
    RenameProperty('step_y', 'pixel_y'),
    
    # Fix older network definitions
    FixNetwork(),
    
    # Standardize pipes
    StandardizePiping(),
    
    # Standardize insulated pipes
    StandardizeInsulatedPipes(),
    
    # Standardize vault flooring
    FixVaultFloors(),
    
    FixIDTags(),
    NukeTags(),
    StandardizeAPCs(),
    FixWindows()
]

tree = ObjectTree()
tree.ProcessFilesFromDME('baystation12.dme')

with open(sys.argv[2], 'r') as repl:
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
            actions += [RenameProperty(old.strip(), new.strip())]
        if subject == 'type':
            old, new = action.split('>')
            newtype = new.strip()
            if tree.GetAtom(newtype) is None:
                print('{0}:{1}: {2}'.format(sys.argv[2], ln, line.strip('\r\n')))
                print('  ERROR: Unable to find replacement type "{0}".'.format(newtype))
                errors += 1
            actions += [ChangeType(old.strip(), newtype)]
    if errors > 0:
        print('!!! {0} errors, please fix them.'.format(errors))
        sys.exit(1)
print('Changes to make:')
for action in actions:
    print(' * ' + str(action))
dmm = Map(tree, forgiving_atom_lookups=1)
dmm.readMap(sys.argv[1])
dmm.writeMap2(sys.argv[1].replace('.dmm', '.dmm2'))
for iid in xrange(len(dmm.instances)):
    atom = dmm.getInstance(iid)
    changes = []
    for action in actions:
        action.SetTree(tree)
        if action.Matches(atom):
            atom = action.Fix(atom)
            changes += [str(action)]
    atom.id = iid
    
    compiled_atom = tree.GetAtom(atom.path)
    if compiled_atom is not None:
        for propname in list(atom.properties.keys()):
            if propname not in compiled_atom.properties and propname not in ('req_access_txt'):
                del atom.properties[propname]
                atom.mapSpecified.remove(propname)
                changes += ['Dropped property {0} (not found in compiled atom)'.format(propname)]
    dmm.setInstance(iid, atom)
    if len(changes) > 0:
        print('{0} (#{1}):'.format(atom.path, atom.id))
        for change in changes:
            print(' * ' + change)
for atom, _ in atomsToFix.items():
    print('Atom {0} needs id_tag.'.format(atom))
with open(sys.argv[1] + '.missing', 'w') as f:
    for atom in sorted(dmm.missing_atoms):
        f.write(atom + "\n")
print('--- Saving...')
dmm.writeMap(sys.argv[1] + '.fixed', Map.WRITE_OLD_IDS)        
dmm.writeMap2(sys.argv[1].replace('.dmm', '.dmm2') + '.fixed')
