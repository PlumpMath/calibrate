#!/bin/bash

arch=$(uname -m)

if [ "$arch" == 'x86_64' ]
then
    ppython test_calibration.py 0 > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_calibration.py 1 > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_random_calibration.py 0 > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_random_calibration.py 1 > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py 0 > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py 1 > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
else
    ppython test_calibration.py 0 > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_calibration.py 1 > /dev/null || { echo A test in test_calibraion has failed; exit 1; }
    ppython test_random_calibration.py 0 > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_random_calibration.py 1 > /dev/null || { echo A test in test_random_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py 0 > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
    ppython test_manual_calibration.py 1 > /dev/null || { echo A test in test_manual_calibraion has failed; exit 1; }
fi


