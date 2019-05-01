"""
Feature class for objects that interact with the Labber API.
Currently, the Labber interface is pretty naive, using the highest-level
API available. After I really get it "working," it would be nice to speed
things up by passing in-memory data buffers to reduce the number of writes,
etc.
"""

import os
import numpy as np
"""
import json
from parsing.h5_handling import import_h5
from parsing.json_encoder import dump_to_json_numpy_text
from parsing.json_encoder import load_from_json_numpy_text
"""
from parsing.labber_serialize import load_labber_scenario_as_dict
from parsing.labber_serialize import save_labber_scenario_from_dict
import platform
import tempfile
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
    # Deserialized template file
    template = DictField(default={})
    template_diffs = DictField(default={})
    template_file_path = ''
    output_file_path = ''

    def __init__(self, labber_client=default_client, **kwargs):
        if default_client:
            self.labber_client = default_client

        super().__init__(**kwargs)
        # Check to see if the template file has been saved in the DySART database;
        # if not, deserialize the .hdf5 on disk.
        if not self.template:
            self.deserialize_template()

        # Set nondefault parameters
        #for kwarg in kwargs:
        #    self.set_value(kwarg, kwargs[kwarg])

        # Deprecated by Simon's changes to Labber API?
        self.config = st.MeasurementObject(self.template_file_path,
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

    def __call__(self, initiating_call=None, **kwargs):
        """
        Thinly wrap the Labber API
        """
        # Handle the keyword arguments by appropriately modifying the config
        # file. This is sort of a stopgap; I'm not really sure it behaves how
        # we want in production.
        for key in kwargs:
            self.set_value(key, kwargs[key])

        # Make RPC to Labber!
        # set the input file.
        self.config.sCfgFileIn = self.emit_labber_input_file()
        self.config.performMeasurement()

    def deserialize_template(self):
        """
        Unmarshall the template file.
        """
        
        """
        # Check if it's an .hdf5 or .json: for now, do this naively
        # by looking at the file extension.
        if self.template_file_path.endswith('.hdf5'):
            self.template = import_h5(self.template_file_path)
        elif self.template_file_path.endswith('.json'):
            with open('self.template_file_path', 'r') as f:
                self.template = json.loads(f.read())
        """
        self.template = load_labber_scenario_as_dict(self.template_file_path,
                            decode_complex=False)

    def set_value(self, label, value):
        """
        Simply wrap the Labber API
        """

        # Explicit type-checking (and behavior dependent on the result) seems really
        # not in the spirit of duck-typing.
        # I'm actually really not super happy with this, but it's what people asked for.
        # TODO Maybe I should argue against it.
        if isinstance(value, list):
            canonicalized_value = value
        elif isinstance(value, np.ndarray):
            canonicalized_value = list(value)
        elif isinstance(value, tuple):
            canonicalized_value = list(np.linspace(*value))
        #else isinstance(value, (int, float, complex)):
        #    canonicalized_value = value
        #    self.config.updateValue(label, canonizalized_value)

        self.template_diffs[label] = canonicalized_value
        self.set_expired(True)
    
    def merge_configs(self):
        """
        TODO write a real docstring here
        Merge the template and diff configuration dictionaries, in preparation
        for serialization
        """
        # TODO actually do it. For now, just return the tamplate.
        return self.template

    def emit_labber_input_file(self):
        """
        TODO write a real docstring here
        Write a temporary .hdf5 input for Labber to consume by attempting to
        combine the template and template_diffs. Under Unix this gets written
        to a tempfile in the enclosing /proc subtree. Windows should use a
        spooled file, which I think "really exists" on that platform.

        Returns a path to the resulting tempfile. 

        TODO UPDATE: the /proc tree doesn't exist on MacOS. Must use a
        different interface on that platform.
        """
        if 'temp' in dir(self) and not self.temp.closed:
            self.temp.close()

        if platform.system() == 'Linux':
            pid = os.getpid()
            temp = tempfile.NamedTemporaryFile(
                mode='w+b', dir='/tmp', suffix='.labber')
            fd = temp.fileno()
            fp = temp.name
            # Merge the template and diffs; write to the tempfile
            save_labber_scenario_from_dict(fp, self.merge_configs())
            #temp.write(dump_to_json_numpy_text(self.merge_configs()))
            # fp = os.path.join(os.sep, 'proc', str(pid), 'fd', str(fd))
        elif platform.system() == 'Darwin':
            raise Exception('Unsupported operationn on this platform')
        elif platform.system() == 'Windows':
            raise Exception('Unsupported operationn on this platform')
        
        # Hold onto this temp file so it doesn't get closed by garbage
        # collection. (Is this the best way to do this?)
        self.temp = temp
        return fp


    @property
    def diffs(self):
        """
        TODO write a real docstring here
        TODO write a real method here
        Pretty-print all the user-specified configuration parameters that
        differ from the template file
        """
        print(self.template_diffs)

    @property
    def input_file(self):
        return self.config.sCfgFileIn

    @property
    def output_file(self):
        return self.config.sCfgFileIn

    def __expired__(self, call_record=None):
        """
        Default expiration condition: is there  a result?
        """
        return (('fit_results' not in self.data)
                 or not self.data['fit_results'])
