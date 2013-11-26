from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3
from positions import Positions
import sys


class World(DirectObject):
    def __init__(self):
        window = ShowBase()
        self.config = {}
        execfile('config_test.py', self.config)
        self.depth = 55
        window.setBackgroundColor(115/255, 115/255, 115/255)
        pos = Positions().get_position(self.depth)

        for i in pos:
            square = window.loader.loadModel("models/plane")
            square.reparentTo(camera)
            square.setScale(1)
            square.setDepthTest(False)
            square.setTransparency(1)
            square.setTexture(window.loader.loadTexture("textures/calibration_square.png"), 1)
            square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
            square.setPos(Point3(i))
            #print square.getPos()
        print 'done'

if __name__ == "__main__":
    print 'auto-running'
    W = World()
    run()
else:
    print 'not auto-running'