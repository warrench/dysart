import json
from fitting import spectra, rabi
from feature import *
from messages import logged
from mongoengine import *
import labber_feature
import Labber
from Labber import ScriptTools
import equs_std.measurements as meas

from uncertainties import ufloat  # Return values with error bars!
from uncertainties.umath import *
import pint  # Units package
ureg = pint.UnitRegistry()


# Question for Simon: this interface actually doesn't seem to work.
# On being passed a .json file, load_scenario_as_dict raises
# No such file or directory: 'path/to/file.labber'.
"""
json/binary <-> dict syntax
-------------------------------------------------------------

import Labber

d = Labber.ScriptTools.load_scenario_as_dict('testfile.json')
print(d)
Labber.ScriptTools.save_scenario_as_binary(d, 'test_out')
Labber.ScriptTools.save_scenario_as_json(d, 'test_out_json')
"""


def no_recorded_result(self, level=0):
    """
    Expiration condition: is there a result?
    """
    return (('fit_results' not in self.data) or not self.data['fit_results'])


class ResonatorSpectrum(labber_feature.LabberFeature):
    pass


class Qubit:
    pass


class QubitSpectrum(labber_feature.LabberFeature):
    """
    Feature object for the spectrum of a qubit. For the purposes of an initial
    demo, this should really be just an abstraction of a polarization-vs-
    frequency plot.

    At the moment, there are a number of ugly hard-coded constants. As soon as
    this _works_, start fixing that first.

    The other incredibly ugly thing is the duplication of the log file: it's
    written once to the output file location, and once to the mongodb database.
    """

    input_file_path = StringField(default=meas.qubit_spec_file)
    output_file_path = StringField(default=meas.qubit_spec_file_out)
    # Channel names: hardcoded for now.
    drive_frequency_channel = StringField(
        default='Single-Qubit Simulator - Drive frequency')
    polarization_Z_channel = StringField( 
        default='Single-Qubit Simulator - Polarization - Z')
    #def __init__(self):
    #    super().__init__()

    @logged(message='measuring qubit spectrum...', end='\n')
    def __call__(self, level=0):
        # TODO: other stuff
        super().__call__()
        # Raw data is now in output_file. Load it into self.data.
        log_file = Labber.LogFile(self.output_file_path)
        num_entries = log_file.getNumberOfEntries()
        self.data['log'].append(log_file.getEntry(num_entries - 1))
        # Fit that data and save the result in fit_results.
        last_entry = self.data['log'][-1]
        drive_frequency_data = last_entry[self.drive_frequency_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = spectra.fit_spectrum(drive_frequency_data, polarization_Z_data, 1)
        self.data['fit_results'].append(fit.params.valuesdict())

    @property
    @refresh
    def center_freq(self):
        """
        Return the best guess for the resonant frequency of the qubit's 0 <-> 1
        transition
        """
        last_fit = self.data['fit_results'][-1]
        center = last_fit['_0_center']
        return center

    @property
    @refresh
    def linewidth(self):
        """
        Return the best guess for the HWHM (or more parameters, depending on the
        choice of fitting routine) of the qubit's 0 <-> 1 transition
        """
        last_fit = self.data['fit_results'][-1]
        fwhm = last_fit['_0_fwhm']
        return fwhm


class QubitRabi(labber_feature.LabberFeature):
    """
    Feature object for a Rabi measurement on a qubit.
    """

    input_file_path = StringField(default=meas.qubit_rabi_file)
    output_file_path = StringField(default=meas.qubit_rabi_file_out)
    # Channel names: hardcoded for now.
    plateau_channel = StringField(
        default='Multi-Qubit Pulse Generator - Plateau')
    polarization_Z_channel = StringField( 
        default='Single-Qubit Simulator - Polarization - Z')
    #def __init__(self):
    #    super().__init__()

    @logged(message='measuring qubit rabi...', end='\n')
    def __call__(self, level=0):
        # TODO: other stuff
        super().__call__()
        # Raw data is now in output_file. Load it into self.data.
        log_file = Labber.LogFile(self.output_file_path)
        num_entries = log_file.getNumberOfEntries()
        self.data['log'].append(log_file.getEntry(num_entries - 1))
        # Fit that data and save the result in fit_results.
        last_entry = self.data['log'][-1]
        plateau_data = last_entry[self.plateau_channel]
        polarization_Z_data = last_entry[self.polarization_Z_channel]
        fit = rabi.fit_rabi(plateau_data, polarization_Z_data)
        self.data['fit_results'].append(fit.params.valuesdict())

    @property
    @refresh
    def frequency(self):
        """
        Return the Rabi frequency at the specified drive amplitude
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['freq']

    @property
    @refresh
    def pi_time(self):
        """
        Return the time to perform an X gate at the specified drive amplitude
        """
        rabi_period = 1/self.frequency
        return rabi_period/2
        

    @property
    @refresh
    def pi_2_time(self):
        """
        Return the time to perform an H gate at the specified drive amplitude
        """
        rabi_period = 1/self.frequency
        return rabi_period/4

    @property
    @refresh
    def decay_rate(self):
        """
        Return the rate at which Rabi oscillations damp out
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['decay']

    @property
    @refresh
    def decay_time(self):
        """
        Return the Rabi decay time (or more parameters, depending on choice of
        fitting routine)
        """
        return 1/self.decay_rate
    
    @property
    @refresh
    def decay_time(self):
        """
        Return the Rabi phase. Note that this can be nonzero, depending on the
        drive pulse shape.
        """
        last_fit = self.data['fit_results'][-1]
        return last_fit['phase']


class QubitRelaxation(labber_feature.LabberFeature):
    """
    Feature object for a T1 measurement on a qubit.
    (Actually, it might make sense for the same Feature class to track all the
    relaxation data. TBD.)
    """

    data = DictField(default={'fit_results': []})
    input_file = StringField(default='')
    output_file = StringField(default='')

    @logged(message='measuring qubit relaxation...', end='\n')
    def __call__(self):
        # TODO: other stuff
        super().__call__(self)
        # TODO: other stuff

    @property
    @refresh
    def time_const(self):
        """
        Return the time for qubit polarization to decay to 1/e of its original
        value
        """
        # TODO
        pass
