import unittest
from positions import Positions

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
            print i
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
            print i
            count += 1
            #print self.pos.get_position(self.depth)
            #self.pos.get_position(self.depth)
        # Try to get another, should not work
        self.assertRaises(StopIteration, next, pos)
        self.assertEqual(count, total)


if __name__ == "__main__":
    unittest.main(verbosity=2)
