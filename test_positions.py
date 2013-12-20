from __future__ import division
import unittest
from positions import Positions
from positions import visual_angle
import numpy as np

class TestPositions(unittest.TestCase):
    def setUp(self):
        self.config = {}
        execfile('config.py', self.config)
        self.depth = 0

    def test_non_random_list_pops(self):
        # make sure all positions are yielded.
        # number of positions
        total = self.config['X_POINTS'] * self.config['Y_POINTS']
        count = 0
        pos = Positions().get_position(self.depth)
        #for i in range(self.config['X_LIMITS'] * self.config['X_LIMITS']):
        for i in pos:
            #print i
            count += 1
            #print self.pos.get_position(self.depth)
            #self.pos.get_position(self.depth)
        # Try to get another, should not work
        self.assertRaises(StopIteration, next, pos)
        self.assertEqual(count, total)

    def test_random_list_pops(self):
        # make sure all positions are yielded.
        # number of positions
        pos = Positions().get_position(self.depth, True)
        total = self.config['X_POINTS'] * self.config['Y_POINTS'] * self.config['POINT_REPEAT']
        count = 0
        #for i in range(self.config['X_LIMITS'] * self.config['X_LIMITS']):
        for i in pos:
            #print i
            count += 1
            #print self.pos.get_position(self.depth)
            #self.pos.get_position(self.depth)
        # Try to get another, should not work
        self.assertRaises(StopIteration, next, pos)
        self.assertEqual(count, total)

    def test_visual_angle(self):
        # visual angle returns deg_per_pix,
        # check with projector parameters
        screen_size = [1337, 991]
        resolution = [1024, 768]
        view_dist = 1219
        deg_per_pix = visual_angle(screen_size, resolution, view_dist)
        self.assertAlmostEqual(deg_per_pix[0], 0.061369, 6)
        self.assertAlmostEqual(deg_per_pix[1], 0.06065, 6)

    def test_visual_angle_positions(self):
        # make sure positions plotted are at increments of 5 degrees visual angle,
        # for this test, just test whatever is in the config file
        pos = Positions().get_position(self.depth, True)
        count = 0
        deg_per_pixel = visual_angle(self.config['SCREEN'], self.config['WIN_RES'], self.config['VIEW_DIST'])
        #
        pass
        #for i in pos:
        #    #print i
        #    count += 1
        #    #print self.pos.get_position(self.depth)
        #    #self.pos.get_position(self.depth)
        #    print 'x', i[0]
        #    print 'y', i[2]
        #    print 'degrees x', i[0] * deg_per_pixel[0]
        #    print 'degrees y', i[1] * deg_per_pixel[1]
        # get x and y position of square



if __name__ == "__main__":
    unittest.main(verbosity=2)
