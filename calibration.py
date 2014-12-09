from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.FunctionInterval import Func, Wait
from direct.task import Task
from panda3d.core import BitMask32
from panda3d.core import WindowProperties, TextNode
from panda3d.core import OrthographicLens, LineSegs
from Square import Square
from Logging import Logging
from positions import visual_angle
import sys
import random
from math import sqrt, radians, cos, sin
from Photos import Photos
# don't always use fake_eye_data, but this just loads the function,
# not the actual data, so no biggie.
from fake_eye_data import yield_eye_data

try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    print 'pydaq loaded'
    LOADED_PYDAQ = True
except ImportError:
    pydaq = None
    print 'Not using PyDaq'
    LOADED_PYDAQ = False


def get_distance(p0, p1):
    """
    (tuple, tuple) -> float
    Returns the distance between 2 points. p0 is a tuple with (x, y)
    and p1 is a tuple with (x1, y1)
    :rtype : tuple
    """
    dist = sqrt((float(p0[0]) - float(p1[0])) ** 2 + (float(p0[1]) - float(p1[1])) ** 2)
    return dist


def check_fixation(eye_data, tolerance, target):
        # expects tolerance in pixels, single float, distance from target allowed
        # expects eye_data and target in a tuple of two floats
        #print 'tolerance', tolerance
        #print 'eye data', eye_data
        #print 'target', target
        distance = get_distance(eye_data, target)
        #print 'distance', distance
        # okay, this works if tolerance is a radius from the center,
        # but not going to work when tolerance is a square.
        if distance > tolerance:
            fixated = False
        else:
            fixated = True
        return fixated


