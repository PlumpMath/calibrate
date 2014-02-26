from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from panda3d.core import BitMask32, getModelPath
from panda3d.core import WindowProperties, TextNode
from panda3d.core import OrthographicLens, LineSegs
from positions import Positions, visual_angle
import sys
import random
import os
import datetime
from time import time, sleep
from math import sqrt, radians, cos, sin

# crazy gymnastics to not load the fake data unless necessary
# only load pydaq if it's available
try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    #print 'loaded'
except:
    print 'Not using PyDaq'


class World(DirectObject):

    def __init__(self, mode=None, test=None):
        #print 'unittest', unittest
        #print 'init'
        #print 'mode', mode
        #print 'test', test
        if test == '1' or test == 1:
            # test (either unittest or testing on mac) so use fake eye data and testing configuration.
            # for testing, always leave gain at one, so eye_data and plot_eye_data are the same
            # if want fake data on windows, change WIN_RES in config_test to an actual resolution to
            # get second window
            self.gain = [1, 1]
            #print 'test'
            self.test = True
            self.daq = False
            import fake_eye_data
            config_file = 'config_test.py'
        else:
            # the voltage from the eye tracker runs from about 5 to -5 volts,
            # so 100 should be sort of close...
            self.gain = [100, 100]
            #print 'no test'
            self.test = False
            self.daq = True
            config_file = 'config.py'

        # seems like we can adjust the offset completely in ISCAN
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
        execfile(config_file, config)
        self.tolerance = config['TOLERANCE']

        # start Panda3d
        self.base = ShowBase()

        #print base.pipe.getDisplayWidth()
        #print base.pipe.getDisplayHeight()
        # if window is offscreen (for testing), does not have WindowProperties,
        # so can't open second window.
        # if an actual resolution in config file, change to that resolution,
        # otherwise keep going...
        if config['WIN_RES'] != 'Test':
            self.setup_window2(config)
        else:
            # resolution in file equal to test, so use the projector screen
            # value for determining pixels size. In this case, accuracy is not
            # important, because never actually calibrating with this setup.
            resolution = [1024, 768]
            self.deg_per_pixel = visual_angle(config['SCREEN'], resolution, config['VIEW_DIST'])[0]

        #print 'window loaded'
        self.eyes = []

        self.open_files(config)

        # starts out not fixated, so no fixation time, and not checking for fixation (will
        # check for fixation when stimulus comes on, if we are doing a random task)
        self.fix_time = None
        self.check_fixation = False

        self.base.setBackgroundColor(115 / 255, 115 / 255, 115 / 255)
        self.base.disableMouse()

        # create square for stimulus
        # scale 17 is one visual angle, linear so just multiply by 17
        self.square = self.create_square(config['SQUARE_SCALE']*17)
        #print 'scale', config['SQUARE_SCALE']*17

        # set up square positions
        self.setup_positions(config)

        # Eye Data and reward
        self.eye_data = []
        self.eye_data.append((0.0, 0.0))
        self.remove_eyes = False
        #self.reward = True

        # initialize list for eye window
        self.eye_window = []

        # set up daq for eye and reward, if on windows and not testing
        # testing random mode depends on being able to control eye position
        if self.daq and not self.test:
            #self.gain = 0
            #self.offset = 0
            self.eye_task = pydaq.EOGTask()
            self.eye_task.SetCallback(self.get_eye_data)
            self.eye_task.StartTask()
            self.reward_task = pydaq.GiveReward()
        else:
            #self.fake_data = fake_eye_data.yield_eye_data((base.win.getXSize()/2, -base.win.getYSize()/2))
            self.fake_data = fake_eye_data.yield_eye_data((0.0, 0.0))
            self.reward_task = None
        self.num_beeps = config['NUM_BEEPS']
        # first task is square_on
        self.next = 0

        # Keyboard stuff:
        self.setup_keys()

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
        # first interval will be the move interval (off to move/on - won't
        # actually move)
        # if not testing, first square will turn on 1 minute after experiment started,
        #  or when the spacebar is pressed to start it early
        # hmmm, 40 seconds is the limit after which windows decides python isn't responding
        # what do I have to do inside the loop so it doesn't think this?
        if self.test:
            self.frameTask.interval = random.uniform(*self.all_intervals[3])
        else:
            self.frameTask.interval = 40
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
            4: 'Square moved and on \n'
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
        #print task.move
        if not task.move:

            #print 'new loop', task.time
            #print 'frame', task.frame
            if task.time > task.interval:
                #print 'actual time interval was over: ', task.interval
                # for auto-random task, if we are checking for fixation,
                # (this happens when square is on, but not yet faded)
                # but don't have a fix_time, then we have not fixated by
                # end of interval, and need to task start over.
                #print 'fix?', self.check_fixation
                #print 'fixation?', self.fix_time
                if self.check_fixation and not self.fix_time:
                    #print 'no fixation, start over'
                    self.redraw_square(None)
                    return task.cont
                elif self.check_fixation:
                    # if we are done with our interval, and haven't restarted
                    # I think we want to reset fix_time
                    self.fix_time = None

                # task.switch will manipulate the square and
                # update the interval to the next task.
                #print task.time
                #print 'task', task.switch[self.next]
                #print 'in frame loop', self.next
                #print 'old interval', task.interval
                task.switch[self.next]()
                #print task.file[self.next]
                #print 'just did task', self.next
                #self.time_data_file.write('test' + '\n')
                self.time_data_file.write(str(time()) + ', ' + task.file[self.next])
                # if we are turning off the square, next is moving.
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

                # if we are at self.next = 4, then the last task was reward,
                # and we need to reset our counter to zero. Since we do square_on
                # at the end of our move method, the incrementing to one at the
                # end of our loop will put as at self.next = 1, (square_fade), which
                # is correct. We need to do this before we change the interval, so
                # that we are using the correct corresponding interval
                if self.next == 4:
                    self.next = 0
                    #print self.all_intervals[self.next]
                interval = random.uniform(*self.all_intervals[self.next])
                #print 'next interval', interval
                task.interval = task.time + interval
                #print 'next switch time', task.interval
                #print 'time now', task.time
                #print 'next', self.next
                self.next += 1
                #print 'update task number', self.next
        else:
            #print "check for key"
            #print self.keys["switch"]
            # check to see if we should move the target
            #print 'switch', self.keys
            # if we haven't received a keypress before interval is over, default to 0,0
            if task.time > task.interval:
                if self.keys["switch"]:
                    #print 'manual move'
                    #print 'switch', self.keys["switch"]
                    self.square_move(self.pos.get_key_position(self.depth, self.keys["switch"]))
                else:
                    # switch to center
                    self.square_move(self.pos.get_key_position(self.depth, 5))

                self.keys["switch"] = 0  # remove the switch flag
                # square is on, so nex thing to happen is it dims,
                # this happens after on interval, 0
                # make sure next interval is based on the time we actually moved the target (now!)
                task.interval = task.time + random.uniform(*self.all_intervals[0])
                # Next is dim, since it turned on when moved
                self.next = 1

                # don't come back here until ready to move again
                task.move = False
                #print 'back to regularly scheduled program'

        # if using fake data, plot
        if self.test:
            self.get_eye_data(self.fake_data.next())

        return task.cont  # Since every return is Task.cont, the task will
        #continue indefinitely

    def start(self):
        # starts the experiment early (normal start time is 2 minutes)
        self.frameTask.interval = 0

    def get_eye_data(self, eye_data):
        # We want to change gain on data being plotted,
        # but write to file the data as received from eye tracker.
        # get last eye position
        #print self.eye_data
        last_eye = self.eye_data_to_pixel(self.eye_data[-1])
        #print 'first eye', self.eye_data_to_pixel(self.eye_data[0])
        #print 'last', last_eye
        plot_eye_data = self.eye_data_to_pixel(eye_data)
        #print 'now', plot_eye_data
        # pydaq calls this function every time it calls back to get eye data,
        # if testing, called from frame_loop with fake data
        self.eye_data.append((eye_data[0], eye_data[1]))
        #print 'size eye data', len(self.eye_data)
        #print eye_data
        #for x in [-3.0, 0.0, 3.0]:
        if self.first:
            #print 'first?', eye_data[0], eye_data[1]
            self.time_data_file.write(str(time()) + ', start collecting eye data\n')
            self.first = False
        if not unittest:
            #print 'last eye', last_eye
            #print 'show eye', plot_eye_data
            if self.remove_eyes:
                #print 'clear eyes'
                # get rid of any eye positions left on screen
                self.clear_eyes()
                self.remove_eyes = False

            eye = LineSegs()
            #eye.setThickness(2.0)
            eye.setThickness(2.0)
            #print 'last', last_eye
            #print 'now', plot_eye_data
            eye.moveTo(last_eye[0], 55, last_eye[1])
            eye.drawTo(plot_eye_data[0], 55, plot_eye_data[1])
            node = render.attachNewNode(eye.create())
            node.show(BitMask32.bit(0))
            node.hide(BitMask32.bit(1))
            self.eyes.append(node)
            #print eye.getVertices()
            #print 'eyes', self.eyes
            #eye = self.smiley.copyTo(self.root)
            #print eye_data[0], eye_data[1]
            #eye.setPos(plot_eye_data[0], 55, plot_eye_data[1], )
            #self.eyes += [eye]
            #self.text3.setText('IScan: ' + '[0, 0]')
            self.text3.setText('IScan: [' + str(round(eye_data[0], 3)) +
                               ', ' + str(round(eye_data[1], 3)) + ']')
        # write eye data and timestamp to file
        #print eye_data
        self.eye_data_file.write(str(time()) + ', ' +
                                 str(eye_data[0]) + ', ' +
                                 str(eye_data[1]) + '\n')
        # when searching for a particular eye data
        # sometimes useful to not print timestamp
        # self.eye_data_file.write(str(eye_data).strip('()') + '\n')

        #print eye_data
        # check if in window for auto-calibrate - only update time if was none
        if self.check_fixation:
            #print 'check fixation', self.check_fixation
            # if already fixated, make sure hasn't left
            #print 'tolerance', self.tolerance
            distance = self.distance((plot_eye_data), (self.square.getPos()[0], self.square.getPos()[2]))
            #print 'distance', distance
            #print self.fix_time
            # change tolerance to pixels, currently in degree of visual angle
            tolerance = self.tolerance / self.deg_per_pixel
            #print tolerance

            if self.fix_time:
                #print 'already fixated'
                if distance > tolerance:
                    # abort trial, start again with square in same position
                    #print 'abort'
                    self.redraw_square(None)
            else:
                #print 'waiting for fixation'
                if distance < tolerance:
                    #print 'and fixated!'
                    #print 'square', self.square.getPos()[0], self.square.getPos()[2]
                    #print 'distance', self.distance((eye_data), (self.square.getPos()[0], self.square.getPos()[2]))
                    #print 'tolerance', self.tolerance
                    #print eye_data
                    self.redraw_square(self.frameTask.time)
                    #self.fix_time = self.frameTask.time
                    #print 'time fixated', self.fix_time
                    #print 'self.next', self.next
                    #interval = self.all_intervals[4]
                    #self.frameTask.interval = self.fix_time + interval
                    #print 'new interval', self.frameTask.interval
        #print eye.getPos()
        #min, max = eye.getTightBounds()
        #size = max - min
        #print size[0], size[2]

    def redraw_square(self, fix_time):
        #print 'redraw square'
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
            # when new target shows up, this will change back to true
            self.check_fixation = False
        else:
            # timer starts out as interval for how long the subject has to fixate,
            # once fixated, need to reset the timer so fixation is held right amount of time.
            # So, keep interval as 1, but set the interval to fixation interval
            #print 'restarting timer for holding fixation'
            self.next = 1
            interval = self.all_intervals[4]

        # new interval always starts with now
        self.frameTask.interval = self.frameTask.time + interval
        self.fix_time = fix_time
        #print 'if not fixated, should be none', self.fix_time

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
        self.text4.setText('Tolerance: ' + str(self.tolerance) + ' degrees from center')
        #self.text2.setText('Tolerance: ' + str(self.tolerance / self.deg_per_pixel) + 'pixels')
        for win in self.eye_window:
            win.detachNode()
        #self.eye_window.detachNode()
        self.show_window(self.square.getPos())

    def change_tasks(self, override=None):
        #print(override)
        if override is not None:
            self.manual = override
            #print('override, manual now', self.manual)
        else:
            # change from manual to auto-calibrate or vise-versa
            self.manual = not self.manual
            #print('switch, manual now', self.manual)
        #print 'task', self.manual
        # get configurations from config file
        config = {}
        execfile('config.py', config)
        # reset stuff
        self.setup_text()
        del self.pos
        self.setup_positions(config)

    # Square Functions
    def square_on(self):
        position = self.square.getPos()
        #print position
        self.time_data_file.write(str(time()) + ', Square Position, ' + str(position[0]) + ', '
                                  + str(position[2]) + '\n')\
        #print 'square', self.manual
        #print 'square on, 0'
        # make sure in correct color
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        # and render
        self.square.reparentTo(render)
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
        self.fixed = False

    def square_fade(self):
        # print 'square fade, 1'
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
            except StopIteration:
                self.close()

        self.square.setPos(Point3(position))
        #print 'square', position[0], position[2]
        # go directly to on
        self.square_on()

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
        angleRadians = radians(360)
        for i in range(50):
            a = angleRadians * i /49
            y = tolerance * sin(a)
            x = tolerance * cos(a)
            eye_window.drawTo((x + square[0], 55, y + square[2]))

        # draw a radius line
        #eye_window.moveTo(square[0], 55, square[2])
        #eye_window.drawTo(square[0], 55, square[2] + self.tolerance)
        #print 'distance drawn', self.distance((square[0], square[2]), (square[0], square[2] + self.tolerance))
        node = render.attachNewNode(eye_window.create())
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.eye_window.append(node)
        #print 'eye window', self.eye_window

    def distance(self, p0, p1):
        """
        (tuple, tuple) -> float
        Returns the distance between 2 points. p0 is a tuple with (x, y)
        and p1 is a tuple with (x1, y1)
        """
        dist = sqrt((float(p0[0]) - float(p1[0])) ** 2 + (float(p0[1]) - float(p1[1])) ** 2)
        return dist

    # Setup Functions

    def setup_text(self):
        self.text = TextNode('gain')
        self.text.setText('Gain: ' + str(self.gain))
        #textNodePath = aspect2d.attachNewNode(self.text)
        textNodePath = render.attachNewNode(self.text)
        textNodePath.setScale(30)
        #textNodePath.setScale(0.1)
        #textNodePath.setPos(-300, 0, 200)
        textNodePath.setPos(100, 0, 300)
        textNodePath.show(BitMask32.bit(0))
        textNodePath.hide(BitMask32.bit(1))

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
        text3NodePath = render.attachNewNode(self.text3)
        text3NodePath.setScale(30)
        text3NodePath.setPos(100, 0, 250)
        text3NodePath.show(BitMask32.bit(0))
        text3NodePath.hide(BitMask32.bit(1))

        if not self.manual:
            self.text4 = TextNode('tolerance')
            self.text4.setText('Tolerance: ' + str(self.tolerance) + 'degrees, alt-arrow to adjust')
            text4NodePath = camera.attachNewNode(self.text4)
            text4NodePath.setScale(30)
            text4NodePath.setPos(100, 0, 200)
            text4NodePath.show(BitMask32.bit(0))
            text4NodePath.hide(BitMask32.bit(1))

    def create_square(self, scale):
        # setting up square object
        obj = self.base.loader.loadModel("models/plane")
        # don't turn on yet
        # make depth greater than eye positions so eye positions are on top of squares
        # initial position of Square
        pos = Point2(0, 0)
        self.depth = 55
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

    # Key Functions
    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def set_key(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

    # this actually assigns keys to methods
    def setup_keys(self):
        self.accept("escape", self.close)  # escape
        # starts turning square on
        self.accept("space", self.start)  # default is the program waits 2 min

        self.accept("m", self.change_tasks)  # switches from manual to auto-calibrate
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
        #print 'second window'
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
            # resolution for main window
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
        lens.setFilmSize(int(resolution[0]),int(resolution[1]))
        #lens.setFilmSize(800, 600)
        # this allows us to layer, as long as we use between -100
        # and 100 for z. (eye position on top of squares)
        lens.setNearFar(-100,100)

        camera = self.base.camList[0]
        camera.node().setLens(lens)
        camera.reparentTo(render)

        camera2 = self.base.camList[1]
        camera2.node().setLens(lens)
        camera2.reparentTo(render)

        # set bit mask for eye positions
        camera.node().setCameraMask(BitMask32.bit(1))
        camera2.node().setCameraMask(BitMask32.bit(0))

        # text only happens on second window
        self.setup_text()

    def set_resolution(self, res):
        # sets the resolution for the main window (projector)
        wp = WindowProperties()
        print 'calibration window', res
        wp.setSize(int(res[0]), int(res[1]))
        #wp.setFullscreen(True)
        #wp.setSize(1600, 900)
        #wp.setOrigin(-1600, 0)
        wp.setOrigin(0, 0)
        #wp.setOrigin(-int(res[0]), 0)
        #wp.setUndecorated(True)
        self.base.win.requestProperties(wp)

    def open_files(self, config):
        # open file for recording eye data
        data_dir = 'data/' + config['SUBJECT']
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.eye_file_name = data_dir + '/eye_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
        self.eye_data_file = open(self.eye_file_name, 'w')
        self.eye_data_file.write('timestamp, x_position, y_position' + '\n')
        # open file for recording event times
        self.time_file_name = data_dir + '/time_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
        self.time_data_file = open(self.time_file_name, 'w')
        self.time_data_file.write('timestamp, task' + '\n')
        # When we first open the file, we will write a line for time started calibration
        self.first = True

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

    # Closing functions
    def close_files(self):
        self.eye_data_file.close()
        self.time_data_file.close()

    def close(self):
        #print 'close'
        if self.daq:
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        self.close_files()
        if unittest:
            self.ignoreAll()  # ignore everything, so nothing weird happens after deleting it.
        else:
            sys.exit()

if __name__ == "__main__":
    #print 'run as module'
    unittest = False
    #print 'main'
    # default is manual
    if len(sys.argv) == 1:
        W = World(1)
    elif len(sys.argv) == 2:
        W = World(sys.argv[1])
    else:
        W = World(sys.argv[1], sys.argv[2])
    run()

else:
    #print 'test'
    # some things we truly only want to do while unit testing
    unittest = True
    # file was imported
    # only happens during testing...
