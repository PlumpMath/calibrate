# This file is only used for unit tests and other testing,
# change win_res here and not in config,
# use 'ppython calibration.py ', (x is 1 manual, 2 random) while testing,
# but not running unit tests, change WIN_RES appropriately.
SUBJECT = 'test'
FAKE_DATA = True
# window resolution, can be a resolution or None for normal panda3d window
# use 'Test' for testing, so does not try to open second window
# use this for unit testing
WIN_RES = 'Test'
# use this for mac, not unit testing
#WIN_RES = None
# use this for windows, not unit testing
#WIN_RES = [1024, 768]
# Screen size
# This is obviously wrong if you aren't calibrating with the projector,
# but shouldn't matter for testing.
SCREEN = [1337, 991]
VIEW_DIST = 1219
# resolution for screen presenting eye data, not used for most testing
EYE_RES = [1280, 800]
#EYE_RES = [1600, 900]

# square scale in degree of visual angle (scales both length and width)
SQUARE_SCALE = 0.5

# How close to the stimulus does the eye position have to be to get reward in
# auto mode? distance in degree of visual angle from center of square, so
# adding half the square to tolerance. If tolerance is 1 + square_scale/2, and
# square_scale is 0.5, then the square is half a degree wide, and the tolerance
# is one degree outside of the square. Tolerance of zero means must be in the
# square
TOLERANCE = 1 + SQUARE_SCALE/2
#TOLERANCE = 22 + SQUARE_SCALE/2

# How far out in visual angle degrees do you want the outer targets?
MAX_DEGREES_X = 15
MAX_DEGREES_Y = 10
# how many times to repeat each point when in random mode
# for testing set this to one, so we know that each time there is a move
# it is to a new place
POINT_REPEAT = 1
# How many points in x direction
X_POINTS = 3
# How many points in y direction
Y_POINTS = 3

# How long must fixate before square changes color
FIX_INTERVAL = 1.0
# How long to wait until next square if break fixation
BREAK_INTERVAL = 1.0
# All intervals represent min and max for a uniform random distribution
# give it equal min and max, and each unique, so we can test intervals.
# Assume random.uniform really works for intervals.
ON_INTERVAL = (0.75, 0.75)  # Time on
FADE_INTERVAL = (0.50, 0.50)  # Time faded
REWARD_INTERVAL = (0.0, 0.0)  # Time from off to reward
MOVE_INTERVAL = (1.0, 1.0)  # Time from fading off until on in new place

# how many rewards per trial
NUM_BEEPS = 3