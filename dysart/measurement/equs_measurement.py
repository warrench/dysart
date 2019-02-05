import os
import datetime as dt
from equs_features import *

# Get the base hdf5 files
std_hdf5_dir = os.path.join(os.getcwd(), 'std-hdf5')
qubit_spec_file = os.path.join(std_hdf5_dir, 'qubit_spec.hdf5')
qubit_rabi_file = os.path.join(std_hdf5_dir, 'qubit_rabi.hdf5')
qubit_relax_file = os.path.join(std_hdf5_dir, 'qubit_relax.hdf5')

##################################
# TODO: set up instrument server #
##################################

##############################################
# Set up the features to do a T1 measurement #
##############################################

print('Setting up the feature tree... ', end='')

# First, the spectrum measurement
qb_spec = QubitSpectrum(qubit_spec_file, )

# Then the Rabi
qb_rabi = QubitRabi(qubit_rabi_file).add_parents(qb_spec)
qb_rabi.spec = qb_spec # This is pretty redundant; makes mistakes easy

# Then the T1
qb_relax = QubitRelaxation(qubit_relax_file).add_parents(qb_rabi)
qb_relax.rabi = qb_rabi # ibid

print('Done.')
