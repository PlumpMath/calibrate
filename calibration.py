from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
#from direct.task.Task import Task
from positions import Positions
import sys
import random

# Constants
TEST = True
if TEST:
    SHORT = 0.2
# All intervals represent min and max for a uniform random distribution
ON_INTERVAL = (2, 3)  # Time on
FADE_INTERVAL = (0.3, 0.7) # Time faded
MOVE_INTERVAL = (2, 3) # Time from fading off until on in new place

class World(DirectObject):
    def __init__(self):
        window = ShowBase()
        self.pos = Positions()
        window.setBackgroundColor(115/255, 115/255, 115/255)
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
        window.disableMouse()
        self.accept("escape", sys.exit)  # escape

        # determines if we are moving manually or randomly
        self.manual = False

        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        if TEST:
            self.frameTask = window.taskMgr.add(self.simple_loop, "simple_loop")
            self.manual = False
        else:
            self.frameTask = window.taskMgr.add(self.frame_loop, "frame_loop")

        #The task object is a good place to put variables that should stay
        #persistant for the task function from frame to frame
        #self.frameTask.last = 0         # (Task) time of the last frame
        # time from on to next fade
        #self.on_int = random.uniform(*ON_INTERVAL)
        # time from fade on to off
        #self.fade_int = random.uniform(*FADE_INTERVAL)
        # time from off to move and on
        #self.move_int = random.uniform(*MOVE_INTERVAL)
        #self.frameTask.next_fade = 2  # wait 2 seconds to first fade
        # first square appears a random number from the move_int after start,
        # these variables need to be changed outside of the loop
        # this is the first interval
        self.interval = random.uniform(*MOVE_INTERVAL)
        # first task is on
        self.next = 0

        # total time to go from on to move, if random
        # self.frameTask.total_int = self.frameTask.on_int + self.frameTask.fade_int + self.frameTask.move_int
        # next move, if random
        #self.frameTask.next_move = self.frameTask.next_on + self.frameTask.total_int

        # waiting for a manual move, True after square turns off in random is on
        self.frameTask.move = False
        self.frameTask.switch = {
            0: self.square_on,
            1: self.square_fade,
            2: self.square_off,
            3: self.square_move}

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
        print 'set key', self.keys[key]

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
            if task.time > self.interval:
                # task.switch will manipulate the square and
                # update the interval to the next task.
                #print task.time
                #print 'task', task.switch[task.now]
                #print 'in frame loop', self.next
                #print 'old interval', task.interval
                task.switch[self.next]()
                #print 'should be updated interval', task.interval
                #print 'new interval', task.new_interval
                self.interval = task.time + self.interval
                #print 'time now', task.time
                #print 'next', self.next
                #print 'interval', self.interval
                # if we are turning off the square, next is moving.
                # Moving may be done manually, so go directly to next fade,
                # since the manual move will go to on automatically
                if self.next == 2 and self.manual:
                    #print 'manual move'
                    task.move = True
                elif self.next == 3:  # manual move never gets here,
                    # on is done automatically with move
                    self.next = 0

                self.next += 1
                #print 'update task number', self.next
        else:
            #print "check for key"
            #print self.keys["switch"]
            # check to see if we should move the target
            #print 'switch', self.keys
            if self.keys["switch"]:
                #print 'switch', self.keys["switch"]
                self.square_move(position = self.pos.get_position(self.depth, self.keys["switch"]))
                self.keys["switch"] = 0  # remove the switch flag
                self.next = 1
                task.move = False

        return task.cont  # Since every return is Task.cont, the task will
        #continue indefinitely

    def simple_loop(self, task):
        # just want to see where the squares are
        if task.time > self.interval:
            print self.next
            task.switch[self.next]()
            self.interval = task.time + SHORT
            # skip dimming and off
            if self.next == 0:
                self.next = 3
            elif self.next == 3:
                self.next = 0

        return task.cont

    def square_on(self):
        print 'square on'
        self.square.reparentTo(camera)
        # next interval is fade on to off
        self.interval = random.uniform(*FADE_INTERVAL)
        #print self.frameTask.new_interval

    def square_fade(self):
        print 'square fade'
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        # next interval is fade off to on, at which time we move
        # if manual move is set, after off we just wait for move, so we
        # won't actually check this interval
        self.interval = random.uniform(*MOVE_INTERVAL)

    def square_off(self):
        print 'square off'
        #print 'parent 1', self.square.getParent()
        self.square.clearColor()
        self.square.detachNode()
        #print 'parent 2', self.square.getParent()
        # next interval is on to fade on
        self.interval = random.uniform(*ON_INTERVAL)

    def square_move(self, position = None):
        print 'square move'
        if not position:
            self.square.setPos(Point3(self.pos.get_position(self.depth)))
        else:
            self.square.setPos(Point3(position))
        # go directly to on
        self.square_on()

    def close(self):
        self.ignoreAll() # ignore everything, so nothing weird happens after deleting it.

if __name__ == "__main__":
    print 'auto-running'
    W = World()
    run()
else:
    print 'not auto-running'