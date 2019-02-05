"""
Feature class for objects that interact with the Labber API.
"""
import os
import platform
import Labber
from Labber import ScriptTools
from feature import Feature

# Set path to executable. This should be done not-here, but it needs to be put
# somewhere for now.
try:
    if platform.system() == 'Darwin':
        ScriptTools.setExePath(os.path.abspath('/Applications/Labber'))
    else if platform.system() == 'Linux':
        pass
    else:
        raise Exception('Unsupported platform!')
except Exception as e:
    pass

class LabberFeature(Feature):

    input_file = ''

    def __init__(self, output_file):
        self.config = ScriptTools.MeasurementObject(self.input_file, output_file)

    def __call__(self, **kwargs):
        """
        Thinly wrap the Labber API
        """
        # Handle the keyword arguments by appropriately modifying the config
        # file. This is sort of a stopgap; I'm not really sure it behaves how
        # we want in production.
        for key in kwargs:
            self.setValue(key, kwargs[key])

        self.config.performMeasurement()

    def setValue(self, label, value):
        """
        Simply wrap the Labber API
        """
        self.config.updateValue('label', value)

    @property
    def input_file(self):
        return self.config.sCfgFileIn

    @property
    def output_file(self):
        return self.config.sCfgFileIn
