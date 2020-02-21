"""
EXPONENTIAL FITTING
===============================

Contains tools for fitting exponentially-decaying (or growing!) curves.
Essentially just a wrapper for lmfit.
"""

# TODO: add version with constant offset

import numpy as np
from lmfit import Model, CompositeModel
from lmfit.models import ExponentialModel, ConstantModel


def fit_exponential(x, y):
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
    exponential_fit_result = em.fit(
        y,
        x=x,
    )
    return exponential_fit_result
