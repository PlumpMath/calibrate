# move the square with the keyboard, or let it go automatically,
# default is automatic
MANUAL = False
# how many times to repeat each point when in random mode
POINT_REPEAT = 2
# How many points in x direction
X_POINTS = 10
# How many points in y direction
Y_POINTS = 10
# x limit, 0 is center, so limit in other direction just negative
X_LIMITS = 20
# y limits, 0 is center, so limit in other direction just negative
Y_LIMITS = 20

# All intervals represent min and max for a uniform random distribution
# give it equal min and max, and each unique, so we can test intervals.
# Assume random.uniform really works for intervals.
ON_INTERVAL = (1.00, 1.00)  # Time on
FADE_INTERVAL = (0.50, 0.50) # Time faded
MOVE_INTERVAL = (0.75, 0.75) # Time from fading off until on in new place