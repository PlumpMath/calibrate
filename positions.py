from panda3d.core import Point2, Point3
import random
# generate positions
# need to:
# a. return position according to a key press
# b. return position randomly from a large set - each point must be sampled x times
# c. return position from a large set in a fixed order
# make position an object?
# make a matrix of large_set * how ever many times per point, and
# remove positions as we use them
# basically same thing for non-random, non-key, but pull out in order
class Positions:
    def __init__(self):
        self.small_set = [(10, 10), (10, 0), (10, -10), (0, 10), (0, 0), (0, -10), (-10, 10), (-10, 0), (-10, -10),]
        self.large_set = [(i, j) for i in range(-10, 11, 5) for j in range(-10, 11, 5)]

    def get_position(self, depth, key=None):
        if key:
            pos = Point2(self.small_set[key-1])
        else:
            # this does not guarantee each point for a given number of times, but works for the moment.
            pos = Point2(random.choice(self.large_set))
            #pos = Point2(10, 10)
        position = (pos.getX(), depth, pos.getY())
        print position
        return position

# random from a grid.
