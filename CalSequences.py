

class CalSequences(object):

    def __init__(self, config):
        self.config = config
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

        # initiate sequences
        self.manual_sequence = None
        self.auto_sequence_one = None
        self.auto_sequence_two = None

        # dictionary for writing to file
        self.sequence_for_file = {
            0: 'Square moved',
            1: 'Square on',
            2: 'Square dims',
            3: 'Square off',
            4: 'Reward',
            5: 'Fixated',
            6: 'Bad Fixation',
        }