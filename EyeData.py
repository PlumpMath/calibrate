from direct.stdpy import threading
from Queue import Queue
from fake_eye_data import yield_eye_data
import logging
from direct.showbase.ShowBase import ShowBase
import sys
# import time

try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    # print 'pydaq loaded'
except ImportError:
    pydaq = None
    # print 'Not using PyDaq'

log_filename = 'test.out'
log_level = logging.DEBUG
# log_level = logging.CRITICAL

# logging.basicConfig(level=log_level,
#                     filename=log_filename,
#                     format='%(asctime)s (%(threadName)-2s) %(message)s',
#                     )


class EyeData(object):

    def __init__(self, show_base, fake_data):
        self.queue = Queue(32)
        self.condition = threading.Condition()
        self.base = show_base
        if not pydaq or fake_data:
            self.origin = (0.0, 0.0)
            self.variance = None
            self.fake_data = None
            self.pydaq = None
            self.data_type = 'Fake Data: ['
        else:
            self.fake_data = None
            self.pydaq = pydaq
            self.eye_task = self.pydaq.EOGTask()
            self.data_type = 'IScan: ['
        self.producer_thread = None
        self.consumer_thread = []
        self.consumer_limit = None  # used for testing, I think this won't be necessary
        # when make actual tests...
        self.logging = None
        self.log_now = False  # if true, new file, if none, log as normal
        logging.debug('Initialized EyeData')

    def produce_queue(self, eye_data):
        if self.log_now is None:
            self.logging.log_eye(eye_data)
        elif self.log_now:
            # if we have a new log file, empty the queue
            self.queue.queue.clear()
            self.logging.log_eye(eye_data)
            self.log_now = None
        logging.debug('received eye data {0}'.format(eye_data))
        self.queue.put(eye_data)
        qsize = self.queue.qsize()
        logging.debug('produced object, size now {0}'.format(qsize))
        self.condition.notify_all()
        # if not being consumed (between tasks), get rid of old data
        if qsize > 20:
            self.queue.get()

    def consume_queue(self):
        val = []
        while not self.queue.empty():
            val.append(self.queue.get())
        logging.debug('object consumed {0}'.format(val))
        qsize = self.queue.qsize()
        logging.debug('consumed object, size now {0}'.format(qsize))
        return val

    def consumer(self):
        """wait for the condition and use the resource, we only allow
        one consumer at a time."""
        logging.debug('Starting consumer thread')
        logging.debug('limit {0}'.format(self.consumer_limit))
        # consumer_limit is for testing
        if self.consumer_limit:
            for i in range(self.consumer_limit):
                with self.condition:
                    self.condition.wait()
                    self.consume_queue()
                    logging.debug('Resource is available, consumer waiting')
        else:
            with self.condition:
                self.condition.wait()
                self.consume_queue()
                logging.debug('Resource is available, consumer waiting')
        logging.debug('left consumer')

    def producer(self):
        """set up the resource to be used by the consumer"""
        logging.debug('Starting producer thread')
        with self.condition:
            if self.pydaq:
                logging.debug('starting eye data task')
                self.eye_task.SetCallback(self.produce_queue)
                self.eye_task.StartTask()
            else:
                logging.debug('start fake eye data task')
                # start fake data at 0,0 for testing
                self.fake_data = yield_eye_data(self.origin, self.variance)
                self.base.taskMgr.add(self.get_fake_data_task, 'fake_eye')
            logging.debug('Making resource available')

    def get_fake_data_task(self, task):
        self.produce_queue(self.fake_data.next())
        return task.cont

    def start_producer_thread(self, thread_name, origin=None, variance=None):
        logging.debug('start thread {0}'.format(thread_name))
        # print 'in producer', origin, variance
        if origin:
            self.origin = origin
        if variance:
            self.variance = variance

            # print('cleared thread')
        if not self.producer_thread:
            self.producer_thread = threading.Thread(name=thread_name, target=self.producer)
            self.producer_thread.start()

    def start_consumer_thread(self, thread_name, new=True):
        # can have more than one consumer
        logging.debug('start thread {0}'.format(thread_name))
        if new:
            self.consumer_thread.append(threading.Thread(name=thread_name, target=self.consumer))
        self.consumer_thread[-1].start()

    def stop_logging(self):
        self.log_now = False

    def start_logging(self, log_object):
        # print 'start logging eye data'
        self.log_now = True
        self.logging = log_object

    def close(self):
        logging.debug('close')
        if self.pydaq:
            # self.eye_task.DoneCallback(self.eye_task)
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        else:
            self.base.taskMgr.remove('fake_eye')
        logging.debug('close finished')

if __name__ == "__main__":
    base = ShowBase()
    ED = EyeData(base, False)
    base.exitFunc = ED.close
    ED.consumer_limit = 1000
    ED.start_producer_thread('producer')
    ED.start_consumer_thread('consumer')
    ED.base.run()
