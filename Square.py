from __future__ import division
from panda3d.core import Point3
from positions import Positions
from direct.showbase.MessengerGlobal import messenger


class Square():

    def __init__(self, config, key_map, base):
        self.key_map = key_map
        self.base = base
        # self.depth needs to be more than zero for stuff to show up,
        # otherwise arbitrary. This is used for positioning squares (Z)
        self.depth = 55
        self.pos = None
        self.manual = None
        # scale 17 is one visual angle, linear so just multiply by 17
        self.square = self.create_square(config['SQUARE_SCALE']*17)
        # print 'scale', config['SQUARE_SCALE']*17

    def create_square(self, scale):
        # setting up square object
        obj = self.base.loader.loadModel("models/plane")
        # don't turn on yet
        # make depth greater than eye positions so eye positions are on top of squares
        # initial position of Square
        obj.setPos(Point3(0, self.depth, 0))  # Set initial position
        # need to scale to be correct visual angle
        # obj.setScale(1)
        obj.setScale(scale)
        # obj.setTransparency(1)
        square = self.base.loader.loadTexture("textures/calibration_square.png")
        obj.setTexture(square, 1)
        # starting color, should be set by model, but let's make sure
        obj.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        return obj

    def setup_positions(self, config, manual):
        # If doing manual, need to initiate Positions differently than if random,
        # so key presses work properly
        self.manual = manual
        if self.manual:
            del self.pos
            # print 'manual positions'
            self.pos = Positions(config)
        else:
            del self.pos
            # print 'auto positions'
            self.pos = Positions(config).get_position(self.depth, True)

    # Square methods
    def turn_on(self):
        # print 'square on'
        # make sure in correct color
        self.square.setColor(150 / 255, 150 / 255, 150 / 255, 1.0)
        # and render
        self.square.reparentTo(self.base.render)
        # make sure in correct color
        # print self.square.getColor()
        # min, max = self.square.getTightBounds()
        # size = max - min
        # print size[0], size[2]
        # print self.square.getPos()
        # print 'square is now on'
        # print 'actually turned on square'
        # print('time', time())

    def fade(self):
        # print 'square fade'
        # heading = self.square.getPos() + (0.05, 0, 0)
        # self.square.setPos(heading)
        # self.square.setColor(175/255, 175/255, 130/255, 1.0)
        self.square.setColor(0.9, 0.9, 0.6, 1.0)

    def turn_off(self):
        # print 'square off'
        # print 'parent 1', self.square.getParent()
        self.square.clearColor()
        self.square.detachNode()
        # print 'actually turned off square'
        # print('time', time())

    def move_for_manual_position(self):
        # used for manual move
        # if a key was pressed, use that for next position
        if self.key_map["switch"]:
            # print 'manual move'
            # print('switch', self.key_map["switch"])
            self.move(self.pos.get_key_position(self.depth, self.key_map["switch"]))
            self.key_map["switch"] = 0  # remove the switch flag
        else:
            # default is the center, which is key 5
            self.move(self.pos.get_key_position(self.depth, 5))

    def move(self, position=None):
        # print 'square move'
        # print 'square position', position
        if not position:
            # print 'trying to get a auto position'
            try:
                position = self.pos.next()
                # print position
            except StopIteration:
                # print('stop iterating!')
                messenger.send("s")
                # Switch to manual and wait
                # need to set a position
                position = (0, self.depth, 0)
                # self.close()
        # print position
        self.square.setPos(Point3(position))
        # print 'square', position[0], position[2]
        # print 'actually moved square'
