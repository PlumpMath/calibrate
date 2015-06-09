from __future__ import division
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import LineSegs, BitMask32
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.FunctionInterval import Func, Wait
import os
import random


class Photos():

    def __init__(self, base, config=None, logging=None, deg_per_pixel=None):
        # photo location
        self.base = base
        self.config = config
        self.logging = logging
        self.x_node = None
        self.photo_path = None
        self.photo_names = []
        self.photo_set = []
        # this variable will change, and then be re-set with the configuration
        self.fixation_timer = config['PHOTO_TIMER']
        self.photo_timer_on = False  # starts out assuming fixated
        self.imageObject = None
        self.photo_gen = None
        # tells calibration routine when it should care about fixation for photos
        self.photo_window = []  # where we will store the fixation window for photos
        self.photo_fix_time = 0  # used to keep track of timing
        self.start_plot_eye_task = None
        self.cross_sequence = None
        self.photo_sequence = None
        self.cross_hair = False
        total_cal_points = config['POINT_REPEAT'] * config['X_POINTS'] * config['Y_POINTS']
        num_photos_in_set = config['NUM_PHOTOS_IN_SET']
        num_poss_photos = total_cal_points // config['CAL_PTS_PER_PHOTO']
        num_sets = num_poss_photos // num_photos_in_set
        # print num_sets
        # show each set twice, so just need half that many
        num_sets //= 2
        num_sets = 1
        # print num_sets
        try:
            last_index = config['LAST_PHOTO_INDEX']
        except KeyError:
            last_index = 0
        self.index_list = create_index_list(num_photos_in_set, num_sets, last_index)
        # print('index list', self.index_list)
        self.end_index = 0
        # photo_size = [1280, 800]
        # ratio of photo is approximately the same as the screen (3:4), which means
        # about same number of pixels in x and y to get same ratio. Not really intuitive.
        photo_size = [600, 600]
        # photo_size = [1000, 800]
        self.tolerance = tuple([x/2 for x in photo_size])
        self.draw_cross(deg_per_pixel)
        self.cross_hair_int = self.config.get('CROSS_HAIR_FIX', (0, 0))
        # print('photo tolerance', self.tolerance)
        self.loop_count = 0
        self.task_timer = 0

    def load_all_photos(self):
        # print 'load all photos'
        for file_name in os.listdir(self.config['PHOTO_PATH']):
            # print file_name
            if file_name.endswith('.bmp'):
                self.photo_names.append(os.path.join(self.config['PHOTO_PATH'], file_name))
        if self.index_list[-1] > len(self.photo_names):
            raise Exception("Not enough Photos in this directory")
        self.load_photo_set()
        # print test

    def load_photo_set(self):
        # print 'load photo set'
        try:
            start_ind = self.index_list.pop(0)
            end_ind = self.index_list.pop(0)
            self.end_index = end_ind
        except IndexError:
            # print 'end of index!'
            return False
        # want photos presented in different order second time,
        # so shuffle list.
        # print 'photos', self.photo_names[start_ind:end_ind]
        self.photo_set = self.photo_names[start_ind:end_ind]
        random.shuffle(self.photo_set)
        # print self.photo_set
        self.photo_gen = self.get_photo()
        return True

    def get_photo(self):
        for photo in self.photo_set:
            yield photo

    def get_next_photo(self):
        # print 'show photo and tolerance'
        self.photo_path = None
        try:
            self.photo_path = self.photo_gen.next()
        except StopIteration:
            # print('stop iterating!')
            check_set = self.load_photo_set()
            if check_set:
                self.photo_path = self.photo_gen.next()
            else:
                # print 'out of photos, cleanup'
                return False
        return True

    def check_trial(self, good_trial, start_plot_eye_task):
        if good_trial:
            self.loop_count += 1
        if self.loop_count == self.config['CAL_PTS_PER_PHOTO']:
            self.loop_count = 0
            # check to see if we are out of photos
            new_photo = self.get_next_photo()
        else:
            # not time for photos, return
            return False
        if not new_photo:
            # if no more photos, return
            return False
        else:
            self.start_plot_eye_task = start_plot_eye_task
            # still here? start the photo loop!
            self.start_photo_loop()
            return True

    def start_photo_loop(self):
        self.setup_photo_sequences()
        self.cross_hair = True
        self.cross_sequence.start()

    def setup_photo_sequences(self):
        # start with cross hair, treat like fixation point, so first wait for fixation
        plot_eye = Func(self.start_plot_eye_task, check_eye=False)
        watch_eye = Func(self.start_plot_eye_task, check_eye=True)
        watch_eye_timer = Func(self.start_plot_eye_task, check_eye=True, timer=True)
        cross_on = Func(self.show_cross_hair)
        write_to_file_cross_on = Func(self.write_to_file, 'Cross on')
        write_to_file_fix = Func(self.write_to_file, 'Fixated')
        cross_off = Func(self.clear_cross_hair)
        write_to_file_cross_off = Func(self.write_to_file, 'Cross off')
        cross_interval = random.uniform(*self.cross_hair_int)
        photo_on = Func(self.show_photo)
        write_to_file_photo_on = Func(self.write_to_file, 'Photo on')
        set_photo_timer = Func(self.set_photo_timer)

        self.cross_sequence = Parallel(cross_on, write_to_file_cross_on, watch_eye_timer)

        self.photo_sequence = Sequence(
            Parallel(write_to_file_fix, watch_eye),
            Wait(cross_interval),
            Parallel(cross_off, write_to_file_cross_off, plot_eye),
            Parallel(photo_on, write_to_file_photo_on, set_photo_timer))

    def start_fixation_period(self):
        print 'We have fixation, in subroutine'
        # start next sequence. Can still be aborted, if lose fixation
        # during first interval
        if self.cross_hair:
            print 'on the cross hair'
            self.photo_sequence.start()
        else:
            print 'on the photo'
            self.photo_timer_on = True

    def no_fixation(self, task):
        print 'no fixation or broken, restart cross'
        self.stop_plot_eye_task()
        self.restart_cross_bad_fixation()

    def broke_fixation(self):
        if self.cross_hair:
            # stop checking the eye
            self.stop_plot_eye_task()
            # stop sequence
            self.photo_sequence.pause()
            self.restart_cross_bad_fixation()
        else:
            self.photo_timer_on = False

    def restart_cross_bad_fixation(self):
        self.clear_cross_hair()
        self.write_to_file('Bad Fixation')
        self.base.taskMgr.doMethodLater(self.config['BREAK_INTERVAL'], self.start_photo_loop, 'start_over', extraArgs=[])

    def get_fixation_target(self):
        # for photos, have to do checking of target in Photos
        # timer irrelevant.
        target = None
        on_interval = None
        if self.cross_hair:
            target = (0.0, 0.0)  # cross fixation always in center
            on_interval = random.uniform(*self.config['ON_INTERVAL'])
        return target, on_interval

    def show_cross_hair(self):
        print 'show cross hair'
        self.x_node.show()

    def clear_cross_hair(self):
        print 'clear cross hair'
        self.cross_hair = False
        self.x_node.hide()

    def stop_plot_eye_task(self):
        self.base.taskMgr.remove('plot_eye')

    def show_photo(self):
        self.photo_timer_on = True
        # print self.photo_path
        # print time()
        # print 'show window'
        self.show_window()
        # print 'show actual photo'
        self.imageObject = OnscreenImage(self.photo_path, pos=(0, 0, 0), scale=0.75)
        # print self.imageObject

    def set_photo_timer(self):
        self.base.taskMgr.add(self.timer_task, 'photo_timer_task', uponDeath=self.set_break_timer)
        # print('started timer task', self.fixation_timer)

    def timer_task(self, task):
        # this task collects time. We will only collect time while subject
        # is fixating. After we collect enough viewing time, exit task
        dt = task.time - self.task_timer
        self.task_timer = task.time
        if self.photo_timer_on:
            self.photo_fix_time += dt
        if self.photo_fix_time >= self.fixation_timer:
            return task.done
        else:
            return task.cont

    def old_timer_task(self, task):
        # print('timer', self.fixation_timer)
        # if looks away, add that time to the timer
        # this is because we are 
        # task.time is how long this task has been running
        new_time = task.time
        # print('task time beginning', new_time)
        # if not fixated, and still during fixation period, extend timer
        #
        if not self.photo_timer_on:
            # print 'flagged'
            # print time()
            # print('new time', new_time)
            # print('stashed time', self.time_stash)
            old_time = self.time_stash
            dt = new_time - old_time  # get delta that passed with no fixation
            # print('time adjustment', dt)
            self.fixation_timer += dt  # add that to the timer
            # print('numframes', task.frame)
            # print('current timer', self.fixation_timer)
            # print('total time', task.time)
        self.time_stash = new_time  # set time for next check
        if task.time < self.fixation_timer:
            return task.cont
        self.time_stash = 0
        # print('timer was', self.fixation_timer)
        # print('task time was', task.time)
        # done fixating
        return task.done

    def set_break_timer(self, task):
        # print('remove photo, on break')
        # reset the timer for next time
        self.fixation_timer = self.config['PHOTO_TIMER']
        # print('new timer', self.fixation_timer)
        self.imageObject.destroy()
        self.write_to_file('Photo Off')
        for line in self.photo_window:
            line.detachNode()
        # print time()
        # print 'go on break after photo'
        self.base.taskMgr.doMethodLater(self.config['PHOTO_BREAK_TIMER'], self.send_cleanup, 'photo_send_cleanup')
        # print 'set break'
        # print time()
        return task.done

    def check_fixation(self, eye_data):
        print 'check photo fixation'
        # print('eye', eye_data)
        # print('tolerance', self.tolerance)
        # tolerance is the x, y border that eye_data should
        # be contained in, both should be (x, y) tuple
        # photos are centered, so as long as the absolute value of the eye
        # is less than the absolute value of the tolerance, should be golden
        if abs(eye_data[0]) < abs(self.tolerance[0]) and abs(eye_data[1]) < abs(self.tolerance[1]):
            return True
        return False

    def show_window(self):
        # draw line around target representing how close the subject has to be looking to get reward
        # print('show window around square', square_pos)
        photo_window = LineSegs()
        photo_window.setThickness(2.0)
        photo_window.setColor(1, 0, 0, 1)
        photo_window.moveTo(self.tolerance[0], 55, self.tolerance[1])
        # print photo_window.getCurrentPosition()
        photo_window.drawTo(self.tolerance[0], 55, -self.tolerance[1] - 100)
        # print photo_window.getCurrentPosition()
        photo_window.drawTo(-self.tolerance[0], 55, -self.tolerance[1] - 100)
        # print photo_window.getCurrentPosition()
        photo_window.drawTo(-self.tolerance[0], 55, self.tolerance[1])
        # print photo_window.getCurrentPosition()
        photo_window.drawTo(self.tolerance[0], 55, self.tolerance[1])
        # print photo_window.getCurrentPosition()
        node = self.base.render.attachNewNode(photo_window.create(True))
        node.show(BitMask32.bit(0))
        node.hide(BitMask32.bit(1))
        self.photo_window.append(node)

    def draw_cross(self, deg_per_pixel):
        cross = LineSegs()
        cross.setThickness(2.0)
        # cross hair is 1/2 degree visual angle,
        # so go 1/4 on each side
        dist_from_center = 0.25 / deg_per_pixel
        cross.move_to(0 + dist_from_center, 55, 0)
        cross.draw_to(0 - dist_from_center, 55, 0)
        cross.move_to(0, 55, 0 - dist_from_center)
        cross.draw_to(0, 55, 0 + dist_from_center)
        self.x_node = self.base.render.attachNewNode(cross.create(True))
        self.x_node.hide()

    def write_to_file(self, event, photo=None):
        print 'write to file', event
        self.logging.log_event(event)
        if photo:
            self.logging.log_event(photo)

    def close(self):
        self.base.taskMgr.removeTasksMatching('photo_*')
        with open(self.config['file_name'], 'a') as config_file:
            config_file.write('\nLAST_PHOTO_INDEX = ' + str(self.end_index))

    @staticmethod
    def send_cleanup(task):
        # print time()
        print('after photo cleanup, start next loop')
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
    # print('index_list', index_list)
    last_set = index_list
    for i in range(num_sets):
        next_set = [x + num_photos for x in last_set]
        index_list.extend(next_set)
        last_set = next_set
    return index_list

