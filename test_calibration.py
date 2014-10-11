import unittest
from panda3d.core import loadPrcFileData
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from time import time
import types
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
# codes for w.next
#            0: self.square_on,
#            1: self.square_fade,
#            2: self.square_off,
#            3: self.square_move}

    @classmethod
    def setUpClass(cls):
        if manual:
            print 'starting tests using manual'
            cls.manual = 1
        else:
            print 'starting tests using random'
            cls.manual = 0
        loadPrcFileData("", "window-type offscreen")
        #print 'about to load world'
        cls.w = World(cls.manual, 'config_test.py')
        cls.w.setup_game()

    def setUp(self):
        #print 'setup'
        self.depth = 0
        self.w.start_loop()
        #print('setup done')

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
        if self.w.next != 0:
            square_on = True
            while square_on:
                taskMgr.step()
                #if self.w.next == 3  or self.w.next == 0:
                if self.w.next == 0:
                    square_on = False
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

    def test_square_turns_off(self):
        square_dim = True
        match = 0
        while square_dim:
            taskMgr.step()
            if self.w.next == match:
                square_dim = False
        self.assertFalse(self.w.square.getParent())

    def test_eye_data_written_to_file(self):
        # make sure data is written to file.
        # this is a little tricky, since we don't know where the data is going to be
        # in the file, depends on where we were when we opened the file. Assume that
        # the data file was opened within the first ten time stamps
        #print('manual is', self.w.manual)
        last = self.w.next
        no_change = True
        test = 0
        while no_change:
            taskMgr.step()
            # if taskTask.now changes to 1, then we have just turned on
            if self.w.next != last:
                #print 'we did something'
                no_change = False
                test = time()

        eye_data = self.w.eye_data[:10]
        #print self.w.eye_data[:10]
        # need to stop task, so file is closed
        self.w.close()
        #print(self.w.eye_file_name)
        # since we are using fake data, know that first point is (0,0)
        f = open(self.w.eye_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        #print('what is actually in file after timestamp line')
        my_line = f.readline()
        check_data = None
        for eye in eye_data:
            #print(eye[0])
            if str(eye[0]) in my_line:
                check_data = str(eye[0])
                break
        self.assertIn(check_data, my_line)
        # time is a floating point in seconds, so if we just
        # check to see if the digits from the 10s place on up
        # are there, we know we have a time stamp from the last
        # 100 seconds in the file, and that is good enough, we
        # know there is a time stamp, and it is unlikely that
        # one of the eye positions had these exact numbers
        time_check = int(test - (test % 100)) / 100
        self.assertIn(str(time_check), f.readline())
        f.close()

    def test_tasks_and_timestamp_written_to_file(self):
        #print('manual?', self.w.manual)
        # make sure data is written to file.
        # make sure starts at moving, so will write to file even with random
        start_task = self.w.next
        #print 'start at ', start_task
        no_tasks = True
        # do at least one task
        while no_tasks:
            taskMgr.step()
            if self.w.next != start_task:
                print 'something happened'
                no_tasks = False
        #print 'task now', self.w.next
        # need to stop task, so file is closed
        self.w.close()
        #print self.w.time_file_name
        f = open(self.w.time_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        test_line = f.readline()
        # it is possible reward is the next line, since we don't always start
        # from the beginning.
        #print self.manual
        #print test_line
        if start_task == 3:
            self.assertIn('Reward', test_line)
        elif start_task == 1 and self.manual != 0:
            self.assertIn('no fixation', test_line)
        else:
            self.assertIn('Square', test_line)

    def test_change_from_manual_to_auto_or_vise_versa(self):
        # I think it shouldn't matter if we don't switch back,
        # since everything should work either way, and we change
        # into the opposite direction the next time through
        before = self.w.manual
        #print before
        self.w.flag_task_switch = True
        # run the task long enough to switch
        square_on = True
        last = self.w.next
        #print self.w.next
        while square_on:
            taskMgr.step()
            if self.w.next != last:
                last = self.w.next
            if last == 3 or last == 0:
                square_on = False

        after = self.w.manual
        #print after
        self.assertNotEqual(before, after)

    def test_change_tasks_and_positions_change(self):
        #print('manual is', self.w.manual)
        #print('type', type(self.w.pos))
        self.w.switch_task_flag = True
        # run the task long enough to switch
        last = self.w.next
        #print self.w.next
        square_on = True
        while square_on:
            taskMgr.step()
            if self.w.next != last:
                last = self.w.next
            if last == 3 or last == 0:
                square_on = False
            #print('manual is', self.w.manual)
        #print('type', type(self.w.pos))
        if self.w.manual:
            #print('manual is instance')
            self.assertIsInstance(self.w.pos, types.InstanceType)
            #new_pos = self.w.pos.get_key_position(self.w.depth, 5)
        else:
            #print('not manual, auto is generator')
            self.assertIsInstance(self.w.pos, types.GeneratorType)
            #new_pos = self.w.pos.next()
            #print new_pos
            #switch back - not really the 'correct' way, I know...
            #self.w.change_tasks()
            #print self.w.manual

    def tearDown(self):
        self.w.clear_eyes()
        self.w.close_files()


def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    #print 'run suite'
    # run twice to cover both conditions
    if len(sys.argv) == 2 and is_int_string(sys.argv[1]):
        manual = False
        if int(sys.argv[1]) == 0:
            manual = True
        result = unittest.TextTestRunner(verbosity=2).run(suite())
        if not result.wasSuccessful():
            sys.exit(1)
    else:
        manual = False
        unittest.main(verbosity=2)