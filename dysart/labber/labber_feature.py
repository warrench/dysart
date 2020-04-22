"""
Feature class for objects that interact with the Labber API.
Currently, the Labber interface is pretty naive, using the highest-level
API available. After I really get it "working," it would be nice to speed
things up by passing in-memory data buffers to reduce the number of writes,
etc.
"""

import os
import sys
import copy
from functools import wraps
import numbers
import platform
import re
import tempfile
from typing import List, Optional, Callable, Union

import numpy as np
import mongoengine as me
import Labber
from Labber import ScriptTools as st

from dysart.labber.labber_serialize import load_labber_scenario_as_dict
from dysart.labber.labber_serialize import save_labber_scenario_from_dict
from dysart.labber.labber_util import no_recorded_result
from dysart.feature import Feature, CallRecord, refresh
import dysart.messages.messages as messages
from dysart.messages.errors import UnsupportedPlatformError
import toplevel.conf as conf

# Set path to executable. This should be done not-here, but it needs to be put
# somewhere for now.

if platform.system() == 'Darwin':
    st.setExePath(os.path.join(os.path.sep, 'Applications', 'Labber'))
    MAX_PATH = os.statvfs('/').f_namemax
elif platform.system() == 'Linux':
    st.setExePath(os.path.join(os.path.sep, 'usr', 'share', 'Labber', 'Program'))
    MAX_PATH = os.statvfs('/').f_namemax
elif platform.system() == 'Windows':
    st.setExePath(os.path.join('C:\\', 'Program Files', 'Labber', 'Program'))
    MAX_PATH = 260  # This magic constant is a piece of Windows lore.
else:
    raise UnsupportedPlatformError

"""
Register default labber client. Using a global variable is maybe all right for
testing, but this is a pretty dangerous practice in production code.
"""
default_client = globals().get('dyserver')


# NOTE: This lower-case name is correct! This class is intended to be used as a
# method decorator.
class result:
    """This decorator class annotates a result-yielding method of a Labber feature.
    """
    def __init__(self, fn: Callable) -> None:
        """This accepts a 'result-granting' function and returns a refresh function
        whose return value is cached into the `results` field of `feature` with key
        the name of the wrapped function.

        TODO: Some bad assumptions are being made here:
        * It _forces_ users to remember to name an argument `index`. Nobody will
            remember this. This is a terrible api.
        * It assumes that such a function wants to use only a _single_ result.

        TODO: think about it and assign `index` correctly...
        """

        # First wrap the function to make it refresh
        self.obj = None

        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            feature = args[0] # TODO: is this good practice?

            index = kwargs.get('index') or -1  # default last entry
            hist_len = len(feature.log_history)
            # Ensure that `results` is long enough.
            if index < 0:
                index = len(feature.log_history) + index
            while len(feature.results) <= index:
                feature.results.append({})

            try:
                return_value = feature.results[index][fn.__name__]
            except:
                # TODO: Pokemon exception handling
                return_value = fn(*args, **kwargs)
                feature.results[index][fn.__name__] = return_value
                feature.save()
            return return_value

        wrapped_fn.is_result = True
        self.wrapped_fn = refresh(wrapped_fn)
        self.__name__ = wrapped_fn.__name__  # TODO: using `wraps` right?
        self.__doc__ = wrapped_fn.__doc__

    def __get__(self, obj, objtype):
        """Hack to bind this callable to the parent object.
        """
        self.obj = obj
        return self

    def __call__(self, *args, **kwargs):
        return self.wrapped_fn(self.obj, *args, **kwargs)


