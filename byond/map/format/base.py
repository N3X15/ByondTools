import logging

_log = logging.getLogger("byond.mapformat")
# Decorator
class MapFormat(object):
    all = {}
    def __init__(self, ext, _id=None):
        self.id = _id
        self.extension = ext
    def __call__(self, c):
        if self.id is None:
            fname_p = c.__name__
            self.id = fname_p
        _log.info('Adding Map Format "{}" (.{})...'.format(self.id,self.extension))
        if self.extension in MapFormat.all:
            _log.warn('*.{} FILES ARE ALREADY HANDLED BY {}!'.format(self.extension,self.id))
        MapFormat.all[self.extension] = c
        return c
    
def GetMapFormat(_map,ext):
    f = MapFormat.all.get(ext.strip('.'),None)
    if f is None:
        _log.error('Unable to find MapFormat for {}.'.format(ext))
    return f(_map)
    
class BaseMapFormat:
    def __init__(self, _map):
        self.map = _map
        self.missing_atoms = set()
        
    def Load(self, filename, **kwargs):
        return
    
    def Save(self, filename, **kwargs):
        return