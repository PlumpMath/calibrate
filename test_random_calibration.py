import unittest
# from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
# from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
import fake_eye_data
import datetime

# This test suite is for calibration when in auto (random) mode, and
# not testing stuff that is exactly the same as manual move (iow, before
# mode even kicks in.


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
    # Want to make sure starting in manual and switching to auto works as well
    # as just starting in auto.
    class_switch = False
    #class_switch = True

    @classmethod
    def setUpClass(cls):
        loadPrcFileData("", "window-type offscreen")
        #ConfigVariableString("window-type","offscreen").setValue("offscreen")
        #print 'about to load world'
        # 2 is random mode
        if cls.class_switch:
            print 'class has been run for starting in auto, try starting in manual and switching'
            cls.w = World(1, 1)
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
            cls.w.switch_task = True
        else:
            print 'first time through, run in auto'
            cls.w = World(2, 1)
            cls.class_switch = True

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
        on = False
        # need to show the square, and then get to the dim square method
        while square_on:
            taskMgr.step()
            if self.w.next == 1 and not on:
                # make sure we will fade, only want to run this once...
                #print 'move eye data'
                self.move_eye_to_get_reward()
                on = True
            if self.w.next == 2 and on:
                #print 'square should be dim'
                square_on = False
        #print self.w.square.getColor()
        self.assertNotEqual(self.w.square.getColor(), old_color)

    def test_square_moves_after_fixation(self):
        # get to square on and fixate
        square_off = True
        move = False
        # need to show the square, and then get to the move square method
        while square_off:
            taskMgr.step()
            if self.w.next == 1 and not move:
                #print 'first square on, move eye'
                # find out where the square is...
                square_pos = self.w.square.getPos()
                self.move_eye_to_get_reward()
                move = True
            if self.w.next == 1 and move:
                #print 'and exit'
                square_off = False
        self.assertNotEqual(self.w.square.getPos, square_pos)

    def test_square_turns_off_after_breaking_fixation(self):
       # First get to square on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # make sure looking at right place (breaks fixation)
        self.move_eye_to_get_reward('break')

        # Now wait for 0. This means we should have turned off the square,
        # and next will turn on the square after a missed fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next == 0:
                no_change = False
        self.assertFalse(self.w.square.getParent())

    def test_square_turns_off_after_missed_fixation(self):
       # First get to square on
        square_off = True
        # find out where the square is...
        square_pos = self.w.square.getPos()
        #print 'not looking at ', square_pos
        # make sure looking at right place (not fixation)
        self.move_eye_to_get_reward('not')
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # Now wait for 0. This means we should have turned off the square,
        # and next will turn on the square after a missed fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next == 0:
                no_change = False
        self.assertFalse(self.w.square.getParent())

    def test_repeats_same_square_if_breaks_fixation(self):
        # First get to square on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # find out where the square is...
        square_pos = self.w.square.getPos()
        #print 'about to break, square is ', square_pos
        # make sure looking at right place (breaks fixation)
        self.move_eye_to_get_reward('break')
        # now wait for self.w.next to change again, should be
        # 4, not 2 or 3, since we broke fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next == 0:
                no_change = False
        new_square_pos = self.w.square.getPos()
        #print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

    def test_repeats_same_square_if_no_fixation(self):
        # First get to square on
        square_off = True
        # find out where the square is...
        square_pos = self.w.square.getPos()
        #print 'not looking at ', square_pos
        # make sure looking at right place (not fixation)
        self.move_eye_to_get_reward('not')
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # Now wait for 0. This means we are about to turn on the square after
        # missed fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next == 0:
                no_change = False
        new_square_pos = self.w.square.getPos()
        #print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

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

    def test_timing_on_to_fade_if_fixated(self):
        # once subject fixates, on for fix_interval
        # First get to on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                a = datetime.datetime.now()
                square_off = False
        # make sure looking at right place
        self.move_eye_to_get_reward()
        # now wait for fade:
        square_on = True
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
        # use fix interval, since fake data will start it right away in fixation window
        self.assertAlmostEqual(c.total_seconds(), self.config['FIX_INTERVAL'], 1)

    def test_timing_stimulus_up_if_not_fixated(self):
        # if not fixated, will wait for on duration, then reset
        # First get ready for square on.
        # make sure looking at right (wrong) place
        self.move_eye_to_get_reward('not')
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                a = datetime.datetime.now()
                #print 'square should be on'
                square_off = False
        # now wait for reload:
        #print 'next loop'
        square_on = True
        while square_on:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 0, then we are reloading
            if self.w.next == 0:
                square_on = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # make sure really off, sanity check
        self.assertFalse(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # use fix interval, since fake data will start it right away in fixation window
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 1)

    def test_timing_fade_on_to_off(self):
        self.move_eye_to_get_reward()
        # First get to fade on
        square_dim = True
        while square_dim:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just changed color
            if self.w.next == 2:
                #print 'square should be faded'
                square_dim = False
        # now wait for fade off:
        #print 'square should be faded'
        square_fade = True
        a = datetime.datetime.now()
        while square_fade:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.next == 3:
                #print 'square should be off'
                square_fade = False
        b = datetime.datetime.now()
        c = b - a
        #print 'square should be off'
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really off, sanity check
        self.assertFalse(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_timing_off_to_reward(self):
        # make sure will get reward
        self.move_eye_to_get_reward()
        # First get to on, move eye to get reward, then go to off
        square_on = True
        fade = False
        while square_on:
            #while time.time() < time_out:
            taskMgr.step()
            if self.w.next == 1 and not fade:
                # if we go on during loop, might not be in correct place
                self.move_eye_to_get_reward()
                fade = True
            if self.w.next == 3 and fade:
                # if taskTask.now changes to 3, then we have just turned off
                #print 'square should be off'
                a = datetime.datetime.now()
                square_on = False
                # now wait for move/on:
        # now wait for reward
        no_reward = True
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 4, then we have just turned on
            if self.w.next == 4:
                #print 'square should be off'
                no_reward = False
        b = datetime.datetime.now()
        c = b - a
        #print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['REWARD_INTERVAL'][0], 1)

    def test_timing_reward_to_move(self):
        self.move_eye_to_get_reward()
        # First get to reward
        no_reward = True
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 4, then we just gave reward
            if self.w.next == 4:
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

    def test_timing_for_time_out_if_missed_fixation(self):
        # if not fixated, will wait for break interval after square turns off
        # move eye way outside
        self.move_eye_to_get_reward('not')
        # need timing from square off to back on, after a missed fixation
        # wait for square to turn off
        # if square is currently on, need to wait for it to go off,
        # come back on, and then go back off again, so we are sure we missed fixation,
        # since we can't guarantee there wasn't a fixation before we moved the eye
        last = self.w.next
        #print('next', last)
        if last > 0:
            loop = 2
        else:
            loop = 1
        square_on = True
        #print('first loop', loop)
        while square_on:
            taskMgr.step()
            if self.w.next != last:
                # if starts at zero, won't get here unless
                # it changes to something else first
                last = self.w.next
                #print('last', last)
                #print('loop', loop)
                # if taskTask.now changes to 0, then end of trial,
                # and we have just turned off
                if last == 0:
                    if loop == 2:
                        #print('decrement')
                        loop -= 1
                    else:
                        a = datetime.datetime.now()
                        #print 'square should be back off'
                        square_on = False

        # now wait for square to turn back on
        #print 'next loop'
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then square back on
            if self.w.next == 1:
                #print('square should be back on')
                b = datetime.datetime.now()
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # use fix interval, since fake data will start it right away in fixation window
        self.assertAlmostEqual(c.total_seconds(), self.config['BREAK_INTERVAL'], 1)

    def test_reward_for_looking(self):
        # First get to square on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # make sure looking at right place
        self.move_eye_to_get_reward()
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
        self.assertEqual(self.w.next,3)

    def test_no_reward_if_not_looking(self):
        # First get ready for square on.
        # make sure looking at right (wrong) place
        # move eye away from square
        # if we don't fixate, jumps to 4 without reward
        # I suppose it is possible that square would move
        # to the place I moved it to, but this seems unlikely
        # something to look at if this test fails
        self.move_eye_to_get_reward('not')
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # now wait for self.w.next to change again, should be
        # 4, not 2 or 3. Already on one...
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next != 1:
                no_change = False
        # next step should not be reward or square dims, should be
        # square turns on (without moving)
        self.assertNotEqual(self.w.next,2)
        self.assertNotEqual(self.w.next,3)
        self.assertEqual(self.w.next,0)

    def test_no_reward_if_look_but_break_fixation(self):
        # First get to square on
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # make sure looking at right place
        self.move_eye_to_get_reward('break')
        # now wait for self.w.next to change again, should be
        # 4, not 2 or 3, since we broke fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next != 1:
                no_change = False
        # next step should not be reward or square dims, should be
        # square turns on (without moving)
        self.assertNotEqual(self.w.next,2)
        self.assertNotEqual(self.w.next,3)
        self.assertEqual(self.w.next,0)

    def move_eye_to_get_reward(self, no_reward=[]):
        # find out where the square is...
        square_pos = self.w.square.getPos()
        #print square_pos
        variance = 0.001
        eye_data = (square_pos[0], square_pos[2])
        # default is put eye in square
        if no_reward == 'not':
            # put eye way outside of all possible targets
            #print 'not'
            eye_data = (2000, 2000)
        elif no_reward == 'break':
            #print 'break'
            # start out at fixation, but move out quickly
            variance = 20
        #print 'eye start', eye_data
        #print 'variance', variance
        self.w.fake_data = fake_eye_data.yield_eye_data(eye_data, variance)

    @classmethod
    def tearDownClass(cls):
        taskMgr.remove(cls.w.frameTask)
        cls.w.close()
        del cls.w
        print 'tore down'
        #ConfigVariableString("window-type","onscreen").setValue("onscreen")


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    # run twice to cover both conditions
    unittest.TextTestRunner(verbosity=2).run(suite())
    unittest.TextTestRunner(verbosity=2).run(suite())
    # when you just want to run one test...
    #unittest.main(verbosity=2)
