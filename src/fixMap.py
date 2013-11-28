"""
fixMap.py map.dmm replacements.txt

* Removes step_(x|y)
* Fixes old networking setup.
* Replaces old shit with /vg/ shit.
"""
import sys
from com.byond.map import Map
from com.byond.basetypes import BYONDString, BYONDValue

class Matcher:
    def Matches(self,atom):
        return False
    
    def Fix(self,atom):
        return atom
    
class RenameProperty(Matcher):
    def __init__(self,old,new):
        self.old=old
        self.new=new
        
    def Matches(self,atom):
        if self.old in atom.properties:
            return True
        return False
    
    def Fix(self,atom):
        atom.properties[self.new]=atom.properties[self.old]
        if self.old in atom.mapSpecified:
            atom.mapSpecified+=[self.new]
            atom.mapSpecified.remove(self.old)
        del atom.properties[self.old]
        return atom
    
    def __str__(self):
        return 'Renamed {0} to {1}'.format(self.old,self.new)
    
class ChangeType(Matcher):
    def __init__(self,old,new):
        self.old=old
        self.new=new
        
    def Matches(self,atom):
        if self.old == atom.path:
            return True
        return False
    
    def Fix(self,atom):
        atom.path=self.new
        return atom
    
    def __str__(self):
        return 'Changed type from {0} to {1}'.format(self.old,self.new)

class FixNetwork(Matcher):
    def __init__(self):
        pass
    
    def Matches(self,atom):
        if atom.path.startswith('/obj/machinery/camera') and 'network' in atom.properties:
            return isinstance(atom.properties['network'], BYONDString) and not atom.properties['network'].value.startswith('list(')
        return False
    
    def Fix(self,atom):
        fix=atom.properties['network'].value
        atom.properties['network'] = BYONDValue('list("{0}")'.format(fix))
        return atom
    
    def __str__(self):
        return 'Changed network property to list'
    

actions=[
    # Fix step_x,step_y
    RenameProperty('step_x','pixel_x'),
    RenameProperty('step_y','pixel_y'),
    
    # Fix older network definitions
    FixNetwork()
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
            old,new = action.split('>')
            actions += [RenameProperty(old.strip(),new.strip())]
        if subject == 'type':
            old,new = action.split('>')
            actions += [ChangeType(old.strip(),new.strip())]
            
print('Changes to make:')
for action in actions:
    print(' * '+str(action))

dmm = Map()
dmm.readMap(sys.argv[1])
for tid in xrange(len(dmm.tileTypes)):
    tile = dmm.tileTypes[tid]
    changes=[]
    for i in xrange(len(tile.data)):
        for action in actions:
            if action.Matches(tile.data[i]):
                tile.data[i]=action.Fix(tile.data[i])
                changes+=[str(action)]
    if len(changes)>0:
        print(tile.origID+':')
        for change in changes:
            print(' * '+change)
print('--- Saving...')
dmm.writeMap(sys.argv[1]+'.fixed',Map.WRITE_OLD_IDS)        