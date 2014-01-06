import random
import datetime, threading, time

next_call = time.time()
# create some fake eye data
def create_eye_data(size):
    eye_data = []
    (x, y) = (0.0, 0.0)
    eye_data.append((x, y))
    for i in range(size):
        x = random.uniform(x + 0.5, x - 0.5)
        y = random.uniform(y + 0.5, y - 0.5)
        eye_data.append((x, y))

    return eye_data


def yield_eye_data(origin = [], variance = []):
    global next_call
    #(x, y) = (0, 0)
    # testing always sends in an origin and variance, so changing defaults will not affect tests
    if origin:
        (x, y) = origin
    if not variance:
        variance = 2
    while True:
        #print 'x', x
        #print 'y', y
        yield x, y
        # no drift currently, pure random walk
        x = random.uniform(x + variance, x - variance)
        y = random.uniform(y + variance, y - variance)
    # will continue sending data every x seconds until calling function quits
    next_call = next_call + 0.1
    threading.Timer( next_call - time.time(), yield_eye_data ).start()

yield_eye_data()
