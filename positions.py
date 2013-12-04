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

# get constants from config file
#CONFIG = {}
#execfile('config.py', CONFIG)


class Positions:
    def __init__(self, CONFIG):
        self.small_set = [(-10, -10), (0, -10), (10, -10), (-10, 0), (0, 0), (10, 0), (-10, 10), (0, 10), (10, 10), ]
        x_range = np.linspace(-int(CONFIG['X_LIMITS']), int(CONFIG['X_LIMITS']), CONFIG['X_POINTS'])
        #print x_range
        y_range = np.linspace(-int(CONFIG['Y_LIMITS']), int(CONFIG['Y_LIMITS']), CONFIG['Y_POINTS'])
        self.large_set = [(i, j) for i in x_range for j in y_range]
        #self.large_set = [(i, j) for i in range(-10, 11, 5) for j in range(-10, 11, 5)]


    def get_key_position(self, depth, key=None):
        #print 'get key position', key
        pos = Point2(self.small_set[key-1])
        position = (pos.getX(), depth, pos.getY())
        #print 'position in position', position
        return position

    def get_position(self, depth, do_random=None):
        # default is not random
        if not do_random:
            control_set = self.large_set
            for i in control_set:
                #print 'get random point'
                pos = Point2(i)
                #print 'pos in positions', pos
                yield (pos.getX(), depth, pos.getY())
        else:
            control_set = self.large_set * CONFIG['POINT_REPEAT']
            while len(control_set) > 0:
                pos = Point2(control_set.pop(random.randrange(len(control_set))))
                yield (pos.getX(), depth, pos.getY())
