#------------------------------------------------------------------------------
# Originally cxfreeze-postinstall
#   Script run after installation on Windows to fix up the Python location in
# the script as well as create batch files.
#------------------------------------------------------------------------------

import distutils.sysconfig
import glob, os, sys

vars = distutils.sysconfig.get_config_vars()
prefix = vars["prefix"]
python = sys.executable #os.path.join(prefix, "python.exe")

scriptDir = ''
# Almost verbatim from Pip's sourcecode.
if sys.platform == 'win32':
    scriptDir = os.path.join(sys.prefix, 'Scripts')
else:
    # This is different because it's just plain wrong on Debian.
    #scriptDir = os.path.join(sys.prefix, 'bin')
    scriptDir = os.path.curdir

# Keep in sync with setup.py.
scripts = [
    'dmm',
    'dmi',
	'dmi_compile',
    'dmindent',
    'dmmrender',
    'dmmfix',
    'ss13_gettechlevels',
    
    # Our post-install.  Now run on Linux, as well.
    "byondtools-postinstall"
]
print(" Checking {} for things to fix...".format(scriptDir))
for fileName in glob.glob(os.path.join(scriptDir, "*.py")):
    # skip already created batch files if they exist
    name, ext = os.path.splitext(os.path.basename(fileName))
    if name not in scripts or name == 'byondtools-postinstall':
        continue

    print('Running post-install for {}.'.format(name))
    # copy the file with the first line replaced with the correct python
    fullName = os.path.join(scriptDir, fileName)
    strippedName = os.path.join(scriptDir, name)
    lines = open(fullName).readlines()
    startidx=1
    if not lines[0].strip().startswith('#!'):
        print('WARNING: {} does not have a shebang.'.format(name))
        startidx=0
    
    targetFile = strippedName
    if sys.platform == 'win32':
        targetFile = fullName
    with open(targetFile, "w") as outFile:
        outFile.write("#!{}\n".format(python)) # Not sure why this is done on Windows...
        for line in lines[startidx:]:
            outFile.write(line.rstrip('\r\n \t')+"\n") # Shit happens on Linux if this isn't done.

    if sys.platform == 'win32':
        # create the batch file
        batchFileName = strippedName + ".bat"
        command = "{} {} %*".format(python, targetFile)
        open(batchFileName, "w").write("@echo off\n\n{}".format(command))
    else:
        os.chmod(strippedName, 0755)
        print('CHMOD 755 {}'.format(strippedName))
