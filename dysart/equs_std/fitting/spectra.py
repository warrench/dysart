import numpy as np
from lmfit import Model, CompositeModel
import lmfit.models as models
import operator

# SPECTRUM FITTING #
# Contains tools for fitting resonance spectra. A lot of the method implementations
# in this test version are nearly as naive as possible. Since this is a module that is
# worth getting Right with a capital 'R', and since a lot of people have reinvented
# this wheel before, it would behoove me to review prior art. In particular, it's likely
# that there are standard algorithms and hypothesis tests that are well-known in
# the NMR, HEP, and astronomy communities. Check out any CERN docs on spectrum-fitting;
# they're probably the gold standard. In short, this is abeing written to be deprecated.

# TODO: Review and fix redundancy between SpectrumModel class and spectrum model
# building in fit_spectrum. DRY it out!
# TODO: SpectrumModel constructor is ugly.
# TODO: spectrum_fit is really quite slow.
# TODO: this actually can be rewritten more intelligently.
# Make the guessing functions the guess method of the SpectrumModel class.

# Global definitions
RESONANCE_MODEL = models.ConstantModel() + models.LorentzianModel()


# Classes

class SpectrumModel(CompositeModel):
    """
    An lmfit Model representing a spectrum of finitely-many Lorentzian resonances
    with parameters ``c'', ``_i_amplitude``, ``_i_center``, ``_i_sigma`` for
    i = 0, 1, ..., num_resonances - 1

    Args:
        num_resonances (int): The number of Lorentzian resonances.

    """

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise',
                 name=None, num_resonances=1, **kwargs):

        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy,
                       'independent_vars': independent_vars})

        # This method might be a little bit kludgy. I'm guessing there's a more
        # pythonic way to achieve the same end.
        constant_model = models.ConstantModel(**kwargs)

        # Creates a sequence of LorentzianModel objects with prefixes `_i_`, for
        # i = 0, 1, ..., num_resonances - 1, and sums them.

        # TODO: is there a more elegant way to achieve this behavior? CompositeModel
        # doesn't accept null operands; but maybe there's a better way.
        resonance_model = Model(lambda x: 0)
        for i in range(num_resonances):
            lorentzian_model = models.LorentzianModel(**kwargs)
            lorentzian_model.prefix = '_' + str(i) + '_'
            resonance_model += lorentzian_model

        super(SpectrumModel, self).__init__(constant_model, resonance_model, operator.add, **kwargs)

    def guess(self, data, **kwargs):
        """Estimate initial model parameter values from data"""
        # TODO: implement method
        return

    # Set docblocks to the standard ones for Model classes.
    __init__.__doc__ = models.COMMON_INIT_DOC
    guess.__doc__ = models.COMMON_GUESS_DOC


# Auxiliary functions
def guess_baseline(y):
    """
    Given an array y, guesses the offset level.
    This naive implementation is simply a wrapper for numpy.max.

    Args:
        y (type): Description of parameter `y`.

    Returns:
        type: Description of returned object.

    """

    return np.max(y)


def guess_peak_index(y):
    """
    Given an array y, guesses the center frequency of a resonance.
    This naive implementatin is simply a wrapper for numpy.argmin.

    Args:
        y (numpy.ndarray): A one-dimensional real-valued numpy array.

    Returns:
        int: Index of the center frequency guess.

    """

    return np.argmin(y)


def unbounded_binary_search(y, threshold_value, forward_sense=True, search_interval_guess=1):
    """
    Given an approximately monotonic array, seeks and returns the approximate
    first index at which a specified threshold value is exceeded.

    Args:
        y (numpy.ndarray): A one-dimensional real-valued numpy array.
        threshold_value (numpy.float64): Threshold value to be searched for.
        forward_sense (bool): If true, array is traversed in the forward
        direction. If false, in the reverse direction.
        search_interval_guess (int): size of the first search interval tried.

    Returns:
        int: Approximate first index at which the threshold value is exceeded.

    """

    return


def recursive_linear_search(y, threshold_value, forward_sense=True, step_size=64):
    """
    Given an approximately monotonic array, seeks and returns the approximate
    first index at which a specified threshold value is exceeded.

    Args:
        y (numpy.ndarray): A one-dimensional real-valued numpy array.
        threshold_value (numpy.float64): Threshold value to be searched for.
        forward_sense (bool): If true, array is traversed in the forward
        direction. If false, in the reverse direction.
        step_size (int): Number of indices over which the search steps at once.

    Returns:
        int: Approximate first index at which the threshold value is exceeded.

    """

    # TODO: This is hacky and not terribly pythonic, and should be cleaned up.
    # I think there are also some off-by-one errors in here.
    # TODO: Write (more) tests.

    # Iterate over the array to find the first subinterval where the threshold is exceeded
    step = 0
    subinterval = np.array([])
    if forward_sense:
        while (step * step_size < len(y)) and (y[step * step_size] <= threshold_value):
                step += 1
        subinterval = y[(step - 1) * step_size:min(step * step_size, len(y))]
    else:
        while (step * step_size < len(y)) and (y[(len(y) - 1) - step * step_size] <= threshold_value):
                step += 1
        subinterval = y[max((len(y) - 1) - step * step_size, 0):len(y) - (step - 1) * step_size]

    # Exit in terminal case
    if step_size == 1:
        return step

    # Recurse over the identified subinterval
    recursion_step = recursive_linear_search(
        subinterval,
        threshold_value, forward_sense,
        int(np.floor(np.sqrt(step_size))))

    # Calculate and return the exact index
    return (step - 1) * step_size + recursion_step


