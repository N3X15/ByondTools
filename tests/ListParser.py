'''
Created on Feb 18, 2015

@author: Rob
'''
import unittest

class ListParserTests(unittest.TestCase):
    def setUp(self):
        from byond.script.dmscript import DreamSyntax
        self.syntax = DreamSyntax(list_only=True, simplify_lists=True)
        
    def test_syntax_associative(self):
        testString = 'list("a"=1, "b"="c")'

        result = self.syntax.ParseString(testString)
        
        self.assertEqual(result['a'], 1)
        self.assertEqual(result['b'], 'c')
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()