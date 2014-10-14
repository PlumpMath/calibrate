import unittest
from panda3d.core import loadPrcFileData
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from time import time
import sys
import os

# Tests run fine one at a time, but on Windows, isn't destroying
# the ShowBase instance between suites, for some crazy reason. Meh.
# So, to run in Windows, have to comment out one suite, run once,
# change class_switch to True, run again. Switch everything back.


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
        if manual:
            print 'starting tests using manual'
        else:
            print 'starting tests using random'
        print manual
        loadPrcFileData("", "window-type offscreen")
        #print 'about to load world'
        cls.w = World(manual, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        print 'setup'
        self.w.start_gig()
        print 'started new gig'
        #is it a problem that we start the timer for auto here?
        self.w.start_loop()
        print('setup done')

    def do_a_loop(self):
        # does a full loop if just starting, finishes the current
        # loop if you have already started
        print 'do a loop'
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
                if now > 0:
                    test = 0
            if now == test:
                first_loop = False
        print 'end loop'

    def much_looping(self):
        print 'start test'
        self.do_a_loop()
        print 'now step'
        for i in range(100):
            print('step', i)
            print('next', self.w.next)
            taskMgr.step()

    def test_no_square(self):
        """
        Should start with a blank screen, square has no parent, not rendered.
        This happens at beginning (next = 0) and anytime when about to get reward (next = 3)
        or for random when 0 again.
        Can't guarantee this is run at beginning, but sufficient to check that square is not
        rendered for these two conditions
        """
        #print self.w.square.getParent()
        #
        #self.w.start_loop()
        if self.w.next != 0:
            square_on = True
            while square_on:
                taskMgr.step()
                #if self.w.next == 3  or self.w.next == 0:
                if self.w.next == 0:
                    square_on = False
        self.assertFalse(self.w.square.square.getParent())
        # finish the loop
        self.do_a_loop()

    def test_square_turns_on(self):
        """
        The square should turn on when next is 1
        """
        #time_out = time.time() + 2.1
        #start_time =
        #self.w.start_loop()
        square_off = True
        while square_off:
        #while time.time() < time_out:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next == 1:
                #print 'square should be on'
                square_off = False
        self.assertTrue(self.w.square.square.getParent())

    def test_square_turns_off(self):
        # for auto, will not turn off by hitting next = 4,
        # because will not fixate and will time out instead.
        # in this case, go until cleanup, where it turns to 0
        # and square turns off
        #self.w.start_loop()
        square_dim = True
        match = 4
        if not self.w.manual:
            match = 1
            # go through until match is not zero,
            # then we know we are turning off, and not
            # just never going on.
            while square_dim:
                taskMgr.step()
                if self.w.next == match:
                    square_dim = False
            square_dim = True
            match = 0
        while square_dim:
            taskMgr.step()
            if self.w.next == match:
                square_dim = False
        self.assertFalse(self.w.square.square.getParent())

    def test_eye_data_written_to_file(self):
        # when run as a suite, files don't seem to open and close fast enough, so
        # eye positions can get pretty far along before actually making it into the
        # log file, so using all of the data
        #print 'what time is it?'
        test = time()
        #self.w.start_loop()
        print('manual is', self.w.manual)
        #last = self.w.next
        #no_change = True
        self.do_a_loop()
        eye_data = self.w.eye_data
        file_name = self.w.eye_file_name
        #print self.w.eye_data[:10]
        # make sure files are closed
        self.w.cleanup()
        self.w.end_gig()
        print(self.w.eye_file_name)
        print file_name
        # since we are using fake data, know that first point is (0,0)
        f = open(self.w.eye_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        #print('what is actually in file after timestamp line')
        my_line = f.readline()
        print my_line
        print 'what else you got?'
        print(f.readline())
        print(f.readline())
        print(f.readline())
        print(f.readline())
        f.close()
        check_data = None
        for eye in eye_data:
            #print(eye[0])
            if str(eye[0]) in my_line:
                check_data = str(eye[0])
                print check_data
                break
        self.assertIn(check_data, my_line)
        # time is a floating point in seconds, so if we just
        # check to see if the digits from the 10s place on up
        # are there, we know we have a time stamp from the last
        # 100 seconds in the file, and that is good enough, we
        # know there is a time stamp, and it is unlikely that
        # one of the eye positions had these exact numbers
        time_check = int(test - (test % 100)) / 100
        self.assertIn(str(time_check), my_line)

    def test_tasks_and_timestamp_written_to_file(self):
        #print('manual?', self.w.manual)
        #self.w.start_loop()
        # make sure data is written to file.
        # do a loop
        self.do_a_loop()
        #print 'task now', self.w.next
        # need to make sure file is closed
        self.w.end_gig()
        #print self.w.time_file_name
        f = open(self.w.time_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        test_line = f.readline()
        # should always be starting with square on...
        self.assertIn('Square', test_line)

    def test_change_from_manual_to_auto_or_vise_versa(self):
        # I think it shouldn't matter if we don't switch back,
        # since everything should work either way, and we change
        # into the opposite direction the next time through\
        #self.w.start_loop()
        before = self.w.manual
        #print before
        self.w.flag_task_switch = True
        self.do_a_loop()
        # now make sure it changed.
        after = self.w.manual
        #print after
        self.assertNotEqual(before, after)

    def tearDown(self):
        print 'tearDown'
        # clear out any half-finished tasks
        taskMgr.step()
        self.w.cleanup()
        self.w.end_gig()
        os.remove(self.w.eye_file_name)


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    #print 'run suite'
    # run twice to cover both conditions
    if len(sys.argv) == 2 and is_int_string(sys.argv[1]):
        manual = True
        if int(sys.argv[1]) == 0:
            manual = False
        result = unittest.TextTestRunner(verbosity=2).run(suite())
        if not result.wasSuccessful():
            sys.exit(1)
    else:
        manual = False
        unittest.main(verbosity=2)