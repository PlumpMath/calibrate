from __future__ import division
from panda3d.core import Point2, Point3
import random
import numpy as np
# generate positions
# need to:
# a. return position according to a key press
# b. return position randomly from a large set - each point must be sampled x times
# c. return position from a large set in a fixed order
# make position an object?
# make a matrix of large_set * how ever many times per point, and
# remove positions as we use them
# basically same thing for non-random, non-key, but pull out in order
# projector resolution
# 1024 x 768
# normal panda window resolution (size)
# 800 x 600

class Positions:
    def __init__(self, CONFIG=None):
        if not CONFIG:
            CONFIG = {}
            execfile('config.py', CONFIG)
        # normal panda3d coordinates
        #self.small_set = [(-10, -10), (0, -10), (10, -10), (-10, 0), (0, 0), (10, 0), (-10, 10), (0, 10), (10, 10), ]
        # pixels, top left is 0,0, bottom right is 1024, -768, for projector
        self.res = CONFIG['WIN_RES']
        self.screen = CONFIG['SCREEN']
        self.v_dist = CONFIG['VIEW_DIST']
        if not self.res or self.res == 'Test':
            #print 'test'
            # assume testing, small window
            self.res = (800, 600)

        # limits are in pixels so max degree * pixels per degree
        x = CONFIG['MAX_DEGREES_X'] * self.visual_angle()[0]
        y = CONFIG['MAX_DEGREES_Y'] * self.visual_angle()[1]
        #print x
        #print y

        x_range = np.linspace(x, -x, 3)
        y_range = np.linspace(y, -y, 3)
        # for small set order is important, since these will be mapped to the number keys
        self.small_set = [(i, j) for j in y_range for i in x_range]
        self.small_set.reverse()

        x_range = np.linspace(x, -x, CONFIG['X_POINTS'])
        y_range = np.linspace(y, -y, CONFIG['Y_POINTS'])
        self.large_set = [(i, j) for i in x_range for j in y_range]
        #print self.large_set

        self.repeat = CONFIG['POINT_REPEAT']

    def get_key_position(self, depth, key=None):
        #print 'get key position', key
        pos = Point2(self.small_set[key-1])
        position = (pos.getX(), depth, pos.getY())
        #print 'position in position', position
        return position

    def get_position(self, depth, mode=None):
        # default is not random, large set
        if not mode:
            control_set = self.large_set
            for i in control_set:
                #print 'get non-random point'
                pos = Point2(i)
                #print 'pos in positions', pos
                yield (pos.getX(), depth, pos.getY())
        elif mode == 'small':
            control_set = self.small_set
            for i in control_set:
                pos = Point2(i)
                yield (pos.getX(), depth, pos.getY())
        else:
            control_set = self.large_set * self.repeat
            while len(control_set) > 0:
                pos = Point2(control_set.pop(random.randrange(len(control_set))))
                yield (pos.getX(), depth, pos.getY())

    def get_degree_positions(self, depth):
        # give positions 5 degrees further out every time
        degree = 0
        while degree < 40:
            if degree == 0:
                #print 'yup'
                pos = Point2(0, 0)
                yield (pos.getX(), depth, pos.getY())
            else:
                pix_per_deg = self.visual_angle()
                #print pix_per_deg
                pixels = [i * degree for i in pix_per_deg]
                #print 'x?', pixels[0]
                #print 'y?', pixels[1]
                x = [pixels[0], -pixels[0], 0, 0]
                y = [0, 0, pixels[1], -pixels[1]]
                for i in range(4):
                    pos = Point2(x[i],y[i])
                    yield (pos.getX(), depth, pos.getY())
            degree += 5

    def visual_angle(self):
        #print self.res
        #print self.screen
        #print self.v_dist
        self.pixel = [0, 0]
        self.deg_per_pix = [0, 0]
        self.pix_per_deg = [0, 0]
        self.pixel[0] = self.screen[0]/self.res[0]
        #print self.pixel
        self.pixel[1] = self.screen[1]/self.res[1]
        #print self.pixel[0]/(2*self.v_dist)
        self.deg_per_pix[0] = (2 * np.arctan(self.pixel[0]/(2 * self.v_dist))) * (180/np.pi)
        self.deg_per_pix[1] = (2 * np.arctan(self.pixel[1]/(2 * self.v_dist))) * (180/np.pi)
        self.pix_per_deg[0] = 1 / self.deg_per_pix[0]
        self.pix_per_deg[1] = 1 / self.deg_per_pix[1]
        #print self.pix_per_deg, self.deg_per_pix
        return self.pix_per_deg