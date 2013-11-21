from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from direct.task.Task import Task
import sys
import random

class World(DirectObject):
    def __init__(self):
        window = ShowBase()
        window.setBackgroundColor(115/255, 115/255, 115/255)
        window.setFrameRateMeter(True)
        pos = Point2(0, 0)
        obj = window.loader.loadModel("models/plane")
        obj.reparentTo(window.camera)
        depth = 55
        obj.setPos(Point3(pos.getX(), depth, pos.getY()))  # Set initial posistion
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
        self.square = obj
        window.disableMouse()
        self.accept("escape", sys.exit)  # escape
        self.random = True
        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        self.frameTask = window.taskMgr.add(self.frame_loop, "frame_loop")
        #The task object is a good place to put variables that should stay
        #persistant for the task function from frame to frame
        self.frameTask.last = 0         # (Task) time of the last frame
        # time from on to next fade
        self.frameTask.on_random_int = (2, 3)
        self.frameTask.on_int = random.uniform(*self.frameTask.on_random_int)
        # time from fade on to off
        self.frameTask.fade_random_int = (0.3, 0.7)
        self.frameTask.fade_int = random.uniform(*self.frameTask.fade_random_int)
        # should move_int be infinite for directed?
        self.frameTask.move_random_int = (2, 3)
        self.frameTask.move_int = random.uniform(*self.frameTask.move_random_int)  # time from off to move
        #self.frameTask.next_fade = 2  # wait 2 seconds to first fade
        # first square appears one second after start, this is the first interval
        self.frameTask.interval = 1
        # total time to go from on to move, if random
        self.frameTask.total_int = self.frameTask.on_int + self.frameTask.fade_int + self.frameTask.move_int
        # next move, if random
        self.frameTask.next_move = self.frameTask.next_on + self.frameTask.total_int
        # determines if we are moving randomly or manually
        self.frameTask.random = True
        # waiting for a manual move, True after square turns off in random is on
        self.frameTask.move = False
        self.frameTask.switch = {
            0: self.square_on,
            1: self.square_fade,
            2: self.square_off,
            3: self.square_move}

    def frame_loop(self, task):
        #print task.time
        dt = task.time - task.last
        task.last = task.time
        # are we waiting for a manual move?
        if not task.move:
            if task.time > task.interval:
                task.switch[task.now]
                # if we are turning off the square, next is moving,
                # which may be done manually
                if task.now == 2 and task.random:
                    task.move = True
                    task.now = 0
                elif task.now == 3:
                    task.now = 0
                else:
                    task.now += 1






                print 'off'
                if self.random:
                    task.move = False
                    task.next_on = task.time + random.uniform(*task.on_random_int)
                    task.fade_int = random.uniform(*task.fade_random_int)
                    task.move_int = random.uniform(*task.move_random_int)
                    task.total_int = task.on_int + task.fade_int + task.move_int
                    task.next_move = task.time + task.move_int
            elif task.time > task.next_on + task.on_int:
                print 'fade'
                task.on_int = random.uniform(*task.on_random_int)
            elif task.time > task.next_on:
                print 'on'
        else:
            if task.time > task.next_move:
                print 'move'


    # also change task.interval in these methods:
    def square_on(self, position):
        self.square.reparentTo(window.camera)

    def square_move(self, position):
        self.square.setPos(position)

    def square_fade(self):
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)

    def square_off(self):
        self.square.clearColor()
        self.square.removeNode()

W = World()
run()