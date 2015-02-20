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

class PPStackElement(object):
    def __init__(self, ends=[], toggles=[], blocking=False):
        self.blocking = blocking
        self.ends = ends
        self.toggles = toggles
        
    def isBlocking(self):
        return self.blocking
    
    def gotToken(self, name):
        if name in self.ends:
            return False # Pop off stack
        if name in self.toggles:
            self.blocking = not self.blocking
        return True # continue
    
class IfDefElement(PPStackElement):
    def __init__(self, state):
        super(PPStackElement, self).__init__(self,ends=['endif'],toggles=['else'], blocking=state)
    
class DreamSyntax(object):
    def __init__(self, list_only=False, simplify_lists=False):
        if list_only:
            self.syntax = self.buildListSyntax()
        else:
            self.syntax = self.buildSyntax()
        
        self.simplify_lists=simplify_lists
        
        #: Preprocessor defines.
        self.macros = {}
        
        #: Current #ifdef stack. (PPStackElement)
        self.ifstack = []
        
        self.atomContext = []
        
    def ParseString(self, filename):
        try:
            return self.syntax.parseString(string)
        except pyp.ParseException, err:
            print err.line
            print "-"*(err.column-1) + "^"
            print err
        
    def buildSyntax(self):
        '''WIP'''
        dreamScript = pyp.Forward()
        
        # Constants
        singlelineString = pyp.QuotedString('"','\\').setResultsName('string').setParseAction(self.makeString)
        fileRef = pyp.QuotedString("'",'\\').setResultsName('fileRef').setParseAction(self.makeFileRef)
        multilineString = pyp.QuotedString(quoteChar='{"',endQuoteChar='"}',multiline=True).setResultsName('string').setParseAction(self.makeString)
        number = pyp.Regex(r'\d+(\.\d*)?([eE]\d+)?').setResultsName('number').setParseAction(self.makeNumber)
        
        # Other symbols
        listStart = pyp.Suppress('list(')
        listEnd = pyp.Suppress(')')
        
        VAR_GLOBAL = pyp.Keyword('global')
        VAR_CONST = pyp.Keyword('const')
        SLASH = pyp.Literal('/')
        EQUAL = pyp.Literal('=')
        VAR = pyp.Keyword('var')
        
        #############################
        # Grammar
        #############################
        
        constant = singlelineString | fileRef | multilineString | number | dreamList
        
        #  Lists
        listElement = constant | (constant + EQUAL + constant)
        listElement = pyp.operatorPrecedence(listElement, [
                                ("=", 2, pyp.opAssoc.LEFT,),
                                ])
        listContents = pyp.delimitedList(listElement)
        dreamList << pyp.Group(listStart + listContents + listEnd)
        dreamList.setParseAction(self.handleList)
        
        #  Paths
        
        relpath = pyp.ident | relpath + SLASH + pyp.ident
        abspath = SLASH + relpath
        path = (abspath | relpath).setParseAction(self.handlePath)
        pathslash = path + SLASH
        
        #  Preprocessor stuff
        ppStatement = pyp.Forward()
        
        ppDefine = pyp.Keyword('#define') + pyp.ident.setResultsName('name') + pyp.restOfLine.setResultsName('value')
        ppDefine.setParseAction(self.handlePPDefine)
        ppUndef = pyp.Keyword('#undef') + pyp.ident.setResultsName('name')
        ppUndef.setParseAction(self.handlePPUndef)
        
        ppIfdef = (pyp.Keyword('#ifdef') + pyp.ident.setResultsName('name')).setParseAction(self.handlePPIfdef)
        ppIfndef = (pyp.Keyword('#ifndef') + pyp.ident.setResultsName('name')).setParseAction(self.handlePPIfndef)
        ppElse = (pyp.Keyword('#else') + pyp.ident.setResultsName('name')).setParseAction(self.handlePPElse)
        ppEndif = pyp.Keyword('#endif').setParseAction(self.handlePPElse)
        
        ppStatement = pyp.lineStart + (ppIfdef | ppIfndef | ppElse | ppEndif)
        
        # Var Declarations
        ##########################
        var_modifiers = pyp.ZeroOrMore(SLASH + (VAR_GLOBAL|VAR_CONST)).setResultsName('modifiers')
        var_assignment = EQUAL + constant
        varblock_inner_ref = pyp.ident.setResultsName('name') + pyp.Optional(var_assignment)
        var_argument = VAR + pyp.Optional(abspath) + SLASH +  pyp.ident.setResultsName('name') + pyp.Optional(var_assignment)
        varblock_inner_decl = var_modifiers +  pyp.Optional(abspath) + SLASH + varblock_inner_ref
        varblock_element = varblock_inner_decl | varblock_inner_ref
        varblock = VAR + pyp.indentedBlock(var_blockinner_decl)
        inline_vardecl = VAR + varblock_inner_decl
        vardecl = varblock | inline_vardecl
        
        
        
        # Proc Declarations
        PROC = pyp.Keyword('proc')
        proc_args = '(' + pyp.delimitedList(var_argument | pyp.ident.setResultsName('name')) + ')'
        procblock_proc=pyp.ident.setResultsName('name') + proc_args + pyp.indentedBlock(proc_instructions)
        procblock = PROC + pyp.indentedBlock(procblock_proc, [1])
        
        # Atom blocks
        atomdecl = pyp.Forward()
        atomdecl << path + pyp.indentedBlock(vardecl | atomdecl | procdecl , [1])
        
        
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
        listElement = listConstant | (listConstant + '=' + listConstant)
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
    