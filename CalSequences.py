from __future__ import division
from direct.interval.MetaInterval import Parallel, Sequence
from direct.interval.FunctionInterval import Func, Wait
from direct.showbase.MessengerGlobal import messenger
from Square import Square
from random import uniform


class CalSequences(object):

    def __init__(self, config, base, logging, key_dict=None):
        self.config = config
        self.logging = logging
        self.base = base
        self.key_dict = key_dict
        # Our intervals
        # on_interval - time from on to fade
        # fade_interval - time from fade on to off
        # reward_interval - time from off to reward
        # move_interval - time from reward to move/on
        # fix_interval - used for auto, how long required to fixate
        # break_interval - used for auto, how long time out before
        #            next square on, if missed or broke fixation
        # on, fade, reward, move, fix, break
        self.interval_list = [self.config['ON_INTERVAL'], self.config['FADE_INTERVAL'], self.config['REWARD_INTERVAL'],
                              self.config['MOVE_INTERVAL'], self.config['FIX_INTERVAL'], self.config['BREAK_INTERVAL']]
        # dictionary for writing to file
        self.sequence_for_file = {
            0: 'Square moved',
            1: 'Square on',
            2: 'Square dims',
            3: 'Square off',
            4: 'Reward',
            5: 'Fixated',
            6: 'Bad fixation',
        }

        # initiate sequences
        self.manual_sequence = None
        self.auto_sequence_one = None
        self.auto_sequence_two = None
        # initiate square
        self.square = None
        # keep track of square position, in case we have to repeat a position
        self.square_position = None
        # used for testing
        self.current_task = None

    def setup_manual_sequence(self):
        # print 'setup manual sequence'
        all_intervals = self.create_intervals()
        # functions to use in sequences:
        plot_eye = Func(send_start_plot, check_eye=False)
        square_move = Func(self.square.move_for_manual_position)
        write_to_file_move = Func(self.write_to_file, index=0)
        square_on = Func(self.square.turn_on)
        write_to_file_on = Func(self.write_to_file, index=1)
        square_fade = Func(self.square.fade)
        write_to_file_fade = Func(self.write_to_file, index=2)
        square_off = Func(self.square.turn_off)
        write_to_file_off = Func(self.write_to_file, index=3)
        give_reward = Func(send_message, 'reward')
        write_to_file_reward = Func(self.write_to_file, index=4)
        clear_screen = Func(send_message, 'clear')
        cleanup = Func(self.send_cleanup)

        # Parallel does not wait for tasks to return before returning itself, which
        # works out pretty awesome, since move interval is suppose to be time from reward start
        # until next trial

        self.manual_sequence = Sequence(
            Parallel(square_move, write_to_file_move, plot_eye),
            Parallel(square_on, write_to_file_on),
            Wait(all_intervals[0]),
            Parallel(square_fade, write_to_file_fade),
            Wait(all_intervals[1]),
            Parallel(square_off, write_to_file_off),
            Wait(all_intervals[2]),
            Parallel(give_reward, write_to_file_reward),
            Wait(all_intervals[3]),
            Parallel(clear_screen, cleanup),
        )

    def setup_auto_sequences(self, good_trial):
        # print 'setup auto sequences'
        # print self.square.square.getPos()
        # making two "sequences", although one is just a parallel task
        # auto sequence is going to start with square fading
        all_intervals = self.create_intervals()
        if good_trial:
            self.square_position = None
        # print 'good trial? ', good_trial
        # print 'did square position change? ', self.square_position
        # functions used in sequence
        plot_eye = Func(send_start_plot, check_eye=False)
        watch_eye_timer = Func(send_start_plot, check_eye=True, timer=True)
        watch_eye = Func(send_start_plot, check_eye=True)
        square_move = Func(self.square.move, self.square_position)
        write_to_file_move = Func(self.write_to_file, index=0)
        square_on = Func(self.square.turn_on)
        write_to_file_on = Func(self.write_to_file, index=1)
        write_to_file_fix = Func(self.write_to_file, index=5)
        square_fade = Func(self.square.fade)
        write_to_file_fade = Func(self.write_to_file, index=2)
        square_off = Func(self.square.turn_off)
        write_to_file_off = Func(self.write_to_file, index=3)
        give_reward = Func(send_message, 'reward')
        write_to_file_reward = Func(self.write_to_file, index=4)
        clear_fix = Func(send_message, 'clear_fix')
        clear_screen = Func(send_message, 'clear')
        cleanup = Func(self.send_cleanup)
        # we don't know how long the wait period should be for square on,
        # because that wait period doesn't start until fixation, and we don't
        # know when that will happen. So make two sequences, so wait period
        # is flexible

        # create the first sequence.
        self.auto_sequence_one = Sequence(
            Parallel(square_move, write_to_file_move),
            Parallel(square_on, write_to_file_on, watch_eye_timer))

        # Parallel does not wait for any doLaterMethods to return before returning itself, which
        # works out pretty awesome, since move interval is suppose to be time from reward start
        # until next trial. This would be a problem if there was so much reward that it took up
        # all of the time for the move_interval, but that would be a lot of reward
        # print('pump delay', self.config['PUMP_DELAY'])
        # print('beeps', self.num_beeps)

        self.auto_sequence_two = Sequence(
            Parallel(write_to_file_fix, watch_eye),
            Wait(all_intervals[4]),
            Func(self.stop_plot_eye_task),
            Parallel(square_fade, write_to_file_fade, plot_eye),
            Wait(all_intervals[1]),
            Parallel(square_off, write_to_file_off),
            Wait(all_intervals[2]),
            Parallel(give_reward, write_to_file_reward, clear_fix),
            Wait(all_intervals[3]),
            Parallel(clear_screen, cleanup)
        )

    # Fixation Methods (auto)
    def start_fixation_period(self):
        # print 'We have fixation, auto'
        # start next sequence. Can still be aborted, if lose fixation
        # during first interval
        self.auto_sequence_two.start()

    def no_fixation(self, task):
        # print 'timed out, no fixation'
        # print 'where eye is', self.current_eye_data
        # this task waits run to run for the on interval, if there is a fixation, start_fixation_period
        # will begin and stop this task from running (started from process_eye_data method), if not we start over here
        self.base.taskMgr.remove('plot_eye')
        # print time()
        self.restart_auto_loop_bad_fixation()
        # print 'return wait_off_task'
        return task.done

    def broke_fixation(self):
        # print 'broke fixation'
        # this task is called if fixation is broken, so during second auto-calibrate sequence
        # stop checking the eye
        self.base.taskMgr.remove('plot_eye')
        # stop sequence
        # print 'stop sequence'
        self.auto_sequence_two.pause()
        # self.auto_sequence_two.finish()
        # print 'restart'
        self.restart_auto_loop_bad_fixation()

    def restart_auto_loop_bad_fixation(self):
        # print 'restart auto loop, bad fixation long pause'
        # print time()
        # stop plotting and checking eye data
        # make sure there are no tasks waiting
        # self.base.taskMgr.removeTasksMatching('auto_*')
        # turn off square
        self.square.turn_off()
        # keep square position
        self.square_position = self.square.square.getPos()
        # print self.square_position
        # write to log
        self.write_to_file(index=3)  # square off
        self.write_to_file(index=6)  # bad fixation
        send_message('clear')
        # plot eye, but not checking for fixation
        send_start_plot()
        # now wait, and then start over again.
        all_intervals = self.create_intervals()
        # loop delay is normal time between trials + added delay
        loop_delay = all_intervals[5] + all_intervals[3]
        # wait for loop delay, then cleanup and start over
        self.base.taskMgr.doMethodLater(loop_delay, self.send_cleanup, 'auto_cleanup', extraArgs=[])
        # print 'delay for broken fixation'
        # print(self.base.taskMgr)

    # sequence methods for both auto and manual
    def write_to_file(self, index):
        # print 'first auto sequence is stopped', self.auto_sequence_one.isStopped()
        # print 'second auto sequence is stopped', self.auto_sequence_two.isStopped()
        # print self.base.taskMgr
        # print('write_to_file', self.sequence_for_file[index])
        # print('square position', self.square.square.getPos())

        # if square is turning on, write position of square
        # print index
        if index == 1:
            position = self.square.square.getPos()
            self.logging.log_position(position)
        self.logging.log_event(self.sequence_for_file[index])
        # used for testing
        self.current_task = index
        # print 'current task from game', self.current_task

    def create_intervals(self):
        # print('interval list', self.interval_list)
        all_intervals = [uniform(*i) for i in self.interval_list]
        # print('all intervals', all_intervals)
        return all_intervals

    def get_fixation_target(self):
        target = (self.square.square.getPos()[0], self.square.square.getPos()[2])
        on_interval = uniform(*self.interval_list[0])
        return target, on_interval

    def prepare_task(self, manual):
        # set up square positions,
        # only happens at beginning or changing manual
        self.square = Square(self.config, self.key_dict, self.base)
        self.square.setup_positions(self.config, manual)

    def stop_plot_eye_task(self):
        self.base.taskMgr.remove('plot_eye')

    def send_cleanup(self):
        self.stop_plot_eye_task()
        # for testing, good to know when at end of loop, doesn't affect task at all
        self.current_task = None
        send_message('cleanup')


def send_message(message):
    # print message
    messenger.send(message)


def send_start_plot(check_eye=False, timer=False):
    # print 'plot'
    messenger.send('plot', [check_eye, timer])
