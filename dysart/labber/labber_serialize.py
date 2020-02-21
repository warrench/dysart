import numpy as np
import json
import msgpack
import os


class NumpyTextJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays nicely"""

    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict
        holding dtype, shape and the data as list.
        """
        # special case for complex data
        if isinstance(
                obj, (complex, np.complex128, np.complex64, np.complex_)):
            return dict(__complex__=(obj.real, obj.imag))

        elif isinstance(obj, np.ndarray):
            if not obj.flags['C_CONTIGUOUS']:
                obj = np.ascontiguousarray(obj)
                assert(obj.flags['C_CONTIGUOUS'])
            return dict(
                __ndarray__=obj.flatten().tolist(),
                dtype=str(obj.dtype),
                shape=obj.shape)

        # convert scalar numpy data types to python
        elif isinstance(obj, (np.generic,)):
            # tolist will convert to scalar for scalar input
            return obj.tolist()

        # let the base class default method raise the TypeError
        return json.JSONEncoder(self, obj)


def json_numpy_text_hook(decode_complex):
    def hook(dct):
        """Decodes a previously encoded numpy ndarray with proper shape and dtype.

        :param dct: (dict) json encoded ndarray as text
        :return: (ndarray) if input was an encoded ndarray
        """
        if isinstance(dct, dict):
            if '__ndarray__' in dct:
                dtype = dct.get('dtype', 'float')
                if 'shape' in dct:
                    return np.array(
                        dct['__ndarray__'], dtype).reshape(dct['shape'])
                else:
                    return np.array(dct['__ndarray__'], dtype)

            elif '__complex__' in dct and decode_complex:
                return complex(*dct['__complex__'])
        return dct
    return hook


def dump_to_json_numpy_text(obj):
    """Encode obj to json file with numpy data as pure text"""
    return json.dumps(obj, cls=NumpyTextJSONEncoder).encode('utf-8')


def load_from_json_numpy_text(data, decode_complex=True):
    """Decode data from input containing json file encoded as text"""
    return json.loads(data.decode('utf-8'), 
                      object_hook=json_numpy_text_hook(decode_complex))


def encode_msgpack(obj):
    """Binary encoding of numpy arrays with msgpack
    """
    # special case for complex data
    if isinstance(obj, (complex, np.complex128, np.complex64, np.complex_)):
        return dict(__complex__=(obj.real, obj.imag))

    # handle numpy arrays
    elif isinstance(obj, np.ndarray):
        obj_data = obj.tobytes('C')
        return dict(__ndarray__=obj_data,
                    dtype=str(obj.dtype),
                    shape=obj.shape)

    # convert scalar numpy data types to pure python
    elif isinstance(obj, (np.generic,)):
        # tolist will convert to scalar for scalar input
        return obj.tolist()

    return obj


def decode_msgpack(decode_complex):
    """
    Decodes a previously encoded numpy ndarray with proper shape and dtype.

    :param dct: (dict) msgpack encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    def hook(dct):
        if isinstance(dct, dict):
            if '__ndarray__' in dct:
                data = dct['__ndarray__']
                return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
            elif '__complex__' in dct and decode_complex:
                return complex(*dct['__complex__'])
        return dct
    return hook


def save_labber_scenario_from_dict(file_name, config):
    """Save Labber scenario from dict as binary .labber or .json file"""
    # check type of output file
    (base_name, ext) = os.path.splitext(file_name)
    if ext.lower() == '.json':
        # save as json text file
        data = dump_to_json_numpy_text(config)
        file_name_out = file_name
    else:
        # only save to .labber files
        file_name_out = base_name + '.labber'
        data = msgpack.packb(
            config, default=encode_msgpack, use_bin_type=True)

    # write data
    with open(file_name_out, 'wb') as f:
        f.write(data)
    return file_name_out


def load_labber_scenario_as_dict(file_name, decode_complex=True):
    """Load Labber scenario as dict from binary .labber or .json file"""
    # check file type
    (base_name, ext) = os.path.splitext(file_name)
    if ext.lower() == '.json':
        # load from json text file
        with open(file_name, 'rb') as f:
            data = f.read()
        config = load_from_json_numpy_text(data, decode_complex=decode_complex)

    else:
        # if not json, only read from .labber files
        file_name_labber = base_name + '.labber'
        with open(file_name_labber, 'rb') as f:
            data = f.read()
        hook = decode_msgpack(decode_complex)  # check if decode complex!
        config = msgpack.unpackb(
            data, object_hook=hook, encoding='utf-8', use_list=True)
    return config
