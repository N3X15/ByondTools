#!/usr/bin/env python
'''
Run next to a dmi_config.yml file.

Usage:
    $ python dmi_compile.py

dmi_compile.py - Generates a large DMI from several smaller DMIs.

Specifically used for making icons/mob/items_(left|right)hand.dmi in SS13.

Copyright 2013 Rob "N3X15" Nelson <nexis@7chan.org>

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
import os, sys, logging, yaml

from byond.DMI import DMI
from byond.DMI.utils import compare_all

def fail(msg):
    logging.critical(msg)
    sys.exit(1)
    
def requireOption(directive, option, config):
    if option not in config:
        fail('"{0}" directive doesn\'t have "{1}" option in its configuration. Check your dmi_config.yml.'.format(directive,option))
    
def buildDMIFromDir(directory, output):
    dmi = DMI(output)
    logging.info('Creating {0}...'.format(output))
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.dmi') and not filename.endswith('.new.dmi'):
                filepath = os.path.join(root, filename)
                #logging.info('Adding {0}...'.format(filename, output))
                subdmi = DMI(filepath)
                subdmi.loadAll()
                if subdmi.icon_height != 32 or subdmi.icon_width != 32:
                    logging.warn('Skipping {0} - Invalid icon size.'.format(filepath))
                changes = 0
                for state_name in subdmi.states:
                    if state_name in dmi.states:
                        logging.warn('Skipping state {0}:{1} - State exists.'.format(filepath, subdmi.states[state_name].displayName()))
                        continue
                    dmi.states[state_name] = subdmi.states[state_name]
                    changes += 1
                #logging.info('Added {0} states.'.format(changes))
    # save
    logging.info('Saving {0} states to {1}...'.format(len(dmi.states), output))
    dmi.save(output)
    
def handleBuildDMI(config):
    requireOption('buildDMI', 'dir', config)
    requireOption('buildDMI', 'output', config)
    buildDMIFromDir(config['dir'], config['output'])
    
def handleCompare(config):
    requireOption("compare", 'left', config)
    requireOption("compare", 'right', config)
    requireOption("compare", 'report', config)
    compare_all(config['left'], config['right'], config['report'], None, newfile_theirs=False, newfile_mine=False, check_changed=False)
    
if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(levelname)-8s]: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO  # ,
        # filename='logs/main.log',
        # filemode='w'
    )
    
    directives={
        'buildDMI':handleBuildDMI,
        'compare':handleCompare
    }
    
    yml = []
    with open('dmi_config.yml','r') as f:
        yml = yaml.load(f)
    print(repr(yml))
    for listItem in yml:
        for directive,config in listItem.items():
            if directive not in directives:
                fail('Unknown directive '+directive)
            instruction = directives[directive]
            instruction(config)
