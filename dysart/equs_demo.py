#! $DYS_PATH/dysenv/bin/python
# ^ This is potentially fragile; might not work on Windows.

from measurement.equs_features import QubitSpectrum, QubitRabi
from context import Context
from measurement.messages import cprint
from measurement.feature import include_feature

##############################################
# Set up the features to do a T1 measurement #
##############################################

cprint('setting up the feature tree...'.ljust(48), status='normal', end='')

# First, the spectrum measurement
qb_spec = include_feature(QubitSpectrum, 'qb_spec')

# Then the Rabi. Make sure it depends on the transition frequency measured by qb_spec!
qb_rabi = include_feature(QubitRabi, 'qb_rabi')
qb_rabi.parents['spec'] = qb_spec

# Then the T1
#qb_relax = include_feature(QubitRelaxation, 'qb_relax')
#qb_relax.parents['spec'] = qb_rabi

cprint('done.', status='ok', end='\n')
print('\n' + qb_rabi.__str__() + '\n')
