import unittest
from panda3d.core import loadPrcFileData
from panda3d.core import Point3
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
import sys
import datetime

# Tests run fine one at a time, but isn't destroying the ShowBase
# instance between tests. Panda3d peeps are working on this.
# don't use next == 3, as it does it so fast internally in calibration,
# that it next appears to jump from 2 to 4 here.


def is_int_string(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class TestCalibration(unittest.TestCase):
# task.time is not very accurate when running off-screen
#            0: self.square_on,
#            1: self.square_fade,
#            2: self.square_off,
#            3: self.square_move}

    @classmethod
    def setUpClass(cls):
        loadPrcFileData("", "window-type offscreen")
        # all these tests are for manual
        # manual move is mode 1

        cls.w = World(1, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        self.config = {}
        execfile('config_test.py', self.config)
        self.w.start_gig()
        self.w.start_loop()

    def do_a_loop(self):
        # does a full loop if just starting, finishes the current
        # loop if you have already started
        #print 'do a loop'
        test = None
        now = self.w.next
        first_loop = True
        # check each time we change tasks
        # once we get to step 1, can look for the next
        # step zero
        while first_loop:
            taskMgr.step()
            if self.w.next != now:
                #print('do_a_loop', self.w.next)
                now = self.w.next
                if now > 1:
                    test = 0
            if now == test:
                first_loop = False
        #print 'end loop'

    def test_square_fades(self):
        print 'test_square_fades'
        # we may change the actual colors, so just make sure the
        # color before and after the switch are different
        old_color = self.w.square.square.getColor()
        #print 'color', old_color
        square_on = True
        old_step = self.w.next
        print('current step', old_step)
        while square_on:
            taskMgr.step()
            if self.w.next != old_step:
                old_step = self.w.next
                print old_step
            if self.w.next == 2:
                #print 'square should be dim'
                square_on = False
        #print self.w.square.square.getColor()
        self.assertNotEqual(self.w.square.square.getColor(), old_color)

    def test_reward_after_square_off(self):
        print('test_reward_after_square_off')
        # should get reward automatically if on manual
        # check to make sure self.w.num_reward increments
        self.w.keys["switch"] = 7
        no_reward = True
        current_reward = self.w.num_reward
        new_reward = self.w.num_reward
        print current_reward
        while no_reward:
            taskMgr.step()
            #print self.w.next
            new_reward = self.w.num_reward
            if self.w.next > 3:
                no_reward = False
        print new_reward
        self.assertNotEqual(current_reward, new_reward)

    def test_manual_move(self):
        print('test_manual_move')
        # do a full loop
        # check position changed
        #self.w.set_manual(self.config, True)
        old_position = self.w.square.square.getPos()
        # and move
        self.w.keys["switch"] = 8
        # do a loop, so it has a chance to read the switch
        self.do_a_loop()
        # should now be in new position
        #print self.w.keys["switch"]
        #print 'old position', old_position
        self.assertNotEqual(self.w.square.square.getPos(), old_position)

    def test_square_moves_to_center_if_no_keypress(self):
        print('test_square_moves_to_center_if_no_keypress')
        # don't send keypress
        # check position changed/remained in center
        self.do_a_loop()
        #print self.w.square.square.getPos()
        self.assertEqual(self.w.square.square.getPos(), Point3(0, 55, 0))

    def test_on_after_manual_move(self):
        print('test_on_after_manual_move')
        # make sure square goes on after manual move
        # wait for square to turn off, then send signal to move
        signal = False
        while not signal:
            taskMgr.step()
            #print self.w.next
            if self.w.next > 3:
                signal = True
        print 'done with first loop'
        # make sure square is off
        before = self.w.square.square.getParent()
        # and move
        self.w.keys["switch"] = 3
        # we wait until it comes back on
        print 'sent key switch signal'
        square_off = True
        while square_off:
            taskMgr.step()
            #print self.w.next
            # does not loop automatically in unittest mode
            if self.w.next == 0:
                self.w.start_loop()
            if self.w.next == 1:
                square_off = False
        #print 'move'
        #print self.w.square.square.getParent()
        self.assertTrue(self.w.square.square.getParent())
        #print 'next test?'
        # double check square was off to begin with
        self.assertNotEqual(self.w.square.square.getParent(), before)

    def test_manual_move_after_second_keypress(self):
        print('test_manual_move_after_second_keypress')
        # need to make sure still works after first cycle...
        # and move
        self.w.keys["switch"] = 3
        #print 'step'
        self.do_a_loop()
        #print self.w.keys["switch"]
        old_position = self.w.square.square.getPos()
        print 'move again'
        # and move again
        self.w.keys["switch"] = 4
        # and loop again
        self.w.start_loop()
        self.do_a_loop()
        self.assertNotEqual(self.w.square.square.getPos(), old_position)

    def test_timing_on_to_fade(self):
        print('test_timing_on_to_fade')
        # First get to on
        square_off = True
        #print 'time on to fade'
        a = 0
        b = 0
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        # now wait for fade:
        square_on = True
        while square_on:
        #while time.time() < time_out:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == 2:
                #print 'square should be faded'
                square_on = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        # make sure really on, sanity check
        self.assertTrue(self.w.square.square.getParent())
        interval = self.config['ON_INTERVAL'][0]
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), interval, 1)

    def test_timing_on_to_fade_after_manual_move(self):
        print('test_timing_on_to_fade_after_manual_move')
        # We turn on at the same time we move, so check the
        # interval between turning on and fading, which will
        # be when self.w.next switches to 2.
        self.do_a_loop()
        self.w.start_loop()
        # and move
        self.w.keys["switch"] = 3
        #print 'check time'
        b = 0
        a = 0
        # we have set move,
        # we wait until it comes back on
        square_off = True
        while square_off:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.next == 1:
                # okay, should be on now
                square_off = False
        # need to stop when square fades
        square_on = True
        while square_on:
            taskMgr.step()
            b = datetime.datetime.now()
            if self.w.next == 2:
                square_on = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.square.getParent())
        # make sure timing within 2 places
        self.assertAlmostEqual(c.total_seconds(), self.config['ON_INTERVAL'][0], 1)

    def test_timing_fade_on_to_off(self):
        print('test_timing_fade_on_to_off')
        # First get to fade on
        square_dim = True
        square_fade = True
        a = 0
        b = 0
        while square_dim:
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 2, then we have just faded
            if self.w.next == 2:
                #print 'square should be faded'
                square_dim = False
        # now wait for fade off:
        while square_fade:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 3, then we have just turned off
            # if reward interval is zero (usual for our configs), will skip
            # 3 and go to 4, but that is fine, since we are then measuring
            # the same interval
            if self.w.next > 2:
                square_fade = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really off, sanity check
        self.assertFalse(self.w.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        self.assertAlmostEqual(c.total_seconds(), self.config['FADE_INTERVAL'][0], 1)

    def test_timing_off_to_reward(self):
        print('test_timing_off_to_reward')
        # this is problematic, because it is zero in our usual configuration (which is
        # why we skip right over next = 3. So, I think what makes the most sense is making
        # sure that square off to move is the same as reward interval + move interval
        # First get to off
        square_fade = True
        square_not_moved = True
        a = 0
        b = 0
        while square_fade:
            #while time.time() < time_out:
            taskMgr.step()
            a = datetime.datetime.now()
            # if taskTask.now changes to 3, then we have just turned off
            if self.w.next > 2:
                #print 'square should be off'
                square_fade = False
                # now wait for move/on:
        #print 'out of first loop'
        # make sure switching doesn't screw up timing
        self.w.keys["switch"] = 3
        # now wait for reward, when move changes, we are done with reward
        # and ready for moving
        while square_not_moved:
            #while time.time() < time_out:
            taskMgr.step()
            b = datetime.datetime.now()
            # 1 is square just turned on
            #if self.w.next == 0:
            #    self.w.start_loop()
            if self.w.next == 0:
                #print 'square should have moved'
                square_not_moved = False
        c = b - a
        #print 'c', c.total_seconds()
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        config_time = self.config['REWARD_INTERVAL'][0] + self.config['MOVE_INTERVAL'][0]
        self.assertAlmostEqual(c.total_seconds(), config_time, 1)

    def test_timing_move_to_on(self):
        # moved when next is 4
        print 'test_timing_move_to_on'
        # and move
        self.w.keys["switch"] = 8
        square_not_moved = True
        square_off = True
        a = 0
        b = 0
        while square_not_moved:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.next == 4:
                square_not_moved = False

        #print 'next loop'
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 0:
                self.w.start_loop()
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # checking move interval, not actually moving, but this is the time
        # from off to move/on, which we do without the moving part...
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def test_waits_correct_time_with_no_keypress(self):
        print('test_waits_correct_time_with_no_keypress')
        # if we don't press a key, do we still wait the correct
        # time before we move?
        square_not_moved = True
        square_off = True
        a = 0
        b = 0
        while square_not_moved:
            taskMgr.step()
            a = datetime.datetime.now()
            if self.w.next == 4:
                square_not_moved = False

        #print 'next loop'
        while square_off:
            taskMgr.step()
            b = datetime.datetime.now()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 0:
                self.w.start_loop()
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        c = b - a
        #print 'c', c.total_seconds()
        # check that time is close
        #print 'c should be', self.config['MOVE_INTERVAL'][0]
        # make sure really on, sanity check
        self.assertTrue(self.w.square.square.getParent())
        # make sure timing within 1 place, won't be very accurate.
        # but close enough to have correct interval
        # checking move interval, not actually moving, but this is the time
        # from off to move/on, which we do without the moving part...
        self.assertAlmostEqual(c.total_seconds(), self.config['MOVE_INTERVAL'][0], 1)

    def tearDown(self):
        print 'tearDown'
        # clear out any half-finished tasks
        self.w.manual_sequence.finish()
        taskMgr.step()
        self.w.cleanup()
        self.w.end_gig()


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    if len(sys.argv) == 2 and is_int_string(sys.argv[1]):
        result = unittest.TextTestRunner(verbosity=2).run(suite())
        if not result.wasSuccessful():
            sys.exit(1)
    else:
        manual = True
        unittest.main(verbosity=2)