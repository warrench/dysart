import os

"""
Standard measurement files in the EQuS lab
"""

dir_path = os.path.dirname(os.path.realpath(__file__))
qubit_rabi_file = os.path.join(dir_path, 'Simple_Rabi.hdf5')
qubit_rabi_file_out = os.path.join(dir_path, 'Simple_Rabi_out.hdf5')
qubit_spec_file = os.path.join(dir_path, 'Simple_Spectroscopy.hdf5')
qubit_spec_file_out = os.path.join(dir_path, 'Simple_Spectroscopy_out.hdf5')