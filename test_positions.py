from __future__ import division
import unittest
from positions import Positions
from positions import visual_angle


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
        # generator object, will output until done
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
        # make sure furthest out positions are plotted are at the correct visual angle
        # for this test, just test whatever is in the config file, and make sure it
        # is following whatever is there, regardless of if that is really correct (more
        # likely it is me sitting a foot or two away from the laptop, but not going to change
        # the view_dist and screen size since it doesn't really matter...
        max_x = self.config['MAX_DEGREES_X']
        max_y = self.config['MAX_DEGREES_Y']
        deg_per_pixel = visual_angle(self.config['SCREEN'], self.config['WIN_RES'], self.config['VIEW_DIST'])
        #
        # Key 9 should get you the max visual degrees for both x and y. Of course, it will
        # really be farther than the max visual angle, since we are maximizing both x and y,
        # but as long as the cardinal directions are the right visual angle, we understand the
        # corners are really further out, and will take this under consideration
        pos = Positions(self.config)
        pos_9 = pos.get_key_position(self.depth, key=9)
        #print pos_9
        self.assertAlmostEqual(pos_9[0], max_x / deg_per_pixel[0], 4)
        self.assertAlmostEqual(pos_9[2], max_y / deg_per_pixel[1], 4)

if __name__ == "__main__":
    unittest.main(verbosity=2)
