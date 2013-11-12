"""
Python implementation of DreamCool's DM parser/tokenizer.

Used for things.  Like maps.
"""

"""
Represents a line parsed from the source.
"""
import copy
# from com.byond.map import Atom
from ply import *

# This is how everything ticks.  Derived from http://www.byond.com/forum/?post=87746

##############################
# LEXING
##############################
class IndentLexer(object):
    """
A second lexing stage that interprets WHITESPACE
Manages Off-Side Rule for indentation
"""
    def __init__(self, lexer):
        self.indents = [0]  # indentation stack
        self.tokens = []  # token queue
        self.lexer = lexer

    def input(self, *args, **kwds):
        self.lexer.input(*args, **kwds)

    # Iterator interface
    def __iter__(self):
        return self

    def next(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t

    __next__ = next

    def token(self):
        # empty our buffer first
        if self.tokens:
            return self.tokens.pop(0)

        # loop until we find a valid token
        while 1:
            # grab the next from first stage
            token = self.lexer.token()

            # we only care about whitespace
            if not token or token.type != 'WHITESPACE':
                return token

            # check for new indent/dedent
            whitespace = token.value[1:]  # strip \n
            change = self._calc_indent(whitespace)
            if change:
                break

        # indentation change
        if change == 1:
            token.type = 'INDENT'
            return token

        # dedenting one or more times
        assert change < 0
        change += 1
        token.type = 'DEDENT'

        # buffer any additional DEDENTs
        while change:
            self.tokens.append(copy.copy(token))
            change += 1

        return token

    def _calc_indent(self, whitespace):
        "returns a number representing indents added or removed"
        n = len(whitespace)  # number of spaces
        indents = self.indents  # stack of space numbers
        if n > indents[-1]:
            indents.append(n)
            return 1

        # we are at the same level
        if n == indents[-1]:
            return 0

        # dedent one or more times
        i = 0
        while n < indents[-1]:
            indents.pop()
            if n > indents[-1]:
                raise SyntaxError("wrong indentation level")
            i -= 1
        return i

class DMLexer:
    tokens = [
		'LBRACE',
		'PERIOD',
		'RBRACE',
		'RPAREN',
		'LBRACKET',
		'RBRACKET',
		'LPAREN',
		'SEMI',
		'COMMA',
		'COLON',
        'SLASH',
        'IDENTIFIER',
		'LOR',
		'PLUSEQUAL',
		'LSHIFTEQUAL',
		'RSHIFTEQUAL',
		'TIMESEQUAL',
		'OREQUAL',
		'LSHIFT',
		'XOR',
		'MODEQUAL',
		'RSHIFT',
		'PLUS',
		'LE',
		'ANDEQUAL',
		'TIMES',
		'NE',
		'EQ',
		'DIVEQUAL',
		'OR',
		'GE',
		'XOREQUAL',
		'LAND',
		'MINUSEQUAL',
		'MINUS',
		'LT',
		'DIVIDE',
		'MOD',
		'AND',
		'LNOT',
		'NOT',
		'EQUALS',
		'GT',
        'STRING',
        'VAR',
        'PROC',
        'NUMBER',
        'NEWLINE',
        'FILESPEC',
        'MULTISTRING',
        # 'INDENT', 'DEDENT'
    ]
    def __init__(self):
        self.current_depth = 0
        self.brace_depth = 0
        self.last_depth = 0
        
        self.lexer = None
        self.token_stream = None
        
    def parse(self, contents):
        self.lexer = lex.lex(module=self)
        self.input(contents)
        return self.lexer
        
    def _new_token(self, _type, lineno):
        tok = lex.LexToken()
        tok.type = _type
        tok.value = None
        tok.lineno = lineno
        return tok
        
    # The top-level filter adds an ENDMARKER, if requested.
    # Python's grammar uses it.
    def filter_tokens(self, add_endmarker=True):
        token = None
        tokens = iter(self.lexer.token, None)
        for token in tokens:
            yield token
    
        if add_endmarker:
            lineno = 1
            if token is not None:
                lineno = token.lineno
            yield self._new_token("ENDMARKER", lineno)
        
    states = (
        ('REGULAR', 'exclusive'),
        ('COMMENT', 'exclusive'),
        ('MULTICOMMENT', 'exclusive'),
    )
    
    def less(self, n):
        '''Ply doesn't define a yyless-equiv, so let's do that ourselves.'''
        self.lexer.skip(n)
    
    # def t_REGULAR_INDENT(self, token):
    #    r'(?<=\n)[\t ]+'
    #    self.current_depth += len(token.value)
    #    # print(token)
    #    # sys.exit()
    #    # return token
    
    # def t_INDENT(self, token):
    #    r'\n[\t ]+'
    #    self.current_depth += len(token.value)
    #    # print(token)
    #    # sys.exit()
    #    # return token
        
    def t_NONWHITESPACE(self, token):
        r'[^\t\n ]'
        # yyless(0);
        self.less(-1)
        if (self.current_depth > self.last_depth):
            self.lexer.begin('REGULAR')
            token.type = "INDENT"
            token.value = self.current_depth
            return token
        if (self.current_depth < self.last_depth):
            self.last_depth -= 1
            token.type = "DEDENT"
            token.value = self.current_depth
            return token
        self.lexer.begin('REGULAR')
        pass
         
    # def t_newline(self, token):
    #    r'\n+'
    #    self.current_depth = 0
    #    token.type = "NEWLINE"
    #    return token
        
    def t_REGULAR_ESCAPE(self, token):
        r'\\(.|\n)'
        pass
    
    def t_REGULAR_newline(self, token):
        r'\n'
        self.last_depth = self.current_depth
        self.current_depth = 0
        self.lexer.begin('INITIAL')
        token.type = "NEWLINE"
        return token
        
    def t_REGULAR_COMMENT(self, token):
        r'\/\/'
        self.lexer.begin('COMMENT')
        pass
        
    def t_COMMENT_newline(self, token):
        r'\n'
        self.lexer.begin('REGULAR')
        
    def t_COMMENT_CONTENT(self, token):
        r'.'
        pass
        
    def t_REGULAR_MULTICOMMENT(self, token):
        r'\/\*'
        self.lexer.begin('MULTICOMMENT')
        return token
        
    def t_MULTICOMMENT_ESCAPE(self, token):
        r'\\(.|\n)'
        pass
        
    def t_MULTICOMMENT_END(self, token):
        r'\*\/'
        self.lexer.begin('REGULAR')
        
    def t_MULTICOMMENT_CONTENT(self, token):
        r'.|\n'
        pass

    # ## STRINGS
    
    def t_REGULAR_STRING(self, token):
        r'"([^\\\n]|(\\.))*?"'
        token.type = 'STRING'
        token.value = token.value[1:-1]
        return token
    
    def t_REGULAR_FILESPEC(self, token):
        r'\'([^\\\n]|(\\.))*?\''
        token.type = 'FILESPEC'
        token.value = token.value[1:-1]
        return token
    
    def t_REGULAR_MULTISTRING(self, token):
        r'(?s)\{".*?"\}'
        token.type = 'MULTISTRING'
        token.value = token.value[2:-2]
        return token

    # KEYWORDS
    def t_REGULAR_VAR(self, token):
        r'var'
        token.type = "VAR"
        return token
    
    def t_REGULAR_PROC(self, token):
        r'(proc|verb)'
        token.type = "PROC"
        return token
    #t_REGULAR_PLUS = r'\+'
    #t_REGULAR_MINUS = r'-'
    #t_REGULAR_TIMES = r'\*'
    #t_REGULAR_DIVIDE = r'/'
    t_REGULAR_MOD = r'%'
    t_REGULAR_OR = r'\|'
    t_REGULAR_AND = r'&'
    t_REGULAR_NOT = r'~'
    t_REGULAR_XOR = r'\^'
    t_REGULAR_LSHIFT = r'<<'
    t_REGULAR_RSHIFT = r'>>'
    t_REGULAR_LOR = r'\|\|'
    t_REGULAR_LAND = r'&&'
    t_REGULAR_LNOT = r'!'
    t_REGULAR_LT = r'<'
    t_REGULAR_GT = r'>'
    t_REGULAR_LE = r'<='
    t_REGULAR_GE = r'>='
    t_REGULAR_EQ = r'=='
    t_REGULAR_NE = r'!='
    
    # Assignment operators
    
    t_REGULAR_EQUALS = r'='
    t_REGULAR_TIMESEQUAL = r'\*='
    t_REGULAR_DIVEQUAL = r'/='
    t_REGULAR_MODEQUAL = r'%='
    t_REGULAR_PLUSEQUAL = r'\+='
    t_REGULAR_MINUSEQUAL = r'-='
    t_REGULAR_LSHIFTEQUAL = r'<<='
    t_REGULAR_RSHIFTEQUAL = r'>>='
    t_REGULAR_ANDEQUAL = r'&='
    t_REGULAR_OREQUAL = r'\|='
    t_REGULAR_XOREQUAL = r'^='

    # OPERATOR
    t_REGULAR_LPAREN = r'\('
    t_REGULAR_RPAREN = r'\)'
    t_REGULAR_LBRACKET = r'\['
    t_REGULAR_RBRACKET = r'\]'
    # t_REGULAR_LBRACE           = r'\{'
    # t_REGULAR_RBRACE           = r'\}'
    t_REGULAR_COMMA = r','
    t_REGULAR_PERIOD = r'\.'
    t_REGULAR_SEMI = r';'
    t_REGULAR_COLON = r':'
    t_REGULAR_SLASH = r'/'
    t_REGULAR_GLOBAL = r'global'
    
    def t_REGULAR_IDENTIFIER(self, token):
        r'[_a-zA-Z][_0-9a-zA-Z]*'
        token.name = token.value
        token.type = "IDENTIFIER"
        return token

    def t_REGULAR_NUMBER(self, token):
        r'[0-9]+(\.[0-9]+)?'
        token.type = "NUMBER"
        return token

    # Dump extraneous space
    def t_REGULAR_WHITESPACE(self, token):
        r'(?<!\n)[ \t]+'
        pass
    def t_WHITESPACE(self, token):
        r'(?<!\n)[ \t]+'
        pass
    
    def t_error(self, token):
        print('ERROR: \n' + token.value)

##################################################
# TOKENS
##################################################
class DMScriptNode:
    children = []
    parent = None
    
    def __init__(self, parent=None, children=[]):
        self.children = children
        self.parent = parent

    def getFullPath(self):
        o = []
        parent = self.parent
        child = self
        while parent:
            o += [child.name]
            parent, child = parent.parent, parent
        o.reverse()
        return '/' + ('/'.join(o))
    
class DMAtomDeclaration(DMScriptNode):
    def __init__(self, path, parent=None, children=[]):
        DMScriptNode.__init__(self, parent, children)
        

class DMVariable(DMScriptNode):
    def __init__(self, dmtype, name, value, parent=None, children=[]):
        self.dmtype = dmtype
        self.name = name
        self.value = value
        DMScriptNode.__init__(self, parent=parent, children=children)
# Class that parses all in the filestreams given to it.
class DMParser:
    tokens = [
        'INDENT',
        'DEDENT',
        'IDENTIFIER',
        'VAR',
        'PROC',
        'OPERATOR',
        'IN',
        'EXPONENT',
        'EQUAL',
        'LSHIFT',
        'RSHIFT',
        'INCREMENT',
        'DECREMENT',
        'LAND',
        'LOR',
        'LEQUAL',
        'GEQUAL',
        'NEQUAL',
        'STRING',
        'AS',
        'NEWLINE',
        'NUMBER',
        'UMINUS',
        'GLOBAL'
    ]
    precedence = [
                  ('left', "PLUS", "MINUS"),
                  ('left', "TIMES", "SLASH"),
                  ('nonassoc', 'UMINUS'),
                  ('nonassoc', "'('", "')'")
    ]
    
    def __init__(self, lexer=None):
        # Build the parser
        self.parser = yacc.yacc(module=self)
        self.lexer = lexer
        if self.lexer is None:
            lexer = IndentLexer(DMLexer())
    
    def parse(self, s):
        if not s: return
        result = self.parser.parse(s, start='program', lexer=self.lexer)
        print result
       
    def p_program(self, p):
        '''program : global_variable_declaration
                    | atom_declaration'''
        p[0] = p[1]
        
    def p_global_variable_declaration(self, p):
        '''global_variable_declaration : VAR '/' GLOBAL '/' IDENTIFIER EQUALS const_expression
                                       | VAR '/' GLOBAL '/' type '/' IDENTIFIER EQUALS const_expression'''
        if len(p) == 9:
            p[0] = DMVariable(p[5], p[7], p[9])
        elif len(p) == 7:
            p[0] = DMVariable(None, p[5], p[7])
        
    def p_const_expression(self, p):
        '''const_expression : NUMBER 
                            | STRING 
                            | '(' const_expression ')' 
                            |  const_expression '+' const_expression 
                            |  const_expression '-' const_expression 
                            |  const_expression '*' const_expression 
                            |  const_expression '/' const_expression'''
        p[0] = p[1]
        
    def p_atom_declaration(self, p):
        "atom_declaration : type INDENT atom_contents"
        p[0] = DMAtomDeclaration(None, 0, p[1])
        
        
    def p_atom_contents(self,p):
        '''atom_contents : vardef
                         | procdef'''
        p[0]=p[1]
        
    def p_vardef(self, p):
        '''vardef : VAR '/' IDENTIFIER
                  | VAR '/' type '/' IDENTIFIER'''
        print(repr(p))
        
    def p_procdef(self, p):
        '''vardef : PROC '/' IDENTIFIER '(' arguments ')' INDENT proc_contents DEDENT'''
        print(repr(p))
        
    def p_type(self, p):
        '''type : IDENTIFIER
                | type '/' IDENTIFIER'''
        print(repr(p))
    
    # Error rule for syntax errors
    def p_error(self, p):
        print "Syntax error in input:\n{0}".format(p)
    
if __name__ == '__main__':
    import sys, os
    print('N3X15\'s Shitty DM Lexer - Test Script')
    print('Loading {0}...'.format(sys.argv[1]))
    print('----------------------------------------')
    dml = IndentLexer(DMLexer())
    with open(sys.argv[1], 'r') as f:
        buf = []
        s = f.read()
        '''
        for token in dml.parse(s):
            buf += [str(token)]
            if token.type=='NEWLINE':
                print(' '.join(buf))
                buf=[]
        '''
        dmp = DMParser(dml)
        dmp.parse(s)
