from direct.stdpy import threading
from Queue import Queue
from fake_eye_data import yield_eye_data
import logging
from direct.showbase.ShowBase import ShowBase
from sys import path
try:
    path.insert(1, '../pydaq')
    import pydaq
    print 'pydaq loaded'
except ImportError:
    pydaq = None
    print 'Not using PyDaq'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s',
                    )


class EyeData(object):

    def __init__(self):
        self.queue = Queue(32)
        self.condition = threading.Condition()
        self.base = ShowBase()
        if not pydaq:
            self.fake_data = yield_eye_data((0.0, 0.0))
            self.pydaq = None
        else:
            self.fake_data = None
            self.pydaq = pydaq
        self.c1 = threading.Thread(name='c1', target=self.consumer)
        self.c2 = threading.Thread(name='c2', target=self.consumer)
        self.p = threading.Thread(name='p', target=self.producer)

    def produce_queue(self, eye_data):
        print 'producing object for queue', self.queue.put(eye_data)
        print 'size now', self.queue.qsize()

    def consume_queue(self):
        val = self.queue.get(1)
        print 'object consumed', val
        print 'consumed object from queue... size now', self.queue.qsize()

    def consumer(self):
        """wait for the condition and use the resource"""
        logging.debug('Starting consumer thread')
        t = threading.currentThread()
        with self.condition:
            self.condition.wait()
            self.consume_queue()
            logging.debug('Resource is available to consumer')

    def producer(self):
        """set up the resource to be used by the consumer"""
        logging.debug('Starting producer thread')
        if self.pydaq:
            eye_task = pydaq.EOGTask()
            eye_task.SetCallback(self.produce_queue)
            eye_task.StartTask()
        else:
            self.base.taskMgr.add(self.get_fake_data_task, 'fake_eye')
        with self.condition:
            self.produce_queue()
            logging.debug('Making resource available')
            self.condition.notifyAll()

    def get_fake_data_task(self, task):
        self.produce_queue(self.fake_data.next())
        return task.cont


if __name__ == "__main__":
    ED = EyeData()
    ED.base.run()
    ED.c1.start()
    ED.c2.start()
    ED.p.start()
    print 'ok'
