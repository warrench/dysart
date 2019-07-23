"""
Feature class for objects that interact with the Labber API.
Currently, the Labber interface is pretty naive, using the highest-level
API available. After I really get it "working," it would be nice to speed
things up by passing in-memory data buffers to reduce the number of writes,
etc.
"""

import copy
import os
import platform
import tempfile
from typing import Optional  # gotta have those maybe types
from warnings import warn

import numpy as np
from mongoengine import *
import Labber
from Labber import ScriptTools as st

from dysart.labber.labber_serialize import load_labber_scenario_as_dict
from dysart.labber.labber_serialize import save_labber_scenario_from_dict
from dysart.feature import Feature, CallRecord
from dysart.messages.messages import cstr

# Set path to executable. This should be done not-here, but it needs to be put
# somewhere for now.

try:
    if platform.system() == 'Darwin':
        st.setExePath(os.path.join(os.path.sep, 'Applications', 'Labber'))
    elif platform.system() == 'Linux':
        st.setExePath(os.path.join(os.path.sep, 'usr', 'share', 'Labber', 'Program'))
    elif platform.system() == 'Windows':
        pass
    else:
        raise Exception('Unsupported platform!')
except Exception as e:
    pass

"""
Register default labber client. Using a global variable is maybe all right for
testing, but this is a pretty dangerous practice in production code.
"""
if globals().get('dyserver'):
    default_client = dyserver.labber_client
else:
    default_client = None


class LabberFeature(Feature):
    """
    Feature class specialized for integration with Labber.
    Init takes the address of a labber server as an argument.

    """

    # Deserialized template file
    template = DictField(default={})
    template_diffs = DictField(default={})
    template_file_path = ''
    output_file_path = ''
    MAX_LOG_INDEX = 1000

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
        self.data = {'log': [], 'fit_results': []}

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
        self.labber_input_file = self.emit_labber_input_file()
        self.labber_output_file = self.next_log_name()
        self.config.performMeasurement()
        # Clean up: tempfile no longer needed.
        os.unlink(self.labber_input_file)

        # Raw data is now in output_file. Load it into self.data.
        log_file = Labber.LogFile(self.labber_output_file)
        self.data['log'].append({})
        self.data['log'][-1]['log_name'] = self.last_log_name()
        self.data['log'][-1]['entries'] = []
        for i in range(log_file.getNumberOfEntries()):
            self.data['log'][-1]['entries'].append(log_file.getEntry(i))

    def _log_index(self, log_name: str) -> int:
        """
        get the index at the end of a Labber logfile name
        """
        try:
            return int(os.path.splitext(log_name)[0].split('_')[-1])
        except Exception:  # e.g. no logfile with integral suffix, or no file
            return 0

    def last_log_name(self) -> Optional[str]:
        """
        return the base name of the last-incremented log file
        """
        (output_dir, output_fn) = os.path.split(self.output_file_path)

        log_names = [fn for fn in os.listdir(output_dir)
                        if fn.startswith(os.path.splitext(output_fn)[0])]
        if log_names:
            last_log = max(log_names, key=self._log_index)
            return os.path.join(output_dir, last_log)
        else:
            return None

    def log_name(self, index: Optional[int]=None) -> str:
        """
        return a valid log name given a log index.
        """
        if index is not None:
            (base, ext) = self.output_file_path.split('.')
            return base + '_' + str(index) + '.' + ext
        return self.log_name(index=0)

    def next_log_name(self) -> str:
        """
        get the last log name, increment it, and return a valid log name.
        If there are no logs, return the name of log 1.
        """
        last_log = self.last_log_name()
        last_index = self._log_index(last_log)
        if last_index:
            if last_index >= self.MAX_LOG_INDEX:
                warn('log index {} exceeds MAX_LOG_INDEX'.format(last_index + 1))
            return self.log_name(index=last_index + 1)
        else:
            return self.log_name(index=1)

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
        elif isinstance(value, (int, float, complex)):
            canonicalized_value = value
        #    self.config.updateValue(label, canonizalized_value)
        else:
            Exception("I don't know what to do with this value")

        self.template_diffs[label] = canonicalized_value
        #self.set_expired(True)

    def merge_configs(self):
        """
        TODO write a real docstring here
        Merge the template and diff configuration dictionaries, in preparation
        for serialization
        """
        # TODO actually do it. For now, just return the most naive thing possible.
        new_config = copy.deepcopy(self.template)
        for diff_key in self.template_diffs:
            vals = self.template_diffs[diff_key]
            channel = [c for c in new_config['step_channels'] if
                        c['channel_name'] == diff_key]
            channel = [{}] if not channel else channel[0]
            if isinstance(vals, tuple):
                items = channel['step_items'][0]
                items['start'] = vals[0]
                items['stop'] = vals[1]
                items['n_pts'] = vals[2]
                items['center'] = (vals[0] + vals[1])/2
                items['span'] = vals[1] - vals[0]
                items['step'] = items['span']/items['n_pts']
        return new_config

    def emit_labber_input_file(self) -> str:
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
        temp_dir = '/tmp' if platform.system() in ['Linux', 'Darwin']\
                          else 'C:\\Windows\\Temp'
        temp = tempfile.NamedTemporaryFile(delete=False,
            mode='w+b', dir=temp_dir, suffix='.labber')
        fp = temp.name
        temp.close()

        # Merge the template and diffs; write to the tempfile
        save_labber_scenario_from_dict(fp, self.merge_configs())
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
    def labber_input_file(self):
        return self.config.sCfgFileIn

    @labber_input_file.setter
    def labber_input_file(self, x):
        self.config.sCfgFileIn = x

    @property
    def labber_output_file(self):
        return self.config.sCfgFileOut

    @labber_output_file.setter
    def labber_output_file(self, x):
        self.config.sCfgFileOut = x

    def __expired__(self, call_record=None):
        """
        Default expiration condition: is there  a result?
        """
        return (('fit_results' not in self.data)
                 or not self.data['fit_results'])


class LabberCall(CallRecord):
    """
    TODO: docstring
    """

    # should get the max name length on the labber output directory from server
    log_name = StringField(max_length=os.statvfs('/').f_namemax)

    def __init__(self, feature, *args, **kwargs):
        super().__init__(feature, *args, **kwargs)
        self.log_name = feature.next_log_name()
