import unittest
from panda3d.core import loadPrcFileData
from panda3d.core import Point3
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
import sys
import datetime

# Tests run fine one at a time, but isn't destroying the ShowBase
# instance between tests, for some crazy reason. It use to! Meh.


class TestCalibration(unittest.TestCase):
# task.time is not very accurate when running off-screen
#            0: self.square_on,
#            1: self.square_fade,
#            2: self.square_off,
#            3: self.square_move}
    # Want to make sure starting in auto and switching to manual works as well
    # as just starting in auto. Probably won't really use this functionality, but
    # easy to test, and it is available...

    @classmethod
    def setUpClass(cls):
        loadPrcFileData("", "window-type offscreen")
        # all these tests are for manual
        # manual move is mode 1
        if class_switch:
            print 'class has been run for starting in manual, try starting in auto and switching'
            cls.w = World(2, 1)
            # run through a full loop
            square_off = True
            last = 0
            while square_off:
                taskMgr.step()
                if cls.w.next == last:
                    pass
                elif cls.w.next == 0:
                    #print 'square is on!'
                    square_off = False
                else:
                    last = cls.w.next
        else:
            print 'first time through, run in manual'
            cls.w = World(1, 1)
        #print 'loaded world'

    def setUp(self):
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 0

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

    def test_reward_after_square_off(self):
        # should get reward automatically if on manual
        # easiest way to stop after reward on manual is to start,
        # then until it changes twice, at which time should be reward.
        self.w.keys["switch"] = 7
        no_start = True
        while no_start:
            taskMgr.step()
            #print self.w.next
            if self.w.next == 1:
                no_start = False
        # now wait for it to change twice, once for fade, once for reward.
        wait_change_twice = True
        count = 2
        while wait_change_twice:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == count:
                if count == 3:
                    wait_change_twice = False
                else:
                    count += 1
                    # if next step is reward, then we got a reward...
        self.assertEqual(self.w.next, 3)

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

    def test_square_moves_to_center_if_no_keypress(self):
        # Wait for reward, don't send keypress
        # check position changed to center
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
        #print self.w.square.getPos()
        self.assertEqual(self.w.square.getPos(), Point3(0, 55, 0))

    def test_on_after_manual_move(self):
        # make sure square goes on after manual move
        # wait for square to turn off, then send signal to move
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        #print 'done with loop'
        # make sure square is off
        before = self.w.square.getParent()
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

    def test_timing_on_to_fade(self):
        # First get to on
        square_off = True
        a = 0
        #print 'time on to fade'
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                a = datetime.datetime.now()
                square_off = False
        # now wait for fade:
        square_on = True
        b = 0
        while square_on:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == 2:
                b = datetime.datetime.now()
                #print 'square should be faded'
                square_on = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        interval = self.config['ON_INTERVAL'][0]
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), interval, 1)

    def test_timing_on_to_fade_after_manual_move(self):
        # We turn on at the same time we move, so check the
        # interval between turning on and fading, which will
        # be when self.w.next switches to 2.
        signal = False
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                signal = True
        # and move
        self.w.keys["switch"] = 3
        #print 'check time'
        a = 0
        # we have set move,
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                # okay, should be on now
                a = datetime.datetime.now()
                square_off = False
        # need to stop when square fades
        square_on = True
        b = 0
        while square_on:
            taskMgr.step()
            if self.w.next == 2:
                b = datetime.datetime.now()
                square_on = False
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
        #print 'out of first loop'
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
        # first make sure off, turns off when given reward
        # this is when not pressing a key
        print 'timing off to on'
        square_on = True
        a = 0
        while square_on:
            taskMgr.step()
            if self.w.next == 3:
                a = datetime.datetime.now()
                square_on = False
        # make sure really off
        self.assertFalse(self.w.square.getParent())
        #print 'next loop'
        square_off = True
        b = 0
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                b = datetime.datetime.now()
                #print 'square should be on'
                square_off = False
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

    def test_timing_check_for_key_to_move_after_key_press(self):
        # Just making sure that time from when we start waiting for a key press
        # until time square is on is the same as reward to square on, a bit redundant now, really
        no_reward = True
        self.w.keys["switch"] = 7
        a = 0
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if we are at task.move is true, then just gave reward
            if self.w.frameTask.move:
                a = datetime.datetime.now()
                #print 'reward'
                no_reward = False
        # now wait for move/on:
        square_off = True
        b = 0
        while square_off:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                b = datetime.datetime.now()
                #print 'square should be off'
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def test_waits_correct_time_with_no_keypress(self):
        # if we don't press a key, do we still wait the correct
        # time before we move?
        # We turn on at the same time we move, so check the
        # interval between turning off and turning on, which will
        # be when self.w.next switches to 1.
        #old_position = self.w.square.getPos()
        #print old_position
        signal = False
        a = 0
        while not signal:
            taskMgr.step()
            if self.w.frameTask.move is True:
                a = datetime.datetime.now()
                signal = True
        # when w.frameTask.move is True, the square has just turned off
        # time until it is on, and moved
        #print 'check time'
        # we wait until it comes back on
        square_off = True
        b = 0
        while square_off:
            taskMgr.step()
            if self.w.next == 1:
                b = datetime.datetime.now()
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    @classmethod
    def tearDownClass(cls):
        taskMgr.remove(cls.w.frameTask)
        cls.w.close()
        del cls.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCalibration)
    class_switch = False
    if len(sys.argv) == 2:
        print 'yup'
        if sys.argv[1] == 'True':
            print 'true'
            class_switch = True
            print 'go'
        elif sys.argv[1] == 'Mac':
            class_switch = True
            # run twice to cover both conditions
            unittest.TextTestRunner().run(suite)
        print 'test'
        unittest.TextTestRunner().run(suite)
    else:
        # when you just want to the suite from the command line
        # without a sys.argv, in this case, if you want class_switch
        # to be True, must uncomment. gives you more verbosity
        class_switch = True
        unittest.main(verbosity=2)
