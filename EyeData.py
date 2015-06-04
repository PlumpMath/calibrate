from direct.stdpy import threading
from Queue import Queue
from fake_eye_data import yield_eye_data
import logging
from direct.showbase.ShowBase import ShowBase
import sys
import time

try:
    sys.path.insert(1, '../pydaq')
    import pydaq
    print 'pydaq loaded'
except ImportError:
    pydaq = None
    print 'Not using PyDaq'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s',
                    )


class EyeData(object):

    def __init__(self, show_base, fake_data):
        self.queue = Queue(32)
        self.condition = threading.Condition()
        self.base = show_base
        if not pydaq or fake_data:
            self.fake_data = yield_eye_data((0.0, 0.0))
            self.pydaq = None
        else:
            self.fake_data = None
            self.pydaq = pydaq
            self.eye_task = self.pydaq.EOGTask()
        self.threads = []
        self.run_consumer = True
        logging.debug('started threads')

    def produce_queue(self, eye_data):
        # do logging
        logging.debug('received eye data {0}'.format(eye_data))
        self.queue.put(eye_data)
        qsize = self.queue.qsize()
        logging.debug('produced object, size now {0}'.format(qsize))
        self.condition.notify_all()
        if qsize == 32:
            self.close()

    def consume_queue(self):
        val = self.queue.get()
        logging.debug('object consumed {0}'.format(val))
        qsize = self.queue.qsize()
        logging.debug('consumed object, size now {0}'.format(qsize))

    def consumer(self):
        """wait for the condition and use the resource, we only allow
        one consumer at a time."""
        logging.debug('Starting consumer thread')
        # make this loop dependent on whether this consumer is currently
        # running
        while self.run_consumer:
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
                self.base.taskMgr.add(self.get_fake_data_task, 'fake_eye')
            logging.debug('Making resource available')

    def get_fake_data_task(self, task):
        self.produce_queue(self.fake_data.next())
        return task.cont

    def start_thread(self, thread_name, thread_target):
        logging.debug('start thread', thread_name)
        self.threads.append(threading.Thread(name=thread_name, target=thread_target))
        self.threads[-1].start()

    def end_consumer(self):
        self.run_consumer = False

    def close(self):
        self.end_consumer()
        logging.debug('close')
        if self.pydaq:
            self.eye_task.DoneCallback(self.eye_task)
            self.eye_task.StopTask()
            self.eye_task.ClearTask()
        else:
            self.base.taskMgr.remove('fake_eye')
        logging.debug('close finished')

if __name__ == "__main__":
    base = ShowBase()
    ED = EyeData(base, False)
    base.exitFunc = ED.close
    ED.start_thread('producer', ED.producer)
    ED.start_thread('consumer', ED.consumer)
    ED.base.run()