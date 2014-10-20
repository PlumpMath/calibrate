#SUBJECT = 'test'
#SUBJECT = 'Maria'
SUBJECT = 'JN'

#FAKE_DATA = True
# window resolution, can be a resolution or None for normal panda3d window
# if using normal panda3d window, visual angle calculations will be off,
# unless you also change screen and view_dist appropriately, but for testing, should be ok
# WIN_RES is the resolution for the window that we are using for the actual calibration,
# the one used for determining visual angle. Resolution for the second window, set below
#WIN_RES = None
#WIN_RES = [1024, 768]
WIN_RES = [1280, 800]
# Screen size, again for actual calibration, so size of image on projector screen (mm)
SCREEN = [1467, 902]
#SCREEN = [1337, 991]
# mm distance from subject to screen
VIEW_DIST = 1219

# resolution for screen presenting eye data
EYE_RES = [1280, 800]
#EYE_RES = [1600, 900]

# the voltage from the eye tracker runs from about 5 to -5 volts,
# so total 10 variance, with 1280, 800 as resolution, use gain of
# 150 for x, and 100 for y, for total (1500, 1000), which will cover
# the screen
GAIN = [150, 100]

# size of square, scale is in degree of visual angle
# (scales both length and width)
SQUARE_SCALE = 0.5

# How close to the stimulus does the eye position have to be to get reward in
# auto mode? Use number of degrees of visual angle from outside border of square,
# so 0 means has to be in square, 5 is 5 degrees outside of square
degree_out_square = 6

# Tolerance is the distance in degree of visual angle from center of square,
# so add half the square size to tolerance. If tolerance is 1 + square_scale/2, and
# square_scale is 0.5, then the square is half a degree wide, and the tolerance
# is one degree outside of the square. Tolerance of zero means must be in the
# square

TOLERANCE = degree_out_square + SQUARE_SCALE/2

# How far out in visual angle degrees do you want the outer targets?
MAX_DEGREES_X = 10
MAX_DEGREES_Y = 10

# how many times to repeat each point when in random mode
POINT_REPEAT = 5
# How many points in x direction
X_POINTS = 5
# How many points in y direction
Y_POINTS = 5

# All intervals represent min and max for a uniform random distribution
# for intervals where an exact interval is preferred, enter a tuple with the
# same number twice
# How long must fixate before square changes color
FIX_INTERVAL = (1.0, 1.0)
# How long to wait until next square if breaks fixation,
# (in addition to the move interval)
BREAK_INTERVAL = (1.0, 1.0)

#ON_INTERVAL = (0.7, 1.25)  # Time on
#ON_INTERVAL = (1.0, 2.0)  # Time on
#FADE_INTERVAL = (0.35, 0.35)  # Time faded
#REWARD_INTERVAL = (0.0, 0.0)  # Time from off to reward - make go off when turns off
#MOVE_INTERVAL = (2.0, 2.0)  # Time from reward until on in new place

ON_INTERVAL = (1.0, 1.0)  # Time on
FADE_INTERVAL = (0.35, 0.35)  # Time faded
REWARD_INTERVAL = (0.0, 0.0)  # Time from off to reward - make go off when turns off
MOVE_INTERVAL = (2.0, 2.0)  # Time from reward until on in new place (inter-trial interval)
# how many rewards per trial
NUM_BEEPS = 3

PUMP_DELAY = 0.2  # time in seconds between each pulse of the pump

# Stuff for photos
#PHOTO_PATH = 'photos/'  # if path is none, not using photos
PHOTO_PATH = None
PHOTO_TIMER = 2  # how long to show each photo, only counting fixation time
PHOTO_BREAK_TIMER = 2  # time in seconds between photo off and next fixation point
NUM_PHOTOS_IN_SET = 16  # how many photos in each set
CAL_PTS_PER_PHOTO = 3  # how many calibration points to show between each photo
LAST_PHOTO_INDEX = 0  # keeps track of where we are in the directory from day to day.