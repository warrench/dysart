#! $DYS_PATH/dysenv/bin/python
# ^ This is potentially fragile; might not work on Windows.

import os
import datetime as dt
from equs_features import QubitSpectrum, QubitRabi

##################################
# TODO: set up instrument server #
##################################

##############################################
# Set up the features to do a T1 measurement #
##############################################

print('Setting up the feature tree... ', end='')

# First, the spectrum measurement
qb_spec = QubitSpectrum()

# Then the Rabi. Make sure it depends on the transition frequency measured by qb_spec!
qb_rabi = QubitRabi()
qb_rabi.parents['spec'] = qb_spec

# Then the T1
#qb_relax = QubitRelaxation(qubit_relax_file).add_parents(qb_rabi)
#qb_relax.rabi = qb_rabi # ibid

print('Done.')