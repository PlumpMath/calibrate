from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from panda3d.core import BitMask32
from panda3d.core import WindowProperties, TextNode
from panda3d.core import OrthographicLens, LineSegs
from positions import Positions, visual_angle
import sys
import random
import os
import datetime
from time import time, sleep
from math import sqrt, radians, cos, sin
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


class World(DirectObject):

    def __init__(self, mode=None, test=None):
        print mode
        DirectObject.__init__(self)
        # mode sets whether starts at manual or auto, default is manual, auto is 0
        # test sets whether using fake eye data and test_config for config,
        # set to 1 for testing/using fake eye data
        #print 'init'
        #print 'mode', mode
        #print 'test', test
        if test == '1' or test == 1:
            # test (either unittest or testing on mac) so use fake eye data and testing configuration.
            # for testing, always leave gain at one, so eye_data and plot_eye_data are the same
            # if using fake data on windows, also change WIN_RES in config_test to an actual resolution to
            # get second window
            self.gain = [1, 1]
            print 'test'
            self.unittest = True
            self.use_daq_data = False
            self.use_daq_reward = False
            self.use_pydaq = False
            self.config_file = 'config_test.py'
        else:
            self.unittest = False
            self.use_pydaq = True
            self.use_daq_data = True
            self.use_daq_reward = True
            # in case we are not unittesting, but didn't load pydaq
            if not LOADED_PYDAQ:
                self.use_pydaq = False
                self.use_daq_reward = False
            self.config_file = 'config.py'

        # seems like we can adjust the offset completely in ISCAN,
        # so for now just set it here to zero.
        self.offset = [0, 0]
        # Python assumes all input from sys are string, but not
        # input variables
        # setup square positions
        if mode == '1' or mode == 1:
            self.manual = True
        else:
            self.manual = False

        # get configurations from config file
        config = {}
        execfile(self.config_file, config)
        print 'Subject is', config['SUBJECT']
        if config['SUBJECT'] == 'test':
            self.use_daq_data = False

        self.tolerance = config['TOLERANCE']
        #print 'repeat ', config['POINT_REPEAT']

        # start Panda3d
        self.base = ShowBase()

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

        if config['WIN_RES'] != 'Test':
            self.gain = config['GAIN']
            eye_res = self.setup_window2(config)
            # text only happens on second window
            self.setup_text(eye_res)
        else:
            # resolution in file equal to test, so use the projector screen
            # value for determining pixels size. In this case, accuracy is not
            # important, because never actually calibrating with this setup.
            resolution = [1280, 800]
            self.deg_per_pixel = visual_angle(config['SCREEN'], resolution, config['VIEW_DIST'])[0]

        print('gain', self.gain)

        # initialize variable for square positions
        self.pos = None
        #print 'window loaded'
        self.eyes = []

        # initialize file variables
        self.eye_file_name = ''
        self.time_file_name = ''
        self.eye_data_file = None
        self.time_data_file = None
        # When we first open the file, we will write a line for time started calibration
        self.first = True

        # starts out not fixated, so no fixation time, and not checking for fixation (will
        # check for fixation when stimulus comes on, if we are doing a random task)
        self.fix_time = None
        self.check_fixation = False

        self.base.setBackgroundColor(115 / 255, 115 / 255, 115 / 255)
        self.base.disableMouse()

        # create square for stimulus
        # self.depth needs to be more than zero for stuff to show up,
        # otherwise arbitrary. This is used for positioning squares (Z)
        self.depth = 55
        # scale 17 is one visual angle, linear so just multiply by 17
        self.square = self.create_square(config['SQUARE_SCALE']*17)
        #print 'scale', config['SQUARE_SCALE']*17

        # Eye Data
        self.eye_data = []
        # why do I do this?
        self.eye_data.append((0.0, 0.0))
        self.remove_eyes = False

        # initialize list for eye window
        self.eye_window = []

        # initialize signal to switch tasks (manual - auto)
        self.flag_task_switch = False

        # if not testing, first square will wait until spacebar is hit to start
        # if you wait too long, may go into lala land (although I hope this is
        # fixed...).
        if self.unittest:
            self.pause = False
            first_interval = random.uniform(*config['MOVE_INTERVAL'])
        else:
            first_interval = 0
            self.pause = True

        # set up daq for eye and reward, if on windows and not testing
        # testing random mode depends on being able to control eye position
        self.eye_task = None
        self.reward_task = None
        self.fake_data = None


        self.num_beeps = config['NUM_BEEPS']
        # first task is square_on
        self.next = 0

        # Keyboard stuff:
        # initiate
        self.keys = {"switch": 0}

        # Our intervals
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # reward_interval - time from off to reward
        # move_interval - time from reward to move/on
        # fix_interval - used for random, how long required to fixate
        # break_interval - used for random, how long time out before
        #            next square on, if missed or broke fixation
        self.all_intervals = [config['ON_INTERVAL'], config['FADE_INTERVAL'], config['REWARD_INTERVAL'],
                              config['MOVE_INTERVAL'], config['FIX_INTERVAL'], config['BREAK_INTERVAL']]
        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        self.frameTask = self.base.taskMgr.add(self.frame_loop, "frame_loop")
        #print self.frameTask.time

        # The task object is a good place to put variables that should stay
        # persistent for the task function from frame to frame
        # first interval will be the move interval (time from off to move/on)
        #
        self.frameTask.interval = first_interval
        #print 'first interval', self.frameTask.interval

        # Main work horse: index with self.next to choose appropriate method
        self.frameTask.switch = {
            0: self.square_on,
            1: self.square_fade,
            2: self.square_off,
            3: self.give_reward,
            4: self.square_move}

        # Corresponding dictionary for writing to file
        self.frameTask.file = {
            0: 'Square on \n',
            1: 'Square dims \n',
            2: 'Square off \n',
            3: 'Reward \n',
            4: 'Square moved \n'
        }
        # task.move always starts as False, will be changed to true when time
        # to move, if move is manual
        self.frameTask.move = False

    def frame_loop(self, task):
        #print 'in loop'
        #print task.time
        #print task.interval
        #dt = task.time - task.last
        #task.last = task.time
        # are we waiting for a manual move?
        # no, then check if we are past the current interval
        # print task.move
        if self.pause:
            #print('pause')
            return task.cont
        if not task.move:
            # either not time to move, or moving automatically
            #print 'new loop', task.time
            #print 'frame', task.frame
            if task.time > task.interval:
                #print 'actual time interval was:', task.interval
                # for auto-random task, we may be checking for fixation
                # (this happens when square is on, but not yet faded)
                #print 'fix?', self.check_fixation
                #print 'fix_time', self.fix_time
                # self.check_fixation is True or False, depending on whether we
                # are checking for fixation.
                # self.fix_time is either None or the time they have been fixating
                # so if we are checking fixation, but fix_time is none, subject did
                # not manage to fixate in time allotted. If we are checking fixation,
                # and fix_time has a time, then we made it, and need to wait
                # fixation is checked as eye data is collected.
                #print('check fixation', self.check_fixation)
                #print('fix_time', self.fix_time)
                if self.check_fixation and not self.fix_time:
                    #print 'no fixation, start over'
                    self.restart_timer(None)
                    return task.cont
                elif self.check_fixation:
                    # if we are done with our interval, and haven't restarted,
                    # make sure fix_time is reset to none
                    self.fix_time = None

                # task.switch will manipulate the square and
                # update the interval to the next task.
                #print task.time
                #print 'in frame loop', self.next
                #print 'old interval', task.interval
                task.switch[self.next]()
                # prints name of task just did
                #print task.file[self.next]
                # prints number of task just did
                #print 'just did task', self.next
                #self.time_data_file.write('test' + '\n')
                self.time_data_file.write(str(time()) + ', ' + task.file[self.next])
                # if we just gave reward (3), next is moving.
                # check to see if we are moving manually
                # we will set self.next correctly for the next task
                # when we do the manual move
                #print 'in loop', self.manual
                if self.manual and self.next == 3:
                    #if self.next == 3 and self.manual:
                    #print 'manual move', self.manual
                    task.move = True
                    # need interval from off to move
                    task.interval = random.uniform(*self.all_intervals[self.next])
                    #print 'next interval', task.interval
                    #print 'waiting for keypress'
                    task.interval = task.time + task.interval
                    # do not complete this loop
                    return task.cont

                # if we are at self.next = 4, then the last task was moving (since
                # we haven't incremented yet, next was actually already done)
                # now we need to reset our counter to zero (on). Always go immediately
                # from move to on
                if self.next == 4:
                    self.next = 0
                    interval = 0
                else:
                    interval = random.uniform(*self.all_intervals[self.next])
                    self.next += 1
                    #print self.all_intervals[self.next]
                #print 'next interval', interval
                task.interval = task.time + interval
                #print 'update task number', self.next
        else:
            # Manual moving keys
            #print "check for key"
            #print self.keys["switch"]
            # check to see if we should move the target
            #print 'switch', self.keys
            # if we haven't received a keypress before interval is over, default to 0,0
            if task.time > task.interval:
                #print('interval')
                if self.keys["switch"]:
                    #print 'manual move'
                    #print 'switch', self.keys["switch"]
                    self.square_move(self.pos.get_key_position(self.depth, self.keys["switch"]))
                else:
                    # switch to center
                    self.square_move(self.pos.get_key_position(self.depth, 5))

                self.keys["switch"] = 0  # remove the switch flag
                # square is on, so next thing to happen is it dims,
                # this happens after on interval, 0
                # make sure next interval is based on the time we actually moved the target (now!)
                #task.interval = task.time + random.uniform(*self.all_intervals[0])
                # Next is dim, since it turned on when moved
                self.next = 0
                task.interval = 0
                # don't come back here until ready to move again
                task.move = False
                #print 'back to regularly scheduled program'

        # if using fake data, plot
        if not self.use_daq_data:
            self.get_eye_data(self.fake_data.next())

        # check if we should switch from manual to auto or vise-versa
        # do it here before we return so no weirdness in finishing the frame loop
        if self.flag_task_switch:
            #print('yes, switch')
            self.change_tasks()

        return task.cont  # Since every return is Task.cont, the task will
        #continue indefinitely

    # Square Functions
    def square_on(self):
        position = self.square.getPos()
        #print 'square on, 0'
        #print position
        self.time_data_file.write(str(time()) + ', Square Position, ' + str(position[0]) + 
                                  ', ' + str(position[2]) + '\n')
        # make sure in correct color
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        # and render
        self.square.reparentTo(self.base.render)
        #min, max = self.square.getTightBounds()
        #size = max - min
        #print size[0], size[2]
        #print self.square.getPos()
        #print 'square is now on'
        # show window for tolerance
        # and make sure checking for fixation
        if not self.manual:
            self.show_window(position)
            self.check_fixation = True

    def square_fade(self):
        #print 'square fade, 1'
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(0.9, 0.9, 0.6, 1.0)
        # next interval is fade off to on, at which time we move
        # if manual move is set, after off we just wait for move, so we
        # won't actually check this interval
        #self.interval = random.uniform(*MOVE_INTERVAL)
        self.check_fixation = False
        # if square has faded, then we can reset fixation time
        self.fix_time = None

    def square_off(self):
        #print 'square off, 2'
        #print 'parent 1', self.square.getParent()
        self.square.clearColor()
        self.square.detachNode()
        for win in self.eye_window:
            win.detachNode()
        self.remove_eyes = True
        #print 'erase eye window'
        #self.eye_window.detachNode()
        #print 'parent 2', self.square.getParent()
        # next interval is on to fade on
        #self.interval = random.uniform(*ON_INTERVAL)
        #print 'next-on-interval', self.interval

    def give_reward(self):
        #print 'reward, 3'
        # only give reward if pydaq is setup
        for i in range(self.num_beeps):
            if self.reward_task:
                self.reward_task.pumpOut()
                sleep(.2)
            print 'beep'

    def square_move(self, position=None):
        #print 'square move, 4'
        #print 'square position', position
        if not position:
            #print 'trying to get a auto position'
            try:
                position = self.pos.next()
                #print position
            except StopIteration:
                #print('stop iterating!')
                # Switch to manual and wait
                self.flag_task_switch = True
                self.pause = True
                # need to set a position
                position = Point3(0, 0, 0)
                #self.close()

        self.square.setPos(Point3(position))
        #print 'square', position[0], position[2]

    def restart_timer(self, fix_time):
        # either restarting the timer because fixation was broken, or because fixation was
        # initiated
        #print 'restart timer'
        # if fix_time is none, then restarting because fixation was broken, or never fixated,
        # immediately turn off square and start over.
        if not fix_time:
            # if fix_time is none, will continue as none...
            #print 'restart, did not fixate'
            #print 'no reward!'
            self.time_data_file.write(str(time()) + ', ' + 'no fixation or broken, restart' + '\n')
            # turn off target immediately, and write that to file
            self.square_off()
            self.time_data_file.write(str(time()) + ', ' + 'Square off\n')
            # next time through, don't want to move, just show same target
            self.next = 0
            # and interval before turns on will be break interval
            interval = self.all_intervals[5]
            #print('interval should now be', interval)
            # when new target shows up, this will change back to true
            self.check_fixation = False
        else:
            # timer starts out as interval for how long the subject has to start fixation,
            # once fixated, need to reset the timer so fixation is held right amount of time.
            # So, keep the next period as 1 (square on), but set the interval to fixation interval
            #print 'restarting timer for holding fixation'
            #print('next is now', self.next)
            self.next = 1
            #print('now it is 1')
            interval = self.all_intervals[4]

        # new interval always starts with now
        self.frameTask.interval = self.frameTask.time + interval
        # time has been fixating already (still none if broke fixation)
        self.fix_time = fix_time
        #print 'if not fixated, should be none', self.fix_time

    def start(self):
        # starts the experiment (otherwise start time is 2 minutes after
        # world is created)
        self.frameTask.interval = 0
        self.pause = False

    def get_eye_data(self, eye_data):
        # pydaq calls this function every time it calls back to get eye data,
        # if testing, called from frame_loop with fake data
        # We want to change gain on data being plotted, and
        # write eye data (as is, no adjustments) and timestamp to file
        # if we are paused, do not plot eye data (pausing messes up
        # with cleanup), but still collect the data
        if self.first:
            #print 'first?', eye_data[0], eye_data[1]
            self.time_data_file.write(str(time()) + ', start collecting eye data\n')
            self.first = False
        self.eye_data_file.write(str(time()) + ', ' +
                                 str(eye_data[0]) + ', ' +
                                 str(eye_data[1]) + '\n')
        # when searching for a particular eye data
        # sometimes useful to not print timestamp
        # self.eye_data_file.write(str(eye_data).strip('()') + '\n')

        if not self.pause:
            # stuff for plotting
            #print 'not paused'
            # convert to pixels for plotting, need the eye position
            # from the last run for the starting position, and the
            # current eye position for ending position
            last_eye = self.eye_data_to_pixel(self.eye_data[-1])
            plot_eye_data = self.eye_data_to_pixel(eye_data)
            # save current data, so can erase plot later
            self.eye_data.append((eye_data[0], eye_data[1]))
            #print 'size eye data', len(self.eye_data)

            # unittesting is the only time there is no second screen, so
            # impossible to do eye positions
            if not self.unittest:
                # any reason we can't get rid of the the previous self.eye_data here,
                # instead of when we clear the screen? Pop from the beginning?
                if self.remove_eyes:
                    #print 'clear eyes'
                    # get rid of any eye positions left on screen
                    self.clear_eyes()
                    self.remove_eyes = False
                # plot new eye segment
                eye = LineSegs()
                #eye.setThickness(2.0)
                eye.setThickness(2.0)
                #print 'last', last_eye
                #print 'now', plot_eye_data
                eye.moveTo(last_eye[0], 55, last_eye[1])
                eye.drawTo(plot_eye_data[0], 55, plot_eye_data[1])
                #print('plotted eye', plot_eye_data)
                #min, max = eye.getTightBounds()
                #size = max - min
                #print size[0], size[2]
                node = self.base.render.attachNewNode(eye.create(True))
                node.show(BitMask32.bit(0))
                node.hide(BitMask32.bit(1))
                self.eyes.append(node)
                if self.use_daq_data:
                    self.text3.setText('IScan: [' + str(round(eye_data[0], 3)) +
                                       ', ' + str(round(eye_data[1], 3)) + ']')
                else:
                    self.text3.setText('Fake Data: [' + str(round(eye_data[0], 3)) +
                                       ', ' + str(round(eye_data[1], 3)) + ']')
            # check if in window for auto-calibrate - only update time if was none previously
            if self.check_fixation:
                #print 'check fixation', self.check_fixation
                # if already fixated, make sure hasn't left
                #print 'tolerance', self.tolerance
                distance = get_distance(plot_eye_data, (self.square.getPos()[0], self.square.getPos()[2]))
                #print 'distance', distance
                # self.fix_time is how long subject has been fixating
                #print 'fix_time', self.fix_time
                # change tolerance to pixels, currently in degree of visual angle
                tolerance = self.tolerance / self.deg_per_pixel
                #print tolerance

                if self.fix_time:
                    #print 'already fixated'
                    # if already fixated, make sure doesn't break fixation
                    if distance > tolerance:
                        # abort trial, start again with square in same position
                        #print 'abort'
                        self.restart_timer(None)
                else:
                    #print 'waiting for fixation'
                    if distance < tolerance:
                        #print 'and fixated!'
                        #print 'square', self.square.getPos()[0], self.square.getPos()[2]
                        #print 'distance', self.distance((eye_data), (self.square.getPos()[0], self.square.getPos()[2]))
                        #print 'tolerance', self.tolerance
                        #print eye_data
                        # restart timer, started fixating now
                        self.restart_timer(self.frameTask.time)
                        #print 'time fixated', self.fix_time
                        #print 'self.next', self.next

    def eye_data_to_pixel(self, eye_data):
        # change the offset and gain as necessary, so eye data looks
        # right on screen. Actually, most of this is changed in IScan
        # before it ever makes it to this machine, but found we have to
        # at least change the gain by a couple of order of magnitudes
        return [(eye_data[0] + self.offset[0]) * self.gain[0],
                (eye_data[1] + self.offset[1]) * self.gain[1]]

    def change_gain_or_offset(self, ch_type, x_or_y, ch_amount):
        if ch_type == 'gain':
            self.gain[x_or_y] += ch_amount
            self.text.setText('Gain:' + str(self.gain))
            self.time_data_file.write(
                str(time()) + ', Change Gain, ' +
                str(self.gain[0]) + ', ' +
                str(self.gain[1]) + '\n')
        else:
            self.offset[x_or_y] += ch_amount
            #self.text2.setText('Offset:' + '[{0:03.2f}'.format(self.offset[0])
            #                   + ', ' + '{0:03.2f}]'.format(self.offset[1]))
            self.time_data_file.write(
                str(time()) + ', Change Offset, ' +
                str(self.offset[0]) + ', ' +
                str(self.offset[1]) + '\n')

    def change_tolerance(self, direction):
        self.tolerance += direction
        self.set_text4()
        #self.text4.setText('Tolerance: ' + str(self.tolerance) + ' degrees from center')
        #self.text2.setText('Tolerance: ' + str(self.tolerance / self.deg_per_pixel) + 'pixels')
        for win in self.eye_window:
            win.detachNode()
        #self.eye_window.detachNode()
        self.show_window(self.square.getPos())

    def change_tasks(self):
        # change from manual to auto-calibrate or vise-versa
        self.manual = not self.manual
        #print('switched manual?', self.manual)
        # do not finish whatever loop you were in
        # not sure how to do this
        # close stuff
        if self.use_daq_data:
            #print 'stopping daq tasks'
            # have to stop tasks before closing files
            self.eye_task.DoneCallback(self.eye_task)
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        self.close_files()
        del self.pos
        #self.clear_eyes()
        # clear text from IScan, rest should be okay, since not
        # updated frequently
        # self.text3.removeNode()
        #print 'task', self.manual
        # get configurations from config file
        config = {}
        execfile(self.config_file, config)
        # reset stuff
        self.flag_task_switch = False
        self.frameTask.move = False
        self.next = 0
        if not self.unittest:
            # text4 and text5 change
            self.set_text4()
            self.set_text5()
        self.setup_positions(config)
        self.open_files(config)
        if self.use_pydaq:
            self.start_eye_task()

    def clear_eyes(self):
        # We can now stop plotting eye positions,
        # and get rid of old eye positions.
        for eye in self.eyes:
            eye.removeNode()
        #print 'should be no nodes now', self.eyes
        self.eyes = []
        # now can also get rid of eye_data, except the last position, so we don't eat up all of our memory
        last_eye = self.eye_data[-1]
        self.eye_data = []
        self.eye_data.append(last_eye)
        #print 'eye data clear, should be just one position', self.eye_data

    def show_window(self, square):
        # draw line around target representing how close the subject has to be looking to get reward
        #print 'show window'
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
            eye_window.drawTo((x + square[0], 55, y + square[2]))

        # draw a radius line
        #eye_window.moveTo(square[0], 55, square[2])
        #eye_window.drawTo(square[0], 55, square[2] + self.tolerance)
        #print 'distance drawn', self.distance((square[0], square[2]), (square[0], square[2] + self.tolerance))
        # True optimizes the line segments, which sounds useful
        node = self.base.render.attachNewNode(eye_window.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_window.append(node)
        #print 'eye window', self.eye_window

    @staticmethod
    def distance(p0, p1):
        """
        (tuple, tuple) -> float
        Returns the distance between 2 points. p0 is a tuple with (x, y)
        and p1 is a tuple with (x1, y1)
        """
        dist = sqrt((float(p0[0]) - float(p1[0])) ** 2 + (float(p0[1]) - float(p1[1])) ** 2)
        return dist

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
        print(res_eye[1]/2 - res_eye[1]/6)
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

    def create_square(self, scale):
        # setting up square object
        obj = self.base.loader.loadModel("models/plane")
        # don't turn on yet
        # make depth greater than eye positions so eye positions are on top of squares
        # initial position of Square
        pos = Point2(0, 0)
        obj.setPos(Point3(pos.getX(), self.depth, pos.getY()))  # Set initial posistion
        # need to scale to be correct visual angle
        #obj.setScale(1)
        obj.setScale(scale)
        #obj.setTransparency(1)
        square = self.base.loader.loadTexture("textures/calibration_square.png")
        obj.setTexture(square, 1)
        # starting color, should be set by model, but let's make sure
        obj.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        return obj

    def setup_positions(self, config):
        # If doing manual, need to initiate Positions differently than if random,
        # so key presses work properly
        if self.manual:
            #print 'manual'
            self.pos = Positions(config)
        else:
            #print 'manual is false, auto'
            self.pos = Positions(config).get_position(self.depth, True)

    def setup_pydaq(self):
        #print 'setup pydaq'
        if self.use_daq_data:
            self.start_eye_task()
        if self.use_daq_reward:
            #print 'setup reward'
            self.start_reward_task()

    def start_eye_task(self):
        self.eye_task = pydaq.EOGTask()
        self.eye_task.SetCallback(self.get_eye_data)
        self.eye_task.StartTask()

    def start_reward_task(self):
        self.reward_task = pydaq.GiveReward()

    # Key Functions
    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def set_key(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

    def switch_task_flag(self, val):
        self.flag_task_switch = val

    # this actually assigns keys to methods
    def setup_keys(self):
        self.accept("escape", self.close)  # escape
        # starts turning square on
        self.accept("space", self.start)  # default is the program waits 2 min

        #self.accept("m", self.change_tasks)
        # switches from manual to auto-calibrate or vise-versa,
        # but only at end of current loop (after reward)
        # True signifies that we want to change
        self.accept("s", self.switch_task_flag, [True])
        # For adjusting calibration
        # inputs, gain or offset, x or y, how much change
        # gain - up and down are y
        self.accept("shift-arrow_up", self.change_gain_or_offset, ['gain', 1, 1])
        self.accept("shift-arrow_up-repeat", self.change_gain_or_offset, ['gain', 1, 1])
        self.accept("shift-arrow_down", self.change_gain_or_offset, ['gain', 1, -1])
        self.accept("shift-arrow_down-repeat", self.change_gain_or_offset, ['gain', 1, -1])
        # gain - right and left are x
        self.accept("shift-arrow_right", self.change_gain_or_offset, ['gain', 0, 1])
        self.accept("shift-arrow_right-repeat", self.change_gain_or_offset, ['gain', 0, 1])
        self.accept("shift-arrow_left", self.change_gain_or_offset, ['gain', 0, -1])
        self.accept("shift-arrow_left-repeat", self.change_gain_or_offset, ['gain', 0, -1])
        # offset - up and down are y
        self.accept("control-arrow_up", self.change_gain_or_offset, ['offset', 1, 1])
        self.accept("control-arrow_up-repeat", self.change_gain_or_offset, ['offset', 1, 1])
        self.accept("control-arrow_down", self.change_gain_or_offset, ['offset', 1, -1])
        self.accept("control-arrow_down-repeat", self.change_gain_or_offset, ['offset', 1, -1])
        # offset - right and left are x
        self.accept("control-arrow_right", self.change_gain_or_offset, ['offset', 0, 1])
        self.accept("control-arrow_right-repeat", self.change_gain_or_offset, ['offset', 0, 1])
        self.accept("control-arrow_left", self.change_gain_or_offset, ['offset', 0, -1])
        self.accept("control-arrow_left-repeat", self.change_gain_or_offset, ['offset', 0, -1])

        # For adjusting tolerance (allowable distance from target that still gets reward)
        self.accept("alt-arrow_up", self.change_tolerance, [0.5])
        self.accept("alt-arrow_down", self.change_tolerance, [-0.5])

        # this really doesn't need to be a dictionary now,
        # but may want to use more keys eventually
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

    def setup_window2(self, config):
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
        resolution = config['WIN_RES']
        res_eye = config['EYE_RES']
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
        # degree per pixel is important only for determining where to plot squares, no effect
        # on eye position plotting, so use projector resolution, screen size, etc
        self.deg_per_pixel = visual_angle(config['SCREEN'], resolution, config['VIEW_DIST'])[0]
        print 'deg_per_pixel', self.deg_per_pixel
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
        print 'calibration window', res
        wp.setSize(int(res[0]), int(res[1]))
        #wp.setSize(1600, 900)
        #wp.setOrigin(-1600, 0)
        wp.setOrigin(0, 0)
        #wp.setOrigin(-int(res[0]), 0)
        #wp.setUndecorated(True)
        self.base.win.requestProperties(wp)

    def setup_task(self):
        # get configurations from config file
        config = {}
        execfile(self.config_file, config)
        # set up square positions
        self.setup_positions(config)
        # set up keys
        self.setup_keys()
        # open files
        self.open_files(config)
        if not self.use_daq_data:
            self.fake_data = yield_eye_data((0.0, 0.0))
        if self.use_pydaq:
            # start pydaq stuff
            self.setup_pydaq()

    # File methods
    def open_files(self, config):
        # open file for recording eye data
        subject = config['SUBJECT']
        data_dir = 'data/' + config['SUBJECT']
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if self.manual:
            self.eye_file_name = data_dir + '/eye_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
            self.time_file_name = data_dir + '/time_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
        else:
            self.eye_file_name = data_dir + '/eye_cal2_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
            self.time_file_name = data_dir + '/time_cal2_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")

        #print('open', self.eye_file_name)
        # open file for recording eye positions
        self.eye_data_file = open(self.eye_file_name, 'w')
        self.eye_data_file.write('timestamp, x_position, y_position, for subject: ' + subject + '\n')
        # open file for recording event times
        self.time_data_file = open(self.time_file_name, 'w')
        self.time_data_file.write('timestamp, task, for subject: ' + subject + '\n')

        # open and close file for keeping configuration info
        # turns out there is a lot of extra crap in the config dictionary,
        # and I haven't figured out a pretty way to get rid of the extra crap.
        # Honestly, the best thing may be to just make a copy of the original damn file.
        # maybe look to see how pandaepl handles this
        #config_file_name = data_dir + '/config_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")

        #w = csv.writer(open(config_file_name, 'w'))
        #for name, value in config.items():
        #    w.writerow([name, value])

        #for name, value in config.items():
        #    print name, value
        # if you want to see the frame rate
        # window.setFrameRateMeter(True)

    # Closing methods
    def close_files(self):
        #print('close', self.eye_file_name)
        self.eye_data_file.close()
        self.time_data_file.close()

    def close(self):
        #print 'close'
        if self.use_daq_data:
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        self.close_files()
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
    W.setup_task()
    W.base.run()

