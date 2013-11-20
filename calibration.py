from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3


import sys

class World(DirectObject):
    def __init__(self):
        window = ShowBase()
        base.setBackgroundColor(115/255, 115/255, 115/255)
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
        base.disableMouse()
        self.accept("escape-q", sys.exit)  # escape

        #Now we create the task. taskMgr is the task manager that actually calls
        #The function each frame. The add method creates a new task. The first
        #argument is the function to be called, and the second argument is the name
        #for the task. It returns a task object, that is passed to the function
        #each frame
        self.frameTask = window.taskMgr.add(self.frameLoop, "frameLoop")
        #The task object is a good place to put variables that should stay
        #persistant for the task function from frame to frame
        self.frameTask.last = 0         #Task time of the last frame

    def frameLoop(self, task):
        heading = self.square.getPos()
        self.square.setPos(heading + 0.1)
        print 'loop'


W = World()
run()