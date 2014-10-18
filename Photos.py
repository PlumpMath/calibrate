from __future__ import division
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger
import os
#from time import time

#### Shit! How do I keep track of where I am in the directory after I quit
#### the application?


class Photos():

    def __init__(self, config=None):
        # photo location
        self.config = config
        self.root_dir = config['PHOTO_PATH']
        self.photo_names = []
        self.photo_set = []
        self.timer = config['PHOTO_TIMER']
        self.break_time = config['PHOTO_BREAK_TIMER'] + self.timer  # accumulate together
        self.flag_timer = False  # starts out assuming fixated
        self.imageObject = None
        self.photo_gen = None
        self.check_eye = False
        self.photo_center = (0, 0)
        self.time_stash = 0  # used to keep track of timing
        self.cal_pts_per_photo = config['CAL_PTS_PER_PHOTO']
        total_cal_points = config['POINT_REPEAT'] * config['X_POINTS'] * config['Y_POINTS']
        num_photos_in_set = config['NUM_PHOTOS_IN_SET']
        num_poss_photos = total_cal_points // self.cal_pts_per_photo
        num_sets = num_poss_photos // num_photos_in_set
        print num_sets
        # show each set twice, so just need half that many
        num_sets //= 2
        print num_sets
        try:
            last_index = config['LAST_PHOTO_INDEX']
        except KeyError:
            last_index = 0
        self.index_list = create_index_list(num_photos_in_set, num_sets, last_index)
        self.current_set = 0
        #photo_size = [800, 600]
        photo_size = [1000, 800]
        self.tolerance = tuple([x/2 for x in photo_size])

    def load_all_photos(self):
        print 'load all photos'
        for file_name in os.listdir(self.root_dir):
            #print file_name
            if file_name.endswith('.bmp'):
                self.photo_names.append(os.path.join(self.root_dir, file_name))
        if self.index_list[-1] > len(self.photo_names):
            raise Exception("Not enough Photos in this directory")
        self.load_photo_set()

    def load_photo_set(self):
        print 'load photo set'
        try:
            start_ind = self.index_list.pop(0)
            end_ind = self.index_list.pop(0)
        except IndexError:
            return False
        self.photo_set = self.photo_names[start_ind:end_ind]
        self.photo_gen = self.get_photo()
        return True

    def get_photo(self):
        for photo in self.photo_set:
            yield photo

    def show_photo(self):
        print 'show photo'
        photo_path = None
        try:
            photo_path = self.photo_gen.next()
        except StopIteration:
            #print('stop iterating!')
            check_set = self.load_photo_set()
            if check_set:
                photo_path = self.photo_gen.next()
            else:
                self.total_cal_points = None
                messenger.send('cleanup')
        print photo_path
        self.imageObject = OnscreenImage(photo_path, pos=(0, 0, 0))
        self.check_eye = True
        taskMgr.add(self.timer_task, 'timer_task', uponDeath=self.cleanup)

    def timer_task(self, task):
        #print 'timer task'
        # if looks away, add that time to the timer
        new_time = task.time
        if not self.flag_timer:
            #print time()
            old_time = self.time_stash
            dt = new_time - old_time
            self.timer += dt
            #print('numframes', task.frame)
            #print('current timer', self.timer)
            #print('total time', task.time)
        self.time_stash = new_time
        if task.time < self.timer:
            return task.cont
        #print('remove photo')
        self.check_eye = False
        self.imageObject.destroy()
        # now go on break, unfortunately we will continue to
        # call destroy, since I can't figure out a way to
        # test if the image is still there
        if task.time < self.break_time:
            return task.cont
        # return to regularly scheduled program
        # reset the timer
        self.timer = self.config['PHOTO_TIMER']
        return task.done

    @staticmethod
    def cleanup(task):
        print('cleanup, start next loop')
        messenger.send('cleanup')


def create_index_list(num_photos, num_sets, first_index=None):
    # because of indexing starting at zero and using range,
    # num_sets makes one set if num_sets is zero, which doesn't make
    # much sense from a user point of view, so subtract off one
    num_sets -= 1
    if not first_index:
        first_index = 0
    index_list = [first_index, num_photos] * 2
    last_set = index_list
    for i in range(num_sets):
        next_set = [x + num_photos for x in last_set]
        index_list.extend(next_set)
        last_set = next_set
    return index_list