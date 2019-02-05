import os

"""
Standard measurement files in the EQuS lab
"""

dir_path = os.path.dirname(os.path.realpath(__file__)) 
qubit_rabi_file = os.path.join(dir_path, 'qubit_rabi.hdf5')
qubit_spec_file = os.path.join(dir_path, 'qubit_spec_file.hdf5')
