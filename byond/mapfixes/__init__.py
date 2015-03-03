import logging, glob, os, sys
from .base import MapFix, GetDependencies

_log = logging.getLogger('byond.mapfixes')

def Load():
    _log.info('Loading MapFix Modules...')
    for f in glob.glob(os.path.dirname(__file__) + "/*.py"):
        modName = 'byond.mapfixes.' + os.path.basename(f)[:-3]
        _log.debug(' Loading module ' + modName)
        mod = __import__(modName)
        for attr in dir(mod):
            if not attr.startswith('_'):
                #print('  {} = {}'.format(attr,getattr(mod, attr)))
                globals()[attr] = getattr(mod, attr)
                
def GetFixesForNS(namespaces, load_dependencies=True):
    selected = [None] + namespaces
    depends = GetDependencies()
    if load_dependencies:
        changed = True
        while changed:
            changed = False
            for cat in selected:
                if cat is None: continue  # Global namespace is always needed.
                _log.debug('Checking dependencies for {}...'.format(cat))
                if cat in depends:
                    for newcat in depends[cat]:
                        if newcat not in selected:
                            _log.debug('Selected dependency {} (required by {})'.format(newcat,cat))
                            selected += [newcat]
                            changed = True
    o = []
    for cat in selected:
        for _, val in MapFix.all[cat].items():
            o += [val()]
    return o
