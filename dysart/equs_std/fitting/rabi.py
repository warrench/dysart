"""
RABI FITTING
===============================

Contains tools for fitting decaying Rabi oscillations.
"""

# TODO: add version with constant offset;
#       multiple decay envelopes

import numpy as np
from lmfit import Model, CompositeModel
from lmfit.models import ExponentialModel


def decaying_sinusoid(x, c, amp, freq, phase, decay):
    return c + amp * np.exp(- x * decay) * np.cos(2 * np.pi * freq * x + phase)

# Parameter guess functions are as dumb as possible for now. Leave this until
# something breaks. Worse is better.


def guess_c(x, y):
    return np.mean(y)


def guess_amp(x, y):
    abs_amp = (np.max(y) - np.min(y))/2
    if np.argmax(y) < np.argmin(y):
        return abs_amp
    else:
        return -abs_amp


def guess_freq(x, y):
    amin = np.argmin(y)
    amax = np.argmax(y)
    pi_time = np.abs(x[amin] - x[amax])
    return 1/(2 * pi_time)


def guess_phase(x, y):
    return 0


def guess_decay(x, y):
    return 1/x[-1]


def fit_rabi(x, y):
    """
    Args:
        x (numpy.ndarray): A one-dimensional real-valued numpy array, the independent variable
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the dependent variable.
    Returns:
        type: lmfit.model.ModelResult

    """
    c_guess = guess_c(x, y)
    amp_guess = guess_amp(x, y)
    freq_guess = guess_freq(x, y)
    phase_guess = guess_phase(x, y)
    decay_guess = guess_decay(x, y)

    model = Model(decaying_sinusoid)
    rabi_fit_result = model.fit(y, x=x, c=c_guess, amp=amp_guess, freq=freq_guess,
                                        phase=phase_guess, decay=decay_guess)

    return rabi_fit_result