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


    def setUp(self):
        loadPrcFileData("", "window-type offscreen")
        #ConfigVariableString("window-type","offscreen").setValue("offscreen")
        #print 'about to load world'
        # all these tests are for manual
        # manual move is mode 1
        self.w = World(1)
        #print 'loaded world'
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

    def test_correct_reward_after_square_off(self):
        # should only get reward automatically if on manual
        # easiest way to stop after reward on manual is to
        # go to second time next = 1
        # this test collects all the print statements, so is a
        # little awkward for troubleshooting...
        # best to comment out held, sys.stdout line, but keep
        # in mind, this ensures failure
        self.w.keys["switch"] = 7
        held, sys.stdout = sys.stdout, StringIO()
        no_reward = True
        loop = 0
        last_next = 0
        while no_reward:
            taskMgr.step()
            #print self.w.next
            if self.w.next == 1 and self.w.next != last_next:
                if loop == 0:
                    #print 'loop 1'
                    loop += 1
                elif loop == 1:
                    #print 'reward?'
                    no_reward = False
            last_next = self.w.next
        output = 'beep\n' * self.config['NUM_BEEPS']
        self.assertIn(output, sys.stdout.getvalue())

    def test_timing_off_to_reward(self):
        # only get reward automatically if on manual
        # First get to off
        square_fade = True
        while square_fade:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.next == 3:
                #print 'square should be off'
                square_fade = False
                # now wait for move/on:
        print 'out of first loop'
        self.w.keys["switch"] = 3
        # now wait for reward, when move changes, we are done with reward
        # and ready for moving
        no_reward = True
        a = datetime.datetime.now()
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to , then we are done with reward,
            # ready to move to square on
            if self.w.frameTask.move:
                #print 'square should be off'
                no_reward = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['REWARD_INTERVAL'][0], 1)

    def test_timing_reward_to_move(self):
        # only get reward automatically if on manual
        # First get to reward
        no_reward = True
        self.w.keys["switch"] = 7
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if we are at task.move is true, then just gave reward
            if self.w.frameTask.move:
                #print 'reward'
                no_reward = False
        # now wait for move/on:
        square_off = True
        a = datetime.datetime.now()
        while square_off:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be off'
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
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def test_manual_move(self):
        # Wait for signal for move, send keypress,
        # wait for actual move,
        # check position changed
        #self.w.set_manual(self.config, True)
        old_position = self.w.square.getPos()
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
                #print 'made it out of loop!'
        # and move
        self.w.keys["switch"] = 7
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                square_off = False
        #print self.w.keys["switch"]
        #print 'old position', old_position
        self.assertNotEqual(self.w.square.getPos(), old_position)

    def test_on_after_manual_move(self):
        # make sure square goes on after manual move
        # wait for square to turn off, then send signal to move
        before = self.w.square.getParent()
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        #print 'done with loop'
        # and move
        # and move
        self.w.keys["switch"] = 3
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                square_off = False

        #print 'move'
        #print self.w.square.getParent()
        self.assertTrue(self.w.square.getParent())
        #print 'next test?'
        # double check square was off to begin with
        self.assertNotEqual(self.w.square.getParent(), before)

    def test_manual_move_after_second_keypress(self):
        # need to make sure still works after first cycle...
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        # and move
        self.w.keys["switch"] = 3
        #print 'step'
        taskMgr.step()
        #print self.w.keys["switch"]
        old_position = self.w.square.getPos()
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        # and move
        self.w.keys["switch"] = 4
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                square_off = False
        self.assertNotEqual(self.w.square.getPos(), old_position)

    def test_waits_correct_time_to_manual_move(self):
        # We turn on at the same time we move, so check the
        # interval between turning off and turning on, which will
        # be when self.w.next switches to 1.
        old_position = self.w.square.getPos()
        #print old_position
        signal = False
        # go ahead and make the key switch, should not affect the first
        # move, since it is always fixed at center
        self.w.keys["switch"] = 3
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        # when w.frameTask.move is True, the square has just turned off
        # time until it is on, and moved
        #print 'check time'
        a = datetime.datetime.now()
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                square_off = False

        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def test_waits_correct_time_after_manual_move(self):
        # We turn on at the same time we move, so check the
        # interval between turning on and fading, which will
        # be when self.w.next switches to 2.
        old_position = self.w.square.getPos()
        #print old_position
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        # and move
        self.w.keys["switch"] = 3
        #print 'check time'

        # we have set move,
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                square_off = False
        #
        # okay, should be on now
        a = datetime.datetime.now()
        # need to stop when square fades
        square_on = True
        while square_on:
            taskMgr.step()
            if self.w.next == 2:
                square_on = False

        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 1)

    def tearDown(self):
        taskMgr.remove(self.w.frameTask)
        self.w.close()
        del self.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")


if __name__ == "__main__":
    unittest.main(verbosity=2)