class LogHistory:
    """Abstracts history of Labber output files as an array-like object. This
    should be considered mostly an implementation detail of the Result class.

    TODO: should this subclass an abc?
    TODO: should this support slicing? Yeah, probably. That would be awesome.
    TODO: should/can we assume that there are never any holes in the history?
          currently _assumes that there are no holes._
    TODO: cache size is currently unbounded.

    """

    def __init__(self, feature_id: str, labber_data_dir: str, log_name_template: str):
        self.feature_id = feature_id
        # Sanitize data dirs that may contain e.g. '~'
        self.labber_data_dir = os.path.expanduser(labber_data_dir)
        os.makedirs(self.labber_data_dir, exist_ok=True)

        self.log_name_template = log_name_template
        self.log_cache = {}  # contains logs that are held in memory

    def __getitem__(self, index: Union[int, slice])\
            -> "Optional[Union[Labber.LogFile, List[Labber.LogFile]]]":  # not sure of type?
        # TODO: _really_ think if this is the right way to write this
        if type(index) == int:
            if index < 0:
                return self.__getitem__(len(self) + index)
            else:
                log_path = self.log_path(index)
                if not os.path.isfile(log_path):
                    raise IndexError('Labber logfile with index {} cannot be found'.format(index))
                if log_path not in self.log_cache:
                    log_file = Labber.LogFile(self.log_path(index))
                    self.log_cache[log_path] = []
                    for i in range(log_file.getNumberOfEntries()):
                        self.log_cache[log_path].append(log_file.getEntry(i))

                return self.log_cache[log_path]
        elif type(index) == slice:
            # TODO is a less naive implementation possible here?
            # Probably should do some bounds checking, at least.
            return [self[i] for i in range(index.start, index.stop, index.step)]
        else:
            raise TypeError

    def __contains__(self, index: int) -> bool:
        """Check whether an index is used"""
        return self.log_name(index) in os.listdir(self.labber_data_dir)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n <= len(self.get_log_paths()):
            log = self.__getitem__(self._n)
            self._n += 1
            return log
        else:
            raise StopIteration

    def __len__(self) -> int:
        """Gets the number of extant log files."""
        return sum([(1 if self.is_log(fn) else 0)
                    for fn in os.listdir(self.labber_data_dir)])

    def __bool__(self) -> bool:
        """Returns True iff there is at least one entry"""
        return any([(1 if self.is_log(fn) else 0)
                    for fn in os.listdir(self.labber_data_dir)])

    def log_name(self, index: int) -> str:
        """Gets the log name associated with an index"""
        return f'_{self.feature_id}_{index}'.join(
            os.path.splitext(self.log_name_template))

    def log_path(self, index: int) -> str:
        """Gets the log path associated with an index"""
        return os.path.join(self.labber_data_dir, self.log_name(index))

    def get_index(self, file_name: str) -> Optional[int]:
        """Gets the index of a filename if it is an output log name, or None if
        it is not."""
        root, ext = os.path.splitext(self.log_name_template)
        pattern = f'^{root}_{self.feature_id}_(\\d+){ext}$'
        m = re.search(pattern, file_name)
        return int(m.groups()[0]) if m else None

    def is_log(self, file_name: str) -> bool:
        """Checks if a file name corresponds to an output file in the history"""
        return self.get_index(file_name) is not None

    def get_log_paths(self) -> List[str]:
        """Gets all the logs saved in the labber data directory"""
        return [os.path.join(self.labber_data_dir, p)
                for p in os.listdir(self.labber_data_dir)
                if self.is_log(p)]

    def next_log_path(self) -> str:
        """Gets the path of the next log file to be created"""
        return self.log_path(len(self))


