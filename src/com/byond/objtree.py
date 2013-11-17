'''
Superficially generate an object/property tree
'''
import re, logging, os
from .basetypes import *

REGEX_TABS = re.compile('^(?P<tabs>\t*)')  # \s*$
REGEX_VARIABLE_STRING = re.compile('^(?P<tabs>\t+)(?:var/)?(?P<type>[a-zA-Z0-9_]*/)?(?P<variable>[a-zA-Z0-9_]+)\s*=\s*(?P<qmark>[\'"])(?P<content>.+)(?P=qmark)\s*$')
REGEX_VARIABLE_NUMBER = re.compile('^(?P<tabs>\t+)(?:var/)?(?P<type>[a-zA-Z0-9_]*/)?(?P<variable>[a-zA-Z0-9_]+)\s*=\s*(?P<content>[0-9\.]+)\s*$')
REGEX_ATOMDEF = re.compile('^(?P<tabs>\t*)(?P<atom>[a-zA-Z0-9_/]+)\\{?\\s*$')
REGEX_ABSOLUTE_PROCDEF = re.compile('^(?P<tabs>\t*)(?P<atom>[a-zA-Z0-9_/]+)/(?P<proc>[a-zA-Z0-9_]+)\((?P<args>.*)\)\\{?\s*$')
REGEX_RELATIVE_PROCDEF = re.compile('^(?P<tabs>\t*)(?P<proc>[a-zA-Z0-9_]+)\((?P<args>.*)\)\\{?\\s*$')
REGEX_LINE_COMMENT = re.compile('//.*?$')

def debug(filename, line, path, message):
    print('{0}:{1}: {2} - {3}'.format(filename, line, '/'.join(path), message))

