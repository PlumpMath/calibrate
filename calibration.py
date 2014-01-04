from __future__ import division
#import direct.showbase.ShowBase
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from panda3d.core import BitMask32, getModelPath
from panda3d.core import WindowProperties, TextNode
#from pandac.PandaModules import ClockObject
#from panda3d.core import GraphicsWindow
from panda3d.core import OrthographicLens, LineSegs
#from direct.task.Task import Task
from positions import Positions
import sys
import random
import os
import datetime
from time import time, sleep
from math import sqrt, radians, cos, sin

#from pandaepl import ptime

# crazy gymnastics to not load the fake data unless necessary
try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    #print 'loaded'
except:
    pass

# IF SWITCHING MACHINES, ALWAYS MAKE SURE CONFIG HAS CORRECT RESOLUTION!!!!
# NEED TO SAVE STUFF NECESSARY FOR CALIBRATION - RESOLUTION, ETC.

class World(DirectObject):


    def __init__(self, mode=None):
        #print 'unittest', unittest
        #print 'init'
        #print manual
        # on the assumption that the voltage from the eye tracker runs from about 0 to 6 volts,
        # 100 should be sort of close...
        #self.gain = [100, 100]
        self.gain = [100, 100]
        self.offset = [0, 0]
        # True for fake data, false for pydaq provides data
        # only need to change this for testing on windows
        self.test = True
        #self.test = False
        # Python assumes all input from sys are string, but not
        # input variables
        if mode == '1' or mode == 1:
            self.manual = True
        else:
            self.manual = False
            #print 'manual', self.manual

        try:
            pydaq
            self.daq = True
        except NameError:
            self.daq = False
            # if there is no daq, we are on mac, and must be in test mode
            self.test = True
            # If we are on the mac (no pydaq), always testing,
        # and always load fade data
        # if on windows, only do it while testing
        if self.test:
            import fake_eye_data

            self.daq = False
        if unittest:
            #print 'yup, still unittest'
            config_file = 'config_test.py'
            # if doing tests, I think we need fake data
            self.test = True
            #FrameBufferProperties.getDefault()
            #WindowProperties.getDefault()
        else:
            config_file = 'config.py'

        # get configurations from config file
        config = {}
        execfile(config_file, config)
        self.tolerance = config['TOLERANCE']

        #window = direct.showbase.ShowBase.ShowBase()
        self.base = ShowBase()

        #print base.pipe.getDisplayWidth()
        #print base.pipe.getDisplayHeight()
        # if window is offscreen (for testing), does not have WindowProperties,
        # should be better way to deal with this, but haven't found it yet.
        # if an actual resolution in config file, change to that resolution,
        # otherwise keep going...
        if config['WIN_RES'] != 'Test':
            props = WindowProperties()
            #props.setForeground(True)
            props.setCursorHidden(True)
            self.base.win.requestProperties(props)
            #print props

            # Need to get this better. keypress only works with one window.
            # plus looks ugly.

            window2 = self.base.openWindow()
            window2.setClearColor((115 / 255, 115 / 255, 115 / 255, 1))
            #window2.setClearColor((1, 0, 0, 1))
            #props.setCursorHidden(True)
            #props.setOrigin(0, 0)
            resolution = config['WIN_RES']
            if resolution is not None:
                self.set_resolution(resolution)
                props.setOrigin(0, 0)
                props.setSize(1024, 768)
            else:
                props.setOrigin(600, 200)  # make it so windows aren't on top of each other
                resolution = [800, 600]  # if no resolution given, assume normal panda window

            window2.requestProperties(props)
            #print window2.getRequestedProperties()

            lens = OrthographicLens()
            lens.setFilmSize(int(resolution[0]),int(resolution[1]))
            #lens.setFilmSize(800, 600)
            lens.setNearFar(-100,100)

            camera = self.base.camList[0]
            camera.node().setLens(lens)
            camera.reparentTo( render )

            camera2 = self.base.camList[1]
            camera2.node().setLens(lens)
            camera2.reparentTo( render )

            self.text = TextNode('gain')
            self.text.setText('Gain: ' + str(self.gain))
            textNodePath = aspect2d.attachNewNode(self.text)
            textNodePath.setScale(0.1)
            #textNodePath.setPos(-300, 0, 200)
            textNodePath.setPos(0.1, 0, 0.9)

            self.text2 = TextNode('offset')
            self.text2.setText('Offset: ' + str(self.offset))
            text2NodePath = aspect2d.attachNewNode(self.text2)
            text2NodePath.setScale(0.1)
            #textNodePath.setPos(-300, 0, 200)
            text2NodePath.setPos(0.1, 0, 0.8)

            self.text3 = TextNode('iscan')
            self.text3.setText('IScan: ' + '[0, 0]')
            text3NodePath = aspect2d.attachNewNode(self.text3)
            text3NodePath.setScale(0.1)
            #textNodePath.setPos(-300, 0, 200)
            text3NodePath.setPos(0.1, 0, 0.7)

            self.text4 = TextNode('tolerance')
            self.text4.setText('Tolerance: ' + str(self.tolerance) + ' pixels')
            text3NodePath = aspect2d.attachNewNode(self.text4)
            text3NodePath.setScale(0.1)
            #textNodePath.setPos(-300, 0, 200)
            text3NodePath.setPos(0.1, 0, 0.6)

            # eye position is just a smiley painted black
            #self.smiley = self.base.loader.loadModel('smiley')
            #self.smiley.reparentTo(camera)
            #self.smiley.setPos(-3, 0, 3)
            #self.smiley.setPos(0, 55, 0)
            #self.smiley.setColor(0, 0, 0, 0)
            #self.smiley.setColor(0, 0, 1, 0)
            #self.smiley.setScale(0.1)
            #self.smiley.setScale(1.001)
            #self.smiley.setScale(3)
            #min, max = self.smiley.getTightBounds()
            #size = max - min
            #print size[0], size[2]
            camera.node().setCameraMask(BitMask32.bit(0))
            camera2.node().setCameraMask(BitMask32.bit(1))
            #self.smiley.hide(BitMask32.bit(1))
            #self.smiley.show(BitMask32.bit(0))
            # if root is set to camera, don't see at all
            # if set to pixel2d, see large on first, and teeny on second. meh.
            #self.root = self.base.render.attachNewNode("Root")
            #self.root = self.base.render.attachNewNode("Root")

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
        self.square = self.create_square()

        # if doing manual calibration, always get reward after square turns off,
        # if auto, require fixation. If doing manual, need to initiate Positions
        # differently than if random
        if self.manual:
            #print 'yes, still manual'
            #self.reward = True
            self.pos = Positions(config)
        else:
            #print 'manual is false'
            #self.reward = False
            self.pos = Positions(config).get_position(self.depth, True)

        # Eye Data and reward
        self.eye_data = []
        self.eye_data.append((0.0, 0.0))
        self.remove_eyes = False
        #self.reward = True

        # first square is always in center
        self.eye_window = []
        if not self.manual:
            self.show_window((0,0,0))


        if self.daq:
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
        self.accept("escape", self.close)  # escape
        # starts turning square on
        self.accept("space", self.start)  # default is the program waits 2 min

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
        self.accept("alt-arrow_up", self.change_tolerance, [1])
        self.accept("alt-arrow_down", self.change_tolerance, [-1])

        # minutes and then starts, spacebar will start the program right away
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

        # Our intervals
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # reward_interval - time from off to reward
        # move_interval - time from reward to move/on
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
            0: 'Square on',
            1: 'Square dims',
            2: 'Square off',
            3: 'Reward',
            4: 'Square moves'
        }
        # task.move always starts as False, will be changed to true when time
        # to move, if move is manual
        self.frameTask.move = False

    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def set_key(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

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
                if self.check_fixation and not self.fix_time:
                    #print 'no fixation, start over'
                    self.restart_task(None)
                    return task.cont
                # task.switch will manipulate the square and
                # update the interval to the next task.
                #print task.time
                #print 'task', task.switch[self.next]
                #print 'in frame loop', self.next
                #print 'old interval', task.interval
                task.switch[self.next]()
                #print task.file[self.next]
                print 'just did task', self.next
                #self.time_data_file.write('test' + '\n')
                self.time_data_file.write(str(time()) + ', ' + task.file[self.next] + '\n')
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
            self.time_data_file.write(str(time()) + ', start collecting eye data' + '\n')
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
            self.text3.setText('IScan: [' + str(round(eye_data[0], 3)) + ', ' + str(round(eye_data[1], 3)) + ']')

        self.eye_data_file.write(str(time()) + ', ' + str(eye_data).strip('()') + '\n')
        #print eye_data
        # check if in window for auto-calibrate - only update time if was none
        if self.check_fixation:
            #print 'check fixation', self.check_fixation
            # if already fixated, make sure hasn't left
            if self.fix_time:
                #print 'already fixated'
                if self.distance((eye_data), (self.square.getPos()[0], self.square.getPos()[2])) > self.tolerance:
                    # abort trial, start again with square in same position
                    print 'abort'
                    self.restart_task(None)
            else:
                #print 'waiting for fixation'
                if self.distance((eye_data), (self.square.getPos()[0], self.square.getPos()[2])) < self.tolerance:
                    print 'and fixated!'
                    #print 'square', self.square.getPos()[0], self.square.getPos()[2]
                    #print 'distance', self.distance((eye_data), (self.square.getPos()[0], self.square.getPos()[2]))
                    #print 'tolerance', self.tolerance
                    #print eye_data
                    self.restart_task(self.frameTask.time)
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

    def restart_task(self, fix_time):
        #print 'restarting'
        # if fix_time is none, then restarting because fixation was broken, or never fixated,
        # immediately turn off square and start over.
        if not fix_time:
            print 'restart, did not fixate'
            print 'no reward!'
            self.time_data_file.write(str(time()) + ', ' + 'no fixation, restart' + '\n')
            self.next = 4
            interval = self.all_intervals[5]
            # when new target shows up, this will change back to true
            self.check_fixation = False
        else:
            # timer starts out as interval for how long the subject has to fixate,
            # once fixated, need to reset the timer so fixation is held right amount of time.
            # So, keep interval as 1, but set the interval to fixation interval
            print 'restarting timer for holding fixation'
            self.next = 1
            interval = self.all_intervals[4]
        # new interval always starts with now
        self.frameTask.interval = self.frameTask.time + interval
        self.fix_time = fix_time
        #print self.fix_time

    def eye_data_to_pixel(self, eye_data):
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
            self.text2.setText('Offset:' + '[{0:03.2f}'.format(self.offset[0])
                               + ', ' + '{0:03.2f}]'.format(self.offset[1]))
            self.time_data_file.write(
                str(time()) + ', Change Offset, ' +
                str(self.offset[0]) + ', ' +
                str(self.offset[1]) + '\n')

    def change_tolerance(self, direction):
        self.tolerance += direction
        self.text4.setText('Tolerance: ' + str(self.tolerance) + ' pixels')
        for win in self.eye_window:
            win.detachNode()
        #self.eye_window.detachNode()
        self.show_window(self.square.getPos())

    def square_on(self, position=[]):
        # default is center
        if not position:
            position = [0, 0, 0]
        self.time_data_file.write(str(time()) + ', Square on, ' + str(position[0]) + ', '
                                  + str(position[2]) + '\n')\
        #print 'square', self.manual
        print 'square on, 0'
        #Pos(Point3(pos.getX(), self.depth, pos.getY()
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        #self.square.reparentTo(camera)
        # if on camera don't see in either window,
        # pixel2d only see in first window
        self.square.reparentTo( render )
        min, max = self.square.getTightBounds()
        size = max - min
        #print size[0], size[2]
        #print self.square.getPos()
        # next interval is fade on to off
        #self.interval = random.uniform(*FADE_INTERVAL)
        #print self.frameTask.new_interval
        #print 'square is now on'
        if not self.manual:
            self.check_fixation = True
        self.fixed = False

    def square_fade(self):
        print 'square fade, 1'
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
        print 'square off, 2'
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
        print 'reward, 3'
        #out = sys.stdout
        # only want to check this if on random?
        #if not self.manual:
            #print 'random?, check reward'
            #self.reward = self.check_fixation()
        #print 'reward', self.reward
        #if self.reward:
        for i in range(self.num_beeps):
            if self.reward_task:
                self.reward_task.pumpOut()
                sleep(.2)
                print 'beep'
        #    else:
        #        out.write("beep\n")

    def square_move(self, position=None):
        print 'square move, 4'
        #print 'square position', position
        if not position:
            #print 'trying to get a auto position'
            try:
                position = self.pos.next()
            except StopIteration:
                self.close()

        self.square.setPos(Point3(position))
        # show window for tolerance
        if not self.manual:
            self.show_window(position)
        #print 'square', position[0], position[2]
        # go directly to on
        self.square_on(position)

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
        #self.tolerance =
        #print 'square', square[0], square[2]
        eye_window = LineSegs()
        eye_window.setThickness(2.0)
        eye_window.setColor(1, 0, 0, 1)
        angleRadians = radians(360)
        for i in range(50):
            a = angleRadians * i /49
            y = self.tolerance * sin(a)
            x = self.tolerance * cos(a)
            eye_window.drawTo((x + square[0], 55, y + square[2]))

        #eye_window.moveTo(square[0] + self.tolerance, 55, square[2] + self.tolerance)
        #eye_window.drawTo(square[0] - self.tolerance, 55, square[2] + self.tolerance)
        #eye_window.drawTo(square[0] - self.tolerance, 55, square[2] - self.tolerance)
        #eye_window.drawTo(square[0] + self.tolerance, 55, square[2] - self.tolerance)
        #eye_window.drawTo(square[0] + self.tolerance, 55, square[2] + self.tolerance)
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

    def create_square(self):
        # initial position of Square
        pos = Point2(0, 0)
        #pos = Point2((base.win.getXSize()/2, -base.win.getYSize()/2))
        #print pos
        # setting up square object
        obj = self.base.loader.loadModel("models/plane")
        # don't turn on yet
        # obj.reparentTo(camera)
        # make depth greater than eye positions so eye positions are on top of squares,
        # intuitive, eh?
        self.depth = 55
        obj.setPos(Point3(pos.getX(), self.depth, pos.getY()))  # Set initial posistion
        #self.time_data_file.write(str(time()) + ', Square on, ' + str(pos.getX()) + ', '
        #                          + str(pos.getY()) + '\n')\
        #self.time_data_file.write(str(time()) + ', First Position, ' + str(pos.getX()) + ', ' + str(pos.getY()) + '\n')
        # need to scale to be correct visual angle
        #obj.setScale(1)
        # scale 17 is one visual angle in x and y direction
        obj.setScale(8.5)
        #obj.setTransparency(1)
        square = self.base.loader.loadTexture("textures/calibration_square.png")
        obj.setTexture(square, 1)
        # starting color, should be set by model, but let's make sure
        obj.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        return obj

    def set_resolution(self, res):
        wp = WindowProperties()
        #print res
        #wp.setSize(int(res[0]), int(res[1]))
        #wp.setFullscreen(True)
        wp.setSize(1600, 900)
        wp.setOrigin(-1600, 0)
        wp.setUndecorated(True)
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
            self.ignoreAll() # ignore everything, so nothing weird happens after deleting it.
        else:
            sys.exit()


if __name__ == "__main__":
    #print 'run as module'
    unittest = False
    #print 'main'
    # default is manual
    if len(sys.argv) == 1:
        W = World(1)
    else:
        W = World(sys.argv[1])
    run()

else:
    #print 'test'
    unittest = True

    # file was imported
    # only happens during testing...
