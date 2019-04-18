"""
Feature class for objects that interact with the Labber API.
Currently, the Labber interface is pretty naive, using the highest-level
API available. After I really get it "working," it would be nice to speed
things up by passing in-memory data buffers to reduce the number of writes,
etc.
"""

import os
import platform
import Labber
from mongoengine import *
from Labber import ScriptTools as st
from .feature import Feature
from .messages import cstr
from context import Context

# Set path to executable. This should be done not-here, but it needs to be put
# somewhere for now.

try:
    if platform.system() == 'Darwin':
        st.setExePath(os.path.join(os.path.sep, 'Applications', 'Labber'))
    elif platform.system() == 'Linux':
        st.setExePath(os.path.join(os.path.sep, 'usr', 'share', 'Labber', 'Program'))
    else:
        raise Exception('Unsupported platform!')
except Exception as e:
    pass

"""
Connect to default labber client
This behavior is all right for testing, but unexpected side effects like this
should probably be considered unacceptable in deployed code.
"""
if Context.labber_client:
    default_client = Context.labber_client
else:
    try:
        default_client = Labber.connectToServer('localhost')
        # For now, connect to insruments _here_, rather than on feature init.
        #for inst in client.getListOfInstrumentsString():
        #    client.connectToInstrument(inst)
    except Exception as e:
        default_client = None


class LabberFeature(Feature):
    """
    Feature class specialized for integration with Labber.
    Init takes the address of a labber server as an argument.

    """

    data = DictField(default={'log': [], 'fit_results': []})
    input_file_path = ''
    output_file_path = ''

    def __init__(self, labber_client=default_client, **kwargs):
        if default_client:
            self.labber_client = default_client
        super().__init__(**kwargs)

        # Deprecated by Simon's changes to Labber API?
        self.config = st.MeasurementObject(self.input_file_path,
                                           self.output_file_path)

    def __status__(self):
        """
        Verbose status string should contain recent fit results;
        or, if there are none, the empty string
        """
        def strrep_val(x):
            return str(x)

        s = ''
        if not self.data['fit_results']:
            return s

        last_fit = self.data['fit_results'][-1]
        max_len = max(map(len, last_fit.keys()))  # longest param name 
        for param in last_fit:
            s += cstr(param.ljust(max_len, ' '), 'italic') + ' : ' +\
                 strrep_val(last_fit[param]) + '\n'
        return s

        
    def __call__(self, **kwargs):
        """
        Thinly wrap the Labber API
        """
        # Handle the keyword arguments by appropriately modifying the config
        # file. This is sort of a stopgap; I'm not really sure it behaves how
        # we want in production.
        for key in kwargs:
            self.setValue(key, kwargs[key])

        # Make RPC to Labber!
        self.config.performMeasurement()

    def setValue(self, label, value):
        """
        Simply wrap the Labber API
        """
        self.config.updateValue(label, value)
        self.set_expired(True)

    @property
    def input_file(self):
        return self.config.sCfgFileIn

    @property
    def output_file(self):
        return self.config.sCfgFileIn

    def __expired__(self, level=0):
        """
        Default expiration condition: is there  a result?
        """
        return (('fit_results' not in self.data)
                 or not self.data['fit_results'])
