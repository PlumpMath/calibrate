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
        # first square appears one second after start
        self.frameTask.next_on = 1
        # total time to go from on to move, if random
        self.frameTask.total_int = self.frameTask.on_int + self.frameTask.fade_int + self.frameTask.move_int
        # next move, if random
        self.frameTask.next_move = self.frameTask.next_on + self.frameTask.total_int
        # self.task.move gets changed to true after a move, false when square goes off
        # if not moving is not random, always true
        self.task.move = True

    def frame_loop(self, task):
        #print task.time
        dt = task.time - task.last
        task.last = task.time
        # have we moved?
        if task.move:
            if task.time > task.next_on + task.on_int + task.fade_int:
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







        #if self.random:
        #    if task.time > task.next_move:
        #        print 'move'
        #if task.time > task.next_fade:
        #    #print 'fade'
        #    #print task.time
        #    # next fade will be now plus the duration of this fade
        #    # plus the dark period
        #    task.next_fade = task.time + task.fade_int + task.dark_int
        #    #print 'next dark', task.next_dark
        #    #print 'next fade', task.next_fade
        #    self.fade()
        #elif task.time > task.next_dark:
        #    # next dark will be after next fade
        #    task.next_dark = task.next_fade + task.fade_int
        #    #print 'darken'
        #    #print task.time
        #    self.dark()
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #print self.square.getPos()
        #print 'loop'
        return Task.cont # task will continue indefinitely

    def move(self, position):
        self.square.setPos(position)

    def fade(self):
        #heading = self.square.getPos() + (0.05, 0, 0)
        #self.square.setPos(heading)
        #self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)

    def dark(self):
        self.square.clearColor()

W = World()
run()