import unittest
from panda3d.core import loadPrcFileData
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
import fake_eye_data
import datetime
import sys

# This test suite is for calibration when in auto (random) mode, and
# not testing stuff that is exactly the same as manual move (which is
# tested in generic test_calibration suite).


def is_int_string(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


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

    @classmethod
    def setUpClass(cls):
        loadPrcFileData("", "window-type offscreen")
        #ConfigVariableString("window-type","offscreen").setValue("offscreen")
        #print 'about to load world'
        # run in auto, 0
        cls.w = World(0, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        self.config = {}
        execfile('config_test.py', self.config)
        self.w.start_gig()
        self.w.start_loop()

    def test_square_fades(self):
        # we may change the actual colors, so just make sure the
        # color before and after the switch are different
        old_color = self.w.square.square.getColor()
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
        #print self.w.square.square.getColor()
        self.assertNotEqual(self.w.square.square.getColor(), old_color)

    def test_square_moves_after_fixation(self):
        # get to square on and fixate
        square_off = True
        move = False
        square_pos = 0
        # need to show the square, and then get to the move square method
        while square_off:
            taskMgr.step()
            if self.w.next == 1 and not move:
                #print 'first square on, move eye'
                # find out where the square is...
                square_pos = self.w.square.square.getPos()
                self.move_eye_to_get_reward()
                move = True
            if self.w.next == 1 and move:
                #print 'and exit'
                square_off = False
        self.assertNotEqual(self.w.square.square.getPos, square_pos)

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
        self.assertFalse(self.w.square.square.getParent())

    def test_square_turns_off_after_missed_fixation(self):
       # First get to square on
        square_off = True
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
        self.assertFalse(self.w.square.square.getParent())

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
        square_pos = self.w.square.square.getPos()
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
        new_square_pos = self.w.square.square.getPos()
        #print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

    def test_repeats_same_square_if_no_fixation(self):
        # First get to square on
        square_off = True
        # find out where the square is...
        square_pos = self.w.square.square.getPos()
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
        new_square_pos = self.w.square.square.getPos()
        #print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

    def test_square_turns_on_after_move(self):
        count = 0
        square_off = True
        last = self.w.next
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
            if self.w.next != last:
                last = self.w.next
                print last
            if last == 0:
                #print 'new loop'
                # last will only be 0 the second time around
                self.w.start_loop()
                count = 1
            if last == 1 and count == 1:
                #print 'square should be on for second time'
                square_off = False
            if last == 1:
                self.move_eye_to_get_reward()
        self.assertTrue(self.w.square.square.getParent())

    def test_timing_on_to_fade_if_fixated(self):
        # once subject fixates, on for fix_interval
        # First get to on
        square_off = True
        a = 0
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
        self.assertTrue(self.w.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # use fix interval, since fake data will start it right away in fixation window
        self.assertAlmostEqual(c.total_seconds(), self.config['FIX_INTERVAL'][0], 1)

    ### Timing on square on is off by 0.09s!
    # usually I check by when next changes, which is in writing to file,
    # which happens at the same time, but takes longer, which may be the problem
    def test_timing_stimulus_up_if_not_fixated(self):
        # if not fixated, will be on for on duration, then reset
        # First get ready for square on.
        # make sure looking at right (wrong) place
        square_off = True
        square_on = True
        a = 0
        b = 0
        print(self.w.square.square.getParent())
        print 'start'
        self.move_eye_to_get_reward('not')
        while square_off:
            taskMgr.step()
            a = datetime.datetime.now()
            # if square is parented to render, it is on, otherwise has no parent
            if self.w.square.square.getParent():
                print 'square should be on'
                square_off = False
        # now wait for square to turn back off:
        #print 'next loop'
        while square_on:
            taskMgr.step()
            if not self.w.square.square.getParent():
                b = datetime.datetime.now()
                print 'square should be off'
                square_on = False

        # there is an approximately 0.09s delay between the square turning
        # on, and it registering here (because the program is busy writing
        # to file at the same time, presumably), so fudging a bit here
        c = b - a
        c = c + datetime.timedelta(seconds=0.05)
        print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 1)

    def test_timing_fade_on_to_off(self):
        self.move_eye_to_get_reward()
        # First get to fade on
        square_dim = True
        square_fade = True
        a = 0
        b = 0
        while square_dim:
        #while time.time() < time_out:
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 2, then we have just changed color
            if self.w.next == 2:
                #print 'square should be faded'
                square_dim = False
        # now wait for fade off:
        #print 'square should be faded'
        while square_fade:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.next > 2:
                #print 'square should be off'
                square_fade = False
        c = b - a
        #print 'square should be off'
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really off, sanity check
        self.assertFalse(self.w.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_timing_off_to_reward(self):
        # make sure will get reward
        self.move_eye_to_get_reward()
        # First get to on, move eye to get reward, then go to off
        square_on = True
        fade = False
        no_reward = True
        a = 0
        b = 0
        while square_on:
            #while time.time() < time_out:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.next == 1 and not fade:
                # if we go on during loop, might not be in correct place
                self.move_eye_to_get_reward()
                fade = True
            if self.w.next > 3 and fade:
                # if taskTask.now changes to 3, then we have just turned off
                #print 'square should be off'
                square_on = False
                # now wait for move/on:
        # now wait for reward

        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 4, then we have just turned on
            if self.w.next == 4:
                #print 'square should be off'
                no_reward = False
        c = b - a
        #print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['REWARD_INTERVAL'][0], 1)

    def test_timing_reward_to_move(self):
        self.move_eye_to_get_reward()
        # First get to reward
        no_reward = True
        square_off = True
        a = 0
        b = 0
        while no_reward:
            #while time.time() < time_out:
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 4, then we just gave reward
            if self.w.next == 4:
                #print 'reward'
                no_reward = False
        # now wait for move/on:
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            if self.w.next == 0:
                self.w.start_loop()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be off'
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.square.getParent())
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
        # assuming we have done everything correctly in teardown and setup, we should never have
        # anything except next = 0 to start with
        self.assertTrue(self.w.next == 0)
        #print('next', last)
        square_on = True
        square_off = True
        a = 0
        b = 0
        while square_on:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.next > 0:
                if not self.w.square.square.getParent():
                    # square turned off
                    square_on = False
                    #print 'square off, I think'
                    #print self.w.next
        # now wait for square to turn back on
        #print 'next loop'
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            if self.w.next == 0:
                self.w.start_loop()
            if self.w.square.square.getParent():
                #print('square should be back on')
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # the break is the move interval + break interval
        break_time = self.config['BREAK_INTERVAL'][0] + self.config['MOVE_INTERVAL'][0]
        self.assertAlmostEqual(c.total_seconds(), break_time, 1)

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
        no_reward = True
        while no_reward:
            taskMgr.step()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next > 3:
                no_reward = False
        self.assertTrue(self.w.num_reward > 1)

    def test_no_reward_if_not_looking(self):
        # First get ready for square on.
        # make sure looking at right (wrong) place
        # move eye away from square
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
        # at zero now, started over
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next != 1:
                no_change = False
        # next step should not be reward or square dims, should be
        # square turns on (without moving)
        self.assertNotEqual(self.w.next, 2)
        self.assertNotEqual(self.w.next, 3)
        self.assertEqual(self.w.next, 0)

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
        # 0, not 2 or 3, since we broke fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.next != 1:
                no_change = False
        # next step should not be reward or square dims, should be
        # square turns on (without moving)
        self.assertNotEqual(self.w.next, 2)
        self.assertNotEqual(self.w.next, 3)
        self.assertEqual(self.w.next, 0)

    def move_eye_to_get_reward(self, no_reward=None):
        # find out where the square is...
        # default is stays in fixation window for reward
        square_pos = self.w.square.square.getPos()
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

    def tearDown(self):
        print 'tearDown'
        # clear out any half-finished tasks
        if self.w.auto_sequence:
            self.w.auto_sequence.finish()
        taskMgr.step()
        self.w.cleanup()
        self.w.end_gig()


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    # make a suite if running from file
    if len(sys.argv) == 2 and is_int_string(sys.argv[1]):
        print 'suite'
        result = unittest.TextTestRunner(verbosity=2).run(suite())
        if not result.wasSuccessful():
            sys.exit(1)
    else:
        print 'not suite'
        unittest.main(verbosity=2)