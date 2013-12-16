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
        resolution = CONFIG['WIN_RES']
        if not resolution:
            # assume testing, small window
            resolution = (800, 600)
        print resolution
        #padding = 100  # number of pixels from points to outer edge of screen
        padding = CONFIG['PADDING']
        #x_range = np.linspace(padding, int(resolution[0]) - padding, 3)
        #y_range = np.linspace(-padding, -int(resolution[1]) + padding, 3)
        x = resolution[0]/2 - padding
        y = resolution[1]/2 - padding
        x_range = np.linspace(x, -x, 3)
        y_range = np.linspace(y, -y, 3)
        self.small_set = [(i, j) for i in x_range for j in y_range]

        #self.small_set = [(100, -100), (500, -100), (900, -100), (100, 200), (500, 200), (900, 900), (0, 100), (200, 500), (400, 900), ]

        #x_range = np.linspace(-int(CONFIG['X_LIMITS']), int(CONFIG['X_LIMITS']), CONFIG['X_POINTS'])
        #print x_range
        #y_range = np.linspace(-int(CONFIG['Y_LIMITS']), int(CONFIG['Y_LIMITS']), CONFIG['Y_POINTS'])
        # Pixels
        #x_range = np.linspace(int(CONFIG['X_LIMITS'][0]), int(CONFIG['X_LIMITS'][1]), CONFIG['X_POINTS'])
        #print x_range
        #y_range = np.linspace(int(CONFIG['Y_LIMITS'][0]), int(CONFIG['Y_LIMITS'][1]), CONFIG['Y_POINTS'])

        #x_range = np.linspace(padding, resolution[0] - padding, CONFIG['X_POINTS'])
        #y_range = np.linspace(-padding, -resolution[1] + padding, CONFIG['Y_POINTS'])

        x_range = np.linspace(x, -x, CONFIG['X_POINTS'])
        y_range = np.linspace(y, -y, CONFIG['Y_POINTS'])
        self.large_set = [(i, j) for i in x_range for j in y_range]
        #print self.large_set
        #self.large_set = [(i, j) for i in range(-10, 11, 5) for j in range(-10, 11, 5)]
        self.repeat = CONFIG['POINT_REPEAT']

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
            control_set = self.large_set * self.repeat
            while len(control_set) > 0:
                pos = Point2(control_set.pop(random.randrange(len(control_set))))
                yield (pos.getX(), depth, pos.getY())
