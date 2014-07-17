'''
World simulation.  Like Map but high-performance, theoretically.

MIT goes here.

Created on Jun 15, 2014

@author: Rob "N3X15" Nelson <nexisentertainment@gmail.com>
'''

from map import Map, MapLayer

class World(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        self.instances=[]
        self.tiles={}
        self.z_constraints=[]
        
        # :type loaded_map: Map
        self.loaded_map = Map()