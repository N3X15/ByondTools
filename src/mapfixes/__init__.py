import logging, glob, os
from .base import MapFix

_dependencies = {}

def Load():
    logging.info('Loading MapFix Modules...')
    for f in glob.glob(os.path.dirname(__file__) + "/*.py"):
        modName = 'mapfixes.' + os.path.basename(f)[:-3]
        logging.info(' Loading module ' + modName)
        mod = __import__(modName)
        if 'dependencies' in dir(mod):
            for dependee, dependencies in mod.dependencies.items():
                if dependee not in _dependencies:
                    _dependencies[dependee] = []
                _dependencies[dependee] += dependencies
        for attr in dir(mod):
            if not attr.startswith('_'):
                globals()[attr] = getattr(mod, attr)
                
def GetFixesForNS(namespaces, load_dependencies=True):
    selected = [None] + namespaces
    if load_dependencies:
        changed = True
        while changed:
            changed = False
            for cat in selected:
                if cat is None: continue  # Global namespace is always needed.
                if cat in _dependencies:
                    for newcat in _dependencies[cat]:
                        if newcat not in selected:
                            selected += newcat
                            changed = True
    o = []
    for cat in selected:
        for _, val in MapFix.all[cat].items():
            o += [val()]
    return o
