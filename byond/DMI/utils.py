'''
Copyright 2013-2015 Rob "N3X15" Nelson <nexis@7chan.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import os, logging, sys, traceback, fnmatch

from . import DMI

# TODO: Need to switch to logging. - N3X

def compare(theirsfile, minefile, parser, reportstream, **kwargs):
    # print('\tD %s -> %s' % (theirsfile, minefile))
    theirs = []
    theirsDMI = None
    mine = []
    mineDMI = None
    states = []
    
    new2mineFilename = minefile.replace('.dmi', '.new.dmi')
    new2theirsFilename = theirsfile.replace('.dmi', '.new.dmi')
    
    new2mine=None
    if os.path.isfile(new2mineFilename):
        os.remove(new2mineFilename)
    if kwargs.get('newfile_mine',True):
        new2mine = DMI(new2mineFilename)
    
    new2theirs=None
    if os.path.isfile(new2theirsFilename):
        os.remove(new2theirsFilename)
    if kwargs.get('newfile_theirs',False):
        new2theirs = DMI(new2theirsFilename)
    
    
    o = ''
    if(os.path.isfile(theirsfile)):
        try:
            theirsDMI = DMI(theirsfile)
            theirsDMI.loadAll()
            theirs = theirsDMI.states
        except SystemError as e:
            print("!!! Received SystemError in %s, halting: %s" % (theirs.filename, traceback.format_exc(e)))
            print('# of cells: %d' % len(theirs.states))
            print('Image h/w: %s' % repr(theirs.size))
            sys.exit(1)
        except Exception as e:
            print("Received error, continuing: %s" % traceback.format_exc())
            o += "\n {0}: Received error, continuing: {1}".format(theirsfile, traceback.format_exc())
        for stateName in theirs:
            if stateName not in states:
                states.append(stateName)
    if(os.path.isfile(minefile)):
        try:
            mineDMI = DMI(minefile)
            mineDMI.loadAll()
            mine = mineDMI.states
        except SystemError as e:
            print("!!! Received SystemError in %s, halting: %s" % (mine.filename, traceback.format_exc(e)))
            print('# of cells: %d' % len(mine.states))
            print('Image h/w: %s' % repr(mine.size))
            sys.exit(1)
        except Exception as e:
            print("Received error, continuing: %s" % traceback.format_exc())
            o += "\n {0}: Received error, continuing: {1}".format(minefile, traceback.format_exc())
        for stateName in mine:
            if stateName not in states:
                states.append(stateName)
    for state in sorted(states):
        inTheirs = state in theirs
        inMine = state in mine 
        if inTheirs and not inMine:
            o += '\n + {1}'.format(minefile, state)
            if new2mine is not None:
                new2mine.states[state] = theirsDMI.states[state]
        elif not inTheirs and inMine:
            o += '\n - {1}'.format(theirsfile, state)
            if new2theirs is not None:
                new2theirs.states[state] = mineDMI.states[state]
        elif inTheirs and inMine:
            if theirs[state].ToString() != mine[state].ToString():
                o += '\n - {0}: {1}'.format(mine[state].displayName(), mine[state].ToString())
                o += '\n + {0}: {1}'.format(theirs[state].displayName(), theirs[state].ToString())
            elif kwargs.get('check_changed',True):
                diff_count=0
                for i in xrange(len(theirs[state].icons)):
                    theirF = theirs[state].icons[i]
                    myF = theirs[state].icons[i] 
                    
                    theirData = list(theirF.getdata())
                    myData = list(myF.getdata())
                    #diff = []
                    
                    for i in xrange(len(theirData)):
                        dr = theirData[i][0] - myData[i][0]
                        dg = theirData[i][1] - myData[i][1]
                        db = theirData[i][2] - myData[i][2]
                        #diff[idx] = (abs(dr), abs(dg), abs(db))
                        if((dr != 0) or (dg != 0) or (db != 0)):
                            diff_count += 1
                            break
                if diff_count > 0:
                    o += '\n ! {0}: {1} frames differ'.format(theirs[state].displayName(), diff_count)
                    if new2mine is not None:
                        new2mine.states[state] = theirsDMI.states[state]
                    if new2theirs is not None:
                        new2theirs.states[state] = mineDMI.states[state]
    if o != '': 
        reportstream.write('\n--- {0}'.format(theirsfile))
        reportstream.write('\n+++ {0}'.format(minefile))
        reportstream.write(o)
        
        if new2mine is not None:
            if len(new2mine.states) > 0:
                new2mine.save(new2mineFilename)
            else:
                if os.path.isfile(new2mineFilename):
                    os.remove(new2mineFilename)
                    #print('RM {0}'.format(new2mineFilename))
        if new2theirs is not None:
            if len(new2theirs.states) > 0:
                new2theirs.save(new2theirsFilename)
            else:
                if os.path.isfile(new2theirsFilename):
                    os.remove(new2theirsFilename)
                    #print('RM {0}'.format(new2theirsFilename))
                    
def get_dmi_data(path, dest, parser):
    if(os.path.isfile(path)):
        dmi = DMI(path)
        with open(dest, 'w') as f:
            f.write(dmi.getHeader())
                
def set_dmi_data(path, headerFile, parser):
    if(os.path.isfile(path)):
        dmi = DMI(path)
        with open(headerFile, 'r') as f:
            dmi.setHeader(f.read(), path)

def make_dmi(path, dest, parser):
    if(os.path.isfile(path)):
        dmi = None
        try:
            dmi = DMI(dest)
            dmi.make(path)
            dmi.save(dest)
        except SystemError as e:
            print("!!! Received SystemError in %s, halting: %s" % (dmi.filename, traceback.format_exc(e)))
            print('# of cells: %d' % len(dmi.states))
            print('Image h/w: %s' % repr(dmi.size))
            sys.exit(1)
        except Exception as e:
            print("Received error, continuing: %s" % traceback.format_exc())

def make_dmi(path, dest, parser):
    if(os.path.isfile(path)):
        dmi = None
        try:
            dmi = DMI(dest)
            dmi.make(path)
            dmi.save(dest)
        except SystemError as e:
            print("!!! Received SystemError in %s, halting: %s" % (dmi.filename, traceback.format_exc(e)))
            print('# of cells: %d' % len(dmi.states))
            print('Image h/w: %s' % repr(dmi.size))
            sys.exit(1)
        except Exception as e:
            print("Received error, continuing: %s" % traceback.format_exc())

def disassemble(path, to, parser):
    print('\tD %s -> %s' % (path, to))
    if(os.path.isfile(path)):
        dmi = None
        try:
            dmi = DMI(path)
            dmi.extractTo(to, parser.suppress_post_process)
        except SystemError as e:
            print("!!! Received SystemError in %s, halting: %s" % (dmi.filename, traceback.format_exc(e)))
            print('# of cells: %d' % len(dmi.states))
            print('Image h/w: %s' % repr(dmi.size))
            sys.exit(1)
        except Exception as e:
            print("Received error, continuing: %s" % traceback.format_exc())

                    
def cleanup(subject):
    print('Cleaning...')
    for root, _, filenames in os.walk(subject):
        for filename in fnmatch.filter(filenames, '*.new.dmi'):
            path = os.path.join(root, filename)
            print('RM {0}'.format(path))
            os.remove(path)

def disassemble_all(in_dir, out_dir, parser):
    print('D_A %s -> %s' % (in_dir, out_dir))
    for root, dirnames, filenames in os.walk(out_dir):
        for filename in fnmatch.filter(filenames, '*.new.dmi'):
            path = os.path.join(root, filename)
            print('RM {0}'.format(path))
            os.remove(path)
    for root, dirnames, filenames in os.walk(in_dir):
        for filename in fnmatch.filter(filenames, '*.dmi'):
            path = os.path.join(root, filename)
            to = os.path.join(out_dir, path.replace(in_dir, '').replace(os.path.basename(path), ''))
            disassemble(path, to, parser)
    

def compare_all(left_dir, right_dir, report, parser, **kwargs):
    logging.info('Comparing {} vs. {}...'.format(left_dir, right_dir))
    with open(report, 'w') as report:
        report.write('# DMITool Difference Report: {0} {1}'.format(os.path.abspath(left_dir), os.path.abspath(right_dir)))
        for root, dirnames, filenames in os.walk(left_dir):
            for filename in fnmatch.filter(filenames, '*.dmi'):
                left = os.path.join(root, filename)
                right = os.path.join(right_dir, left.replace(left_dir, '').replace(os.path.basename(left), ''))
                right = os.path.join(right, filename)
                
                left = os.path.abspath(left)
                right = os.path.abspath(right)
                
                compare(left, right, parser, report, **kwargs)
