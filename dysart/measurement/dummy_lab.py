"""
Dummy device code for running and testing DySART measurement infrastructure.

Defines classes Fizzer, Fizzmeter and Carbonator, which represent a carbonated
liquid whose level of fizziness is monitored by a fizzmeter and controlled with
a feedback system.
"""

import time
import numpy as np
day_sec = 60 * 60 * 24


def shifted_logistic(x):
    return 2 / (1 + np.exp(-2 * x)) - 1


class Device:

    def __init__(self, decal_rate=1e-3, cal_delay=1):
        """
        Initializes device by setting decalibration rate in units/sqrt(second)
        and setting the cal time by a refresh() call.
        """
        self.decal_rate = decal_rate  # Decalibration rate in 1/second
        self.cal_delay = cal_delay
        # Call base-class refresh without ambiguity
        Device.refresh(self, time.time())

    def refresh(self, t_new):
        """
        Resets the calibration time
        """
        self.cal_time = t_new


class Fizzer(Device):
    """
    A cool glass of fizzy substance. Maintains carbonation level and fizziness,
    updating every time a public method is called.
    """

    def __init__(self, carbonation=1, time_const_sec=1):
        """
        Initializes Fizzer with time constant 1 day
        """
        self.fizzmeter = None
        self.carbonation = carbonation
        self.time_const_sec = time_const_sec
        super().__init__()

    def refresh(self):
        """
        Update stale values
        """
        t_new = time.time()
        dt = t_new - self.cal_time
        carbonation = self.carbonation*np.exp(-dt/self.time_const_sec)
        self.carbonation = carbonation
        super().refresh(t_new)

    def add_carbonation(self, carbonation):
        self.carbonation += carbonation
        self.refresh()

    def get_carbonation(self):
        self.refresh()
        return self.carbonation

    def get_fizziness(self):
        """
        Fizziness is some function of carbonation that's linear at low levels,
        and saturates to 1 ("most fizzy!") at high carbonation. This is not
        a physically or chemically accurate model.j
        """
        carbonation = self.get_carbonation()
        fizziness = shifted_logistic(carbonation)
        return fizziness


class Fizzmeter(Device):
    """
    Measures the fizziness of a Fizzer. Measurement bias is controlled by
    decal_rate parameter, which must be routinely calibrated away.
    """

    def __init__(self, response_delay=0.25, uncertainty=0.0001,
                 decal_time_sec=1000):
        self.fizzer = None
        self.measurements = []
        self.response_delay = response_delay
        self.uncertainty = uncertainty
        self.bias = 0
        super().__init__(decal_rate=1 / decal_time_sec)

    def refresh(self):
        """
        Update stale values
        """
        t_new = time.time()
        dt = t_new - self.cal_time
        self.bias += np.random.normal(0, np.sqrt(dt * self.decal_rate))
        super().refresh(t_new)

    def attach_fizzer(self, fizzer):
        """
        Put a fizzer into the fizzmeter to measure it!
        Return error code 1 if fizzer is in another fizzmeter.
        """
        if fizzer.fizzmeter is not None:
            return 1
        if self.fizzer is not None:
            self.fizzer.fizzmeter = None
            self.fizzer = fizzer
            self.fizzer.fizzmeter = self
        return 0

    def remove_fizzer(self):
        """
        Take out the fizzer. Return error code 1 if there is none.
        """
        if self.fizzer is None:
            return 1
        self.fizzer.fizzmeter = None
        self.fizzer = None
        return 0

    def measure(self):
        """
        Adds the fizziness of a Fizzer to measurement list, delayed by response
        time, plus added noise. Return error code 1 if there is no fizzer.
        """
        if self.fizzer is None:
            return 1
        time.sleep(self.response_delay)
        self.refresh()
        noise = np.random.normal(0, self.uncertainty)
        self.measurements.append(self.fizzer.get_fizziness() +
                                 self.bias + noise)
        return 0

    def calibrate(self):
        time.sleep(self.cal_delay)
        self.bias = 0
        self.refresh()


class Carbonator(Device):

    def __init__(self, response_delay=0.5, uncertainty=0.01):
        super().__init__()
        self.response_delay = response_delay
        self.uncertainty = uncertainty

    def refresh(self):
        """
        Update stale values
        """
        t_new = time.time()
        super().refresh(t_new)

    def get_uncertainty(self):
        self.refresh()
        return self.uncertainty

    def carbonate(self, fizzer, carbonation):
        noise = np.random.normal(0, self.get_uncertainty())


class Spinner(Device):

    def __init__(self):
        super().__init__()

    def refresh(self):
        """
        Update stale values
        """
        pass


class Spinmeter(Device):

    def __init__(self):
        super().__init__()

    def refresh(self):
        """
        Update stale values
        """
        pass


class Buzzer(Device):

    def __init__(self):
        pass

    def get_buzziness(self):
        pass


class Buzzmeter(Device):

    def __init__(self):
        pass
