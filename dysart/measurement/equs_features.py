from feature import *
from messages import *
from mongoengine import *
import labber_feature
from Labber import ScriptTools
import equs_std.measurements as meas

from uncertainties import ufloat  # Return values with error bars!
from uncertainties.umath import *
import pint  # Units package
ureg = pint.UnitRegistry()

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
    """

    data = DictField(default={'fit_results': []})
    input_file = StringField(deault=meas.qubit_spec_file)

    @logged(message='measuring qubit spectrum...', end='')
    def __call__(self):
        print('input_file is ' + input_file)
        # TODO: other stuff
        super().__call__(self)
        # Raw data is now in output_file.
        # Fit that data and save the result in fit_results.


    @property
    @refresh
    def center_freq(self):
        """
        Return the best guess for the resonant frequency of the qubit's 0 <-> 1
        transition
        """
        return self.data['fit_results'][-1][]
        pass

    @property
    @refresh
    def linewidth(self):
        """
        Return the best guess for the HWHM (or more parameters, depending on the
        choice of fitting routine) of the qubit's 0 <-> 1 transition
        """
        # TODO
        pass


class QubitRabi(LabberFeature):
    """
    Feature object for a Rabi measurement on a qubit.
    """
    
    data = DictField(default={'fit_results': []})
    input_file = StringField(default=meas.qubit_rabi_file)

    @logged(message='measuring qubit rabi...', end='')
    def __call__(self):
        # TODO: other stuff
        super().__call__(self)
        # TODO: other stuff

    @property
    @refresh
    def frequency(self):
        """
        Return the Rabi frequency at the specified drive amplitude
        """
        # TODO
        pass

    @property
    @refresh
    def pi_time(self):
        """
        Return the time to perform an X gate at the specified drive amplitude
        """
        # TODO
        pass

    @property
    @refresh
    def pi_2_time(self):
        """
        Return the time to perform an H gate at the specified drive amplitude
        """
        # TODO
        pass

    @property
    @refresh
    def decay_time(self):
        """
        Return the Rabi decay time (or more parameters, depending on choice of
        fitting routine)
        """
        # TODO
        pass


class QubitRelaxation(LabberFeature):

    data = DictField(default={'fit_results': []})
    input_file = StringField(default='')

    @logged(message='measuring qubit relaxation...', end='')
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
