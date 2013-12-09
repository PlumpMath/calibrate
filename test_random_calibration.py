import unittest
from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from StringIO import StringIO
import sys
import datetime

# This test suite is for calibration when in auto (random) mode.as
# not testing stuff that is exactly the same as manual move (iow, before
# mode even kicks in. Too much of a time sync, and if it works for manual,
# no reason to think it won't work for auto. Will be really obvious if it
# doesn't anyway..

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


    def setUp(self):
        loadPrcFileData("", "window-type offscreen")
        #ConfigVariableString("window-type","offscreen").setValue("offscreen")
        #print 'about to load world'
        self.w = World(False)
        #print 'loaded world'
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

    def test_square_moves_automatically(self):
        old_position = self.w.square.getPos()
        count = 0
        square_not_moved = True
        last = 0
        # square moves when frameTask.now changes to 1 the second time
        while square_not_moved:
            taskMgr.step()
            #print 'task.!', self.w.next
            #print 'count', count
            if self.w.next == last:
                # print 'no change'
                pass
            elif self.w.next == 1:  # if taskTask.now changes to 1,
                # then we have just turned on
                #print 'square is on!'
                last = self.w.next
                count += 1
            else:
                #print 'change, but not square on'
                last = self.w.next

            if count == 2:
                #print 'square should be on for second time'
                square_not_moved = False
        self.assertNotEqual(self.w.square.getPos(), old_position)

    def test_square_turns_on_after_move(self):
        count = 0
        square_off = True
        last = 0
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            #print count
            # need to check for frameTask.now to change to 1 the second time
            # (first time is just the beginning of the task, before moving)
            # if taskTask.now changes to 1, then we have just turned on
            # sometimes, especially with off-screen, the timing isn't accurate,
            # and we have to calls to the same function right in a row. Make sure
            # when frameTask.now is one, it is changing from something else.
            if self.w.next == last:
                pass
            elif self.w.next == 1:
                #print 'square is on!'
                last = self.w.next
                count += 1
            else:
                last = self.w.next

            if count == 2:
                #print 'square should be on for second time'
                square_off = False
        self.assertTrue(self.w.square.getParent())

    def test_timing_off_to_on(self):
        square_off = True
        a = datetime.datetime.now()
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # checking move interval, not actually moving, but this is the time
        # from off to move/on, which we do without the moving part...
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

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
            # if taskTask.now changes to 1, then we have just turned on
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
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 2:
                #print 'square should be on'
                square_dim = False
        # now wait for fade off:
        square_fade = True
        a = datetime.datetime.now()
        while square_fade:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 3:
                #print 'square should be on'
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

    def test_timing_off_to_reward(self):
        # only get reward automatically if on manual
        # First get to off
        square_fade = True
        while square_fade:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 3:
                #print 'square should be off'
                square_fade = False
                # now wait for move/on:
        # now wait for reward
        no_reward = True
        a = datetime.datetime.now()
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 4:
                #print 'square should be off'
                no_reward = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['REWARD_INTERVAL'][0], 1)

    # need to rework this so we get reward, also need tests for timing after move
    #def test_timing_reward_to_move(self):
    #    # only get reward automatically if on manual
    #    self.w.manual = True
    #    # First get to reward
    #    no_reward = True
    #    while no_reward:
    #        #while time.time() < time_out:
    #        taskMgr.step()
    #        # if taskTask.now changes to 4, then we just gave reward
    #        if self.w.next == 4:
    #            #print 'reward'
    #            no_reward = False
    #    # now wait for move/on:
    #    square_off = True
    #    a = datetime.datetime.now()
    #    while square_off:
    #        #while time.time() < time_out:
    #        taskMgr.step()
    #        # if taskTask.now changes to 1, then we have just turned on
    #        if self.w.next == 1:
    #            #print 'square should be off'
    #            square_off = False
    #    b = datetime.datetime.now()
    #    c = b - a
    #    #print 'c', c.total_seconds()
    #    # check that time is close
    #    #print 'c should be', self.config['MOVE_INTERVAL'][0]
    #    # make sure really on, sanity check
    #    self.assertTrue(self.w.square.getParent())
    #    # make sure timing within 1 place, won't be very accurate.
    #    # but close enough to have correct interval
    #    self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def tearDown(self):
        taskMgr.remove(self.w.frameTask)
        self.w.close()
        del self.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")


if __name__ == "__main__":
    unittest.main(verbosity=2)

