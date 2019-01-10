# Put modules to test on the path
import env
# Add some helper packages
import numpy as np
import matplotlib.pyplot as pyplot
# Add modules to test
import unittest as ut
import dysart.measurement.dummy_lab as dummy_lab
# Timing
import time
from timeit import timeit
day_sec = 60 * 60 * 24

# Fixing random seed. There are a lot of pseudorandom tests in this module, so
# it is essential that you take care to ensure that (a) there is no particular
# sensitivity to the value of this seed, (b) that the seed is not changed
# arbitrarily from test to test, or better yet both.
np.random.seed(433937620)


class TestFizzer(ut.TestCase):
    """
    Basic functionality testing for Fizzer class. Make sure that each of the
    basic methods is not obviously broken.
    """

    def setUp(self):
        # Set up a fizzer with time constant 10 seconds
        self.f = dummy_lab.P_Fizzer(time_const_sec=10)
        # Error tolerance
        self.epsilon = 0.001

    def test_decay_time(self):
        sleep_time_sec = 0.5
        c_init = self.f.get_carbonation()
        time.sleep(sleep_time_sec)
        c_final = self.f.get_carbonation()
        ratio = c_final/c_init
        expected_ratio = np.exp(-sleep_time_sec/self.f.time_const_sec)
        self.assertLess(abs(ratio - expected_ratio), self.epsilon)

    def test_decay_time_with_refresh(self):
        sleep_time_sec = 0.5
        c_init = self.f.get_carbonation()
        time.sleep(sleep_time_sec)
        self.f.refresh()
        time.sleep(sleep_time_sec)
        c_final = self.f.get_carbonation()
        ratio = c_final/c_init
        expected_ratio = np.exp(-2*sleep_time_sec/self.f.time_const_sec)
        self.assertLess(abs(ratio - expected_ratio), self.epsilon)

    def test_add_carbonation(self):
        c_init = self.f.get_carbonation()
        self.f.add_carbonation(2)
        c_final = self.f.get_carbonation()
        self.assertLess(c_final - c_init - 2, self.epsilon)

    def test_fizziness_slope(self):
        dc = 0.01
        self.f.carbonation = dc
        fizziness = self.f.get_fizziness()
        slope = fizziness/dc
        self.assertLess(abs(1 - slope), self.epsilon)

    def test_fizziness_saturation(self):
        dc = 1e6
        self.f.carbonation = dc
        fizziness = self.f.get_fizziness()
        self.assertLess(abs(1 - fizziness), self.epsilon)


class TestFizzmeter(ut.TestCase):
    """
    Basic functionality test for the Fizzmeter class. Make sure that each of
    the basic methods is not obviously broken.
    """

    def setUp(self):
        # Set up a fizzer with time constant 10 seconds
        self.f = dummy_lab.P_Fizzer(time_const_sec=10)
        # Set up a fizzmeter
        self.fm = dummy_lab.P_Fizzmeter(response_delay=0.0)
        # Error tolerance
        self.epsilon = 0.001

    def test_measure(self):
        """
        This one is super hacky and probably not a very reliable/solid test.
        """
        for i in range(5):
            time.sleep(0.2)
            fizziness = self.f.get_fizziness()
            measured_fizz = self.fm.measure(self.f)
            self.assertLess(abs(fizziness - measured_fizz),
                            (15*np.sqrt((i + 1)))*self.epsilon)


if __name__ == '__main__':
    ut.main()
