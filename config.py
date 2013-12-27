SUBJECT = 'test'

# window resolution, can be a resolution or None for normal panda3d window
WIN_RES = None
#WIN_RES = [1024, 768]
# Screen size
SCREEN = [1337, 991]
VIEW_DIST = 1219

# How close to the stimulus does the monkey have to be to get reward in
# auto mode? distance in pixels
TOLERANCE = 100

# How far out in visual angle degrees do you want the outer targets?
MAX_DEGREES_X = 5
MAX_DEGREES_Y = 5

# how many times to repeat each point when in random mode
POINT_REPEAT = 2
# How many points in x direction
X_POINTS = 5
# How many points in y direction
Y_POINTS = 5

# All intervals represent min and max for a uniform random distribution
#ON_INTERVAL = (0.7, 1.25)  # Time on
ON_INTERVAL = (2, 2)  # Time on
FADE_INTERVAL = (0.35, 0.35) # Time faded
REWARD_INTERVAL = (0, 0) # Time from off to reward - make go off when turns off
MOVE_INTERVAL = (1, 1) # Time from reward until on in new place

# how many rewards per trial
NUM_BEEPS = 3