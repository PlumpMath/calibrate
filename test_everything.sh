#!/bin/bash

arch=$(uname -m)

if [ "$arch" == 'x86_64' ]
then
    # with a mac, we can just run once, and it will run both conditions for each test file
    ppython test_calibration.py mac > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_random_calibration.py mac > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py mac > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
else
    ppython test_calibration.py False > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_calibration.py True > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_random_calibration.py False > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_random_calibration.py True > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py False > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py True > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
fi