def guess_hwhm(x, y, peak_index_guess, baseline_guess, initial_step_size=64):
    """
    Given an array and guesses for the vertical offset and location of a resonance,
    estimates the half-width-at-half-max linewidth of that resonance.

    Assumes that x is linearly spaced.

    Args:
        x (numpy.ndarray): A one-dimensional real-valued numpy array, the frequency domain variable.
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the signal variable.
        peak_index_guess (int): Estimated resonance location.
        baseline_guess (numpy.float64): Estimated vertical offset.
        initial_step_size (int): Coarseness of initial search.

    Returns:
        type: Description of returned object.

    """

    # Estimate where the resonance reaches 1/2 max on left-hand shoulder
    left_shoulder_index_guess = recursive_linear_search(
        y[:peak_index_guess],
        # TODO: shouldn't this be -, and why doesn't it work with -?
        (baseline_guess - y[peak_index_guess]) / 2,
        False,
        initial_step_size)

    # Estimate where the resonance reaches 1/2 max on right-hand shoulder
    right_shoulder_index_guess = recursive_linear_search(
        y[peak_index_guess:],
        # TODO: shouldn't this be -, and why doesn't it work with -?
        (baseline_guess - y[peak_index_guess]) / 2,
        True,
        initial_step_size)

    # Unsigned average of these two estimates
    hwhm_index_guess = int(np.round((right_shoulder_index_guess + left_shoulder_index_guess) / 2))

    return np.abs(x[hwhm_index_guess] - x[0])


def guess_amplitude(y, peak_index_guess, baseline_guess, hwhm_guess):
    """
    Coarsely estimates the amplitude of a Lorentzian resonance.

    Args:
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the signal variable.
        peak_index_guess (int): Guess of the index of Lorentzian resonance.
        baseline_guess (numpy.float64): Guess of the signal background offset.

    Returns:
        type: Description of returned object.

    """

    return np.pi * hwhm_guess * (y[peak_index_guess] - baseline_guess)


# Core functions

def find_resonance(x, y):
    """
    Seeks a candidate Lorentzian resonance in data, performs a least-squares
    regression and returns best-fit parameters.

    Args:
        x (numpy.ndarray): A one-dimensional real-valued numpy array, the frequency domain variable.
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the signal variable.

    Returns:
        type: lmfit.model.ModelResult

    """

    peak_index_guess = guess_peak_index(y)
    baseline_guess = guess_baseline(y)
    hwhm_guess = guess_hwhm(x, y, peak_index_guess, baseline_guess, initial_step_size=1)
    amplitude_guess = guess_amplitude(y, peak_index_guess, baseline_guess, hwhm_guess)
    resonance_fit_result = RESONANCE_MODEL.fit(
        y,
        x=x,
        amplitude=amplitude_guess,
        center=x[peak_index_guess],
        sigma=hwhm_guess,
        c=baseline_guess)
    return resonance_fit_result


def remove_resonance_from_data(y, resonance_fit_result):
    """
    Subtracts a best-fit Lorentzian resonance from a data series.

    Args:
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the signal variable.
        resonance_fit_result (lmfit.model.ModelResult): fit result to an identified resonance.

    Returns:
        type: Description of returned object.

    """

    return y - resonance_fit_result.best_fit


def fit_spectrum(x, y, num_resonances):
    """
    Iteratively identifies canditate resonances, performs a least-squares regression,
    and removes the identified resonance from the data. This function is `dumb'
    in the sense that it abdicates responsibility for hypothesis testing.

    Having both find_resonance and find_resonances might be a bad naming convention.

    Args:
        x (numpy.ndarray): A one-dimensional real-valued numpy array, the frequency domain variable.
        y (numpy.ndarray): A one-dimensional real-valued numpy array, the signal variable.
        num_resonances (type): Description of parameter `num_resonances`.

    Returns:
        type: Description of returned object.

    """

    # First pass, picking out resonances one-by-one.
    # Build model for whole spectrum along the way.
    resonance_fit_results = []
    spectrum_model = models.ConstantModel()
    y_copy = y
    for i in range(num_resonances):
        resonance_fit_results.append(find_resonance(x, y_copy))
        y_copy = remove_resonance_from_data(y_copy, resonance_fit_results[-1])

        # Make a Lorentzian model for each resonance, with prefixes for proper name-mangling.
        lorentzian_model = models.LorentzianModel()
        lorentzian_model.prefix = '_' + str(i) + '_'
        spectrum_model += lorentzian_model

    # Sum up all the offsets from each resonance model
    net_offset = sum(resonance_fit_results[i].params['c'].value for i in range(num_resonances))
    # Build a dict of all the Lorentzian parameters
    lorentzian_params = {}
    for i in range(num_resonances):
        lorentzian_params['_' + str(i) + '_amplitude'] = resonance_fit_results[i].params['amplitude'].value
        lorentzian_params['_' + str(i) + '_center'] = resonance_fit_results[i].params['center'].value
        lorentzian_params['_' + str(i) + '_sigma'] = resonance_fit_results[i].params['sigma'].value
    # And re-adjust the best fit.
    spectrum_fit_result = spectrum_model.fit(y, x=x, c=net_offset, **lorentzian_params)
    return spectrum_fit_result


def resonance_rejection_filter(resonance):
    """
    Applies a criterion to reject some resonances as non-signal artifacts.
    This implementation is pure filler, and simply rejects resonances with
    half-width at half max less than ______.

    Args:
        resonance (type): Description of parameter `resonance`.

    Returns:
        type: Description of returned object.

    """
    return
