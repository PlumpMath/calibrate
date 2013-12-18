# This file is only used for unittests
SUBJECT = 'test'
# window resolution, can be a resolution or None for normal panda3d window
# use 'Test' for testing, so does not try to open second window
#WIN_RES = 'Test'
WIN_RES = [1024, 768]
# Screen size
SCREEN = [1327, 991]
VIEW_DIST = 1219
# number of pixels from outer edges to first point
PADDING = 100
# how many times to repeat each point when in random mode
POINT_REPEAT = 2
# How many points in x direction
X_POINTS = 10
# How many points in y direction
Y_POINTS = 10
# x limit, 0 is center, so limit in other direction just negative
X_LIMITS = 15
# y limits, 0 is center, so limit in other direction just negative
Y_LIMITS = 10

# All intervals represent min and max for a uniform random distribution
# give it equal min and max, and each unique, so we can test intervals.
# Assume random.uniform really works for intervals.
ON_INTERVAL = (0.75, 0.75)  # Time on
FADE_INTERVAL = (0.50, 0.50) # Time faded
REWARD_INTERVAL = (0, 0) # Time from off to reward
MOVE_INTERVAL = (1.0, 1.0) # Time from fading off until on in new place

# how many rewards per trial
NUM_BEEPS = 3