from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import BitMask32
from panda3d.core import WindowProperties, TextNode
from panda3d.core import OrthographicLens, LineSegs
from Logging import Logging
from positions import visual_angle
from EyeData import EyeData
from CalSequences import CalSequences
import sys
from math import sqrt, radians, cos, sin
from Photos import Photos


try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    print 'pydaq loaded'
except ImportError:
    pydaq = None
    print 'Not using PyDaq'


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
        # print 'tolerance', tolerance
        # print 'eye data', eye_data
        # print 'target', target
        distance = get_distance(eye_data, target)
        # print 'distance', distance
        # okay, this works if tolerance is a radius from the center,
        # but not going to work when/if tolerance is a square
        if distance > tolerance:
            fixated = False
        else:
            fixated = True
        # print 'check fixation, verdict is', fixated
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
        # print('manual', self.manual)
        if not config_file:
            config_file = 'config.py'

        self.pydaq = pydaq

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
            # print 'test'
            self.testing = True
            self.use_daq_reward = False
        else:
            self.testing = False
            self.use_daq_reward = self.config.setdefault('REWARD', True)

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
        # print 'repeat ', self.config['POINT_REPEAT']

        # assume 0.2 seconds for pump delay, if not set
        self.config.setdefault('PUMP_DELAY', 0.2)

        # start Panda3d
        self.base = ShowBase()

        # make a new variable, so we can toggle it
        self.sub_index = None
        self.call_subroutine = []

        # This will be the photo object, if we are showing photos
        self.photos = None

        # initialize text before setting up second window.
        # text will be overridden there.
        # text only happens on second window
        self.text = None
        self.text2 = None
        self.text3 = None
        self.text4 = None
        self.text5 = None

        # print base.pipe.getDisplayWidth()
        # print base.pipe.getDisplayHeight()
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
        # print 'window loaded'
        # empty list for plotting eye nodes
        self.eye_nodes = []
        self.current_eye_data = None
        # initialize file variables
        self.eye_file_name = ''
        self.time_file_name = ''
        self.eye_data_file = None
        self.time_data_file = None

        # starts out not fixated, and not checking for fixation (will
        # check for fixation when stimulus comes on, if we are doing an auto task)
        self.fixated = False

        self.base.setBackgroundColor(115 / 255, 115 / 255, 115 / 255)
        self.base.disableMouse()

        # create dummy variable for helper objects
        self.logging = None
        self.eye_data = None
        self.sequences = None

        # initialize list for eye window
        self.eye_window = []

        # initialize signal to switch tasks (manual - auto)
        self.flag_task_switch = False

        # set up daq for reward, if on windows and not testing
        # testing auto mode depends on being able to control eye position
        self.reward_task = None

        self.num_beeps = self.config['NUM_BEEPS']  # number of rewards each time
        self.num_reward = 0  # count number of rewards
        # current task is used for testing, changes at start of each new task
        self.current_task = None

        # Keyboard stuff:
        # initiate
        self.key_dict = {"switch": 0}

    def start_gig(self):
        # used when beginning in either auto or manual mode,
        # either at start or after switching
        # print 'start new gig'
        if not self.testing:
            # text4 and text5 change
            self.set_text4()
            self.set_text5()
        # open files, start data stream, prepare tasks
        self.logging.open_files(self.manual, self.tolerance)
        self.logging.log_config('Gain', self.gain)
        self.logging.log_config('Offset', self.offset)
        self.eye_data.start_logging(self.logging)
        self.sequences.prepare_task(self.manual)

    def end_gig(self):
        # used when end in either auto or manual mode,
        # either at start or after switching
        # print 'end gig'
        # clear screen
        # self.clear_eyes()
        # close stuff
        self.eye_data.stop_logging()
        self.logging.close_files()

    def change_tasks(self):
        # change from manual to auto-calibrate or vise-versa
        # print 'change task'
        self.manual = not self.manual
        # print('switched manual?', self.manual)
        # reset stuff
        self.flag_task_switch = False
        self.end_gig()
        self.start_gig()
        # if going from manual to auto, start automatically, otherwise
        # wait for keypress to start.
        if not self.manual:
            self.start_main_loop()

    def start_main_loop(self, good_trial=None):
        # check to see if manual, no subroutines for manual
        if self.manual:
            self.sequences.setup_manual_sequence()
            self.sequences.manual_sequence.start()
        else:
            # check to see if we are doing a subroutine
            print 'new loop, not manual'
            do_subroutine = False
            if self.call_subroutine:
                print 'check subroutines'
                for index, tasks in enumerate(self.call_subroutine):
                    do_subroutine = tasks.check_trial(good_trial, self.start_plot_eye_task)
                    if do_subroutine:
                        print 'show photo'
                        self.sub_index = index
                        break
                    else:
                        self.sub_index = None
            print 'after call_subroutine, do_subroutine now', do_subroutine
            if not do_subroutine:
                print 'show square'
                self.sequences.setup_auto_sequences(good_trial)
                self.sequences.auto_sequence_one.start()

    def cleanup_main_loop(self):
        print 'cleanup main loop'
        # print('time', time())
        # end of loop, check to see if we are switching tasks, start again
        good_trial = self.num_reward > 0
        self.num_reward = 0
        self.fixated = False
        # for testing, good to know when at end of loop, doesn't affect task at all
        self.current_task = None
        # if we change tasks, wait for keypress to start again
        if self.flag_task_switch:
            # print 'change tasks'
            self.change_tasks()
        else:
            # unit tests we step through, rather than
            # run main loop
            if not self.testing:
                # print 'start next loop'
                self.start_main_loop(good_trial)
        # print('done cleanup_main_loop')

    def give_reward(self):
        # if got reward, square can move
        # print 'reward, 3'
        # print(self.base.taskMgr)
        # give reward for each num_beeps
        # give one reward right away, have
        # to wait delay before giving next reward
        if self.reward_task:
            # print 'first reward'
            self.num_reward = 1
            self.reward_task.pumpOut()
            # if using actual reward have to wait to give next reward
            self.base.taskMgr.doMethodLater(self.config['PUMP_DELAY'], self.reward_after_pause, 'reward')
        else:
            for i in range(self.num_beeps):
                # print 'beep'
                self.num_reward += 1
        # print 'give reward returns'
        # print('time', time())

    def reward_after_pause(self, task):
        # print 'give another reward'
        self.reward_task.pumpOut()
        self.num_reward += 1
        if self.num_reward < self.num_beeps:
            return task.again
        # print 'reward done'
        return task.done

    def clear_screen(self):
        # print 'clear screen'
        # We can now stop plotting eye positions,
        # and get rid of old eye positions.
        self.stop_plot_eye_task()
        # remove threshold window around square
        for win in self.eye_window:
            win.detachNode()
        if self.eye_nodes:
            # print self.eye_nodes
            # can do this in a loop, since does not
            # delete object from list
            for eye in self.eye_nodes:
                if not eye.isEmpty():
                    eye.removeNode()
        self.current_eye_data = None
        # print 'should be no nodes now', self.eye_nodes
        self.eye_nodes = []

    # Eye plotting
    def start_plot_eye_task(self, check_eye=False, timer=False):
        # print 'start plot eye task'
        target = None
        if check_eye:
            target, on_interval = self.check_fixation_target()
            if timer:
                self.start_fixation_timer(target, on_interval)
            self.stop_plot_eye_task()
        self.base.taskMgr.add(self.process_eye_data, 'plot_eye', extraArgs=[check_eye, target], appendTask=True)

    def stop_plot_eye_task(self):
        self.base.taskMgr.remove('plot_eye')

    def check_fixation_target(self):
        if self.sub_index is not None:
            # would be great if this were more generic, but works for now
            target, on_interval = self.call_subroutine[self.sub_index].get_fixation_target()
            print target, on_interval
        else:
            # else is going to be regular auto calibrate
            target, on_interval = self.sequences.get_fixation_target()
        return target, on_interval

    # Eye Methods
    def start_fixation_timer(self, target, on_interval):
        # print 'show fixation window, start timer'
        self.show_window(target)
        # start timing for on task, this runs for target on time and waits for fixation,
        # if no fixation, method runs to abort trial
        # print time()
        if self.sub_index is not None:
            no_fix_task = self.call_subroutine[self.sub_index].no_fixation
        else:
            no_fix_task = self.sequences.no_fixation
        self.base.taskMgr.doMethodLater(on_interval, no_fix_task, 'wait_for_fix')
        # print('should still not be fixated', self.fixated)

    def process_eye_data(self, check_eye=None, target=None, task=None):
        # get data from producer
        eye_data = self.eye_data.consume_queue()
        if not eye_data:
            return task.cont
        # print 'plot eye data', eye_data
        # convert to pixels for plotting and testing distance,
        # need the eye position from the last run for the starting
        # position for move to position for plotting, and the
        # current eye position for ending position
        if not self.current_eye_data:
            # print 'use first data point in this chunk'
            # if no previous eye, just use first data point
            start_eye = self.eye_data_to_pixel(eye_data[0])
        else:
            # print 'use previous data'
            start_eye = self.current_eye_data[-1]
        # print 'eye data in calibration', start_eye
        # print start_eye
        # save data
        self.current_eye_data = [self.eye_data_to_pixel(data_point) for data_point in eye_data]
        self.plot_eye_trace(start_eye)
        # and set text to last data point
        if not self.testing:
            self.text3.setText(self.eye_data.data_type + str(round(self.current_eye_data[-1][0], 3)) +
                               ', ' + str(round(self.current_eye_data[-1][1], 3)) + ']')
        if check_eye:
            # print 'check fixation'
            self.evaluate_fixation(target)
        return task.cont

    def plot_eye_trace(self, first_eye):
        # print 'plot trace'
        # if plotting too many eye positions, things slow down and
        # python goes into lala land. Never need more than 500, and
        # last 300 is definitely plenty, so every time it hits 500,
        # get rid of first 200.
        if len(self.eye_nodes) > 500:
            # print('get rid of eye nodes', len(self.eye_nodes))
            # Since this just removes the node, but doesn't delete
            # the object in the list, can do this in a for loop,
            for index in range(200):
                self.eye_nodes[index].removeNode()
            # now get rid of the empty nodes in eye_nodes
            # print('new length', len(self.eye_nodes))
            self.eye_nodes = self.eye_nodes[200:]
            # print('new length', len(self.eye_nodes))
        eye = LineSegs()
        # eye.setThickness(2.0)
        eye.setThickness(2.0)
        # print 'last', last_eye
        # print 'now', self.current_eye_data
        eye.moveTo(first_eye[0], 55, first_eye[1])
        for data_point in self.current_eye_data:
            eye.drawTo(data_point[0], 55, data_point[1])
        # print('plotted eye', eye_data_to_plot)
        node = self.base.render.attachNewNode(eye.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_nodes.append(node)
        # print 'end plot trace'

    def evaluate_fixation(self, target):
        previous_fixation = self.fixated
        # convert tolerance to pixels
        tolerance = self.tolerance / self.deg_per_pixel
        # send in eye data converted to pixels, self.current_eye_data
        fixated = []
        if target is None:
            for data_point in self.current_eye_data:
                fixated.append(self.call_subroutine[self.sub_index].check_fixation(data_point))
        for data_point in self.current_eye_data:
            fixated.append(check_fixation(data_point, tolerance, target))
        # print 'fixation array', fixated
        self.fixated = all(fixated)
        # print('fixated?', self.fixated)
        # need to check if time to start fixation period or time to end
        # fixation period, otherwise business as usual
        if self.fixated and not previous_fixation:
            print 'fixated, start fixation period'
            # end waiting period
            self.base.taskMgr.remove('wait_for_fix')
            # start fixation period
            if self.sub_index is not None:
                print 'subroutine'
                self.call_subroutine[self.sub_index].start_fixation_period()
            else:
                print 'auto_fix'
                self.sequences.start_fixation_period()
        elif not self.fixated and previous_fixation:
            print 'broke fixation'
            if self.sub_index is not None:
                self.call_subroutine[self.sub_index].broke_fixation()
            else:
                self.sequences.broke_fixation()

    def eye_data_to_pixel(self, eye_data):
        # change the offset and gain as necessary, so eye data looks
        # right on screen. Actually, most of this is changed in IScan
        # before it ever makes it to this machine, but found we have to
        # at least change the gain by a couple of order of magnitudes
        return [(eye_data[0] + self.offset[0]) * self.gain[0],
                (eye_data[1] + self.offset[1]) * self.gain[1]]

    def start_eye_data(self, start_pos=None, variance=None):
        # if we are sending in variance, then coming from testing and we need to close first
        # (just stops task producing fake data, so we can restart in different place)
        if variance is not None:
            self.eye_data.close()
        self.eye_data.start_producer_thread('producer', origin=start_pos, variance=variance)
        self.eye_data.start_consumer_thread('consumer')

    def show_window(self, target_pos):
        # draw line around target representing how close the subject has to be looking to get reward
        # print('show window around square', square_pos)
        tolerance = self.tolerance / self.deg_per_pixel
        # print 'tolerance in pixels', tolerance
        # print 'square', square[0], square[2]
        eye_window = LineSegs()
        eye_window.setThickness(2.0)
        eye_window.setColor(1, 0, 0, 1)
        angle_radians = radians(360)
        for i in range(50):
            a = angle_radians * i / 49
            y = tolerance * sin(a)
            x = tolerance * cos(a)
            eye_window.drawTo((x + target_pos[0], 55, y + target_pos[1]))
        # draw a radius line
        # eye_window.moveTo(square[0], 55, square[2])
        # eye_window.drawTo(square[0], 55, square[2] + self.tolerance)
        # print 'distance drawn', self.distance((square[0], square[2]), (square[0], square[2] + self.tolerance))
        # True optimizes the line segments, which sounds useful
        node = self.base.render.attachNewNode(eye_window.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_window.append(node)

    # Setup Functions
    def setup_text(self, res_eye):
        # print 'make text'
        self.text = TextNode('gain')
        self.text.setText('Gain: ' + str(self.gain))
        # text_nodepath = aspect2d.attachNewNode(self.text)
        text_node_path = self.base.render.attachNewNode(self.text)
        text_node_path.setScale(25)
        text_node_path.setPos(0 - res_eye[0]/4, 0, res_eye[1]/2 - res_eye[1]/16)
        text_node_path.show(BitMask32.bit(0))
        text_node_path.hide(BitMask32.bit(1))

        # if decide to use it again, need to move IScan text down
        self.text2 = TextNode('offset')
        self.text2.setText('Offset: ' + str(self.offset))
        text2_node_path = self.base.render.attachNewNode(self.text2)
        text2_node_path.setScale(25)
        text2_node_path.setPos(0, 0, res_eye[1]/2 - res_eye[1]/16)
        text2_node_path.show(BitMask32.bit(0))
        text2_node_path.hide(BitMask32.bit(1))

        self.text3 = TextNode('IScan')
        self.text3.setText('IScan: ' + '[0, 0]')
        text3_node_path = self.base.render.attachNewNode(self.text3)
        text3_node_path.setScale(25)
        text3_node_path.setPos(0 + res_eye[0]/4, 0, res_eye[1]/2 - res_eye[1]/16)
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
            # text4_node_path.setPos(0, 0, 270)
            text4_node_path.setPos(0, 0, res_eye[1]/2 - res_eye[1] * 2 / 16)
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
            # text5_node_path.setPos(-600, 0, 350)
            text5_node_path.setPos(-res_eye[0]/2 + res_eye[0] * 1 / 16, 0, res_eye[1]/2 - res_eye[1] * 1 / 16)
            text5_node_path.show(BitMask32.bit(0))
            text5_node_path.hide(BitMask32.bit(1))
        if self.manual:
            text_notice = 'Manual'
        else:
            text_notice = 'Auto'
        self.text5.setText(text_notice)

    def start_reward_task(self):
        self.reward_task = pydaq.GiveReward()

    # Key Functions
    # key press or messenger methods
    def change_gain_or_offset(self, ch_type, x_or_y, ch_amount):
        if ch_type == 'Gain':
            self.gain[x_or_y] += ch_amount
            self.text.setText('Gain:' + str(self.gain))
            self.logging.log_change(ch_type, self.gain)

        else:
            self.offset[x_or_y] += ch_amount
            self.text2.setText('Offset:' + str(self.offset))
            self.logging.log_change(ch_type, self.offset)

    def change_tolerance(self, direction):
        # print 'change tolerance'
        self.tolerance += direction
        self.logging.log_change('Tolerance', self.tolerance)
        self.set_text4()
        # self.text4.setText('Tolerance: ' + str(self.tolerance) + ' degrees from center')
        # self.text2.setText('Tolerance: ' + str(self.tolerance / self.deg_per_pixel) + 'pixels')
        for win in self.eye_window:
            win.detachNode()
        # self.eye_window.detachNode()
        target = self.sequences.get_fixation_target()
        self.show_window(target[0])

    # As described earlier, this simply sets a key in the self.key_dict dictionary to
    # the given value
    def set_key(self, key, val):
        self.key_dict[key] = val
        # print 'set key', self.key_dict[key]

    def switch_task_flag(self):
        # print 'switch tasks'
        self.flag_task_switch = True

    # this actually assigns keys to methods
    def setup_keys(self):
        self.accept("escape", self.close)  # escape
        # starts turning square on
        self.accept("space", self.start_main_loop)
        # switches from manual to auto-calibrate or vise-versa,
        # but only at end of current loop (after reward)
        # True signifies that we want to change
        self.accept("s", self.switch_task_flag)
        # For adjusting calibration
        # inputs, gain or offset, x or y, how much change
        # gain - up and down are y
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
        self.accept("control-arrow_up", self.change_gain_or_offset, ['Offset', 1, 0.5])
        self.accept("control-arrow_up-repeat", self.change_gain_or_offset, ['Offset', 1, 0.5])
        self.accept("control-arrow_down", self.change_gain_or_offset, ['Offset', 1, -0.5])
        self.accept("control-arrow_down-repeat", self.change_gain_or_offset, ['Offset', 1, -0.5])
        # offset - right and left are x
        self.accept("control-arrow_right", self.change_gain_or_offset, ['Offset', 0, 0.5])
        self.accept("control-arrow_right-repeat", self.change_gain_or_offset, ['Offset', 0, 0.5])
        self.accept("control-arrow_left", self.change_gain_or_offset, ['Offset', 0, -0.5])
        self.accept("control-arrow_left-repeat", self.change_gain_or_offset, ['Offset', 0, -0.5])

        # For adjusting tolerance (allowable distance from target that still gets reward)
        self.accept("alt-arrow_up", self.change_tolerance, [0.5])
        self.accept("alt-arrow_up-repeat", self.change_tolerance, [0.5])
        self.accept("alt-arrow_down", self.change_tolerance, [-0.5])
        self.accept("alt-arrow_down-repeat", self.change_tolerance, [-0.5])

        # send messages from other classes
        # done with an outside process, time to cleanup
        self.accept("cleanup", self.cleanup_main_loop)
        self.accept("reward", self.give_reward)
        self.accept("clear", self.clear_screen)
        self.accept("plot", self.start_plot_eye_task)
        # keys will update the list, and loop will query it
        # to get new position
        # why is this a dictionary? It only has one entry?!?!
        self.key_dict = {"switch": 0}
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

    # setup methods
    def setup_window2(self):
        # print 'second window, for researcher'
        props = WindowProperties()
        # props.setForeground(True)
        props.setCursorHidden(True)
        try:
            self.base.win.requestProperties(props)
            # print props
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
            # props.setOrigin(0, 0)
            # resolution for second window, one for plotting eye data
            # props.setSize(1024, 768)
            props.setSize(int(res_eye[0]), int(res_eye[1]))
        else:
            props.setOrigin(600, 200)  # make it so windows aren't on top of each other
            resolution = [800, 600]  # if no resolution given, assume normal panda window
            # x and y are pretty damn close, so just us x
        # degree per pixel is important only for determining where to plot squares and
        # determining tolerance, but no effect on actual eye position plotting, uses projector
        # resolution, screen size, etc
        self.deg_per_pixel = visual_angle(self.config['SCREEN'], resolution, self.config['VIEW_DIST'])[0]
        # print 'deg_per_pixel', self.deg_per_pixel
        # set the properties for eye data window
        window2.requestProperties(props)
        # print window2.getRequestedProperties()

        # orthographic lens means 2d, then we can set size to resolution
        # so coordinate system is in pixels
        lens = OrthographicLens()
        lens.setFilmSize(int(resolution[0]), int(resolution[1]))
        # lens.setFilmSize(800, 600)
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
        # print 'calibration window', res
        wp.setSize(int(res[0]), int(res[1]))
        # wp.setSize(1600, 900)
        # wp.setOrigin(-1600, 0)
        wp.setOrigin(0, 0)
        # wp.setOrigin(-int(res[0]), 0)
        # wp.setUndecorated(True)
        self.base.win.requestProperties(wp)

    def setup_game(self):
        # this only happens once, at beginning
        # set up keys
        self.setup_keys()
        self.logging = Logging(self.config)
        self.sequences = CalSequences(self.config, self.logging, self.base, self.key_dict)
        if self.config.setdefault('PHOTO_PATH', False):
            self.photos = Photos(self.config, self.base, self.logging, self.deg_per_pixel)
            self.photos.load_all_photos()
            self.call_subroutine.append(self.photos)
            print 'call_subroutine', self.call_subroutine
        # start generating/receiving data
        self.eye_data = EyeData(self.base, self.config['FAKE_DATA'])
        self.start_eye_data()
        # start reward capabilities, if using daq
        if self.use_daq_reward:
            # print 'setup reward'
            self.start_reward_task()
        if not self.testing:
            self.start_gig()

    def close(self):
        # print 'close'
        # if we close during a photo showing or photo break, will interrupt task
        # also want to keep track of where we ended. Move this to Photos.
        # make sure eye data is
        # close any subroutines
        if self.call_subroutine:
            for tasks in self.call_subroutine:
                tasks.close()
        self.eye_data.close()
        self.logging.close_files()
        if self.testing:
            self.ignoreAll()  # ignore everything, so nothing weird happens after deleting it.
        else:
            sys.exit()

if __name__ == "__main__":
    # print 'run as module'
    # print 'main'
    # default is manual
    if len(sys.argv) == 1:
        W = World(1)
    elif len(sys.argv) == 2:
        W = World(sys.argv[1])
    else:
        W = World(sys.argv[1], sys.argv[2])
    W.setup_game()
    W.base.run()
