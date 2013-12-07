"""
fixMap.py map.dmm replacements.txt

* Removes step_(x|y)
* Fixes old networking setup.
* Replaces old shit with /vg/ shit.
"""
import sys
from com.byond.map import Map
from com.byond.basetypes import BYONDString, BYONDValue, Atom

class Matcher:
    def Matches(self, atom):
        return False
    
    def Fix(self, atom):
        return atom
    
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
    STATE_TO_TYPE={
        'manifold-b-f':'/obj/machinery/atmospherics/pipe/manifold/supply/hidden',
        'manifold-r-f':'/obj/machinery/atmospherics/pipe/manifold/scrubbers/hidden',
        'manifold-f':'/obj/machinery/atmospherics/pipe/manifold/general/hidden',
        'manifold-b':'/obj/machinery/atmospherics/pipe/manifold/supply/visible',
        'manifold-r':'/obj/machinery/atmospherics/pipe/manifold/scrubbers/visible',
        'manifold':'/obj/machinery/atmospherics/pipe/manifold/general/visible',
    }
    def __init__(self):
        return
        
    def Matches(self, atom):
        if atom.path == '/obj/machinery/atmospherics/pipe/manifold' and 'icon_state' in atom.mapSpecified:
            return atom.properties['icon_state'].value in self.STATE_TO_TYPE
        return False
    
    def Fix(self, atom):
        icon_state=atom.properties['icon_state'].value
        new_atom=Atom(self.STATE_TO_TYPE[icon_state])
        if 'dir' in atom.mapSpecified:
            new_atom.properties['dir']=BYONDValue(atom.properties['dir'].value)
            new_atom.mapSpecified += ['dir']
        return new_atom
    
    def __str__(self):
        return 'Standardized pipe manifold'
    
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
        return 'Changed type from {0} to {1}'.format(self.old, self.new)

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
    

actions = [
    # Fix step_x,step_y
    RenameProperty('step_x', 'pixel_x'),
    RenameProperty('step_y', 'pixel_y'),
    
    # Fix older network definitions
    FixNetwork(),
    
    # Standardize pipes
    StandardizeManifolds()
]
with open(sys.argv[2], 'r') as repl:
    for line in repl:
        if line.startswith('#'):
            continue
        if line.strip() == '':
            continue
        # PROPERTY: step_x > pixel_x
        # TYPE: /obj/item/key > /obj/item/weapon/key/janicart
        subject, action = line.split(':')
        subject = type.lower()
        if subject == 'property':
            old, new = action.split('>')
            actions += [RenameProperty(old.strip(), new.strip())]
        if subject == 'type':
            old, new = action.split('>')
            actions += [ChangeType(old.strip(), new.strip())]
            
print('Changes to make:')
for action in actions:
    print(' * ' + str(action))

dmm = Map()
dmm.readMap(sys.argv[1])
for tid in xrange(len(dmm.tileTypes)):
    tile = dmm.tileTypes[tid]
    changes = []
    for i in xrange(len(tile.data)):
        for action in actions:
            if action.Matches(tile.data[i]):
                tile.data[i] = action.Fix(tile.data[i])
                changes += [str(action)]
    if len(changes) > 0:
        print(tile.origID + ':')
        for change in changes:
            print(' * ' + change)
print('--- Saving...')
dmm.writeMap(sys.argv[1] + '.fixed', Map.WRITE_OLD_IDS)        
