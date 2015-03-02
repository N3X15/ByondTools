'''
Created on Jan 1, 2014

@author: Rob
'''
import unittest

class AtomTest(unittest.TestCase):
    def test_copy_consistency(self):
        from byond.basetypes import Atom, BYONDString, BYONDValue
        atom = Atom('/datum/test',__file__,0)
        
        atom.properties['dir']=BYONDValue(2)
        atom.properties['name']=BYONDString('test datum')
        
        atom.mapSpecified=['dir','name']
        
        atom2=atom.copy()
        
        atom_serialized=atom.dumpPropInfo('test')
        atom2_serialized=atom2.dumpPropInfo('test')
        
        self.assertEqual(atom_serialized, atom2_serialized)
        
    def test_serialization(self):
        from byond.basetypes import Atom, BYONDString, BYONDValue
        atom = Atom('/datum/test',__file__,0)
        
        # Assign properties.  Order is important (orderedDict!)
        atom.properties['dir']=BYONDValue(2)
        atom.properties['name']=BYONDString('test datum')
        
        # What we expect after running str().
        atom_serialized='/datum/test{dir=2;name="test datum"}'
        
        # Check it
        self.assertEqual(str(atom), atom_serialized)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()