import unittest
from panda3d.core import loadPrcFileData
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from time import time
import sys


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
    # codes for w.current_task
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
        # print 'about to load world'
        cls.w = World(manual, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        print 'setup'
        self.w.start_gig()
        print 'started new gig'
        # is it a problem that we start the timer for auto here?
        self.w.start_main_loop()
        print('setup done')

    def finish_loop(self):
        # does a full loop if just ended, finishes the current
        # loop if you have already started
        # always ends at cleanup
        print 'finish loop'
        taskMgr.step()
        if self.w.current_task is None:
            print 'restarted loop'
            self.w.start_main_loop()
        now = self.w.current_task
        first_loop = True
        print 'now before loop', now
        # check each time we change tasks
        while first_loop:
            taskMgr.step()
            if self.w.current_task != now:
                print('took a step', self.w.current_task)
                now = self.w.current_task
                if now is None:
                    first_loop = False
        print 'end loop'

    def much_looping(self):
        print 'start test'
        self.finish_loop()
        print 'now step'
        for i in range(100):
            print('step', i)
            print('next', self.w.current_task)
            taskMgr.step()

    def test_square_turns_on(self):
        """
        The square should turn on when next is 1
        """
        # time_out = time.time() + 2.1
        # start_time =
        # self.w.start_main_loop()
        square_off = True
        while square_off:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.current_task == 1:
                # print 'square should be on'
                square_off = False
        self.assertTrue(self.w.square.square.getParent())

    def test_square_turns_off(self):
        """
        Square should go off at current_task is 3. At that point, make sure square has no parent,
        so not rendered, if task higher than 2.
        For random, if there is no fixation, never makes it to 2, so make sure off when None
        (wait period before start of trial)
        """
        # print self.w.square.getParent()
        #
        # self.w.start_main_loop()
        now = self.w.current_task
        if self.w.current_task != 0:
            square_on = True
            while square_on:
                taskMgr.step()
                if self.w.current_task != now:
                    print 'currently', self.w.current_task
                    now = self.w.current_task
                if self.w.current_task is None or self.w.current_task > 2:
                    square_on = False
                # if self.w.current_task == 3  or self.w.current_task == 0:
        print 'check if on'
        self.assertFalse(self.w.square.square.getParent())
        # finish the loop
        self.finish_loop()

    def test_eye_data_written_to_file(self):
        # since this is fake data, the first data point should always be (0, 0)
        # we are also going to make sure that there is a reasonable
        # time stamp
        # print 'what time is it?'
        test = time()
        # do a loop, make sure there is data
        self.finish_loop()
        # make sure files are closed before opening them up
        # for reading
        self.w.end_gig()
        print(self.w.logging.eye_file_name)
        f = open(self.w.logging.eye_file_name, 'r')
        # the first line is a header
        self.assertIn('timestamp', f.readline())
        my_line = f.readline()
        # print my_line
        f.close()
        # since we are using fake data, know that first point is (0,0)
        check_data = '0.0, 0.0'
        self.assertIn(check_data, my_line)
        # time is a floating point in seconds, so if we just
        # check to see if the digits from the 10s place on up
        # are there, we know we have a time stamp from the last
        # 100 seconds in the file, and that is good enough, we
        # know there is a time stamp, and it is unlikely that
        # one of the eye positions had these exact numbers
        time_check = int(test - (test % 100)) / 100
        self.assertIn(str(time_check), my_line)
        print 'end check eye data written to file'

    def test_tasks_and_timestamp_written_to_file(self):
        # print('manual?', self.w.manual)
        # self.w.start_main_loop()
        # make sure data is written to file.
        # do a loop
        self.finish_loop()
        # print 'task now', self.w.current_task
        # need to make sure file is closed
        self.w.end_gig()
        # print self.w.logging.time_file_name
        f = open(self.w.logging.time_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        # next line gives tolerance, if random mode
        if not self.w.manual:
            self.assertIn('Tolerance', f.readline())
        # get offset and gain
        self.assertIn('Gain', f.readline())
        self.assertIn('Offset', f.readline())
        # should always be starting with square on...
        self.assertIn('Square', f.readline())

    def test_change_from_manual_to_auto_or_vise_versa(self):
        # I think it shouldn't matter if we don't switch back,
        # since everything should work either way, and we change
        # into the opposite direction the next time through\
        # self.w.start_main_loop()
        before = self.w.manual
        # print before
        self.w.flag_task_switch = True
        print 'switched tasks'
        self.finish_loop()
        # now make sure it changed.
        after = self.w.manual
        # print after
        self.assertNotEqual(before, after)

    def tearDown(self):
        print 'tearDown'
        # clear out any half-finished tasks
        if self.w.current_task is not None:
            self.finish_loop()
        self.w.end_gig()

        # os.remove(self.w.logging.eye_file_name)


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    # print 'run suite'
    # run twice to cover both conditions
    if len(sys.argv) == 2 and is_int_string(sys.argv[1]):
        manual = 1
        if int(sys.argv[1]) == 0:
            manual = 0
        result = unittest.TextTestRunner(verbosity=2).run(suite())
        if not result.wasSuccessful():
            sys.exit(1)
    else:
        manual = 1
        unittest.main(verbosity=2)
