from __future__ import division
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import LineSegs, BitMask32
import os
from time import time

#### Shit! How do I keep track of where I am in the directory after I quit
#### the application?


class Photos():

    def __init__(self, base, config=None, logging=None):
        # photo location
        self.base = base
        self.config = config
        self.logging = logging

        self.photo_names = []
        self.photo_set = []
        # this variable will change, and then be re-set with the configuration
        self.fixation_timer = config['PHOTO_TIMER']
        self.flag_timer = False  # starts out assuming fixated
        self.imageObject = None
        self.photo_gen = None
        # tells calibration routine when it should care about fixation for photos
        self.check_eye = False  # true means check fixation, false means stop checking
        self.photo_window = []  # where we will store the fixation window for photos
        self.time_stash = 0  # used to keep track of timing
        # this will change when finished with all sets
        self.cal_pts_per_photo = config['CAL_PTS_PER_PHOTO']
        total_cal_points = config['POINT_REPEAT'] * config['X_POINTS'] * config['Y_POINTS']
        num_photos_in_set = config['NUM_PHOTOS_IN_SET']
        num_poss_photos = total_cal_points // self.cal_pts_per_photo
        num_sets = num_poss_photos // num_photos_in_set
        #print num_sets
        # show each set twice, so just need half that many
        num_sets //= 2
        num_sets = 1
        #print num_sets
        try:
            last_index = config['LAST_PHOTO_INDEX']
        except KeyError:
            last_index = 0
        self.index_list = create_index_list(num_photos_in_set, num_sets, last_index)
        #print('index list', self.index_list)
        self.end_index = 0
        #photo_size = [1280, 800]
        # ratio of photo is approximately the same as the screen (3:4), which means
        # about same number of pixels in x and y to get same ratio. Not really intuitive.
        photo_size = [600, 600]
        #photo_size = [1000, 800]
        self.tolerance = tuple([x/2 for x in photo_size])
        #print('photo tolerance', self.tolerance)

    def load_all_photos(self):
        #print 'load all photos'
        for file_name in os.listdir(self.config['PHOTO_PATH']):
            #print file_name
            if file_name.endswith('.bmp'):
                self.photo_names.append(os.path.join(self.config['PHOTO_PATH'], file_name))
        if self.index_list[-1] > len(self.photo_names):
            raise Exception("Not enough Photos in this directory")
        test = self.load_photo_set()
        #print test

    def load_photo_set(self):
        #print 'load photo set'
        try:
            start_ind = self.index_list.pop(0)
            end_ind = self.index_list.pop(0)
            self.end_index = end_ind
        except IndexError:
            #print 'end of index!'
            return False
        self.photo_set = self.photo_names[start_ind:end_ind]
        #print self.photo_set
        self.photo_gen = self.get_photo()
        return True

    def get_photo(self):
        for photo in self.photo_set:
            yield photo

    def show_photo(self):
        #print 'show photo and tolerance'
        photo_path = None
        try:
            photo_path = self.photo_gen.next()
        except StopIteration:
            #print('stop iterating!')
            check_set = self.load_photo_set()
            if check_set:
                photo_path = self.photo_gen.next()
            else:
                self.cal_pts_per_photo = None
                #print 'out of photos, cleanup'
                return
        self.check_eye = True
        #print photo_path
        #print time()
        #print 'show window'
        self.show_window()
        #print 'show actual photo'
        self.imageObject = OnscreenImage(photo_path, pos=(0, 0, 0), scale=0.75)
        self.write_to_file('Photo On', photo_path)
        #print self.imageObject
        self.base.taskMgr.add(self.timer_task, 'photo_timer_task', uponDeath=self.set_break_timer)
        #print('started timer task', self.fixation_timer)

    def timer_task(self, task):
        #print('timer', self.fixation_timer)
        # if looks away, add that time to the timer
        # task.time is how long this task has been running
        new_time = task.time
        #print('task time beginning', new_time)
        # if not fixated, and still during fixation period, extend timer
        if not self.flag_timer:
            #print 'flagged'
            #print time()
            #print('new time', new_time)
            #print('stashed time', self.time_stash)
            old_time = self.time_stash
            dt = new_time - old_time  # get delta that passed with no fixation
            #print('time adjustment', dt)
            self.fixation_timer += dt  # add that to the timer
            #print('numframes', task.frame)
            #print('current timer', self.fixation_timer)
            #print('total time', task.time)
        self.time_stash = new_time  # set time for next check
        if task.time < self.fixation_timer:
            return task.cont
        self.time_stash = 0
        #print('timer was', self.fixation_timer)
        #print('task time was', task.time)
        # done fixating
        return task.done

    def set_break_timer(self, task):
        #print('remove photo, on break')
        self.check_eye = False
        # reset the timer for next time
        self.fixation_timer = self.config['PHOTO_TIMER']
        #print('new timer', self.fixation_timer)
        self.imageObject.destroy()
        self.write_to_file('Photo Off')
        for line in self.photo_window:
            line.detachNode()
        #print time()
        #print 'go on break'
        self.base.taskMgr.doMethodLater(self.config['PHOTO_BREAK_TIMER'], self.send_cleanup, 'photo_send_cleanup')
        #print 'set break'
        #print time()

    def check_fixation(self, eye_data):
        #print('eye', eye_data)
        #print('tolerance', self.tolerance)
        # tolerance is the x, y border that eye_data should
        # be contained in, both should be (x, y) tuple
        # photos are centered, so as long as the absolute value of the eye
        # is less than the absolute value of the tolerance, should be golden
        if abs(eye_data[0]) < abs(self.tolerance[0]) and abs(eye_data[1]) < abs(self.tolerance[1]):
            return True
        return False

    def show_window(self):
        # draw line around target representing how close the subject has to be looking to get reward
        #print('show window around square', square_pos)
        photo_window = LineSegs()
        photo_window.setThickness(2.0)
        photo_window.setColor(1, 0, 0, 1)
        photo_window.moveTo(self.tolerance[0], 55, self.tolerance[1])
        #print photo_window.getCurrentPosition()
        photo_window.drawTo(self.tolerance[0], 55, -self.tolerance[1])
        #print photo_window.getCurrentPosition()
        photo_window.drawTo(-self.tolerance[0] + 100, 55, -self.tolerance[1])
        #print photo_window.getCurrentPosition()
        photo_window.drawTo(-self.tolerance[0] + 100, 55, self.tolerance[1])
        #print photo_window.getCurrentPosition()
        photo_window.drawTo(self.tolerance[0], 55, self.tolerance[1])
        #print photo_window.getCurrentPosition()
        node = self.base.render.attachNewNode(photo_window.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.photo_window.append(node)

    def write_to_file(self, event, photo=None):
        self.logging.log_event(event)
        if photo:
            self.logging.log_event(photo)

    @staticmethod
    def send_cleanup(task):
        #print time()
        #print('cleanup, start next loop')
        messenger.send('cleanup')
        return task.done


def create_index_list(num_photos, num_sets, first_index=None):
    # because of indexing starting at zero and using range,
    # num_sets makes one set if num_sets is zero, which doesn't make
    # much sense from a user point of view, so subtract off one
    num_sets -= 1
    if not first_index:
        first_index = 0
    # last photo is first + num_photos
    last_index = first_index + num_photos
    index_list = [first_index, last_index] * 2
    #print('index_list', index_list)
    last_set = index_list
    for i in range(num_sets):
        next_set = [x + num_photos for x in last_set]
        index_list.extend(next_set)
        last_set = next_set
    return index_list



