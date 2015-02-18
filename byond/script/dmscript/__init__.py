'''
Copyright (c)2015 Rob "N3X15" Nelson

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

:author: Rob "N3X15" Nelson <nexisentertainment@gmail.com>
'''

from byond.basetypes import BYONDFileRef, BYONDList, BYONDString, BYONDValue
import pyparsing as pyp

class DreamSyntax(object):
    def __init__(self, list_only=False, simplify_lists=False):
        if list_only:
            self.syntax = self.buildListSyntax()
        else:
            self.syntax = self.buildSyntax()
        
        self.simplify_lists=simplify_lists
        
    def ParseString(self, string):
        try:
            return self.syntax.parseString(string)
        except pyp.ParseException, err:
            print err.line
            print "-"*(err.column-1) + "^"
            print err
        
    def buildSyntax(self):
        '''WIP'''
        dreamScript = pyp.Forward()
        
        # Literals
        singlelineString = pyp.QuotedString('"','\\').setResultsName('string').setParseAction(self.makeListString)
        fileRef = pyp.QuotedString("'",'\\').setResultsName('fileRef').setParseAction(self.makeFileRef)
        multilineString = pyp.QuotedString(quoteChar='{"',endQuoteChar='"}',multiline=True).setResultsName('string').setParseAction(self.makeListString)
        number = pyp.Regex(r'\d+(\.\d*)?([eE]\d+)?').setResultsName('number').setParseAction(self.makeListNumber)
        
        return dreamScript
        
    def buildListSyntax(self):
        dreamList = pyp.Forward()
        
        # Literals
        singlelineString = pyp.QuotedString('"','\\').setResultsName('string').setParseAction(self.makeListString)
        fileRef = pyp.QuotedString("'",'\\').setResultsName('fileRef').setParseAction(self.makeFileRef)
        multilineString = pyp.QuotedString(quoteChar='{"',endQuoteChar='"}',multiline=True).setResultsName('string').setParseAction(self.makeListString)
        number = pyp.Regex(r'\d+(\.\d*)?([eE]\d+)?').setResultsName('number').setParseAction(self.makeListNumber)
        
        # Other symbols
        listStart = pyp.Suppress('list(')
        listEnd = pyp.Suppress(')')
        
        # Grammar
        listConstant = singlelineString | fileRef | multilineString | number | dreamList
        listElement = listConstant | (listConstant + pyp.Literal('=') + listConstant)
        listElement = pyp.operatorPrecedence(listElement, [
                                ("=", 2, pyp.opAssoc.LEFT,),
                                ])
        listContents = pyp.delimitedList(listElement)
        dreamList << pyp.Group(listStart + listContents + listEnd)
        dreamList.setParseAction(self.makeList)
        
        return dreamList

    def makeListString(self,s,l,t):
        return self.makeString(s, l, t, True)
    def makeString(self, s, l, toks, from_list=False):
        #print('makeString(%r)' % toks[0])
        if self.simplify_lists:
            return [toks[0]]
        return [BYONDString(toks[0])]
    
    def makeFileRef(self, s,l,toks):
        #print('makeFileRef(%r)' % toks[0])
        return [BYONDFileRef(toks[0])]
    
    def makeListNumber(self,s,l,t):
        return self.makeString(s, l, t, True)
    
    def makeNumber(self, s,l,toks, from_list=False):
        #print('makeNumber(%r)' % toks[0])
        return [BYONDValue(float(toks[0]))]

    def makeList(self, toks):
        #print('makeList')
        #for i in range(len(toks)):
        #   print('{} = {}'.format(i,toks[i]))
        toks = toks[0]
        print('makeList(%r)' % toks)
        if len(toks[0]) == 1: # Constant, so a non-assoc list.
            l=[]
            for tok in toks:
                l.append(tok[0][1])
            return l
        else: # Associative
            l={}
            for k,_,v in toks:
                l[k]=v
            return l
        
def ParseDreamList(string):
    return DreamSyntax(list_only=True, simplify_lists=True).ParseString(string)
    