class ObjectTree:
    reserved_words = ('else', 'break', 'return', 'continue', 'spawn', 'proc')
    stdlib_files=(
        'dm_std.dm',
        'atom_defaults.dm'
    )
    def __init__(self):
        self.LoadedStdLib=False
        self.Atoms = {}
        self.Tree = Atom('')
        self.cpath = []
        self.popLevels = []
        self.InProc = []
        self.pindent = 0  # Previous Indent
        self.ignoreLevel = []  # Block Comments
        self.ignoreStartIndent = -1
        self.debugOn = True
        self.ignoreDebugOn = False
        self.ignoreTokens = {
            '/*':'*/',
            '{"':'"}'
        }
        self.defines={}
        self.defineMatchers={}
        
        nit = self.ignoreTokens.copy()
        for start, stop in self.ignoreTokens.iteritems():
            nit[stop] = None
        self.ignoreTokens = nit
    
    def ProcessMultiString(self, filename, line, ignoreLevels, current_buffer):
        return '"{0}"'.format(current_buffer)
    
    def SplitPath(self, string):
        o = []
        buf = []
        inProc = False
        for chunk in string.split('/'):
            if not inProc: 
                if '(' in chunk and ')' not in chunk:
                    inProc = True
                    buf += [chunk]
                else:
                    o += [chunk]
            else:
                if ')' in chunk:
                    o += ['/'.join(buf + [chunk])]
                    inProc = False
                else:
                    buf += [chunk]
        return o
        
    def ProcessFilesFromDME(self, dmefile='baystation12.dme', ext='.dm'):
        if not self.LoadedStdLib:
            stdlib_dir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
            stdlib_dir=os.path.join(stdlib_dir,'stdlib')
            for filename in self.stdlib_files:
                self.ProcessFile(os.path.join(stdlib_dir,filename))
                
        print('--- Parsing DM files...')
        numFilesTotal = 0
        rootdir = os.path.dirname(dmefile)
        with open(dmefile, 'r') as dmeh:
            for line in dmeh:
                if line.startswith('#include'):
                    inString = False
                    # escaped=False
                    filename = ''
                    for c in line:
                        """
                        if c == '\\' and not escaped:
                            escaped = True
                            continue
                        if escaped:
                            if
                            escaped = False
                            continue
                        """         
                        if c == '"':
                            inString = not inString
                            if not inString:
                                filepath = os.path.join(rootdir, filename)
                                if filepath.endswith(ext):
                                    # print('Processing {0}...'.format(filepath))
                                    self.ProcessFile(filepath)
                                    numFilesTotal += 1
                                filename = ''
                            continue
                        else:
                            if inString:
                                filename += c
        self.MakeTree()
                    
    def ProcessAtom(self, filename, ln, line, atom, atom_path, numtabs, procArgs=None):
        # Reserved words that show up on their own
        if atom in ObjectTree.reserved_words:
            return
        
        # Other things to ignore (false positives, comments)
        if atom.startswith('var/') or atom.startswith('//'):
            return
        
        # Things part of a string or list.
        if numtabs > 0 and atom.strip().startswith('/'):
            return
        
        # Was used to debug a weird path resolution issue with mecha boards.
        # if line.strip()=='/obj/machinery/disposalpipe':
        #    debugOn = True
        if self.debugOn: print('{} > {}'.format(numtabs, line.rstrip()))
        
        if numtabs == 0:
            self.cpath = atom_path
            if self.cpath[0] != '':
                self.cpath.insert(0, '')
            self.popLevels = [len(self.cpath)]
            if self.debugOn: debug(filename, ln, self.cpath, '0 - ' + repr(atom_path))
            
        elif numtabs > self.pindent:
            self.cpath += atom_path
            self.popLevels += [len(atom_path)]
            if self.debugOn: debug(filename, ln, self.cpath, '>')
            
        elif numtabs < self.pindent:
            if self.debugOn: print('({} - {})={}: {}'.format(self.pindent, numtabs, self.pindent - numtabs, repr(self.cpath)))
            for _ in range(self.pindent - numtabs + 1):
                popsToDo = self.popLevels.pop()
                if self.debugOn: print(' pop {} {}'.format(popsToDo, self.popLevels))
                for i in range(popsToDo):
                    self.cpath.pop()
                    if self.debugOn: print('  pop {}/{}: {}'.format(i + 1, popsToDo, repr(self.cpath)))
            self.cpath += atom_path
            self.popLevels += [len(atom_path)]
            if self.debugOn: debug(filename, ln, self.cpath, '<')
            
        elif numtabs == self.pindent:
            levelsToPop = self.popLevels.pop()
            for i in range(levelsToPop):
                self.cpath.pop()
            self.cpath += atom_path
            self.popLevels += [len(atom_path)]
            if self.debugOn: print('popLevels: ' + repr(self.popLevels))
            if self.debugOn: debug(filename, ln, self.cpath, '==')
            
        npath = '/'.join(self.cpath)
        if npath not in self.Atoms:
            if procArgs is not None:
                #print(npath)
                assert npath.endswith(')')
                self.Atoms[npath] = Proc(npath, procArgs, filename, ln)
            else:
                self.Atoms[npath] = Atom(npath, filename, ln)
            #if self.debugOn: print('Added ' + npath)
        self.pindent = numtabs
    
    def ProcessFile(self, filename):
        self.cpath = []
        self.popLevels = []
        self.pindent = 0  # Previous Indent
        self.ignoreLevel = []
        self.debugOn = False
        self.ignoreDebugOn = False
        self.ignoreStartIndent = -1
        self.ignoringProc = ''
        with open(filename, 'r') as f:
            ln = 0
            ignoreLevel = []
            
            for line in f:
                ln += 1
                
                skipNextChar = False
                nl = ''
                    
                line = line.rstrip()
                line_len = len(line)
                for i in xrange(line_len):
                    c = line[i]
                    nc = ''
                    if line_len > i + 1:
                        nc = line[i + 1]
                    tok = c + nc
                    # print(tok)
                    if skipNextChar:
                        if self.ignoreDebugOn: print('Skipping {}.'.format(repr(tok)))
                        skipNextChar = False
                        continue
                    if tok == '//':
                        # if self.ignoreDebugOn: debug(filename,ln,self.cpath,'{} ({})'.format(tok,len(ignoreLevel)))
                        if len(ignoreLevel) == 0:
                            break
                    if tok in self.ignoreTokens:
                        pc = ''
                        if i > 0:
                            pc = line[i-1]
                        if tok=='{"' and pc=='"':
                            continue
                        # if self.ignoreDebugOn: print(repr(self.ignoreTokens[tok]))
                        stop = self.ignoreTokens[tok]
                        if stop == None:  # End comment
                            if len(ignoreLevel) > 0:
                                if ignoreLevel[-1] == tok:
                                    skipNextChar = True
                                    ignoreLevel.pop()
                                    continue
                                else:
                                    continue
                        else:  # Start comment
                            skipNextChar = True
                            ignoreLevel += [stop]
                            continue
                        if self.ignoreDebugOn: debug(filename, ln, self.cpath, '{} ({})'.format(tok, len(ignoreLevel)))
                    if len(ignoreLevel) == 0:
                        nl += c
                if line != nl:
                    if self.ignoreDebugOn: print('IN : ' + line)
                    line = nl
                    if self.ignoreDebugOn: print('OUT: ' + line)
                    
                if len(ignoreLevel) > 0:
                    continue
                
                line = REGEX_LINE_COMMENT.sub('', line)
                
                if line.strip() == '':
                    continue
                
                if line.startswith("#"):
                    if line.endswith('\\'): continue
                    if line.startswith('#define'):
                        # #define SOMETHING Value
                        defineChunks = line.split(None,3)
                        if len(defineChunks)==2:
                            defineChunks+=[1]
                        #print(repr(defineChunks))
                        try:
                            if '.' in defineChunks[2]:
                                self.defines[defineChunks[1]]=BYONDValue(float(defineChunks[2]),filename,ln)
                            else:
                                self.defines[defineChunks[1]]=BYONDValue(int(defineChunks[2]),filename,ln)
                        except:
                            self.defines[defineChunks[1]]=BYONDString(defineChunks[2],filename,ln)
                    elif line.startswith('#undef'):
                        undefChunks = line.split(' ',2)
                        if undefChunks[1] in self.defines:
                            del self.defines[undefChunks[1]]
                    else:
                        chunks=line.split(' ')
                        print('BUG: Unhandled preprocessor directive {} in {}:{}'.format(chunks[0],filename,ln))
                    continue
                else:
                    for key,define in self.defines.items():
                        if key in line:
                            if key not in self.defineMatchers:
                                self.defineMatchers[key]=re.compile(r'\b'+key+r'\b')
                            newline=self.defineMatchers[key].sub(str(define.value),line)
                            #print('OLD: {}'.format(line))
                            #print('PPD: {}'.format(newline))
                            line=newline
                
                m = REGEX_TABS.match(line)
                if m is not None:
                    numtabs = len(m.group('tabs'))
                    if self.ignoreStartIndent > -1 and self.ignoreStartIndent < numtabs:
                        if self.debugOn: print('TABS: {} ? {} - {}: {}'.format(numtabs, self.ignoreStartIndent, self.ignoringProc, line))
                        continue
                    else:
                        if self.debugOn and self.ignoreStartIndent > -1: print('BREAK ({} -> {}): {}'.format(self.ignoreStartIndent, numtabs, line))
                        self.ignoreStartIndent = -1
                        self.ignoringProc = ''
                else:
                    if self.debugOn and self.ignoreStartIndent > -1: print('BREAK ' + line)
                    self.ignoreStartIndent = -1
                    self.ignoringProc = ''
                
                m = REGEX_ATOMDEF.match(line)
                if m is not None:
                    numtabs = len(m.group('tabs'))
                    atom = m.group('atom')
                    atom_path = self.SplitPath(atom)
                    self.ProcessAtom(filename, ln, line, atom, atom_path, numtabs)
                    continue
                
                m = REGEX_ABSOLUTE_PROCDEF.match(line)
                if m is not None:
                    numtabs = len(m.group('tabs'))
                    atom = '{0}/{1}({2})'.format(m.group('atom'), m.group("proc"), m.group('args')) 
                    atom_path = self.SplitPath(atom)
                    #print('PROCESSING ABS PROC AT INDENT > ' + str(numtabs) + " " + atom+" -> "+repr(atom_path))
                    self.ProcessAtom(filename, ln, line, atom, atom_path, numtabs, m.group('args').split(','))
                    self.ignoreStartIndent = numtabs
                    self.ignoringProc = atom
                    continue
                
                m = REGEX_RELATIVE_PROCDEF.match(line)
                if m is not None:
                    numtabs = len(m.group('tabs'))
                    atom = '{}({})'.format(m.group("proc"), m.group('args')) 
                    atom_path = self.SplitPath(atom)
                    #print('IGNORING RELATIVE PROC AT INDENT > ' + str(numtabs) + " " + line)
                    self.ProcessAtom(filename, ln, line, atom, atom_path, numtabs, m.group('args').split(','))
                    self.ignoreStartIndent = numtabs
                    self.ignoringProc = atom
                    continue
                
                path = '/'.join(self.cpath)
                if len(self.cpath) > 0 and 'proc' in self.cpath:
                    continue
                m = REGEX_VARIABLE_STRING.match(line)
                if m is not None:
                    if path not in self.Atoms:
                        self.Atoms[path] = Atom(path)
                    name = m.group('variable')
                    content = m.group('content')
                    qmark = m.group('qmark')
                    if self.debugOn: print('{3}: var/{0} = {1}{2}{1}'.format(name, qmark, content,path))
                    if qmark == '"':
                        self.Atoms[path].properties[name] = BYONDString(content, filename, ln)
                    else:
                        self.Atoms[path].properties[name] = BYONDFileRef(content, filename, ln)
                m = REGEX_VARIABLE_NUMBER.match(line)
                if m is not None:
                    if path not in self.Atoms:
                        self.Atoms[path] = Atom(path)
                    name = m.group('variable')
                    content = m.group('content')
                    if self.debugOn: print('var/{0} = {1}'.format(name, content))
                    if '.' in content:
                        self.Atoms[path].properties[name] = BYONDValue(float(content), filename, ln)
                    else:
                        self.Atoms[path].properties[name] = BYONDValue(int(content), filename, ln)
    def MakeTree(self):
        print('Generating Tree...')
        self.Tree = Atom('/')
        with open('objtree.txt', 'w') as f:
            for key in sorted(self.Atoms):
                f.write("{0}\n".format(key))
                atom = self.Atoms[key]
                cpath = []
                cNode = self.Tree
                fullpath = self.SplitPath(atom.path)
                truncatedPath = fullpath[1:]
                for path_item in truncatedPath:
                    cpath += [path_item]
                    cpath_str = '/'.join([''] + cpath)
                    # if path_item == 'var':
                    #    if path_item not in cNode.properties:
                    #        cNode.properties[fullpath[-1]]='???'
                    if path_item not in cNode.children:
                        if cpath_str in self.Atoms:
                            cNode.children[path_item] = self.Atoms[cpath_str]
                        else:
                            if '(' in path_item:
                                cNode.children[path_item] = Proc('/'.join([''] + cpath),[])
                            else:
                                cNode.children[path_item] = Atom('/'.join([''] + cpath))
                        cNode.children[path_item].parent = cNode
                    cNode = cNode.children[path_item]
        self.Tree.InheritProperties()
        print('Processed {0} atoms.'.format(len(self.Atoms)))
        self.Atoms = {}
        
    def GetAtom(self, path):
        if path in self.Atoms:
            return self.Atoms[path]
        
        cpath = []
        cNode = self.Tree
        fullpath = path.split('/')
        truncatedPath = fullpath[1:]
        for path_item in truncatedPath:
            cpath += [path_item]
            if path_item not in cNode.children:
                print('Unable to find {0} (lost at {1})'.format(path, cNode.path))
                print(repr(cNode.children.keys()))
                return None
            cNode = cNode.children[path_item]
        # print('Found {0}!'.format(path))
        self.Atoms[path] = cNode
        return cNode
        
