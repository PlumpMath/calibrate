import unittest
from panda3d.core import loadPrcFileData
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
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
    # Need to make these tests faster. Since we are testing the logic
    # of moving from one task to the next, probably easiest way is to
    # override the intervals to much smaller amounts.

    # self.next advances before the wait period, so for testing
    # we need to use the numbers from calibration advanced by one.
    # square on: 1, square fade: 2, square off: 3,
    # reward: 4, square moves: 5

    @classmethod
    def setUpClass(cls):
        loadPrcFileData("", "window-type offscreen")
        # ConfigVariableString("window-type","offscreen").setValue("offscreen")
        # print 'about to load world'
        # run in auto, 0
        cls.w = World(0, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        self.config = {}
        execfile('config_test.py', self.config)
        self.w.start_gig()
        self.w.start_main_loop()

    def finish_loop(self):
        # does a full loop if just ended, finishes the current
        # loop if you have already started
        # always ends at cleanup
        print 'finish loop'
        taskMgr.step()
        if self.w.sequences.current_task is None:
            print 'restarted loop'
            self.w.start_main_loop()
        now = self.w.sequences.current_task
        first_loop = True
        print 'now before loop', now
        # check each time we change tasks
        while first_loop:
            taskMgr.step()
            if self.w.sequences.current_task != now:
                print('took a step', self.w.sequences.current_task)
                now = self.w.sequences.current_task
                if now is None:
                    first_loop = False
        print 'end loop'

    def test_square_fades(self):
        # we may change the actual colors, so just make sure the
        # color before and after the switch are different
        old_color = self.w.sequences.square.square.getColor()
        # print 'color', old_color
        square_on = True
        on = False
        print 'start loop'
        check = self.w.sequences.current_task
        # need to show the square, and then get to the dim square method
        while square_on:
            taskMgr.step()
            if self.w.sequences.current_task != check:
                check = self.w.sequences.current_task
                print 'new task', check
                print 'square now at', self.w.sequences.square.square.getPos()
            if self.w.sequences.current_task == 1 and not on:
                # make sure we will fade, only want to run this once...
                print 'move eye data'
                self.move_eye_to_get_reward()
                on = True
                print 'moved eye'
            if self.w.sequences.current_task is None:
                # in case we missed the fixation interval
                self.w.start_main_loop()
            if self.w.sequences.current_task == 2 and on:
                print 'square now at', self.w.sequences.square.square.getPos()
                print 'square should be dim'
                square_on = False
        # print self.w.sequences.square.square.getColor()
        self.assertNotEqual(self.w.sequences.square.square.getColor(), old_color)

    def test_square_moves_after_fixation(self):
        # get to square on and fixate
        square_off = True
        move = False
        square_pos = 0
        # need to show the square, and then get to the move square method
        while square_off:
            taskMgr.step()
            if self.w.sequences.current_task == 1 and not move:
                # print 'first square on, move eye'
                # find out where the square is...
                square_pos = self.w.sequences.square.square.getPos()
                self.move_eye_to_get_reward()
                move = True
            if self.w.sequences.current_task == 1 and move:
                # print 'and exit'
                square_off = False
        self.assertNotEqual(self.w.sequences.square.square.getPos, square_pos)

    def test_square_turns_off_after_breaking_fixation(self):
        # First get to square on
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
        # make sure looking at right place (breaks fixation)
        self.move_eye_to_get_reward('break')

        # Now wait for break fixation, make sure square is turned off
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task == 6:
                no_change = False
        self.assertFalse(self.w.sequences.square.square.getParent())

    def test_square_turns_off_after_missed_fixation(self):
        print 'square turns off after missed fixation'
        # First get to square on
        square_off = True
        # make sure looking at right place (not fixation)
        self.move_eye_to_get_reward('not')
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
        print 'first loop over'
        # Now wait for 5, bad fixation. We should now have turned off the square,
        # and next will turn on the square after a missed fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task == 6:
                no_change = False
        self.assertFalse(self.w.sequences.square.square.getParent())

    def test_repeats_same_square_if_breaks_fixation(self):
        # First get to square on
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
            if self.w.sequences.current_task is None:
                self.w.start_main_loop()
        # find out where the square is...
        square_pos = self.w.sequences.square.square.getPos()
        # print 'about to break, square is ', square_pos
        # make sure looking at right place (breaks fixation)
        self.move_eye_to_get_reward('break')
        # now force self.w.sequences.current_task to change so fixation breaks
        no_change = True
        test = 1
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task != test:
                if test == 1:
                    test = self.w.sequences.current_task
                else:
                    no_change = False
        print 'current task', self.w.sequences.current_task
        # 6 is broken fixation
        self.assertEqual(self.w.sequences.current_task, None)
        new_square_pos = self.w.sequences.square.square.getPos()
        print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

    def test_repeats_same_square_if_no_fixation(self):
        # First get to square on
        square_off = True
        # print 'not looking at ', square_pos
        # make sure looking at right place (not fixation)
        self.move_eye_to_get_reward('not')
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
            if self.w.sequences.current_task is None:
                self.w.start_main_loop()
        # find out where the square is...
        square_pos = self.w.sequences.square.square.getPos()
        # Now wait for None. This means we are about to turn on the square again after
        # missed fixation
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task is None:
                no_change = False
        new_square_pos = self.w.sequences.square.square.getPos()
        # print 'should be in same place', new_square_pos
        self.assertEqual(square_pos, new_square_pos)

    def test_square_turns_on_after_move(self):
        count = 0
        square_off = True
        last = self.w.sequences.current_task
        not_moved = True
        # do a full loop where we get reward, double check it moves, and then check to make sure
        # square turns on again
        while square_off:
            taskMgr.step()
            # print count
            # need to check for frameTask.now to change to 1 the second time
            # (first time is just the beginning of the task, before moving)
            # if taskTask.now changes to 1, then we have just turned on
            # sometimes, especially with off-screen, the timing isn't accurate,
            # and we have to calls to the same function right in a row. Make sure
            # when frameTask.now is one, it is changing from something else.
            if self.w.sequences.current_task != last:
                last = self.w.sequences.current_task
                print last
            if last is None:
                print 'None, restart'
                # last will only be None at end
                self.w.start_main_loop()
                count = 1
            if last == 1 and count == 1:
                # print 'square should be on for second time'
                square_off = False
            if last == 1 and count == 0 and not_moved:
                self.move_eye_to_get_reward()
                not_moved = False
        self.assertTrue(self.w.sequences.square.square.getParent())

    def test_timing_on_to_fade_if_fixated(self):
        # once subject fixates, on for fix_interval
        # First get to on
        square_off = True
        a = 0
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                a = datetime.datetime.now()
                square_off = False
        # make sure looking at right place
        self.move_eye_to_get_reward()
        # now wait for fade:
        square_on = True
        while square_on:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 2:
                # print 'square should be on'
                square_on = False
        b = datetime.datetime.now()
        c = b - a
        # print 'c', c.total_seconds()
        # check that time is close
        # print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.sequences.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # use fix interval, since fake data will start it right away in fixation window
        self.assertAlmostEqual(c.total_seconds(), self.config['FIX_INTERVAL'][0], 1)

    def test_timing_stimulus_up_if_not_fixated(self):
        # if not fixated, will be on for on duration, then reset
        # First get ready for square on.
        # make sure looking at right (wrong) place
        square_off = True
        square_on = True
        a = 0
        b = 0
        # print(self.w.sequences.square.square.getParent())
        # print 'start'
        self.move_eye_to_get_reward('not')
        while square_off:
            taskMgr.step()
            a = datetime.datetime.now()
            # if square is parented to render, it is on, otherwise has no parent
            if self.w.sequences.square.square.getParent():
                # print 'square should be on'
                square_off = False
        # now wait for square to turn back off:
        # print 'next loop'
        while square_on:
            taskMgr.step()
            if not self.w.sequences.square.square.getParent():
                b = datetime.datetime.now()
                # print 'square should be off'
                square_on = False

        c = b - a
        # this is consistently off by about 0.07s in tests, but not off when actually
        # running the task and not running 'offscreen'. Must have something to do with
        # the frame rate Panda3d assumes when running offscreen. This is the only task
        # where this shows up, and it is the only task where I am actually checking the
        # rendering (all others I have 'better?' ways of testing. Hmmm.
        #
        c = c + datetime.timedelta(seconds=0.05)
        # print 'c', c.total_seconds()
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
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 2, then we have just changed color
            if self.w.sequences.current_task == 2:
                # print 'square should be faded'
                square_dim = False
        # now wait for fade off:
        # print 'square should be faded'
        while square_fade:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.sequences.current_task > 2:
                # print 'square should be off'
                square_fade = False
        c = b - a
        # print 'square should be off'
        # print 'c', c.total_seconds()
        # check that time is close
        # print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really off, sanity check
        self.assertFalse(self.w.sequences.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_timing_off_to_reward(self):
        # make sure time to reward accurate
        # this is problematic, because it is zero in our usual configuration (which is
        # why we skip right over next = 3. So, I think what makes the most sense is making
        # sure that square off to move is the same as reward interval + move interval
        self.move_eye_to_get_reward()
        # First get to on, move eye to get reward, then go to off
        square_on = True
        fade = False
        no_reward = True
        a = 0
        b = 0
        while square_on:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.sequences.current_task == 1 and not fade:
                # if we go on during loop, might not be in correct place
                self.move_eye_to_get_reward()
                fade = True
            if not self.w.sequences.square.square.getParent() and fade:
                # square is off
                # print 'square should be off'
                square_on = False
                # now wait for move/on:
        # now wait for reward
        print 'wait for '
        while no_reward:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 4, then we have reward
            if self.w.sequences.current_task == 4:
                # print 'reward'
                no_reward = False
        c = b - a
        print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        config_time = self.config['REWARD_INTERVAL'][0]
        self.assertAlmostEqual(c.total_seconds(), config_time, 1)

    # ## if I run this as a suite, this does not wait for reward times, but if I run it by itself, it does
    # ## meh, can't figure out what is screwing up timing. clearly there is still some residue from the last
    # ## test, but can't figure out what it may be.
    def test_timing_reward_to_on(self):
        # First get to reward
        # print self.w.interval_list
        no_reward = True
        square_off = True
        a = 0
        b = 0
        self.move_eye_to_get_reward()
        fade = False
        while no_reward:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.sequences.current_task == 1 and not fade:
                # if we go on during loop, might not be in correct place
                self.move_eye_to_get_reward()
                fade = True
            # if taskTask.now changes to 4, then we just started reward,
            # however we have to wait for all of the reward to be given,
            # but for testing this should be zero, since not using pydaq
            if self.w.sequences.current_task == 4:
                print 'test: reward'
                no_reward = False
        # now wait for move/on:
        print 'reward'
        previous = self.w.sequences.current_task
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            if self.w.sequences.current_task != previous:
                print('test:', self.w.sequences.current_task)
                previous = self.w.sequences.current_task
            if self.w.sequences.current_task is None:
                print 'loop'
                self.w.start_main_loop()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                print 'square should be on'
                square_off = False
        c = b - a
        print 'c', c.total_seconds()
        # check that time is close
        # print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.sequences.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # move interval is from start of reward until move, so includes time it takes
        # for reward
        delay = self.config['MOVE_INTERVAL'][0]
        self.assertAlmostEqual(c.total_seconds(), delay, 1)

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
        print 'where we are', self.w.sequences.current_task
        self.assertTrue(self.w.sequences.current_task is None)
        # print('next', last)
        square_on = True
        square_off = True
        a = 0
        b = 0
        while square_on:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.sequences.current_task > 0:
                if not self.w.sequences.square.square.getParent():
                    # square turned off
                    square_on = False
                    # print 'square off, I think'
                    # print self.w.sequences.current_task
        # now wait for square to turn back on
        print 'next loop'
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            if self.w.sequences.current_task is None:
                self.w.start_main_loop()
            if self.w.sequences.square.square.getParent():
                # print('square should be back on')
                square_off = False
        c = b - a
        print 'c', c.total_seconds()
        # check that time is close
        # print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # the break is the move interval + break interval
        break_time = self.config['BREAK_INTERVAL'][0] + self.config['MOVE_INTERVAL'][0]
        self.assertAlmostEqual(c.total_seconds(), break_time, 1)

    def test_reward_for_looking(self):
        # First get to square on
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
            if self.w.sequences.current_task is None:
                self.w.start_main_loop()
        # make sure looking at right place
        print 'move eye, I hope'
        self.move_eye_to_get_reward()
        print 'current task', self.w.sequences.current_task
        no_reward = True
        now = self.w.sequences.current_task
        # wait for reward
        while no_reward:
            taskMgr.step()
            if now != self.w.sequences.current_task:
                now = self.w.sequences.current_task
                print 'now', now
            # if taskTask.now changes to 4, then getting reward
            if self.w.sequences.current_task == 4:
                no_reward = False
        self.assertTrue(self.w.num_reward > 1)

    def test_no_reward_if_not_looking(self):
        # First get ready for square on.
        # make sure looking at right (wrong) place
        # move eye away from square
        self.move_eye_to_get_reward('not')
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
        # now wait for self.w.sequences.current_task to change again, will run through
        # turning off, bad fixation and switch to None all at once
        no_change = True
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task != 1:
                no_change = False
        print 'end second loop', self.w.sequences.current_task
        # next step should not be reward or square dims, should be
        # 6, bad fixation
        self.assertNotEqual(self.w.sequences.current_task, 2)
        self.assertNotEqual(self.w.sequences.current_task, 3)
        self.assertEqual(self.w.sequences.current_task, 6)

    def test_no_reward_if_look_but_break_fixation(self):
        # First get to square on
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.sequences.current_task == 1:
                # print 'square should be on'
                square_off = False
        # make sure looking at right place
        self.move_eye_to_get_reward('break')
        # we will fixate, and then break fixation, so wait for
        # self.w.sequences.current_task to change twice, then should be
        # 6, since we broke fixation
        no_change = True
        now = 1
        while no_change:
            taskMgr.step()
            if self.w.sequences.current_task != now:
                if self.w.sequences.current_task == 5:
                    now = 5
                else:
                    no_change = False
        # next step should not be reward or square dims, should be
        # square turns on (without moving)
        self.assertNotEqual(self.w.sequences.current_task, 2)
        self.assertNotEqual(self.w.sequences.current_task, 3)
        self.assertEqual(self.w.sequences.current_task, 6)

    def move_eye_to_get_reward(self, no_reward=None):
        print 'Attempting to move eye'
        # find out where the square is...
        # default is stays in fixation window for reward
        square_pos = self.w.sequences.square.square.getPos()
        print square_pos
        variance = 0.001
        start_pos = (square_pos[0], square_pos[2])
        # default is put eye in square
        if no_reward == 'not':
            # put eye way outside of all possible targets
            # print 'not'
            start_pos = (2000, 2000)
        elif no_reward == 'break':
            # print 'break'
            # start out at fixation, but move out quickly
            variance = 20
        print 'eye start', start_pos
        # print 'variance', variance
        self.w.start_eye_data(start_pos, variance)
        print 'moved eye'

    def tearDown(self):
        print 'tearDown'
        # clear out any half-finished tasks
        if self.w.sequences.current_task is not None:
            self.finish_loop()
        self.w.end_gig()
        print 'task mgr at tear down', self.w.base.taskMgr


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
