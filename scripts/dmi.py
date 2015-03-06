#!/usr/bin/env python
"""
DMI SPLITTER-UPPER THING

Makes merging sprites a hell of a lot easier.
by N3X15 <nexis@7chan.org>

Requires PIL
Written for Python 2.7.
"""

import sys, os, traceback, fnmatch, argparse

from byond.DMI import DMI
from byond.DMI.utils import *

args = ()
	
def main():
	opt = argparse.ArgumentParser()  # version='0.1')
	opt.add_argument('-p', '--suppress-post-processing', dest='suppress_post_process', default=False, action='store_true')
	command = opt.add_subparsers(help='The command you wish to execute', dest='MODE')
	
	_disassemble = command.add_parser('disassemble', help='Disassemble a single DMI file to a destination directory')
	_disassemble.add_argument('file', type=str, help='The DMI file to disassemble.', metavar='file.dmi')
	_disassemble.add_argument('destination', type=str, help='The directory in which to dump the resulting images.', metavar='dest/')
	
	_disassemble_all = command.add_parser('disassemble-all', help='Disassemble a directory of DMI files to a destination directory')
	_disassemble_all.add_argument('source', type=str, help='The DMI files to disassemble.', metavar='source/')
	_disassemble_all.add_argument('destination', type=str, help='The directory in which to dump the resulting images.', metavar='dest/')
	
	_compile = command.add_parser('compile', help='Compile a .dmi.mak file')
	_compile.add_argument('makefile', type=str, help='The .dmi.mak file to compile.', metavar='file.dmi.mak')
	_compile.add_argument('destination', type=str, help='The location of the resulting .dmi file.', metavar='file.dmi')
	
	_compare = command.add_parser('compare', help='Compare two DMI files and note the differences')
	_compare.add_argument('theirs', type=str, help='One side of the difference', metavar='theirs.dmi')
	_compare.add_argument('mine', type=str, help='The other side.', metavar='mine.dmi')
	
	_compare_all = command.add_parser('compare-all', help='Compare two DMI file directories and note the differences')
	_compare_all.add_argument('theirs', type=str, help='One side of the difference', metavar='theirs/')
	_compare_all.add_argument('mine', type=str, help='The other side.', metavar='mine/')
	_compare_all.add_argument('report', type=str, help='The file the report is saved to', metavar='report.txt')
	
	_get_dmi_data = command.add_parser('get-dmi-data', help='Extract DMI header')
	_get_dmi_data.add_argument('file', type=str, help='DMI file', metavar='file.dmi')
	_get_dmi_data.add_argument('dest', type=str, help='The file where the DMI header will be saved', metavar='dest.txt')
	
	_set_dmi_data = command.add_parser('set-dmi-data', help='Set DMI header')
	_set_dmi_data.add_argument('file', type=str, help='One side of the difference', metavar='file.dmi')
	_set_dmi_data.add_argument('metadata', type=str, help='DMI header file', metavar='metadata.txt')
	
	_set_dmi_data = command.add_parser('clean', help='Clean up temporary files and *.new.dmi files.')
	_set_dmi_data.add_argument('basedir', type=str, help='Starting directory', metavar='vgstation/')
	
	args = opt.parse_args()
	#print(args)
	if args.MODE == 'compile':
		make_dmi(args.makefile, args.destination, args)
	if args.MODE == 'compare':
		compare(args.theirs, args.mine, args, sys.stdout)
	if args.MODE == 'compare-all':
		compare_all(args.theirs, args.mine, args.report, args)
	elif args.MODE == 'disassemble':
		disassemble(args.file, args.destination, args)
	elif args.MODE == 'disassemble-all':
		disassemble_all(args.source, args.destination, args)
	elif args.MODE == 'get-dmi-data':
		get_dmi_data(args.file, args.dest, args)
	elif args.MODE == 'set-dmi-data':
		set_dmi_data(args.file, args.metadata, args)
	elif args.MODE == 'cleanup':
		cleanup(args.basedir, args)
	else:
		print('!!! Error, unknown MODE=%r' % args.MODE)



class ModeAction(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print('%s %s %s' % (namespace, values, option_string))
		namespace.MODE = self.dest
		namespace.args = values


if __name__ == '__main__':
	main()
