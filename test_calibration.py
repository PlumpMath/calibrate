import unittest
from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from StringIO import StringIO
import sys
import datetime

# Tests run fine one at a time, but isn't destroying the ShowBase
# instance between tests, for some crazy reason. It use to! Meh.

class TestCalibration(unittest.TestCase):
# task.time is not very accurate when running off-screen
# Need to make these tests faster. Since we are testing the logic
# of moving from one task to the next, probably easiest way is to
# override the intervals to much smaller amounts.
# codes for w.next
#            0: self.square_on,
#            1: self.square_fade,
#            2: self.square_off,
#            3: self.square_move}
    ClassIsSetup = False
    #manual = True
    manual = 1

    def setUp(self):
        if not self.ClassIsSetup:
            print "initialize"
            self.setupClass()

        loadPrcFileData("", "window-type offscreen")
        #ConfigVariableString("window-type","offscreen").setValue("offscreen")
        #print 'about to load world'
        #print 'boo', self.manual
        self.w = World(self.manual)
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

    @classmethod
    def setUpClass(cls):
        if cls.ClassIsSetup:
            #cls.manual = False
            cls.manual = 2
        # remember it was setup already
        cls.ClassIsSetup = True

    def test_no_square(self):
        """
        Should start with a blank screen, square has no parent, not rendered
        """
        #print self.w.square.getParent()
        self.assertFalse(self.w.square.getParent())

    def test_square_turns_on(self):
        """
        The square should turn on when next is 1
        """
        #time_out = time.time() + 2.1
        #start_time =
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False

        self.assertTrue(self.w.square.getParent())

    def test_square_fades(self):
        # we may change the actual colors, so just make sure the
        # color before and after the switch are different
        old_color = self.w.square.getColor()
        #print 'color', old_color
        square_on = True
        while square_on:
            taskMgr.step()
            if self.w.next == 2:
                #print 'square should be dim'
                square_on = False
        #print self.w.square.getColor()
        self.assertNotEqual(self.w.square.getColor(), old_color)

    def test_square_turns_off(self):
        square_dim = True
        while square_dim:
            taskMgr.step()
            if self.w.next == 3:
                square_dim = False
        self.assertFalse(self.w.square.getParent())

    def test_timing_off_to_on(self):
        square_off = True
        # Timing for the first one is not very accurate, since timing
        # for the first one starts in init. We will get the timing info
        # directly from the task instead of measuring it here.
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False

        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # checking move interval, not actually moving, but this is the time
        # from off to move/on, which we do without the moving part...
        self.assertAlmostEqual(self.w.frameTask.time, self.config['MOVE_INTERVAL'][0], 1)

    def test_timing_on_to_fade(self):
        # First get to on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # now wait for fade:
        square_on = True
        a = datetime.datetime.now()
        while square_on:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == 2:
                #print 'square should be on'
                square_on = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 1)

    def test_timing_fade_on_to_off(self):
        # First get to fade on
        square_dim = True
        while square_dim:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == 2:
                #print 'square should be faded'
                square_dim = False
        # now wait for fade off:
        square_fade = True
        a = datetime.datetime.now()
        while square_fade:
            taskMgr.step()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.next == 3:
                square_fade = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really off, sanity check
        self.assertFalse(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_eye_data_written_to_file(self):
        # make sure data is written to file.
        # run the trial for a while, since fake data doesn't start
        # collecting until trial starts
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # need to stop task, so file is closed
        self.w.close()
        # since we are using fake data, know that first point is (0,0)
        f = open(self.w.eye_file_name, 'r')
        #print(f.readline())
        self.assertIn('timestamp', f.readline())
        self.assertIn( '0, 0\n', f.readline())
        f.close()

    def test_tasks_and_timestamp_written_to_file(self):
        # make sure data is written to file.
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # need to stop task, so file is closed
        self.w.close()
        # since we are using fake data, know that first point is (0,0)
        f = open(self.w.time_file_name, 'r')
        #print(f.readline())
        self.assertIn('timestamp', f.readline())
        self.assertIn('start calibration', f.readline())
        self.assertIn('Square on', f.readline())

        f.close()

    def tearDown(self):
        taskMgr.remove(self.w.frameTask)
        self.w.close()
        del self.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")

def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite( TestCalibration, 'test' )

if __name__ == "__main__":
    #unittest.main(verbosity=2)
    #print 'run suite'
    # run twice to cover both conditions
    unittest.TextTestRunner(verbosity=1).run(suite())
    unittest.TextTestRunner(verbosity=1).run(suite())

    #unittest.main(verbosity=2)

