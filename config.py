SUBJECT = 'test'
#SUBJECT = 'Gus'

# window resolution, can be a resolution or None for normal panda3d window
# if using normal panda3d window, visual angle calculations will be off,
# unless you also change screen and view_dist appropriately, but for testing, should be ok
# WIN_RES is the resolution for the window that we are using for the actual calibration,
# the one used for determining visual angle. Resolution for the second window, set below
#WIN_RES = None
WIN_RES = [1024, 768]
# Screen size, again for actual calibration, so size of image on projector screen
SCREEN = [1337, 991]
VIEW_DIST = 1219

# resolution for screen presenting eye data
#EYE_RES = [1024, 768]
EYE_RES = [1600, 900]
# square scale in degree of visual angle (scales both length and width)
SQUARE_SCALE = 0.5

# How close to the stimulus does the eye position have to be to get reward in
# auto mode? distance in degree of visual angle from center of square, so
# adding half the square to tolerance. If tolerance is 1 + square_scale/2, and
# square_scale is 0.5, then the square is half a degree wide, and the tolerance
# is one degree outside of the square. Tolerance of zero means must be in the
# square
TOLERANCE = 1 + SQUARE_SCALE/2

# How far out in visual angle degrees do you want the outer targets?
MAX_DEGREES_X = 10
MAX_DEGREES_Y = 10

# how many times to repeat each point when in random mode
POINT_REPEAT = 2
# How many points in x direction
X_POINTS = 5
# How many points in y direction
Y_POINTS = 5

# How long must fixate before square changes color
FIX_INTERVAL = 1.0
# How long to wait until next square if break fixation
BREAK_INTERVAL = 1.0
# All intervals represent min and max for a uniform random distribution
#ON_INTERVAL = (0.7, 1.25)  # Time on
ON_INTERVAL = (1.0, 2.0)  # Time on
FADE_INTERVAL = (0.35, 0.35) # Time faded
REWARD_INTERVAL = (0.0, 0.0) # Time from off to reward - make go off when turns off
MOVE_INTERVAL = (2.0, 2.0) # Time from reward until on in new place

# how many rewards per trial
NUM_BEEPS = 3