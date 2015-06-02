from direct.stdpy import threading
from Queue import Queue
import logging
import time
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
        condition = threading.Condition()
        c1 = threading.Thread(name='c1', target=consumer, args=(condition, q))
        c2 = threading.Thread(name='c2', target=consumer, args=(condition, q))
        p = threading.Thread(name='p', target=producer, args=(condition, q))

    def produce_queue(self, eye_data):
        print 'producing object for queue', self.queue.put(eye_data)
        print 'size now', self.queue.qsize()

    def consume_queue(self):
        val = self.queue.get(1)
        print 'object consumed', val
        print 'consumed object from queue... size now', self.queue.qsize()

    def consumer(self, cond):
        """wait for the condition and use the resource"""
        logging.debug('Starting consumer thread')
        t = threading.currentThread()
        with cond:
            cond.wait()
            self.consume_queue(self.queue)
            logging.debug('Resource is available to consumer')

    def producer(cond, queue):
        """set up the resource to be used by the consumer"""
        logging.debug('Starting producer thread')
        if pydaq:
            eye_task = pydaq.EOGTask()
            eye_task.SetCallback(produce_queue)
            eye_task.StartTask()
        with cond:
            produce_queue(queue)
            logging.debug('Making resource available')
            cond.notifyAll()






c1.start()
time.sleep(1)
c2.start()
time.sleep(1)
p.start()
time.sleep(1)
print 'ok'