from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from Photos import Photos
import sys


class TestPhotos(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        # start Panda3d
        self.base = ShowBase()
        # get configurations from config file
        config_file = 'config.py'
        self.config = {}
        execfile(config_file, self.config)
        self.accept("cleanup", self.cleanup)
        self.accept("escape", self.close)
        self.photos = Photos(self.config)
        self.photos.load_all_photos()
        self.start_loop()

    def start_loop(self):
        self.photos.flag_timer = True
        self.photos.show_photo()

    def cleanup(self):
        print 'cleanup'
        if self.photos.cal_pts_per_photo:
            self.start_loop()
        else:
            print 'done?'

    def close(self):
        print 'time to close'
        self.photos.cal_pts_per_photo = None
        self.photos.imageObject.destroy()
        self.base.taskMgr.remove('timer_task')
        sys.exit()

if __name__ == "__main__":
    TP = TestPhotos()
    TP.base.run()