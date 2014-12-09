from datetime import datetime
from time import time
import sys
import os

try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    LOADED_PYDAQ = True
    #print 'loaded PyDaq'
except ImportError:
    LOADED_PYDAQ = False
    print 'Not using PyDaq'


class Logging():

    def __init__(self, config):
        self.config = config
        self.eye_file_name = None
        self.time_file_name = None
        self.eye_data_file = None
        self.time_data_file = None
        self.send_events = None
        self.send_strobe = None
        self.pydaq_dict = None

    def open_files(self, manual, tolerance):
        # open file for recording eye data
        subject = self.config['SUBJECT']
        data_dir = 'data/' + self.config['SUBJECT']
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if manual:
            self.eye_file_name = data_dir + '/eye_cal_' + datetime.now().strftime("%y_%m_%d_%H_%M")
            self.time_file_name = data_dir + '/time_cal_' + datetime.now().strftime("%y_%m_%d_%H_%M")
        else:
            self.eye_file_name = data_dir + '/eye_cal2_' + datetime.now().strftime("%y_%m_%d_%H_%M")
            self.time_file_name = data_dir + '/time_cal2_' + datetime.now().strftime("%y_%m_%d_%H_%M")
        #print('open', self.eye_file_name)
        # open file for recording eye positions
        self.eye_data_file = open(self.eye_file_name, 'w')
        self.eye_data_file.write('timestamp, x_position, y_position, for subject: ' + subject + '\n')
        # open file for recording event times
        self.time_data_file = open(self.time_file_name, 'w')
        self.time_data_file.write('timestamp, task, for subject: ' + subject + '\n')
        if not manual:
            self.log_config('Tolerance', tolerance)
        self.pydaq_dict = {}
        if self.config['SEND_DATA'] and LOADED_PYDAQ:
            self.open_pydaq()
            self.create_pydaq_dict()
        else:
            print('Not sending digital signals')

        # open and close file for keeping configuration info
        # turns out there is a lot of extra crap in the config dictionary,
        # and I haven't figured out a pretty way to get rid of the extra crap.
        # Honestly, the best thing may be to just make a copy of the original damn file.
        # maybe look to see how pandaepl handles this
        #config_file_name = data_dir + '/config_cal_' + datetime.datetime.now().strftime("%y_%m_%d_%H_%M")

        #w = csv.writer(open(config_file_name, 'w'))
        #for name, value in config.items():
        #    w.writerow([name, value])

        #for name, value in config.items():
        #    print name, value
        # if you want to see the frame rate
        # window.setFrameRateMeter(True)

    def open_pydaq(self):
        self.send_events = pydaq.OutputEvents()
        self.send_strobe = pydaq.StrobeEvents()

    def log_event(self, event):
        # log an event found in log_key
        self.time_data_file.write(str(time()) + ', ' + event + '\n')
        if self.pydaq_dict:
            #print self.pydaq_dict
            if event in self.pydaq_dict:
                #print('event code is: ',self.pydaq_dict[event])
                self.send_events.send_signal(self.pydaq_dict[event])
            else:
                #print('should be photo ', event)
                self.send_events.send_signal(int(event[11:13]))
            self.send_strobe.send_signal()

    def log_position(self, position):
        self.time_data_file.write(str(time()) + ', Square Position, ' + str(position[0]) +
                                  ', ' + str(position[2]) + '\n')

    def log_change(self, change_type, change):
        # was going to try to make this smart, but always either send in a list of 2
        # or a single number, so this turns out to be least complicated way to do it.
        #print(change_type, change)
        if isinstance(change, list):
            self.time_data_file.write(str(time()) +
                                      ', Change ' + change_type + ', ' +
                                      str(change[0]) + ', ' +
                                      str(change[1]) + '\n')
        else:
            self.time_data_file.write(str(time()) +
                                      ', Change ' + change_type + ', ' +
                                      str(change) + '\n')

    def log_config(self, config, value):
        self.time_data_file.write(str(time()) + ', ' + config + ', ' +
                                  str(value) + '\n')
            
    def log_eye(self, eye_data):
        self.eye_data_file.write(str(time()) + ', ' +
                                 str(eye_data[0]) + ', ' +
                                 str(eye_data[1]) + '\n')
            
    def create_pydaq_dict(self):
        self.pydaq_dict = {
            'Square on': 100,
            'Square dims': 101,
            'Square off': 102,
            'Reward': 103,
            'Square moved': 104,
            'Fixated': 105,
            'No fixation or broken, restart': 106,
            'Photo On': 107,
            'Photo Off': 108}

    # Closing methods
    def close_files(self):
        #print('close', self.eye_file_name)
        self.eye_data_file.close()
        self.time_data_file.close()
        if self.pydaq_dict:
            self.send_events.close()
            self.send_strobe.close()
