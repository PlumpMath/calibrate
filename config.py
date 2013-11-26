# move the square with the keyboard, or let it go automatically
MANUAL = False
# how many times to repeat each point when in random mode
POINT_REPEAT = 2
# How many points in x direction
X_POINTS = 5
# How many points in y direction
Y_POINTS = 5
# x limit, 0 is center, so limit in other direction just negative
X_LIMITS = 10
# y limits, 0 is center, so limit in other direction just negative
Y_LIMITS = 10

# All intervals represent min and max for a uniform random distribution
ON_INTERVAL = (2, 3)  # Time on
FADE_INTERVAL = (0.3, 0.7) # Time faded
MOVE_INTERVAL = (2, 3) # Time from fading off until on in new place