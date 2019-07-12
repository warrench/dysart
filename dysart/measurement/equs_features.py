import json
from .fitting import spectra, rabi
from .feature import *
from .messages import logged
from mongoengine import *
from .labber_feature import LabberFeature
import Labber
from Labber import ScriptTools
from .equs_std import measurements as meas

from uncertainties import ufloat  # Return values with error bars!
from uncertainties.umath import *
import pint  # Units package
ureg = pint.UnitRegistry()


def no_recorded_result(self, level=0):
    """
    Expiration condition: is there a result?
    """
    return (('fit_results' not in self.data) or not self.data['fit_results'])


class ResonatorSpectrum(LabberFeature):
    pass


class Qubit:
    pass


class QubitSpectrum(LabberFeature):
    """
    Feature object for the spectrum of a qubit. For the purposes of an initial
    demo, this should really be just an abstraction of a polarization-vs-
    frequency plot.

    At the moment, there are a number of ugly hard-coded constants. As soon as
    this _works_, start fixing that first.

    The other incredibly ugly thing is the duplication of the log file: it's
    written once to the output file location, and once to the mongodb database.
    """
    call_message = 'measuring qubit spectrum'
    template_file_path = StringField(default=meas.qubit_spec_file)
    output_file_path = StringField(default=meas.qubit_spec_file_out)

    # Instrument names: hardcoded for now.
    pulse_generator = StringField(
        default='Multi-Qubit Pulse Generator - '
    )
    qubit_simulator = StringField(
        default='Single-Qubit Simulator - '
    )

    # Channel names: hardcoded for now.
    drive_frequency_channel = StringField(
        default='Single-Qubit Simulator - Drive frequency'
    )
    polarization_Z_channel = StringField(
        default='Single-Qubit Simulator - Polarization - Z'
    )

    def __call__(self, initiating_call=None):
        # Make the Labber measurement. Afterward, data is in self.data['log']
        super().__call__(initiating_call=initiating_call)

        # Fit that data and save the result in fit_results.
        last_entry = self.data['log'][-1]
        drive_frequency_data = last_entry[self.drive_frequency_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = spectra.fit_spectrum(drive_frequency_data, polarization_Z_data, 1)
        self.data['fit_results'].append(fit.params.valuesdict())

    @refresh
    def center_freq(self):
        """
        Return the best guess for the resonant frequency of the qubit's 0 <-> 1
        transition
        """
        last_fit = self.data['fit_results'][-1]
        center = last_fit['_0_center']
        return center

    @refresh
    def linewidth(self):
        """
        Return the best guess for the HWHM (or more parameters, depending on the
        choice of fitting routine) of the qubit's 0 <-> 1 transition
        """
        last_fit = self.data['fit_results'][-1]
        fwhm = last_fit['_0_fwhm']
        return fwhm/2


class QubitRabi(LabberFeature):
    """
    Feature object for a Rabi measurement on a qubit.
    """

    call_message = 'measuring qubit rabi'
    template_file_path = StringField(default=meas.qubit_rabi_file)
    output_file_path = StringField(default=meas.qubit_rabi_file_out)

    # Instrument names: hardcoded for now.
    pulse_generator = StringField(
        default='Multi-Qubit Pulse Generator - '
    )
    qubit_simulator = StringField(
        default='Single-Qubit Simulator - '
    )

    # Channel names: hardcoded for now.
    plateau_channel = StringField(
        default='Multi-Qubit Pulse Generator - Plateau'
    )
    polarization_Z_channel = StringField(
        default='Single-Qubit Simulator - Polarization - Z'
    )

    def __call__(self, initiating_call=None, **kwargs):
        # Obtain parameters from parents
        center_freq = self.parents['spec'].center_freq
        freq_channel = self.parents['spec'].drive_frequency_channel

        # RPC to labber and save data
        super().__call__(initiating_call=initiating_call,
                         freq_channel=center_freq)

        # Fit that data and save the result in fit_results.
        last_entry = self.data['log'][-1]
        plateau_data = last_entry[self.plateau_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = rabi.fit_rabi(plateau_data, polarization_Z_data)
        self.data['fit_results'].append(fit.params.valuesdict())

    @refresh
    def frequency(self):
        """
        Return the Rabi frequency at the specified drive amplitude
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['freq']

    @refresh
    def pi_time(self):
        """
        Return the time to perform an X gate at the specified drive amplitude
        """
        rabi_period = 1/self.frequency()
        return rabi_period/2

    @refresh
    def pi_2_time(self):
        """
        Return the time to perform an H gate at the specified drive amplitude
        """
        rabi_period = 1/self.frequency()
        return rabi_period/4

    @refresh
    def decay_rate(self):
        """
        Return the rate at which Rabi oscillations damp out
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['decay']

    @refresh
    def decay_time(self):
        """
        Return the Rabi decay time (or more parameters, depending on choice of
        fitting routine)
        """
        return 1/self.decay_rate()

    @refresh
    def phase(self):
        """
        Return the Rabi phase. Note that this can be nonzero, depending on the
        drive pulse shape.
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['phase']


class QubitRelaxation(LabberFeature):
    """
    Feature object for a T1 measurement on a qubit.
    (Actually, it might make sense for the same Feature class to track all the
    relaxation data. TBD.)
    """

    data = DictField(default={'fit_results': []})
    input_file = StringField(default='')
    output_file = StringField(default='')

    @logged(message='measuring qubit relaxation', end='\n')
    def __call__(self, **kwargs):
        # TODO: other stuff
        super().__call__(self)
        # TODO: other stuff

    @refresh
    def time_const(self):
        """
        Return the time for qubit polarization to decay to 1/e of its original
        value
        """
        # TODO
        pass
