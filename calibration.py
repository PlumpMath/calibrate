from __future__ import division
#import direct.showbase.ShowBase
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from panda3d.core import BitMask32, getModelPath
from panda3d.core import WindowProperties
from pandac.PandaModules import ClockObject
#from direct.task.Task import Task
from positions import Positions
import sys
import random
import os
import datetime
from pandaepl import ptime
# crazy gymnastics to not load the fake data unless necessary
try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    #print 'loaded'
except:
    pass

class World(DirectObject):
    def __init__(self, manual=None):
        #print 'init'
        # True for fake data, false for pydaq provides data
        # only need to change this for testing on windows
        self.test = False
        # Python assumes all input are string?
        #
        if manual == 'True':
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

        #window = direct.showbase.ShowBase.ShowBase()
        self.win = ShowBase()

        panda = self.win.loader.loadModel('panda')
        panda.reparentTo(self.win.render)

        # if window is offscreen (for testing), does not have WindowProperties,
        # should be better way to deal with this, but haven't found it yet.
        # if an actual resolution in config file, change to that resolution,
        # otherwise keep going...
        if config['WIN_RES'] != 'Test':
            props = WindowProperties()
            props.setForeground(True)
            #props.setCursorHidden(True)
            self.win.win.requestProperties(props)
            #print props

            # Need to get this better. keypress only works with one window.
            # plus looks ugly.
            # when getting eye data, probably should put in a list of tuples, separate class,
            # also write to file

            window2 = self.win.openWindow()
            window2.setClearColor((115 / 255, 115 / 255, 115 / 255, 1))
            #props.setCursorHidden(True)
            props.setForeground(False)
            props.setOrigin(600, 200) #any pixel on the screen you want
            window2.requestProperties(props)
            #print window2.getRequestedProperties()

            camera = self.win.camList[0]
            camera2 = self.win.camList[1]

            self.smiley = self.win.loader.loadModel('smiley')
            self.smiley.reparentTo(camera)
            self.smiley.setPos(-3, 55, 3)
            self.smiley.setColor(0, 0, 0, 0)
            self.smiley.setScale(0.1)
            camera.node().setCameraMask(BitMask32.bit(0))
            camera2.node().setCameraMask(BitMask32.bit(1))
            self.smiley.hide(BitMask32.bit(0))
            self.smiley.show(BitMask32.bit(1))

            self.root = self.win.render.attachNewNode("Root")
            if config['WIN_RES'] is not None:
                self.set_resolution(config['WIN_RES'])

        #print 'window loaded'
        self.eyes = []

        # open file for recording eye data
        data_dir = 'data/' + config['SUBJECT']
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.eye_file_name = data_dir + '/eye_cal_' +datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
        self.eye_data_file = open(self.eye_file_name, 'w')
        # open file for recording event times
        self.time_file_name = data_dir + '/time_cal_' +datetime.datetime.now().strftime("%y_%m_%d_%H_%M")
        self.time_data_file = open(self.time_file_name,'w')
        self.first = True

        # if you want to see the frame rate
        # window.setFrameRateMeter(True)

        self.win.setBackgroundColor(115 / 255, 115 / 255, 115 / 255)
        self.win.disableMouse()
        # initial position of Square
        pos = Point2(0, 0)
        # setting up square object
        obj = self.win.loader.loadModel("models/plane")
        # don't turn on yet
        # obj.reparentTo(camera)
        self.depth = 55
        obj.setPos(Point3(pos.getX(), self.depth, pos.getY()))  # Set initial posistion
        # need to scale to be correct visual angle
        obj.setScale(1)
        obj.setTransparency(1)
        square = self.win.loader.loadTexture("textures/calibration_square.png")
        obj.setTexture(square, 1)
        # starting color, should be set by model, but let's make sure
        obj.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        self.square = obj

        # if doing manual calibration, always get reward after square turns off,
        # if auto, require fixation. If doing manual, need to initiate Positions
        # differently than if random
        if self.manual:
            #print 'yes, still manual'
            self.reward = True
            self.pos = Positions(config)
        else:
            self.reward = False
            self.pos = Positions(config).get_position(self.depth)

        # Eye Data and reward
        self.eye_data = []
        if self.daq:
            self.gain = 0
            self.offset = 0
            self.eye_task = pydaq.EOGTask()
            self.eye_task.SetCallback(self.get_eye_data)
            self.eye_task.StartTask()
            self.reward_task = pydaq.GiveReward()
        else:
            self.fake_data = fake_eye_data.yield_eye_data()
            self.reward_task = None
        self.num_beeps = config['NUM_BEEPS']
        # first task is square_on
        self.next = 0

        # Keyboard stuff:
        self.accept("escape", self.close)  # escape
        # this really doesn't need to be a dictionary now,
        # but may want to use more keys eventually
        # keys will update the list, and loop will query it
        # to get new position
        self.keys = {"switch" : 0}
        # keyboard
        self.accept("1", self.setKey, ["switch", 1])
        self.accept("2", self.setKey, ["switch", 2])
        self.accept("3", self.setKey, ["switch", 3])
        self.accept("4", self.setKey, ["switch", 4])
        self.accept("5", self.setKey, ["switch", 5])
        self.accept("6", self.setKey, ["switch", 6])
        self.accept("7", self.setKey, ["switch", 7])
        self.accept("8", self.setKey, ["switch", 8])
        self.accept("9", self.setKey, ["switch", 9])

        # Our intervals
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # reward_interval - time from off to reward
        # move_interval - time from reward to move/on
        self.all_intervals = [config['ON_INTERVAL'], config['FADE_INTERVAL'], config['REWARD_INTERVAL'], config['MOVE_INTERVAL']]
        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        self.frameTask = self.win.taskMgr.add(self.frame_loop, "frame_loop")
        #print self.frameTask.time
        # this is the first interval - time from move to on
        # The task object is a good place to put variables that should stay
        # persistent for the task function from frame to frame
        # first interval will be the move interval (off to move/on - won't
        # actually move)
        self.frameTask.interval = random.uniform(*self.all_intervals[3])
        #print 'first interval', self.frameTask.interval

        # Main work horse: index with self.next to choose appropriate method
        self.frameTask.switch = {
            0: self.square_on,
            1: self.square_fade,
            2: self.square_off,
            3: self.give_reward,
            4: self.square_move}

        # task.move always starts as False, will be changed to true when time
        # to move, if move is manual
        self.frameTask.move = False

    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def setKey(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

    def get_eye_data(self, eye_data):
        # pydaq calls this function every time it calls back to get eye data,
        # if testing, called from frame_loop with fake data
        self.eye_data.append(eye_data)
        #VLQ.getInstance().writeLine("EyeData",
        #                            [((eye_data[0] * self.gain[0]) - self.offset[0]),
        #                             ((eye_data[1] * self.gain[1]) - self.offset[1])])
        #print eye_data
        #for x in [-3.0, 0.0, 3.0]:
        if self.first:
            self.time_data_file.write('start calibration' + '\n')
        if not unittest:
            eye = self.smiley.copyTo(self.root)
            #print eye_data[0], eye_data[1]
            eye.setPos(eye_data[0], 55, eye_data[1], )
            self.eyes += [eye]
        self.eye_data_file.write(str(eye_data).strip('()') + '\n')

    def frame_loop(self, task):
        #print 'in loop'
        #print task.time
        #dt = task.time - task.last
        #task.last = task.time
        # are we waiting for a manual move?
        #print task.move
        if not task.move:
            #print 'new loop', task.time
            #print 'frame', task.frame
            if task.time > task.interval:
                # task.switch will manipulate the square and
                # update the interval to the next task.
                #print task.time
                #print 'task', task.switch[task.now]
                #print 'in frame loop', self.next
                #print 'old interval', task.interval
                task.switch[self.next]()
                #print 'just did task', self.next
                #print 'should be updated interval', task.interval
                #print 'new interval', task.new_interval
                #print self.all_intervals
                #print self.next
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
                task.interval = random.uniform(*self.all_intervals[self.next])
                #print 'next interval', task.interval
                task.interval = task.time + task.interval
                #print 'next switch time', task.interval
                #print 'time now', task.time
                #print 'next', self.next
                self.next += 1
                #print 'update task number', self.next
        else:
            print "check for key"
            #print self.keys["switch"]
            # check to see if we should move the target
            #print 'switch', self.keys
            # it is possible to change the keypress before the last square turns off,
            # in this case we want to make sure we wait, before switching task.move to false
            if self.keys["switch"] and task.time > task.interval:
                if task.time > task.interval:
                    #print 'manual move'
                    #print 'switch', self.keys["switch"]
                    self.square_move(self.pos.get_key_position(self.depth, self.keys["switch"]))
                    self.keys["switch"] = 0  # remove the switch flag
                    # square is on, so nex thing to happen is it dims,
                    # this happens after on interval, 0
                    # make sure next interval is based on the time we actually moved the target (now!)
                    task.interval = task.time + random.uniform(*self.all_intervals[0])
                    # Next is dim, since it turned on when
                    self.next = 1

                    # don't come back here until ready to move again
                    task.move = False
                    #print 'back to regularly scheduled program'

        # if using fake data, plot
        if self.test:
            self.get_eye_data(self.fake_data.next())

        return task.cont  # Since every return is Task.cont, the task will
        #continue indefinitely

    def square_on(self):
        #print 'square', self.manual
        #print 'square on, 0'
        #print self.square.getPos()
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        self.square.reparentTo(camera)
        # next interval is fade on to off
        #self.interval = random.uniform(*FADE_INTERVAL)
        #print self.frameTask.new_interval
        #print 'square is now on'

    def square_fade(self):
        #print 'square fade, 1'
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        # next interval is fade off to on, at which time we move
        # if manual move is set, after off we just wait for move, so we
        # won't actually check this interval
        #self.interval = random.uniform(*MOVE_INTERVAL)

    def square_off(self):
        #print 'square off, 2'
        #print 'parent 1', self.square.getParent()
        self.square.clearColor()
        self.square.detachNode()
        #print 'parent 2', self.square.getParent()
        # next interval is on to fade on
        #self.interval = random.uniform(*ON_INTERVAL)
        #print 'next-on-interval', self.interval
        # when the square goes off, get rid of eye positions.
        for eye in self.eyes:
            eye.removeNode()
        self.eyes = []

    def give_reward(self):
        out = sys.stdout
        #print 'reward'
        if self.reward:
            for i in range(self.num_beeps):
                if self.reward_task:
                    self.reward_task.pumpOut()
                else:
                    out.write("beep\n")

    def square_move(self, position=None):
        #print 'square move, 3'
        #print 'position', position
        if not position:
            #print 'trying to get a auto position'
            self.square.setPos(Point3(self.pos.next()))
            #print self.square.getPos()
        else:
            self.square.setPos(Point3(position))
        # go directly to on
        self.square_on()

    #def set_manual(self, config, manual=None):
    #    # allow to override manual setting in config file
    #    # for non-random, non-manual:
    #    if manual is None:
    #        self.manual = config['MANUAL']
    #    else:
    #        self.manual = manual
    #    # self.manual is now true or false
    #    if not self.manual:
    #        self.pos = Positions(config).get_position(self.depth)
    #    else:
    #        self.pos = Positions(config)

    def set_resolution(self, res):
        wp = WindowProperties()
        wp.setSize(res)
        wp.setFullscreen(True)
        self.win.requestProperties(wp)

    def close(self):
        #print 'close'
        if self.daq:
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        self.eye_data_file.close()
        self.time_data_file.close()
        if unittest:
            self.ignoreAll() # ignore everything, so nothing weird happens after deleting it.
        else:
            sys.exit()

if __name__ == "__main__":
    #print 'run as module'
    unittest = False
    #print 'main'
    W = World(sys.argv[1])
    run()
else:
    #print 'test'
    unittest = True

    # file was imported
    # only happens during testing...
