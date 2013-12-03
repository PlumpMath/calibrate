from __future__ import division
import direct.showbase.ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from panda3d.core import BitMask32, WindowProperties
#from direct.task.Task import Task
from positions import Positions
import sys
import random

# Constants
class World(DirectObject):
    def __init__(self):
        # get configurations from config file
        config = {}
        execfile(config_file, config)
        window = direct.showbase.ShowBase.ShowBase()

        props = WindowProperties()
        props.setForeground(True)
        #props.setCursorHidden(True)
        window.win.requestProperties(props)


        print props
        panda = window.loader.loadModel('panda')
        panda.reparentTo(window.render)
        # Need to get this better. keypress only works with one window.
        # plus looks ugly.
        # when getting eye data, probably should put in a list of tuples, separate class,
        # also write to file

        window2 = window.openWindow()
        window2.setClearColor((115/255, 115/255, 115/255, 1))
        #props.setCursorHidden(True)
        props.setForeground(False)
        props.setOrigin(600,200) #any pixel on the screen you want
        window2.requestProperties(props)
        print window2.getRequestedProperties()



        camera = window.camList[0]
        camera2 = window.camList[1]

        smiley = window.loader.loadModel('smiley')
        smiley.reparentTo(camera)
        smiley.setPos(-3, 55, 3)
        camera.node().setCameraMask(BitMask32.bit(0))
        camera2.node().setCameraMask(BitMask32.bit(1))
        smiley.hide(BitMask32.bit(0))
        smiley.show(BitMask32.bit(1))
        #self.pos = Positions()
        window.setBackgroundColor(115/255, 115/255, 115/255)
        window.disableMouse()

        self.accept("escape", sys.exit)  # escape

        # if you want to see the frame rate
        # window.setFrameRateMeter(True)
        pos = Point2(0, 0)
        obj = window.loader.loadModel("models/plane")
        # don't turn on yet
        # obj.reparentTo(camera)
        self.depth = 55
        obj.setPos(Point3(pos.getX(), self.depth, pos.getY()))  # Set initial posistion
        obj.setScale(1)
        # Tells panda not to worry about the order this is drawn in (prevents effect
        # know as z-fighting)
        obj.setBin('unsorted', 0)
        # Tells panda not to check if something has already drawn in front of it
        # (Everything at same depth)
        obj.setDepthTest(False)
        obj.setTransparency(1)
        square = window.loader.loadTexture("textures/calibration_square.png")
        obj.setTexture(square, 1)
        # starting color, should be set by model, but let's make sure
        obj.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        self.square = obj

        # determines if we are moving manually or randomly,
        # eventually this should be an argument for running as script,
        # so we can switch modes.
        self.set_manual(config)

        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        self.frameTask = window.taskMgr.add(self.frame_loop, "frame_loop")
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # move_interval - time from off to move/on
        self.all_intervals = [config['ON_INTERVAL'], config['FADE_INTERVAL'], config['MOVE_INTERVAL']]
        # this is the first interval - time from move to on
        # The task object is a good place to put variables that should stay
        # persistent for the task function from frame to frame
        # first interval will be the move interval (off to move/on - won't
        # actually move)
        self.frameTask.interval = random.uniform(*self.all_intervals[2])

        # Main work horse: index with self.next to choose appropriate method
        self.frameTask.switch = {
            0: self.square_on,
            1: self.square_fade,
            2: self.square_off,
            3: self.square_move}

        # task.move always starts as False, will be changed to true when time
        # to move, if move is manual
        self.frameTask.move = False

        # first task is square_on
        self.next = 0

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

    #As described earlier, this simply sets a key in the self.keys dictionary to
    #the given value
    def setKey(self, key, val):
        self.keys[key] = val
        #print 'set key', self.keys[key]

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
                #print 'should be updated interval', task.interval
                #print 'new interval', task.new_interval
                #print self.all_intervals
                #print self.next
                # if we are turning off the square, next is moving.
                # check to see if we are moving manually
                # we will set self.next correctly for the next task
                # when we do the manual move
                if self.next == 2 and self.manual:
                    #print 'manual move'
                    task.move = True
                    return task.cont
                # if we are at self.next = 3, then the last task was moving,
                # and we need to reset our counter to zero. Since we do square_on
                # at the end of our move method, the incrementing to one at the
                # end of our loop will put as at self.next = 1, (square_fade), which
                # is correct. We need to do this before we change the interval, so
                # that we are using the correct corresponding interval
                if self.next == 3:
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
            #print "check for key"
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
                    # Next is dim,
                    self.next = 1

                    # don't come back here until ready to move again
                    task.move = False
                    #print 'back to regularly scheduled program'

        return task.cont  # Since every return is Task.cont, the task will
        #continue indefinitely

    def square_on(self):
        print 'square on, 0'
        #print self.square.getPos()
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        self.square.reparentTo(camera)
        # next interval is fade on to off
        #self.interval = random.uniform(*FADE_INTERVAL)
        #print self.frameTask.new_interval
        #print 'square is now on'

    def square_fade(self):
        print 'square fade, 1'
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        # next interval is fade off to on, at which time we move
        # if manual move is set, after off we just wait for move, so we
        # won't actually check this interval
        #self.interval = random.uniform(*MOVE_INTERVAL)

    def square_off(self):
        print 'square off, 2'
        #print 'parent 1', self.square.getParent()
        self.square.clearColor()
        self.square.detachNode()
        #print 'parent 2', self.square.getParent()
        # next interval is on to fade on
        #self.interval = random.uniform(*ON_INTERVAL)
        #print 'next-on-interval', self.interval

    def square_move(self, position=None):
        print 'square move, 3'
        #print 'position', position
        if not position:
            #print 'trying to get a auto position'
            self.square.setPos(Point3(self.pos.next()))
            #print self.square.getPos()
        else:
            self.square.setPos(Point3(position))
        # go directly to on
        self.square_on()

    def set_manual(self, config, manual=None):
        # allow to override manual setting in config file
        # for non-random, non-manual:
        if manual is None:
            self.manual = config['MANUAL']
        else:
            self.manual = manual
        # self.manual is now true or false
        if not self.manual:
            self.pos = Positions(config).get_position(self.depth)
        else:
            self.pos = Positions(config)

    def close(self):
        self.ignoreAll() # ignore everything, so nothing weird happens after deleting it.

if __name__ == "__main__":
    #print 'run as module'
    config_file = 'config.py'
    W = World()
    run()
else:
    # file was imported
    # only happens during testing...
    config_file = 'config_test.py'