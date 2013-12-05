import unittest
from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
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
        self.w = World()
        #print 'loaded world'
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

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
        self.w.close()
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
        # make sure timing within 2 places
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
        # make sure timing within 2 places
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
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_timing_off_to_move(self):
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
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def test_manual_move(self):
        # Wait for signal for move, send keypress,
        # wait for actual move,
        # check position changed
        self.w.set_manual(self.config, True)
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
        self.w.set_manual(self.config, True)
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
        self.w.set_manual(self.config, True)
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
        self.w.set_manual(self.config, True)
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
        self.w.set_manual(self.config, True)
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
        self.assertEqual(f.readline(), '0, 0\n')
        f.close()

    def tearDown(self):
        taskMgr.remove(self.w.frameTask)
        self.w.close()
        del self.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")


if __name__ == "__main__":
    unittest.main(verbosity=2)

