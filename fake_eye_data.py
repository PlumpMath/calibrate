import random


# create some fake eye data
def create_eye_data(size):
    eye_data = []
    (x, y) = (0, 0)
    eye_data.append((x, y))
    for i in range(size - 1):
        x = random.uniform(x + 0.5, x - 0.5)
        y = random.uniform(y + 0.5, y - 0.5)
        eye_data.append((x, y))

    return eye_data
