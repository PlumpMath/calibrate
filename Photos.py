from direct.gui.OnscreenImage import OnscreenImage
from direct.task import Task
from direct.showbase.MessengerGlobal import messenger
import os


class Photos():

    def __init__(self, config = None):
        # photo location
        self.root_dir = config['PHOTO_PATH']
        self.photo_names = []
        self.photo_set = []
        self.timer = config['PHOTO_TIMER']
        self.num_photos_in_set = config['NUM_PHOTOS_IN_SET']
        self.start_num = 0
        self.end_num = self.num_photos_in_set
        self.imageObject = None
        self.photo_gen = None

    def load_all_photos(self):
        print 'load all photos'
        for file_name in os.listdir(self.root_dir):
            #print file_name
            if file_name.endswith('.bmp'):
                self.photo_names.append(os.path.join(self.root_dir, file_name))
        self.load_photo_set()

    def load_photo_set(self):
        print 'load photo set'
        # need to make a check for last photo set
        self.photo_set = self.photo_names[self.start_num:self.end_num]
        # set the next set numbers
        self.start_num = self.end_num
        self.end_num += self.num_photos_in_set
        self.photo_gen = self.get_photo()

    def get_photo(self):
        for photo in self.photo_set:
            yield photo

    def show_photo(self):
        photo_path = None
        try:
            photo_path = self.photo_gen.next()
        except StopIteration:
            #print('stop iterating!')
            self.load_photo_set()
        print photo_path
        self.imageObject = OnscreenImage(photo_path, pos=(0, 0, 0))
        taskMgr.add(self.timer_task, 'timer_task')

    def timer_task(self, task):
        if task.time < self.timer:
            return task.cont
        messenger.send("space")
        return task.done

