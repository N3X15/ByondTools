#!/usr/bin/env python
'''
Created on Feb 28, 2014 to test a bug in DreamMaker.

Requires arial font.
'''
from byond.DMI import DMI, State
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def np_from_img(fname):
    return np.asarray(Image.open(fname), dtype=np.float32)

def save_as_img(ar, fname):
    Image.fromarray(ar.round().astype(np.uint8)).save(fname)

def norm(ar):
    return 255.*np.absolute(ar)/np.max(ar)

DOWN=1
UP=2
LEFT=4
RIGHT=8

def shift(oldf,newf,x,y,size,dir,iters=1):
    ox,oy=x,y
    
    for _ in range(iters):
        if dir & DOWN:
            y += 1
        if dir & UP:
            y -= 1
        if dir & LEFT:
            x -= 1
        if dir & RIGHT:
            x += 1
        # Barrel shift
        if x >= size[0]:
            x = 0
        elif x < 0:
            x = size[0]-1
        if y >= size[1]:
            y = 0
        elif y < 0:
            y = size[1]-1
        
    newf[x,y]=oldf[ox,oy]
    
def layer1_op(oldf,newf,x,y,size):
    shift(oldf,newf,x,y,size,DOWN|LEFT,1)
    
def layer2_op(oldf,newf,x,y,size):
    shift(oldf,newf,x,y,size,DOWN|LEFT,2)

def animate_layer(initial_frame,op,nframes):
    '''
    :param initial_frame Image: Initial frame of the animation.
    :param op callback:
    :param nframes int: Number of frames to generate
    '''
    if initial_frame.mode != 'RGBA':
        image = initial_frame.convert('RGBA')
    frames=[]
    for i in range(nframes):
        if i == 0:
            frames += [initial_frame]
        else:
            oldf = frames[i-1]
            oldp=oldf.load()
            newf = Image.new('RGBA',oldf.size)
            newp=newf.load()
            for x in range(oldf.size[0]):
                for y in range(oldf.size[1]):
                    op(oldp,newp,x,y,oldf.size)
            frames+=[newf]
    return frames

def makeDMI():
    
    dmi = DMI('snowfx.dmi')
    
    # LAYER 1
    state_name='snowlayer1'
    state=State(state_name)
    state.dirs=1
    state.frames=31
    state.icons=animate_layer(Image.open('snow1.png'),layer1_op,31)
    # Add state to DMI
    dmi.states[state_name]=state
    
    # LAYER 2
    state_name='snowlayer2'
    state=State(state_name)
    state.dirs=1
    state.frames=15
    state.icons=animate_layer(Image.open('snow2.png'),layer2_op,15)
    # Add state to DMI
    dmi.states[state_name]=state
    
    #save
    dmi.save('snowfx.dmi', sort=False)
if __name__ == '__main__':
    makeDMI()
