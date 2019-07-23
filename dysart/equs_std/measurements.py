import os

"""
Standard measurement files in the EQuS lab
"""

dir_path = os.path.dirname(os.path.realpath(__file__))

qubit_rabi_file = os.path.join(dir_path, 'qubit_rabi.json')
qubit_rabi_file_out = os.path.join(dir_path, 'qubit_rabi_out.hdf5')
qubit_spec_file = os.path.join(dir_path, 'qubit_spec.json')
qubit_spec_file_out = os.path.join(dir_path, 'qubit_spec_out.hdf5')
