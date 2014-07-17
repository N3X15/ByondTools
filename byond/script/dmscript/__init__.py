from pyparsing import *

body = Forward()

identifier = Word(alphas, alphanums+'_').setResultsName('identifier')
vardecl