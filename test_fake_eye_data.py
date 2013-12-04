import fake_eye_data

test = fake_eye_data.yield_eye_data()
for i in range(10):
    print test.next()

