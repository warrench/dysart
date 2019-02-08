from feature import *
from messages import *
from mongoengine import *
from labber_feature import *
from Labber import ScriptTools
from equs_std import measurements as meas

from uncertainties import ufloat # Return values with error bars!
from uncertainties.umath import *
import pint # Units package
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

    data = DictField(default={'fit_results': []})
    input_file = StringField(deault=meas.qubit_spec_file)

    @logged(message='measuring qubit spectrum...', end='')
    def call__(self):
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
        return self.data['fit_results'][-1]
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
