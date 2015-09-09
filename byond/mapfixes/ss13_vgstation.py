'''
/vg/station-specific fixes.
'''

from .base import Matcher, MapFix, RenameProperty, DeclareDependencies, ChangeType
from byond.basetypes import BYONDString, BYONDValue, Atom, PropertyFlags
from byond.directions import *

DeclareDependencies('vgstation', ['ss13'])

ATMOSBASE = '/obj/machinery/atmospherics'


@MapFix('vgstation')
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

'''
@MapFix('vgstation-NET2')
class NetworkingChangeAtmos(ChangeType):
    def __init__(self):
        ChangeType.__init__(self,'/obj/machinery/atmospherics','/obj/machinery/networked/atmos', fuzzy = True)

@MapFix('vgstation-NET2')
class NetworkingChangePower(ChangeType):
    def __init__(self):
        ChangeType.__init__(self,'/obj/machinery/power','/obj/machinery/networked/power', fuzzy = True)

@MapFix('vgstation-NET2')
class NetworkingChangeFiber(ChangeType):
    def __init__(self):
        ChangeType.__init__(self,'/obj/machinery/fiber','/obj/machinery/networked/fiber', fuzzy = True)
'''


@MapFix('vgstation')
class FixIDTags(Matcher):
    atomsToFix = {}

    def __init__(self):
        pass

    def Matches(self, atom):
        global atomsToFix
        if 'id_tag' in atom.properties:
            compiled_atom = self.tree.GetAtom(atom.path)
            if compiled_atom is None:
                return False
            if 'id_tag' not in compiled_atom.properties:
                FixIDTags.atomsToFix[atom.path] = True
        return 'id' in atom.properties and 'id' in atom.mapSpecified
        # return False

    def Fix(self, atom):
        _id = atom.properties['id']
        id_idx = atom.mapSpecified.index('id')
        atom.properties['id_tag'] = _id
        del atom.properties['id']
        atom.mapSpecified[id_idx] = 'id_tag'
        return atom

    def __str__(self):
        return 'Renamed id to id_tag'


PIPING_LAYER_DEFAULT = 3
PIPING_LAYER_P_X = 5
PIPING_LAYER_P_Y = -5

PIPING_LAYER_MIN = 1
PIPING_LAYER_MAX = 5
@MapFix('vgstation')
class OffsetPipeLayers(Matcher):

    def __init__(self):
        self.pixel_x=0
        self.pixel_y=0
        self.layer=0
        return

    def Matches(self, atom):
        if atom.path.startswith(ATMOSBASE) and 'piping_layer' in atom.mapSpecified:
            return True
        return False

    def Fix(self, atom):
        print('MIN: {}'.format(PIPING_LAYER_MIN))
        print('MAX: {}'.format(PIPING_LAYER_MAX))
        self.layer = int(atom.getProperty('piping_layer'))
        print('LAYER: {}'.format(self.layer))
        if self.layer < PIPING_LAYER_MIN:
            self.layer = PIPING_LAYER_MIN
            atom.setProperty('piping_layer', PIPING_LAYER_MIN, PropertyFlags.MAP_SPECIFIED)
        if self.layer > PIPING_LAYER_MAX:
            self.layer = PIPING_LAYER_MAX
            atom.setProperty('piping_layer', PIPING_LAYER_MAX, PropertyFlags.MAP_SPECIFIED)
        self.pixel_x = (self.layer - PIPING_LAYER_DEFAULT) * PIPING_LAYER_P_X
        self.pixel_y = (self.layer - PIPING_LAYER_DEFAULT) * PIPING_LAYER_P_Y
        atom.properties['pixel_x']=BYONDValue(self.pixel_x)
        atom.setProperty('pixel_x', self.pixel_x, PropertyFlags.MAP_SPECIFIED)
        atom.properties['pixel_y']=BYONDValue(self.pixel_y)
        atom.setProperty('pixel_y', self.pixel_y, PropertyFlags.MAP_SPECIFIED)
        return atom

    def __str__(self):
        return 'Set layered pipe offset to ({},{}) - Layer #{}'.format(self.pixel_x,self.pixel_y,self.layer)

@MapFix('vgstation')
class StandardizeManifolds(Matcher):
    STATE_TO_TYPE = {
        'manifold-b':   ATMOSBASE + '/pipe/manifold/supply/visible',
        'manifold-b-f': ATMOSBASE + '/pipe/manifold/supply/hidden',
        'manifold-r':   ATMOSBASE + '/pipe/manifold/scrubbers/visible',
        'manifold-r-f': ATMOSBASE + '/pipe/manifold/scrubbers/hidden',
        'manifold-c':   ATMOSBASE + '/pipe/manifold/cyan/visible',
        'manifold-c-f': ATMOSBASE + '/pipe/manifold/cyan/hidden',
        'manifold-y':   ATMOSBASE + '/pipe/manifold/yellow/visible',
        'manifold-y-f': ATMOSBASE + '/pipe/manifold/yellow/hidden',
        'manifold-g':   ATMOSBASE + '/pipe/manifold/filtering/visible',
        'manifold-g-f': ATMOSBASE + '/pipe/manifold/filtering/hidden',
        'manifold':     ATMOSBASE + '/pipe/manifold/general/visible',
        'manifold-f':   ATMOSBASE + '/pipe/manifold/general/hidden',
    }

    def __init__(self):
        return

    def Matches(self, atom):
        if atom.path == ATMOSBASE + '/pipe/manifold' and 'icon_state' in atom.mapSpecified:
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


