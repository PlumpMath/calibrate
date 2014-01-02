from __future__ import division
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point2, Point3, NodePath, LineSegs
from panda3d.core import OrthographicLens, Camera
from positions import Positions
from panda3d.core import WindowProperties
from positions import visual_angle
import numpy as np
import sys


class World(DirectObject):
    def __init__(self):

        #ShowBase.__init__(self)
        self.base = ShowBase()
        #print self.base.win.getRejectedProperties()
        self.config = {}
        execfile('config_test.py', self.config)
        resolution = self.config['WIN_RES']
        if not resolution or resolution == 'Test':
            #print 'test'
            # assume testing, small window
            resolution = (800, 600)
        #print resolution
        wp = WindowProperties()
        wp.setSize(int(resolution[0]), int(resolution[1]))
        wp.setOrigin(0, 0)
        wp.setUndecorated(True)
        self.base.win.requestProperties(wp)
        # depth completely doesn't matter for this, since just 2d, and no layers
        #self.depth = 55
        self.depth = 0
        self.base.setBackgroundColor(115/255, 115/255, 115/255)
        # set up a 2d camera
        camera = self.base.camList[0]
        lens = OrthographicLens()
        #print 'xwin', self.base.win.getProperties().getXSize()

        lens.setFilmSize(int(resolution[0]),int(resolution[1]))
        lens.setNearFar(-100,100)
        camera.node().setLens(lens)
        # reparent it to pixel2d, so renders in pixel coordinates
        camera.reparentTo(render)
        #print 'xwin2', self.base.win.getXSize()
        #print self.base.win.getYSize()
        #print camera.ls()
        self.accept("escape", sys.exit)
        self.accept('space', self.next)
        self.accept('a', self.all)
        self.accept('d', self.degree_positions)
        self.accept('s', self.change_square_size)

        self.mode = 0
        self.pos = []
        #self.root = self.base.render.attachNewNode("Root")
        self.make_circle()


        #circle.reparentTo(render)

    def next(self):
        #print 'xwin', self.base.win.getProperties().getXSize()
        if self.mode == 0:
            self.pos = Positions(self.config).get_position(self.depth, 'small')
            self.mode = 1

        square = self.make_square()
        try:
            square.setPos(Point3(self.pos.next()))
            #print square.getPos()
        except StopIteration:
            print 'done'
        #square.setColor(175 / 255, 175 / 255, (i * 7) / 255, 1.0)
        #print square.getColor()

    def all(self):
        if self.mode == 0:
            circle_node = self.make_circle()
            pos = Positions(self.config).get_position(self.depth)
            self.mode = 1
        b = 0
        for i, j in enumerate(pos):
            #b += 0.04  # covers all of the values if using 25 points
            #b += 0.08
            b += 0.03
            #print b
            #print i
            #print j
            square = self.make_square()
            square.setPos(Point3(j))
            #print square.getPos()
            #print square.getTightBounds()
            min, max = square.getTightBounds()
            size = max - min
            #print size[0], size[2]

    def change_square_size(self):
        if self.mode == 0:
            circle_node = self.make_circle()
            pos = Positions(self.config).get_position(self.depth)
            self.mode = 1
        res = [1024, 768]
        # Screen size
        screen = [1337, 991]
        v_dist = 1219
        b = 0
        scale = 1
        for i, j in enumerate(pos):
            #b += 0.04  # covers all of the values if using 25 points
            #b += 0.08
            b += 0.03
            scale += 0.1
            #print b
            #print i
            #print j
            square = self.make_square(scale)
            square.setPos(Point3(j))
            #print square.getPos()
            #print square.getTightBounds()
            min, max = square.getTightBounds()
            size = max - min
            print size[0], size[2]
            deg_per_pixel = visual_angle(screen, res, v_dist)
            print deg_per_pixel
            print 'size in degrees, x', size[0] * deg_per_pixel[0]
            print 'size in degrees, y', size[2] * deg_per_pixel[1]

    def degree_positions(self):
        # set center, than 4 squares in cardinal directions at interval of 5 degree angles
        if self.mode == 0:
            self.pos = Positions(self.config).get_degree_positions(self.depth)
            self.mode = 1
            # get the center position
            square = self.make_square()
            square.setPos(Point3(self.pos.next()))
            #print 'first', square.getPos()
        else:
            try:
                for i in range(4):
                    square = self.make_square()
                    square.setPos(Point3(self.pos.next()))
                    print square.getPos()
            except StopIteration:
                print 'done'

    def make_square(self, scale = []):
        square = self.base.loader.loadModel("models/plane")
        square.reparentTo( render )
        #square.ls()
        #square.setScale(0.05)
        if scale:
            square.setScale(scale)
        else:
            square.setScale(8.5)
        square.setDepthTest(False)
        square.setTransparency(1)
        square.setTexture(self.base.loader.loadTexture("textures/calibration_square.png"), 1)
        # gray
        #square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        # yellow
        #square.setColor(175 / 255, 175 / 255, 130 / 255, 1.0)
        square.setColor(0.9, 0.9, 0.6, 1.0)
        #print square.getX()
        #print square.getY()
        min, max = square.getTightBounds()
        size = max - min
        #print size[0], size[2]
        return square

    def make_circle(self, angle_deg = 360):
        ls = LineSegs()
        angleRadians = np.deg2rad(angle_deg)
        # assume visual angle is approximately the same for x and y,
        # which probably is not true, maybe need to change
        #radius = 1 * Positions().visual_angle()[0]
        res = [1024, 768]
        # Screen size
        screen = [1337, 991]
        v_dist = 1219
        # number of visual angles want circle radius to be
        angle = 0.25
        # visual angle returns degrees per pixel, so invert since
        # we want pixel per degree
        deg_per_pixel = visual_angle(screen, res, v_dist)
        x_radius = angle * 1 / deg_per_pixel[0]
        y_radius = angle * 1 / deg_per_pixel[0]
        for i in range(50):
            a = angleRadians * i / 49
            y = y_radius * np.sin(a)
            #print y
            x = x_radius * np.cos(a)
            #print x
            ls.drawTo(x, self.depth, y)
        #node = ls.create()
        node = render.attachNewNode(ls.create())
        return NodePath(node)

if __name__ == "__main__":
    print 'auto-running'
    W = World()
    run()
else:
    print 'not auto-running'