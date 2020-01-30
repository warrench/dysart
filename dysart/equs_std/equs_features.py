import json

from mongoengine import *
import Labber
from Labber import ScriptTools
from uncertainties import ufloat  # Return values with error bars!
from uncertainties.umath import *
import pint  # Units package

from dysart.feature import *
from dysart.labber.labber_feature import LabberFeature, result
from dysart.equs_std import measurements as meas
from dysart.equs_std.fitting import spectra, rabi
from dysart.messages.messages import logged
from dysart.services.streams import stdimg, stdmsg, stdfit

ureg = pint.UnitRegistry()


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
    """
    call_message = 'measuring qubit spectrum...'
    template_file_path = StringField(default=meas.qubit_spec_file)
    output_file_path = StringField(default=meas.qubit_spec_file_out)

    # Instrument names: hardcoded for now.
    pulse_generator = StringField(default='Multi-Qubit Pulse Generator - ')
    qubit_simulator = StringField(default='Single-Qubit Simulator - ')

    # Channel names: hardcoded for now.
    drive_frequency_channel = StringField(default='Single-Qubit Simulator - Drive frequency')
    polarization_Z_channel = StringField(default='Single-Qubit Simulator - Polarization - Z')

    @result
    def fit(self, index=-1):
        """
        Compute a best fit for the resonance data at this index.
        """
        last_entry = self.log_history[index][-1]
        drive_frequency_data = last_entry[self.drive_frequency_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = spectra.fit_spectrum(drive_frequency_data, polarization_Z_data, 1)
        stdmsg.write('I\'ve just done a fit!\n')
        return fit.params.valuesdict()

    @result
    def center_freq(self, index=-1):
        """
        Return the best guess for the resonant frequency of the qubit's 0 <-> 1
        transition
        """
        last_fit = self.fit(index)
        center = last_fit['_0_center']
        return center

    @result
    def linewidth(self, index=-1):
        """
        Return the best guess for the HWHM (or more parameters, depending on the
        choice of fitting routine) of the qubit's 0 <-> 1 transition
        """
        last_fit = self.fit(index)
        fwhm = last_fit['_0_fwhm']
        return fwhm / 2


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
        center_freq = self.parents['spec'].center_freq()
        freq_channel = self.parents['spec'].drive_frequency_channel

        # RPC to labber and save data
        super().__call__(initiating_call=initiating_call,
                         freq_channel=center_freq)

    @result
    def fit(self, index=-1):
        """
        Compute a best fit for Rabi oscillation data at this index.
        """

        # TODO: log_history should be a member of self, not of self.results.
        # self.results should be totally hidden.

        # fit results and enter them in self.data
        last_entry = self.log_history[index][-1]
        plateau_data = last_entry[self.plateau_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = rabi.fit_rabi(plateau_data, polarization_Z_data)
        return fit.params.valuesdict()

    @result
    def frequency(self, index=-1):
        """
        Return the Rabi frequency at the specified drive amplitude
        """
        last_fit = self.fit(index)
        return last_fit['freq']

    @result
    def pi_time(self, index=-1):
        """
        Return the time to perform an X gate at the specified drive amplitude
        """
        rabi_period = 1 / self.frequency(index)
        return rabi_period / 2

    @result
    def pi_2_time(self, index=-1):
        """
        Return the time to perform an H gate at the specified drive amplitude
        """
        rabi_period = 1 / self.frequency(index)
        return rabi_period / 4

    @result
    def decay_rate(self, index=-1):
        """
        Return the rate at which Rabi oscillations damp out
        """
        last_fit = self.fit(index)
        return last_fit['decay']

    @result
    def decay_time(self, index=-1):
        """
        Return the Rabi decay time (or more parameters, depending on choice of
        fitting routine)
        """
        return 1/self.decay_rate(index)

    @result
    def phase(self, index=-1):
        """
        Return the Rabi phase. Note that this can be nonzero, depending on the
        drive pulse shape.
        """
        last_fit = self.fit(index)
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

    @result
    def time_const(self):
        """
        Return the time for qubit polarization to decay to 1/e of its original
        value
        """
        # TODO
        pass