@MapFix('vgstation')
class StandardizePiping(Matcher):
    TYPE_TRANSLATIONS = {
        ATMOSBASE + '/pipe/simple': 'simple',
        ATMOSBASE + '/pipe/manifold': 'manifold',
        ATMOSBASE + '/pipe/manifold4w': 'manifold4w',
    }
    COLOR_CODES = {
        'b': 'supply',
        'r': 'scrubbers',
        'g': 'filtering',
        'c': 'cyan',
        'y': 'yellow',
        '': 'general'
    }

    def __init__(self):
        self.before = None
        self.after = None
        return

    def trans_simple(self, atom):
        type_tmpl = ATMOSBASE + '/pipe/simple/{color}/{visibility}'
        color_code, visible = self.parseIconState(atom.getProperty('icon_state', ''))
        return self.getNewType(type_tmpl, color_code, visible)

    def trans_manifold(self, atom):
        type_tmpl = ATMOSBASE + '/pipe/manifold/{color}/{visibility}'
        color_code, visible = self.parseIconState(atom.getProperty('icon_state', ''))
        return self.getNewType(type_tmpl, color_code, visible)

    def trans_manifold4w(self, atom):
        type_tmpl = ATMOSBASE + '/pipe/manifold4w/{color}/{visibility}'
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
        self.before = str(atom)
        old_dir = None
        if 'dir' in atom.mapSpecified:
            old_dir = int(atom.getProperty('dir', 2))
        atom = getattr(self, 'trans_{0}'.format(self.TYPE_TRANSLATIONS[atom.path]))(atom)
        if old_dir is not None and old_dir != 2:
            atom.setProperty('dir', old_dir, PropertyFlags.MAP_SPECIFIED)
        self.after = str(atom)
        return atom

    def __str__(self):
        if self.before is not None and self.after is not None:
            return 'Standardized pipe: {0} -> {1}'.format(self.before, self.after)
        else:
            return 'Standardize pipes'


@MapFix('vgstation')
class StandardizeInsulatedPipes(Matcher):
    STATE_TO_TYPE = {
        'intact': ATMOSBASE + '/pipe/simple/insulated/visible',
        'intact-f': ATMOSBASE + '/pipe/simple/insulated/hidden'
    }

    def __init__(self):
        return

    def Matches(self, atom):
        if atom.path == ATMOSBASE + '/pipe/simple/insulated':
            return True
        if atom.path.startswith(ATMOSBASE + '/pipe/simple/insulated') and int(atom.getProperty('dir', 0)) in (3, 8, 12):
            # print(atom.MapSerialize())
            return True
        return False

    def Fix(self, atom):
        newtype = atom.path
        if atom.path == ATMOSBASE + '/pipe/simple/insulated':
            icon_state = ''
            if 'icon_state' in atom.properties:
                icon_state = atom.properties['icon_state'].value
            newtype = self.STATE_TO_TYPE.get(icon_state, ATMOSBASE + '/pipe/simple/insulated/visible')
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


@MapFix('vgstation')
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


@MapFix('vgstation')
class FixVaultFloors(Matcher):
    """
    Changes flooring icons to use /vg/'s standardized vault icons.
    """
    # state:1
    ICON_STATE_CHANGES = {
        'vault:1': {'icon_state': 'dark-markings', 'dir': 2},
        'vault:2': {'icon_state': 'dark vault stripe', 'dir': 2},
        'vault:4': {'icon_state': 'dark-markings', 'dir': 1},
        'vault:8': {'icon_state': 'dark-markings', 'dir': 8},
        'vault:6': {'icon_state': 'dark vault corner', 'dir': 2},
        'vault:10': {'icon_state': 'dark vault corner', 'dir': 8},
        'vault:5': {'icon_state': 'dark vault full', 'dir': 2},
        'vault:9': {'icon_state': 'dark loading', 'dir': 4},

        'vault-border:1': {'icon_state': 'dark vault stripe', 'dir': 2},
        'vault-border:2': {'icon_state': 'dark vault stripe', 'dir': 1},
        'vault-border:4': {'icon_state': 'dark vault stripe', 'dir': 4},
        'vault-border:8': {'icon_state': 'dark vault stripe', 'dir': 8},
        'vault-border:6': {'icon_state': 'dark vault corner', 'dir': 2},
        'vault-border:10': {'icon_state': 'dark vault stripe', 'dir': 5},
        'vault-border:5': {'icon_state': 'dark vault stripe', 'dir': 5},
        'vault-border:9': {'icon_state': 'dark vault stripe', 'dir': 6},
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


@MapFix('vgstation-legacy')
class RenameColorVG(RenameProperty):

    def __init__(self):
        RenameProperty.__init__(self, "color", "_color")
