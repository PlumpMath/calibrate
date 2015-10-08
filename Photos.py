from __future__ import division
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import LineSegs, BitMask32
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.FunctionInterval import Func, Wait
import datetime
import os
import random


class Photos(object):

    def __init__(self, config, base, logging, deg_per_pixel=None):
        # photo location
        self.base = base
        self.config = config
        self.config.setdefault('RANDOM_PHOTOS', True)
        self.logging = logging
        self.x_node = None
        self.photo_path = None
        self.photo_names = []
        self.photo_set = []
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
        self.sets_shown = 0
        num_photos_in_set = self.config['NUM_PHOTOS_IN_SET']
        self.config.setdefault('NUM_PHOTO_SETS', 1)
        # was originally going to determine automatically how many sets we could show,
        # but now we always determine how many to show based on fitting in one calibration
        # routine
        # total_cal_points = self.config['POINT_REPEAT'] * self.config['X_POINTS'] * self.config['Y_POINTS']
        # num_poss_photos = total_cal_points // self.config['CAL_PTS_PER_PHOTO']
        # num_sets = num_poss_photos // num_photos_in_set
        # show each set twice, so just need half that many
        twice = self.config.setdefault('SHOW_PHOTOS_TWICE', False)
        # only show one set per calibration routine
        # last_photo_index is the index after the last photo that was
        # shown last time calibration was run, so first one to show now
        first_index = self.config.setdefault('LAST_PHOTO_INDEX', 0)
        self.index_list = create_index_list(num_photos_in_set, first_index, twice)
        # print('index list', self.index_list)
        # set default end
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
        self.verify_timer = None

    def load_all_photos(self):
        # this should only happen once!
        # print 'load all photos, num cal points'
        # print self.config['CAL_PTS_PER_PHOTO']
        for file_name in os.listdir(self.config['PHOTO_PATH']):
            # print file_name
            if file_name.endswith('.bmp'):
                self.photo_names.append(os.path.join(self.config['PHOTO_PATH'], file_name))
        print 'end of index', self.index_list[-1]
        self.check_photo_end()
        self.load_photo_set()
        # print test

    def check_photo_end(self):
        first_index = self.config['LAST_PHOTO_INDEX']
        num_photos_in_set = self.config['NUM_PHOTOS_IN_SET']
        num_sets = self.config['NUM_PHOTO_SETS']
        last_index = first_index + (num_photos_in_set * num_sets)
        # print 'last index', last_index
        # print 'photos', len(self.photo_names)
        if last_index > len(self.photo_names):
            raise Exception("Not enough Photos in this directory")

    def load_photo_set(self):
        print 'load photo set'
        try:
            start_ind = self.index_list.pop(0)
            end_ind = self.index_list.pop(0)
            self.end_index = end_ind
        except IndexError:
            # print 'end of index!'
            return False
        # check to see if photos should be presented in
        # random order
        print start_ind
        print end_ind
        print 'photos', self.photo_names[start_ind:end_ind]
        self.photo_set = self.photo_names[start_ind:end_ind]
        if self.config['RANDOM_PHOTOS']:
            random.shuffle(self.photo_set)
        # print self.photo_set
        self.photo_gen = self.get_photo()
        return True

    def get_photo(self):
        for photo in self.photo_set:
            print photo
            yield photo

    def get_next_photo(self):
        # print 'show photo and tolerance'
        self.photo_path = None
        try:
            self.photo_path = self.photo_gen.next()
        except StopIteration:
            print('stop iterating!')
            # this is used for automatic presentation of second set.
            check_set = self.load_photo_set()
            if not check_set:
                print "done with repeats, check for next set"
                # if not doing another of same set, are we doing another set?
                self.sets_shown += 1
                check_set = self.advance_photo_index()
            if check_set:
                print 'show next set'
                self.load_photo_set()
                self.photo_path = self.photo_gen.next()
            else:
                print 'out of photos, cleanup', self.sets_shown
                return False
        return True

    def check_trial(self, good_trial, start_plot_eye_task):
        # print 'check trial'
        # print self.loop_count
        # print self.config['CAL_PTS_PER_PHOTO']
        if good_trial:
            self.loop_count += 1
            # print 'advance loop count', self.loop_count
        if self.loop_count == self.config['CAL_PTS_PER_PHOTO']:
            # print 'right amount of good trials, time to check photos'
            self.loop_count = 0
            # check to see if we are out of photos
            new_photo = self.get_next_photo()
            # print 'stop showing photos?', new_photo
        else:
            # not time for photos, return
            # print 'show a fixation square'
            return False
        if not new_photo:
            # if no more photos, return
            return False
        else:
            # print 'okay, actually show a photo'
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
        watch_eye = Func(self.start_plot_eye_task, check_eye=True)
        watch_eye_timer = Func(self.start_plot_eye_task, check_eye=True, timer=True)
        cross_on = Func(self.show_cross_hair)
        write_to_file_cross_on = Func(self.write_to_file, 'Cross on')
        write_to_file_fix = Func(self.write_to_file, 'Fixated')
        cross_off = Func(self.clear_cross_hair)
        write_to_file_cross_off = Func(self.write_to_file, 'Cross off')
        cross_interval = random.uniform(*self.cross_hair_int)
        photo_on = Func(self.show_photo)
        write_to_file_photo_on = Func(self.write_to_file, 'Photo on', self.photo_path)
        set_photo_timer = Func(self.set_photo_timer)

        self.cross_sequence = Parallel(cross_on, write_to_file_cross_on, watch_eye_timer)

        self.photo_sequence = Sequence(
            Parallel(write_to_file_fix, watch_eye),
            Wait(cross_interval),
            Func(self.stop_plot_eye_task),
            Parallel(cross_off, write_to_file_cross_off, watch_eye),
            Parallel(photo_on, write_to_file_photo_on, set_photo_timer))

    def start_fixation_period(self):
        # print 'We have fixation, in subroutine'
        # start next sequence. Can still be aborted, if lose fixation
        # during first interval
        if self.cross_hair:
            # print 'on the cross hair'
            self.photo_sequence.start()
        else:
            # print 'on the photo'
            self.photo_timer_on = True

    def no_fixation(self, task=None):
        # print 'no fixation or broken, restart cross'
        self.stop_plot_eye_task()
        self.restart_cross_bad_fixation()
        return task.done

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
        break_interval = random.uniform(*self.config['BREAK_INTERVAL'])
        self.base.taskMgr.doMethodLater(break_interval, self.start_photo_loop, 'start_over', extraArgs=[])

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
        # print 'show cross hair'
        self.x_node.show()

    def clear_cross_hair(self):
        # print 'clear cross hair'
        self.cross_hair = False
        self.x_node.hide()

    def stop_plot_eye_task(self):
        self.base.taskMgr.remove('plot_eye')

    def show_photo(self):
        # is definitely fixating at start, otherwise
        # photo wouldn't come on
        self.photo_timer_on = True
        # print self.photo_path
        # print time()
        # print 'show window'
        self.show_window()
        # print 'show actual photo'
        self.imageObject = OnscreenImage(self.photo_path, pos=(0, 0, 0), scale=0.75)
        # print self.imageObject

    def set_photo_timer(self):
        self.a = datetime.datetime.now()
        # print 'add photo timer task'
        self.photo_fix_time = 0
        self.task_timer = 0
        self.base.taskMgr.add(self.timer_task, 'photo_timer_task', uponDeath=self.set_break_timer)

    def timer_task(self, task):
        # this task collects time. We will only collect time while subject
        # is fixating. After we collect enough viewing time, exit task
        # first data point does not count, because photo wasn't up yet.
        if self.task_timer != 0:
            dt = task.time - self.task_timer
        else:
            dt = 0
        self.task_timer = task.time
        # dt = datetime.datetime.now() - self.task_timer
        # self.task_timer = datetime.datetime.now()
        if self.photo_timer_on:
            # print dt
            self.photo_fix_time += dt
            # print 'current timer', self.photo_fix_time
        if self.photo_fix_time >= self.config['PHOTO_TIMER']:
            # print datetime.datetime.now() - self.a
            return task.done
        else:
            return task.cont

    def set_break_timer(self, task):
        # print('remove photo, on break')
        self.imageObject.destroy()
        self.write_to_file('Photo off')
        for line in self.photo_window:
            line.detachNode()
        # print time()
        # print 'go on break after photo'
        self.base.taskMgr.doMethodLater(self.config['PHOTO_BREAK_TIMER'], self.send_cleanup, 'photo_send_cleanup')
        # print 'set break'
        # print time()
        return task.done

    def check_fixation(self, eye_data):
        # print 'check photo fixation'
        # print('eye', eye_data)
        # print('tolerance', self.tolerance)
        # tolerance is the x, y border that eye_data should
        # be contained in, both should be (x, y) tuple
        # photos are centered, so as long as the absolute value of the eye
        # is less than the absolute value of the tolerance, should be golden
        # if abs(eye_data[0]) < abs(self.tolerance[0]) and abs(eye_data[1]) < abs(self.tolerance[1]):
        # hack for giuseppe:
        if abs(eye_data[0]) < abs(self.tolerance[0]) and -self.tolerance[1] - 100 < eye_data[1] < self.tolerance[1]:
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
        # photo_window.drawTo(self.tolerance[0], 55, -self.tolerance[1] - 100)
        photo_window.drawTo(self.tolerance[0], 55, -self.tolerance[1])
        # print photo_window.getCurrentPosition()
        # photo_window.drawTo(-self.tolerance[0], 55, -self.tolerance[1] - 100)
        photo_window.drawTo(-self.tolerance[0], 55, -self.tolerance[1])
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
        cross.moveTo(0 + dist_from_center, 55, 0)
        cross.drawTo(0 - dist_from_center, 55, 0)
        cross.moveTo(0, 55, 0 - dist_from_center)
        cross.drawTo(0, 55, 0 + dist_from_center)
        self.x_node = self.base.render.attachNewNode(cross.create(True))
        self.x_node.hide()

    def write_to_file(self, event, photo=None):
        # print 'write to file', event
        self.logging.log_event(event)
        if photo:
            self.logging.log_event(photo)

    def close(self):
        print('close photos')
        self.base.taskMgr.removeTasksMatching('photo_*')
        with open(self.config['file_name'], 'a') as config_file:
            config_file.write('\nLAST_PHOTO_INDEX = ' + str(self.end_index))

    def advance_photo_index(self):
        if self.sets_shown < self.config['NUM_PHOTO_SETS']:
            print 'advance photo index'
            last_index = self.end_index
            num_photos_in_set = self.config['NUM_PHOTOS_IN_SET']
            twice = self.config['SHOW_PHOTOS_TWICE']
            self.index_list = create_index_list(num_photos_in_set,last_index, twice)
            print('index list', self.index_list)
            # reset the count for good fixations. In case there is large time gap
            # between last fix from previous block and this block, probably
            # want to start count again.
            self.loop_count = 0
            return True
        else:
            print 'done with sets', self.sets_shown
            return False

    def send_cleanup(self, task):
        self.stop_plot_eye_task()
        # print time()
        # print('after photo cleanup, start next loop')
        messenger.send('cleanup')
        return task.done


def create_index_list(num_photos, first_index=0, twice=True):
    # last photo is first + num_photos
    last_index = first_index + num_photos
    index_list = [first_index, last_index]
    if twice:
        index_list *= 2
    print('index list', index_list)
    return index_list

