import unittest
from panda3d.core import ConfigVariableString
from panda3d.core import loadPrcFileData
from panda3d.core import VBase4
from direct.task.TaskManagerGlobal import taskMgr
from calibration import World
from time import time
import types

# Tests run fine one at a time, but on Windows, isn't destroying
# the ShowBase instance between suites, for some crazy reason. Meh.
# So, to run in Windows, have to comment out one suite, run once,
# change ClassIsSetup to True, run again. Switch everything back.


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
    ClassIsSetup = False
    #ClassIsSetup = True

    def setUp(self):
        print 'setup'
        #if not self.ClassIsSetup:
        #    print "initialize"
        #    self.setupClass()

        self.config = {}
        execfile('config_test.py', self.config)
        self.w.open_files(self.config)
        self.depth = 0
        # make sure we are still in correct mode
        if self.manual == 1:
            self.w.change_tasks(True)
        else:
            self.w.change_tasks(False)
        #print('setup done')

    @classmethod
    def setUpClass(cls):
        if cls.ClassIsSetup:
            print 'class has been run for manual, switch to random'
            cls.manual = 2
        else:
            print 'first time through, run for manual'
            cls.manual = 1
        loadPrcFileData("", "window-type offscreen")
        #print 'about to load world'
        #print 'boo', cls.manual
        cls.w = World(cls.manual, 1)

        # remember it was setup already
        cls.ClassIsSetup = True

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
                if self.w.next == 3 or self.w.next == 0:
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
        # with manual, we don't use 0, and for random we don't use 3...
        if self.manual == 1:
            match = 3
        else:
            match = 0
        while square_dim:
            taskMgr.step()
            if self.w.next == match:
                square_dim = False
        self.assertFalse(self.w.square.getParent())

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
                test = time()
        eye_data = self.w.eye_data[0]
        #print eye_data
        # need to stop task, so file is closed
        self.w.close()
        # since we are using fake data, know that first point is (0,0)
        f = open(self.w.eye_file_name, 'r')
        #print(f.readline())
        self.assertIn('timestamp', f.readline())
        self.assertIn(str(eye_data[0]), f.readline())
        # time is a floating point in seconds, so if we just
        # check to see if the digits from the 10s place on up
        # are there, we know we have a time stamp from the last
        # 10 seconds in the file, and that is good enough, we
        # know there is a time stamp, and it is unlikely that
        # one of the eye positions had these exact numbers
        time_check = int(test - (test % 10)) / 10
        self.assertIn(str(time_check), f.readline())
        f.close()

    def test_tasks_and_timestamp_written_to_file(self):
        # make sure data is written to file.
        # make sure starts at moving, so will write to file even with random
        start_task = self.w.next
        #print 'start at ', start_task
        no_tasks = True
        # do at least one task
        while no_tasks:
            taskMgr.step()
            if self.w.next != start_task:
                #print 'something happened'
                no_tasks = False
        #print 'task now', self.w.next
        # need to stop task, so file is closed
        self.w.close()
        #print self.w.time_file_name
        f = open(self.w.time_file_name, 'r')
        self.assertIn('timestamp', f.readline())
        self.assertIn('start collecting', f.readline())
        test = f.readline()
        # it is possible reward is the next line, since we don't always start
        # from the beginning. If on random, won't fixate
        print self.manual
        if start_task == 3:
            self.assertIn('Reward', test)
        elif start_task == 1 and self.manual != 1:
            self.assertIn('no fixation', test)
        else:
            self.assertIn('Square', test)

    def test_change_from_manual_to_auto_or_vise_versa(self):
        before = self.w.manual
        self.w.change_tasks()
        after = self.w.manual
        # need to change it back, ugh, this is not so cool...
        #self.w.change_tasks()
        self.assertNotEqual(before, after)

    def test_change_tasks_and_positions_change(self):
        #print('manual is', self.w.manual)
        #print('type', type(self.w.pos))
        self.w.change_tasks()
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
        self.w.close_files()

    @classmethod
    def tearDownClass(cls):
        taskMgr.remove(cls.w.frameTask)
        cls.w.close()
        del cls.w
        print 'tore down'

def suite():
    """Returns a suite with one instance of TestCalibration for each
    method starting with the word test."""
    return unittest.makeSuite(TestCalibration, 'test')

if __name__ == "__main__":
    #print 'run suite'
    # run twice to cover both conditions
    unittest.TextTestRunner(verbosity=2).run(suite())
    unittest.TextTestRunner(verbosity=2).run(suite())
    # when you just want to run one test...
    #unittest.main(verbosity=2)