class LabberFeature(Feature):
    """Feature class specialized for integration with Labber.
    Init takes the address of a labber server as an argument.
    """

    # Deserialized template file
    template = me.DictField(default={})
    template_diffs = me.DictField(default={})
    # TODO note Mongodb docs on performance of ReferenceFields
    results = me.ListField(me.DictField(), default=list)
    template_file_path = ''
    output_file_path = ''

    def __init__(self, labber_client=default_client, **kwargs):
        if labber_client:
            self.labber_client = labber_client

        super().__init__(**kwargs)
        # Check to see if the template file has been saved in the DySART database;
        # if not, deserialize the .hdf5 on disk.
        if not self.template:
            self.deserialize_template()

        # Set nondefault parameters
        # TODO: use Antti's wrapper code here

        # for kwarg in kwargs:
        #    self.set_value(kwarg, kwargs[kwarg])

        # Deprecated by Simon's changes to Labber API?
        self.config = st.MeasurementObject(self.template_file_path,
                                           self.output_file_path)

        self.log_history = LogHistory(self.id,
                                      conf.config['LABBER_DATA_DIR'],
                                      os.path.split(self.output_file_path)[-1])

    # If this turns out to be visibly slow, can be replaced with some metaclass
    # magic
    def _result_methods(self) -> List[callable]:
        """Gets a list of all the methods of this class annotated with @result
        """
        __old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        methods = [getattr(self, name) for name in dir(self)
                          if isinstance(getattr(self, name, None), result)]
        sys.stdout = __old_stdout
        return methods

    def result_methods(self) -> None:
        """Pretty-prints a list of all the methods of this class annotated with
        @result
        """
        print('')
        for m in self._result_methods():
            messages.pprint_func(m.__name__, m.__doc__)
            # messages.pprint_func(prop, self.__class__.__dict__[prop].__doc__)

    def _status(self) -> str:
        """Overriding Feature._status, this method returns a formatted report on the
        easily-representable (i.e. scalar-valued) result methods.
        """
        result_methods = [m.__name__ for m in self._result_methods()]
        max_method_len = max(map(len, result_methods)) if result_methods else 0

        s = ''
        for m in result_methods:
            results_history = self.get_results_history(m)
            val_f = None
            for i, val in enumerate(results_history):
                # If the most recent result exists, format it with 'ok' status
                if val is not None:
                    status_code = 'ok' if isinstance(val, numbers.Number) else 'warn'
                    if isinstance(val, numbers.Number):
                        val_f = messages.cstr('{:+.6e}'.format(val), status_code)
                    else:
                        val_f = messages.cstr('Non-numeric result', status_code)
                    break
            if val_f is None:
                val_f = messages.cstr('No result calculated', 'fail')
            # TODO figure out how nested format strings; then write this with one
            s += ' ' + messages.cstr(m, 'italic') + ' ' * (max_method_len - len(m))\
                    + ' : {}\n'.format(val_f)
        return s

    def __call__(self, initiating_call=None, **kwargs):
        """
        Thinly wrap the Labber API

        TODO: this is really kind of ugly code
        """
        # Handle the keyword arguments by appropriately modifying the config
        # file. This is sort of a stopgap; I'm not really sure it behaves how
        # we want in production.
        for key in kwargs:
            self.set_value(key, kwargs[key])

        # Make RPC to Labber!
        # set the input file.
        self.labber_input_file = self.emit_labber_input_file()
        self.labber_output_file = self.log_history.next_log_path()
        self.config.performMeasurement()
        # Clean up: tempfile no longer needed.
        os.unlink(self.labber_input_file)

        # Raw data is now in output_file. Load it into self.data.
        # TODO do these *do** anything?
        log_name = os.path.split(self.labber_output_file)[-1]
        log_file = Labber.LogFile(self.labber_output_file)

    def all_results(self, index=-1) -> dict:
        """Returns a dict containing all the result values, even if they haven't been
        computed before."""
        d = {}
        for method in self._result_methods():
            d[method.__name__] = method(index=index)
        return d

    def get_results_history(self, result_name: str):
        """Returns a generator containing all the historical values measured for a
        single result method"""

        # use reversed range rather than negative indices to avoid double
        # counting if new results are added between __next__() calls
        return (self.results[index].get(result_name)
                for index in reversed(range(len(self.results))))

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
        """TODO write a real docstring here
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
                items['center'] = (vals[0] + vals[1]) / 2
                items['span'] = vals[1] - vals[0]
                items['step'] = items['span'] / items['n_pts']
        return new_config

    def emit_labber_input_file(self) -> str:
        """TODO write a real docstring here
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
        """TODO write a real docstring here
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

    def expired(self, call_record=None):
        """
        Default expiration condition: is there a result?

        TODO: introspect in call record history for detailed expiration info.
        For now, simply checks if there exists a named output file.
        """
        return no_recorded_result(self) or self.manual_expiration_switch


class LabberCall(CallRecord):
    """
    TODO: docstring
    """

    # should get the max name length on the labber output directory from server
    log_name = me.StringField(max_length=MAX_PATH)

    def __init__(self, feature, *args, **kwargs):
        super().__init__(feature, *args, **kwargs)
        self.log_name = feature.next_log_name()
