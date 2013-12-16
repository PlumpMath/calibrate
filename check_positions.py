from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3, NodePath
from panda3d.core import OrthographicLens, Camera
from positions import Positions
import sys


class World(DirectObject):
    def __init__(self):
        #ShowBase.__init__(self)
        self.base = ShowBase()
        self.config = {}
        execfile('config_test.py', self.config)
        # depth completely doesn't matter, since just 2d
        #self.depth = 55
        self.depth = 0
        self.base.setBackgroundColor(115/255, 115/255, 115/255)
        # set up a 2d camera
        camera = self.base.camList[0]
        lens = OrthographicLens()

        lens.setFilmSize(self.base.win.getProperties().getXSize(), self.base.win.getProperties().getYSize())
        #lens.setFilmSize(800, 600)
        lens.setNearFar(-100,100)
        camera.node().setLens(lens)
        # reparent it to pixel2d, so renders in pixel coordinates
        camera.reparentTo( render )
        #print self.base.win.getXSize()
        #print self.base.win.getYSize()
        #print camera.ls()
        self.accept('space', self.next)
        self.accept('a', self.all)
        self.pos = Positions().get_position(self.depth)

        #square = self.window.loader.loadModel("smiley")
        #square.reparentTo( pixel2d )
        #square.ls()
        ##square.setScale(0.05)
        #square.setScale(20)
        #square.setDepthTest(False)
        #square.setTransparency(1)
        #square.setTexture(self.window.loader.loadTexture("textures/calibration_square.png"), 1)
        ## gray
        ##square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        ## yellow
        ##square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        #square.setColor(0.9, 0.9, 0.6, 1.0)

        #square.setColor(175 / 255, 175 / 255, (i * 7) / 255, 1.0)
        #print square.getColor()

        #square.setPos(Point3(self.pos.next()))
        #print square.getPos()
        #print 'done'

    def next(self):
        #square = self.window.loader.loadModel("smiley")
        square = self.base.loader.loadModel("models/plane")
        square.reparentTo( render )
        #square.ls()
        #square.setScale(0.05)
        square.setScale(20)
        square.setDepthTest(False)
        square.setTransparency(1)
        square.setTexture(self.base.loader.loadTexture("textures/calibration_square.png"), 1)
        # gray
        #square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        # yellow
        #square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        square.setColor(0.9, 0.9, 0.6, 1.0)
        try:
            square.setPos(Point3(self.pos.next()))
            print square.getPos()
        except StopIteration:
            print 'done'
        #square.setColor(175 / 255, 175 / 255, (i * 7) / 255, 1.0)
        #print square.getColor()

    def all(self):
        b = 0
        for i, j in enumerate(self.pos):
            #b += 0.04  # covers all of the values
            b += 0.03
            #print b
            #print i
            print j
            square = self.base.loader.loadModel("models/plane")
            #square = self.window.loader.loadModel("smiley")
            square.reparentTo( render )
            #square.ls()
            square.setScale(20)
            #square.setDepthTest(False)
            square.setTransparency(1)
            square.setTexture(self.base.loader.loadTexture("textures/calibration_square.png"), 1)
            # gray
            #square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
            # yellow
            #square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
            square.setColor(0.9, 0.9, 0.6, 1.0)

            #square.setColor(175 / 255, 175 / 255, (i * 7) / 255, 1.0)
            #print square.getColor()

            square.setPos(Point3(j))
            #print square.getPos()
            #print square.getTightBounds()
        min, max = square.getTightBounds()
        size = max - min
        print size[0], size[2]

if __name__ == "__main__":
    print 'auto-running'
    W = World()
    run()
else:
    print 'not auto-running'