class World(DirectObject):

    def __init__(self, mode=None, config_file=None):
        DirectObject.__init__(self)
        # mode sets whether starts at manual or auto, default is manual, auto is 0
        # Start in auto, if, and only if the input number was a zero,
        if mode == '0' or mode == 0:
            self.manual = False
        else:
            self.manual = True
        #print('manual', self.manual)
        if not config_file:
            config_file = 'config.py'

        # get configurations from config file
        self.config = {}
        execfile(config_file, self.config)
        print 'Subject is', self.config['SUBJECT']
        self.config.setdefault('file_name', config_file)
        print 'Calibration file is', config_file
        # if subject is test, doing unit tests
        if self.config['SUBJECT'] == 'test':
            # doing unittests so use fake eye data and testing configuration.
            # for testing, always leave gain at one, so eye_data and eye_data_to_plot are the same
            self.gain = [1, 1]
            #print 'test'
            self.unittest = True
            self.use_daq_data = False
            self.use_daq_reward = False
        else:
            self.unittest = False
            self.use_daq_data = False  # as opposed to fake data
            self.use_daq_reward = True
            # in case we are not unittesting, but didn't load pydaq
            if not LOADED_PYDAQ:
                self.use_daq_reward = False
                self.use_daq_data = False

        # default is not fake data, and don't send signal
        test_data = self.config.setdefault('FAKE_DATA', False)
        self.config.setdefault('SEND_DATA', False)

        if test_data:
            print('using fake data')

        self.loop_count = 0
        # seems like we can adjust the offset completely in ISCAN,
        # so for now just set it here to zero.
        self.offset = [0, 0]

        # Python assumes all input from sys are string, but not
        # input variables
        # tolerance in degrees, will need to be changed to pixels to be useful,
        # but since tolerance can change (in degrees), makes sense to do this on the fly
        self.tolerance = self.config['TOLERANCE']
        #print 'repeat ', self.config['POINT_REPEAT']

        # assume 0.2 seconds for pump delay, if not set
        self.config.setdefault('PUMP_DELAY', 0.2)

        # start Panda3d
        self.base = ShowBase()

        # check to see if we will be showing photos:
        try:
            self.show_photos = self.config['PHOTO_PATH']
        except KeyError:
            self.show_photos = False

        # This will be the photo object, if we are showing photos
        self.photos = None

        # if no photos, this will always be false, otherwise
        # will switch when showing a photo
        self.fixation_photo_flag = False

        # initialize text before setting up second window.
        # text will be overridden there.
        # text only happens on second window
        # text2 not used anymore, but could be re-implemented,
        # if one was interested in displaying the offset
        self.text = None
        self.text3 = None
        self.text4 = None
        self.text5 = None

        #print base.pipe.getDisplayWidth()
        #print base.pipe.getDisplayHeight()
        # if window is offscreen (for testing), does not have WindowProperties,
        # so can't open second window.
        # if an actual resolution in config file, change to that resolution,
        # otherwise keep going...

        if self.config['WIN_RES'] != 'Test':
            self.gain = self.config['GAIN']
            eye_res = self.setup_window2()
            # text only happens on second window
            self.setup_text(eye_res)
        else:
            # resolution in file equal to test, so use the projector screen
            # value for determining pixels size. In this case, accuracy is not
            # important, because never actually calibrating with this setup.
            resolution = [1280, 800]
            self.deg_per_pixel = visual_angle(self.config['SCREEN'], resolution, self.config['VIEW_DIST'])[0]

        print('gain', self.gain)

        # initialize variable for square positions
        #self.pos = None
        #print 'window loaded'
        self.eye_nodes = []

        # initialize file variables
        self.eye_file_name = ''
        self.time_file_name = ''
        self.eye_data_file = None
        self.time_data_file = None

        # starts out not fixated, and not checking for fixation (will
        # check for fixation when stimulus comes on, if we are doing an auto task)
        self.fixated = False
        self.fixation_check_flag = False

        self.base.setBackgroundColor(115 / 255, 115 / 255, 115 / 255)
        self.base.disableMouse()

        # create dummy variable for square and logging
        self.square = None
        self.logging = None

        # Eye Data
        self.eye_data = []

        # true, clear now, false, plot now, None, do not plot
        self.flag_clear_eyes = None

        # initialize list for eye window
        self.eye_window = []

        # initialize signal to switch tasks (manual - auto)
        self.flag_task_switch = False

        # set up daq for eye and reward, if on windows and not testing
        # testing auto mode depends on being able to control eye position
        self.eye_task = None
        self.reward_task = None
        self.fake_data = None

        self.num_beeps = self.config['NUM_BEEPS']  # number of rewards each time
        self.num_reward = 0  # count number of rewards
        # first task is square_on, which is zero, but we will increment this
        # during the task, so needs to be the last task
        self.next = 0

        # Keyboard stuff:
        # initiate
        self.keys = {"switch": 0}

        # Our intervals
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # reward_interval - time from off to reward
        # move_interval - time from reward to move/on
        # fix_interval - used for auto, how long required to fixate
        # break_interval - used for auto, how long time out before
        #            next square on, if missed or broke fixation
        # on, fade, reward, move
        self.interval_list = [self.config['ON_INTERVAL'], self.config['FADE_INTERVAL'], self.config['REWARD_INTERVAL'],
                              self.config['MOVE_INTERVAL'], self.config['FIX_INTERVAL'], self.config['BREAK_INTERVAL']]

        # initiate sequences
        self.manual_sequence = None
        self.auto_sequence = None
        self.start_auto_sequence = None
        self.square_on_parallel = None

        # Corresponding dictionary for writing to file
        self.sequence_for_file = {
            0: 'Square on',
            1: 'Square dims',
            2: 'Square off',
            3: 'Reward',
            4: 'Square moved'
        }

    def start_gig(self):
        # used when beginning in either auto or manual mode,
        # either at start or after switching
        #print 'start new gig'
         # set up square positions
        self.square.setup_positions(self.config, self.manual)
        if not self.unittest:
            # text4 and text5 change
            self.set_text4()
            self.set_text5()
        # open files
        self.logging.open_files(self.manual, self.tolerance)
        self.logging.log_config('Gain', self.gain)
        self.logging.log_config('Offset', self.offset)
        if not self.config['FAKE_DATA']:
            self.start_eye_task()
        else:
            # start fake data yield, if not using eye tracker
            # start over from zero for testing so we know what
            # first eye position is.
            #print 'get fake data'
            self.fake_data = yield_eye_data((0.0, 0.0))
            self.base.taskMgr.add(self.get_fake_data_task, 'fake_eye')

    def end_gig(self):
        # used when end in either auto or manual mode,
        # either at start or after switching
        #print 'end gig'
        # close stuff
        if not self.config['FAKE_DATA']:
            #print 'stopping daq tasks'
            # have to stop tasks before closing files
            self.eye_task.DoneCallback(self.eye_task)
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        else:
            self.base.taskMgr.remove('fake_eye')
        self.logging.close_files()
        #self.square.pos = None

    def change_tasks(self):
        # change from manual to auto-calibrate or vise-versa
        #print 'change task'
        self.manual = not self.manual
        #print('switched manual?', self.manual)
        # reset stuff
        self.flag_task_switch = False
        self.end_gig()
        self.start_gig()
        # if going from manual to auto, start automatically, otherwise
        # wait for keypress to start.
        if not self.manual:
            self.start_loop()

    def start_loop(self, good_trial=None):
        # good_trial signifies if there was a reward last loop,
        # for photos, we only count good trials
        #print('start loop')
        #print('time', time())
        # starts every loop, either at the end of one loop, or after a break
        # start plotting eye position
        self.flag_clear_eyes = False
        #print('time', time())
        if self.manual:
            #print 'manual'
            self.setup_manual_sequence()
            self.manual_sequence.start()
        else:
            #print 'auto'
            # always start out not fixated
            self.fixated = False
            # check to see if we are showing a photo
            #print('loop count before photo', self.loop_count)
            if self.show_photos:
                if good_trial:
                    self.loop_count += 1
                    #print('good trial, loop count now', self.loop_count)
                #print('loop count', self.loop_count)
                #print self.photos.cal_pts_per_photo
                # check to see if it is time to show a photo
                if self.loop_count == self.photos.cal_pts_per_photo:
                    self.flag_clear_eyes = False
                    self.fixation_photo_flag = True
                    #print 'about to call show photo from start_loop'
                    self.photos.show_photo()
                    #print 'called show photo from start_loop'
                    self.loop_count = 0
                    # if there were no photos, continue on to
                    # calibrations, otherwise, we are done here
                    if self.photos.cal_pts_per_photo is None:
                        #print 'no more photos, continue to regularly scheduled program'
                        self.photo_end = self.photos.end_index
                        # don't need to check for photos now
                        self.show_photos = None
                        self.fixation_photo_flag = False
                    else:
                        return
            #print 'showed calibration point'
            #print('loop count after checking/showing photo', self.loop_count)
            # setup sequences
            self.setup_auto_sequences()
            #print 'turn on timer for square on, waiting for fixation'
            # turn on square and timer
            self.square_on_parallel.start()
        #print('done start loop')
        #print('time', time())

    def cleanup(self):
        #print('cleanup method')
        #print('time', time())
        # end of loop, check to see if we are switching tasks, start again
        self.next = 0
        good_trial = self.num_reward > 0
        self.num_reward = 0
        # if we change tasks, wait for keypress to start again
        if self.flag_task_switch:
            #print 'change tasks'
            self.change_tasks()
        else:
            if not self.unittest:
                #print 'start next loop'
                self.start_loop(good_trial)
                #print('leaving cleanup')
        #print('done cleanup')

    def setup_manual_sequence(self):
        #print 'setup manual sequence'
        all_intervals = self.create_intervals()
        square_on = Func(self.square.turn_on)
        square_fade = Func(self.square.fade)
        square_off = Func(self.square.turn_off)
        give_reward = Func(self.give_reward)
        clear_eyes = Func(self.set_flag_clear_screen)
        square_move = Func(self.square.move_for_manual_position)
        write_to_file = Func(self.write_to_file)
        cleanup = Func(self.cleanup)

        # Parallel does not wait for any doLaterMethods to return before returning itself, which
        # works out pretty awesome, since move interval is suppose to be time from reward start
        # until next trial

        self.manual_sequence = Sequence(
            Parallel(square_on, write_to_file),
            Wait(all_intervals[0]),
            Parallel(square_fade, write_to_file),
            Wait(all_intervals[1]),
            Parallel(square_off, write_to_file),
            Wait(all_intervals[2]),
            Parallel(give_reward, write_to_file, clear_eyes),
            Wait(all_intervals[3]),
            Parallel(square_move, write_to_file),
            cleanup,
        )

    def setup_auto_sequences(self):
        #print 'setup auto sequences'
        # making two "sequences", although one is just a parallel task
        # auto sequence is going to start with square fading
        all_intervals = self.create_intervals()
        square_on = Func(self.square.turn_on)
        end_timer = Func(self.end_fixation_timer)
        square_fade = Func(self.square.fade)
        square_off = Func(self.square.turn_off)
        give_reward = Func(self.give_reward)
        clear_eyes = Func(self.set_flag_clear_screen)
        square_move = Func(self.square.move)
        write_to_file = Func(self.write_to_file)
        cleanup = Func(self.cleanup)
        # check for fixation and set up auto_task as timer
        wait_on = Func(self.start_check_fixation)

        self.square_on_parallel = Parallel(square_on, write_to_file, wait_on)

        # Parallel does not wait for any doLaterMethods to return before returning itself, which
        # works out pretty awesome, since move interval is suppose to be time from reward start
        # until next trial. This would be a problem if there was so much reward that it took up
        # all of the time for the move_interval, but that would be a lot of reward
        #print('pump delay', self.config['PUMP_DELAY'])
        #print('beeps', self.num_beeps)

        self.auto_sequence = Sequence(
            Parallel(square_fade, write_to_file, end_timer),
            Wait(all_intervals[1]),
            Parallel(square_off, write_to_file),
            Wait(all_intervals[2]),
            Parallel(give_reward, write_to_file, clear_eyes),
            Wait(all_intervals[3]),
            Parallel(square_move, write_to_file),
            cleanup,
        )

    ### all tasks
    def wait_between_reward(self, task):
        #print 'give another reward'
        self.reward_task.pumpOut()
        self.num_reward += 1
        if self.num_reward < self.num_beeps:
            return task.again
        #print 'reward done'
        return task.done

    def wait_off_task(self, task):
        #print 'time up, restart'
        #print time()
        # this task will run for the on interval, if there is a fixation, initiate_fixation_period
        # will begin (started from get_eye_data method), if not we start over here
        self.restart_auto_loop()
        #print 'return wait_off_task'
        return task.done

    def wait_auto_sequence_task(self, task):
        #print 'held fixation, start sequence'
        # made it through fixation, will get reward, stop checking for fixation
        self.fixation_check_flag = False
        # so, auto_sequence doesn't return until it has completed the whole
        # sequence, which could mean we have already called the task again before
        # we return. meh. we could remove the task in the sequence, I suppose.
        self.auto_sequence.start()
        return task.done

    def wait_cleanup_task(self, task):
        #print 'move to cleanup'
        #print time()
        self.cleanup()
        return task.done

    def get_fake_data_task(self, task):
        self.get_eye_data(self.fake_data.next())
        return task.cont

    # auto calibrate methods
    def initiate_fixation_period(self):
        #print 'initiate fixation period'
        # subject has fixated, if makes it through fixation interval, will start sequence to get reward, otherwise
        # will abort and start over
        # first stop the on interval
        self.base.taskMgr.remove('auto_off_task')
        self.logging.log_event('Fixated')
        # now start the fixation interval
        fixate_interval = random.uniform(*self.interval_list[4])
        #print('fixate interval', fixate_interval)
        self.base.taskMgr.doMethodLater(fixate_interval, self.wait_auto_sequence_task, 'auto_sequence')

    def end_fixation_timer(self):
        #print 'remove fixation timer'
        self.base.taskMgr.remove('auto_sequence')
        
    def recover_from_broken_fixation(self):
        #print 'recover from broken fixation'
        # method to restart the task if fixation is broken
        # stop auto_sequence from starting
        self.base.taskMgr.remove('auto_sequence')
        #print(self.base.taskMgr)
        self.restart_auto_loop()

    def restart_auto_loop(self):
        #print 'restart auto loop, long pause'
        #print time()
        # stop checking fixation
        self.fixation_check_flag = False
        # make sure there are no tasks waiting
        self.base.taskMgr.removeTasksMatching('auto_*')
        # turn off square
        self.square.turn_off()
        # write to log
        self.logging.log_event(self.sequence_for_file[2])
        self.logging.log_event('No fixation or broken, restart')
        self.set_flag_clear_screen()
        # now wait, and then start over again.
        all_intervals = self.create_intervals()
        # loop delay is normal time between trials + added delay
        loop_delay = all_intervals[5] + all_intervals[3]
        # wait for loop delay, then cleanup and start over
        self.base.taskMgr.doMethodLater(loop_delay, self.wait_cleanup_task, 'auto_cleanup')
        #print(self.base.taskMgr)

    def set_flag_clear_screen(self):
        #print 'remove eye trace and fixation window, if there is one'
        # get rid of eye trace
        self.flag_clear_eyes = True
        # remove window around square
        for win in self.eye_window:
            win.detachNode()

    # sequence methods for both auto and manual
    def create_intervals(self):
        all_intervals = [random.uniform(*i) for i in self.interval_list]
        #print('all intervals', all_intervals)
        return all_intervals

    def give_reward(self):
        #print 'reward, 3'
        #print(self.base.taskMgr)
        # give reward for each num_beeps
        # give one reward right away, have
        # to wait delay before giving next reward
        if self.reward_task:
            #print 'first reward'
            self.num_reward = 1
            self.reward_task.pumpOut()
            # if using actual reward have to wait to give next reward
            self.base.taskMgr.doMethodLater(self.config['PUMP_DELAY'], self.wait_between_reward, 'reward')
        else:
            for i in range(self.num_beeps):
                #print 'beep'
                self.num_reward += 1
        #print 'give reward returns'
        #print('time', time())

    def write_to_file(self):
        #print('now', self.next)
        #print(self.sequence_for_file[self.next])
        # write to file, advance next for next write
        self.logging.log_event(self.sequence_for_file[self.next])
        # if this is first time through, write position of square
        if self.next == 0:
            position = self.square.square.getPos()
            self.logging.log_position(position)
        # next only affects what we are writing to file,
        self.next += 1
        #print('next', self.next)

    ##### Eye Methods
    def start_check_fixation(self):
        #print 'check for fixation'
        #print('should not be fixated', self.fixated)
        # show window for tolerance, if auto
        # and make sure checking for fixation
        # only used for auto
        position = self.square.square.getPos()
        on_interval = random.uniform(*self.interval_list[0])
        #print('on interval', on_interval)
        self.show_window(position)
        self.fixation_check_flag = True
        # start timing for on task, this runs for square on time and waits for fixation,
        # if no fixation, method runs to abort trial
        #print time()
        self.base.taskMgr.doMethodLater(on_interval, self.wait_off_task, 'auto_off_task')
        #print('should still not be fixated', self.fixated)

    def plot_eye_trace(self, last_eye):
        # if plotting too many eye positions, things slow down and
        # python goes into lala land. Never need more than 500, and
        # last 300 is definitely plenty, so every time it hits 500,
        # get rid of first 200.
        if len(self.eye_nodes) > 500:
            #print('get rid of eye nodes', len(self.eye_nodes))
            # Since this just removes the node, but doesn't delete
            # the object in the list, can do this in a for loop,
            for index in range(200):
                self.eye_nodes[index].removeNode()
            # now get rid of the empty nodes in eye_nodes
            #print('new length', len(self.eye_nodes))
            self.eye_nodes = self.eye_nodes[200:]
            #print('new length', len(self.eye_nodes))
        eye = LineSegs()
        # eye.setThickness(2.0)
        eye.setThickness(2.0)
        #print 'last', last_eye
        #print 'now', self.eye_data
        eye.moveTo(last_eye[0], 55, last_eye[1])
        eye.drawTo(self.eye_data[0], 55, self.eye_data[1])
        #print('plotted eye', eye_data_to_plot)
        #min, max = eye.getTightBounds()
        #size = max - min
        #print size[0], size[2]
        node = self.base.render.attachNewNode(eye.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_nodes.append(node)

    def get_eye_data(self, eye_data):
        # pydaq calls this method every time it calls back to get eye data,
        # if testing, self.get_fake_data_task calls this method with fake data
        # We want to change gain on data being plotted, and
        # write eye data (as is, no adjustments) and timestamp to file
        # if we are paused, do not plot eye data (pausing messes up
        # with cleanup), but still collect the data
        self.logging.log_eye(eye_data)
        # when searching for a particular eye data
        # sometimes useful to not print timestamp
        # self.eye_data_file.write(str(eye_data).strip('()') + '\n')
        # convert to pixels for plotting and testing distance,
        # need the eye position from the last run for the starting
        # position for move to position for plotting, and the
        # current eye position for ending position
        if not self.eye_data:
            #print 'use same data for start as finish'
            # if no previous eye, just have same start and
            # end position
            start_eye = self.eye_data_to_pixel(eye_data)
        else:
            #print 'use previous data'
            start_eye = self.eye_data
        #print start_eye
        # save current data, so can use it for start position next time
        self.eye_data = self.eye_data_to_pixel(eye_data)

        # stuff for plotting
        # when unittesting there is no second screen, so
        # impossible to actually plot eye positions or other
        # stuff to researchers screen
        if not self.unittest:
            if self.flag_clear_eyes:
                #print 'clear eyes'
                # get rid of any eye positions left on screen
                self.clear_eyes()
                # don't start plotting until we restart task
                self.flag_clear_eyes = None
            elif self.flag_clear_eyes is None:
                #print 'do not plot eyes'
                pass
            else:
                #print 'plot eyes'
                # plot new eye segment
                self.plot_eye_trace(start_eye)

            if not self.config['FAKE_DATA']:
                self.text3.setText('IScan: [' + str(round(eye_data[0], 3)) +
                                   ', ' + str(round(eye_data[1], 3)) + ']')
            else:
                self.text3.setText('Fake Data: [' + str(round(eye_data[0], 3)) +
                                   ', ' + str(round(eye_data[1], 3)) + ']')

        # check if in window for auto-calibrate
        if self.fixation_check_flag:
            previous_fixation = self.fixated
            target = (self.square.square.getPos()[0], self.square.square.getPos()[2])
            # convert tolerance to pixels
            tolerance = self.tolerance / self.deg_per_pixel
            # send in eye data converted to pixels, self.eye_data
            self.fixated = check_fixation(self.eye_data, tolerance, target)
            #print('fixated?', self.fixated)
            if self.fixated and not previous_fixation:
                #print 'fixated, start fixation period'
                # start fixation period
                self.initiate_fixation_period()
            elif not self.fixated and previous_fixation:
                #print 'broke fixation'
                # if broke fixation, stop checking for fixation
                self.fixation_check_flag = False
                # abort trial, start again with square in same position
                self.recover_from_broken_fixation()
            # if checking fixation on square, not showing photos,
            # so can immediately return
            return
        if self.fixation_photo_flag:
            # for photos, only switch the fixation_check_flag when done
            # showing a photo, stop timer when not fixating, turn back on when
            # fixating
            self.photos.flag_timer = self.photos.check_fixation(self.eye_data)
            # time to stop worrying about fixation and drawing eye positions
            if not self.photos.check_eye:
                #print 'stop checking fixation'
                self.fixation_photo_flag = False
                self.flag_clear_eyes = True

    def eye_data_to_pixel(self, eye_data):
        # change the offset and gain as necessary, so eye data looks
        # right on screen. Actually, most of this is changed in IScan
        # before it ever makes it to this machine, but found we have to
        # at least change the gain by a couple of order of magnitudes
        return [(eye_data[0] + self.offset[0]) * self.gain[0],
                (eye_data[1] + self.offset[1]) * self.gain[1]]

    def clear_eyes(self):
        # We can now stop plotting eye positions,
        # and get rid of old eye positions.
        if self.eye_nodes:
            #print self.eye_nodes
            # can do this in a loop, since does not
            # delete object from list
            for eye in self.eye_nodes:
                eye.removeNode()
        #print 'should be no nodes now', self.eye_nodes
        self.eye_nodes = []

    def show_window(self, square_pos):
        # draw line around target representing how close the subject has to be looking to get reward
        #print('show window around square', square_pos)
        tolerance = self.tolerance / self.deg_per_pixel
        #print 'tolerance in pixels', tolerance
        #print 'square', square[0], square[2]
        eye_window = LineSegs()
        eye_window.setThickness(2.0)
        eye_window.setColor(1, 0, 0, 1)
        angle_radians = radians(360)
        for i in range(50):
            a = angle_radians * i / 49
            y = tolerance * sin(a)
            x = tolerance * cos(a)
            eye_window.drawTo((x + square_pos[0], 55, y + square_pos[2]))

        # draw a radius line
        #eye_window.moveTo(square[0], 55, square[2])
        #eye_window.drawTo(square[0], 55, square[2] + self.tolerance)
        #print 'distance drawn', self.distance((square[0], square[2]), (square[0], square[2] + self.tolerance))
        # True optimizes the line segments, which sounds useful
        node = self.base.render.attachNewNode(eye_window.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_window.append(node)

    # Setup Functions
    def setup_text(self, res_eye):
        #print 'make text'
        self.text = TextNode('gain')
        self.text.setText('Gain: ' + str(self.gain))
        #text_nodepath = aspect2d.attachNewNode(self.text)
        text_node_path = self.base.render.attachNewNode(self.text)
        text_node_path.setScale(25)
        #text_node_path.setScale(0.1)
        #text_node_path.setPos(-300, 0, 200)
        #text_node_path.setPos(0, 0, 350)
        text_node_path.setPos(0 + res_eye[0]/14, 0, res_eye[1]/2 - res_eye[1]/16)
        text_node_path.show(BitMask32.bit(0))
        text_node_path.hide(BitMask32.bit(1))

        # not using offset for our purposes presently
        # if decide to use it again, need to move IScan text down
        # self.text2 = TextNode('offset')
        # self.text2.setText('Offset: ' + str(self.offset))
        # text2NodePath = render.attachNewNode(self.text2)
        # text2NodePath.setScale(30)
        # text2NodePath.setPos(500, 0, 250)
        # text2NodePath.show(BitMask32.bit(0))
        # text2NodePath.hide(BitMask32.bit(1))

        self.text3 = TextNode('IScan')
        self.text3.setText('IScan: ' + '[0, 0]')
        text3_node_path = self.base.render.attachNewNode(self.text3)
        text3_node_path.setScale(25)
        #text3_node_path.setPos(0, 0, 310)
        text3_node_path.setPos(0 + res_eye[0]/14, 0, res_eye[1]/2 - res_eye[1] * 2 / 16)
        text3_node_path.show(BitMask32.bit(0))
        text3_node_path.hide(BitMask32.bit(1))

        self.set_text4(res_eye)
        self.set_text5(res_eye)

    def set_text4(self, res_eye=None):
        degree = unichr(176).encode('utf-8')
        # set up text, if it hasn't been done before
        if not self.text4:
            self.text4 = TextNode('tolerance')
            self.text4.setText('Tolerance: ' + str(self.tolerance) + degree + ' V.A., \n alt-arrow to adjust')
            text4_node_path = self.base.camera.attachNewNode(self.text4)
            text4_node_path.setScale(25)
            #text4_node_path.setPos(0, 0, 270)
            text4_node_path.setPos(0 + res_eye[0]/14, 0, res_eye[1]/2 - res_eye[1] * 3 / 16)
            text4_node_path.show(BitMask32.bit(0))
            text4_node_path.hide(BitMask32.bit(1))

        # if we are in manual mode, show nothing, otherwise show tolerance.
        if not self.manual:
            self.text4.setText('Tolerance: ' + str(self.tolerance) + degree + ' V.A., \n alt-arrow to adjust')
        else:
            self.text4.setText('')

    def set_text5(self, res_eye=None):
        if not self.text5:
            self.text5 = TextNode('task_type')
            text5_node_path = self.base.camera.attachNewNode(self.text5)
            text5_node_path.setScale(25)
            #text5_node_path.setPos(-600, 0, 350)
            text5_node_path.setPos(-res_eye[0]/2 + res_eye[0] * 1 / 16, 0, res_eye[1]/2 - res_eye[1] * 1 / 16)
            text5_node_path.show(BitMask32.bit(0))
            text5_node_path.hide(BitMask32.bit(1))
        if self.manual:
            text_notice = 'Manual'
        else:
            text_notice = 'Auto'
        self.text5.setText(text_notice)

    def start_eye_task(self):
        self.eye_task = pydaq.EOGTask()
        self.eye_task.SetCallback(self.get_eye_data)
        self.eye_task.StartTask()

    def start_reward_task(self):
        self.reward_task = pydaq.GiveReward()

    # Key Functions
    ### key press or messenger methods
    def change_gain_or_offset(self, ch_type, x_or_y, ch_amount):
        if ch_type == 'Gain':
            self.gain[x_or_y] += ch_amount
            self.text.setText('Gain:' + str(self.gain))
            self.logging.log_change(ch_type, self.gain)

        else:
            self.offset[x_or_y] += ch_amount
            self.logging.log_change(ch_type, self.offset)

    def change_tolerance(self, direction):
        #print 'change tolerance'
        self.tolerance += direction
        self.logging.log_change('Tolerance', self.tolerance)
        self.set_text4()
        #self.text4.setText('Tolerance: ' + str(self.tolerance) + ' degrees from center')
        #self.text2.setText('Tolerance: ' + str(self.tolerance / self.deg_per_pixel) + 'pixels')
        for win in self.eye_window:
            win.detachNode()
        #self.eye_window.detachNode()
        self.show_window(self.square.square.getPos())

    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def set_key(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

    def switch_task_flag(self):
        #print 'switch tasks'
        self.flag_task_switch = True

    # this actually assigns keys to methods
    def setup_keys(self):
        self.accept("escape", self.close)  # escape
        # starts turning square on
        self.accept("space", self.start_loop)
        # switches from manual to auto-calibrate or vise-versa,
        # but only at end of current loop (after reward)
        # True signifies that we want to change
        self.accept("s", self.switch_task_flag)
        # For adjusting calibration
        # inputs, gain or offset, x or y, how much change
        # gain - up and down are y
        # done with an outside process, time to cleanup
        self.accept("cleanup", self.cleanup)
        self.accept("shift-arrow_up", self.change_gain_or_offset, ['Gain', 1, 1])
        self.accept("shift-arrow_up-repeat", self.change_gain_or_offset, ['Gain', 1, 1])
        self.accept("shift-arrow_down", self.change_gain_or_offset, ['Gain', 1, -1])
        self.accept("shift-arrow_down-repeat", self.change_gain_or_offset, ['Gain', 1, -1])
        # gain - right and left are x
        self.accept("shift-arrow_right", self.change_gain_or_offset, ['Gain', 0, 1])
        self.accept("shift-arrow_right-repeat", self.change_gain_or_offset, ['Gain', 0, 1])
        self.accept("shift-arrow_left", self.change_gain_or_offset, ['Gain', 0, -1])
        self.accept("shift-arrow_left-repeat", self.change_gain_or_offset, ['Gain', 0, -1])
        # offset - up and down are y
        self.accept("control-arrow_up", self.change_gain_or_offset, ['Offset', 1, 1])
        self.accept("control-arrow_up-repeat", self.change_gain_or_offset, ['Offset', 1, 1])
        self.accept("control-arrow_down", self.change_gain_or_offset, ['Offset', 1, -1])
        self.accept("control-arrow_down-repeat", self.change_gain_or_offset, ['Offset', 1, -1])
        # offset - right and left are x
        self.accept("control-arrow_right", self.change_gain_or_offset, ['Offset', 0, 1])
        self.accept("control-arrow_right-repeat", self.change_gain_or_offset, ['Offset', 0, 1])
        self.accept("control-arrow_left", self.change_gain_or_offset, ['Offset', 0, -1])
        self.accept("control-arrow_left-repeat", self.change_gain_or_offset, ['Offset', 0, -1])

        # For adjusting tolerance (allowable distance from target that still gets reward)
        self.accept("alt-arrow_up", self.change_tolerance, [0.5])
        self.accept("alt-arrow_up-repeat", self.change_tolerance, [0.5])
        self.accept("alt-arrow_down", self.change_tolerance, [-0.5])
        self.accept("alt-arrow_down-repeat", self.change_tolerance, [-0.5])

        # keys will update the list, and loop will query it
        # to get new position
        self.keys = {"switch": 0}
        # keyboard
        self.accept("1", self.set_key, ["switch", 1])
        self.accept("2", self.set_key, ["switch", 2])
        self.accept("3", self.set_key, ["switch", 3])
        self.accept("4", self.set_key, ["switch", 4])
        self.accept("5", self.set_key, ["switch", 5])
        self.accept("6", self.set_key, ["switch", 6])
        self.accept("7", self.set_key, ["switch", 7])
        self.accept("8", self.set_key, ["switch", 8])
        self.accept("9", self.set_key, ["switch", 9])

    ### setup methods
    def setup_window2(self):
        #print 'second window, for researcher'
        props = WindowProperties()
        #props.setForeground(True)
        props.setCursorHidden(True)
        try:
            self.base.win.requestProperties(props)
            #print props
        except AttributeError:
            print 'Cannot open second window. To open just one window, ' \
                  'change the resolution in the config file to Test ' \
                  'or change the resolution to None for default Panda window'
            # go ahead and give the traceback and exit
            raise

        # Need to get this better. keypress only works with one window.
        # plus looks ugly.
        window2 = self.base.openWindow()
        window2.setClearColor((115 / 255, 115 / 255, 115 / 255, 1))
        #window2.setClearColor((1, 0, 0, 1))
        #props.setCursorHidden(True)
        #props.setOrigin(0, 0)
        # resolution of window for actual calibration
        resolution = self.config['WIN_RES']
        res_eye = self.config['EYE_RES']
        # if resolution given, set the appropriate resolution
        # otherwise assume want small windows
        if resolution is not None:
            # resolution for main window, subjects monitor
            self.set_resolution(resolution)
            # properties for second window
            props.setOrigin(-int(res_eye[0]), 0)
            #props.setOrigin(0, 0)
            # resolution for second window, one for plotting eye data
            #props.setSize(1024, 768)
            props.setSize(int(res_eye[0]), int(res_eye[1]))
        else:
            props.setOrigin(600, 200)  # make it so windows aren't on top of each other
            resolution = [800, 600]  # if no resolution given, assume normal panda window
            # x and y are pretty damn close, so just us x
        # degree per pixel is important only for determining where to plot squares and
        # determining tolerance, but no effect on actual eye position plotting, uses projector
        # resolution, screen size, etc
        self.deg_per_pixel = visual_angle(self.config['SCREEN'], resolution, self.config['VIEW_DIST'])[0]
        #print 'deg_per_pixel', self.deg_per_pixel
        # set the properties for eye data window
        window2.requestProperties(props)
        #print window2.getRequestedProperties()

        # orthographic lens means 2d, then we can set size to resolution
        # so coordinate system is in pixels
        lens = OrthographicLens()
        lens.setFilmSize(int(resolution[0]), int(resolution[1]))
        #lens.setFilmSize(800, 600)
        # this allows us to layer, as long as we use between -100
        # and 100 for z. (eye position on top of squares)
        lens.setNearFar(-100, 100)

        camera = self.base.camList[0]
        camera.node().setLens(lens)
        camera.reparentTo(self.base.render)

        camera2 = self.base.camList[1]
        camera2.node().setLens(lens)
        camera2.reparentTo(self.base.render)

        # set bit mask for eye positions
        camera.node().setCameraMask(BitMask32.bit(1))
        camera2.node().setCameraMask(BitMask32.bit(0))
        return res_eye

    def set_resolution(self, res):
        # sets the resolution for the main window (projector)
        wp = WindowProperties()
        #print 'calibration window', res
        wp.setSize(int(res[0]), int(res[1]))
        #wp.setSize(1600, 900)
        #wp.setOrigin(-1600, 0)
        wp.setOrigin(0, 0)
        #wp.setOrigin(-int(res[0]), 0)
        #wp.setUndecorated(True)
        self.base.win.requestProperties(wp)

    def setup_game(self):
        # this only happens once, at beginning
        # set up keys
        self.setup_keys()
        # create square object
        self.square = Square(self.config, self.keys, self.base)
        self.logging = Logging(self.config)
        if self.show_photos:
            self.photos = Photos(self.base, self.config, self.logging)
            self.photos.load_all_photos()
        # start fake data yield, if not using eye tracker
        if self.config['FAKE_DATA']:
            print 'get fake data'
            self.fake_data = yield_eye_data((0.0, 0.0))
        # start reward capabilities, if using daq
        if self.use_daq_reward:
            #print 'setup reward'
            self.start_reward_task()
        if not self.unittest:
            self.start_gig()

    def close(self):
        #print 'close'
        # if we close during a photo showing or photo break, will interrupt task
        # also want to keep track of where we ended. Move this to Photos.
        if self.photos:
            self.base.taskMgr.removeTasksMatching('photo_*')
            with open(self.config['file_name'], 'a') as config_file:
                config_file.write('\nLAST_PHOTO_INDEX = ' + str(self.photos.end_index))
            # make sure eye data was cleared
            self.flag_clear_eyes = True
        if not self.config['FAKE_DATA']:
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        self.logging.close_files()
        if self.unittest:
            self.ignoreAll()  # ignore everything, so nothing weird happens after deleting it.
        else:
            sys.exit()

if __name__ == "__main__":
    #print 'run as module'
    #print 'main'
    # default is manual
    if len(sys.argv) == 1:
        W = World(1)
    elif len(sys.argv) == 2:
        W = World(sys.argv[1])
    else:
        W = World(sys.argv[1], sys.argv[2])
    W.setup_game()
    W.base.run()
