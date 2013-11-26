import unittest
from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
import datetime
global taskMgr
#from positions import positions
#import time

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
        self.w = World()
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

    def test_no_square(self):
        """
        Should start with a blank screen, square has no parent, not rendered
        """
        #print self.w.square.getParent()
        self.w.__init__()
        self.assertFalse(self.w.square.getParent())

    def test_square_turns_on(self):
        """
        The square should turn on after one second
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

            #for tasks in taskMgr.getTasks():
            #    print tasks
            #    if tasks.find('frame_loop'):
            #        print 'yes'
            #if task
            #print time.time()
            #print 'time out', time_out
        #print 'close'
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

    def test_manual_move(self):
        # Wait for signal for move, send keypress,
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
        #print 'step'
        taskMgr.step()
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
        #print 'step'
        taskMgr.step()
        #self.w.square_move()
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
        taskMgr.step()
        self.assertNotEqual(self.w.square.getPos(), old_position)

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
        taskMgr.step()
        #print 'check time'
        a = datetime.datetime.now()
        # we have moved, need to stop when square fades
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
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 2)

    def tearDown(self):
        #print 'teardown'
        taskMgr.remove(self.w.frameTask)
        self.w.close()
        del self.w

        #ConfigVariableString("window-type","onscreen").setValue("onscreen")


if __name__ == "__main__":
    unittest.main(verbosity=2)

