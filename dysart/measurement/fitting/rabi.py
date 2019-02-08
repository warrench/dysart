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


def fit_rabi(x, y):
    """
    Fits a data set to an exponential with a constant offset, returns best-fit
    parameters: `amplitude`, `decay,` and `c`

    Args:
        x (numpy.ndarray): A one-dimensional real-valued numpy array, the independent variable
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the dependent variable.
    Returns:
        type: lmfit.model.ModelResult

    """
    em = ExponentialModel()
    si =
    rabi_model = em * si
    rabi_fit_result = rabi_model.fit(
        y,
        x=x,
    )

    return rabi_fit_result

class SinusoidalModel(Model):
    """
    An lmfit model representing a decaying sinusoid.
    """

    def __init__(self, independent_vars['x'], prefix='', nan_policy='raise',
                 name=None, **kwargs):

        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy,
                       'independent_vars' = independent_vars})
