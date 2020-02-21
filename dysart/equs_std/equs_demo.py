from dysart.equs_std.equs_features import QubitSpectrum, QubitRabi
from dysart.messages.messages import cprint, StatusMessage
from dypy import include_feature

##############################################
# Set up the features to do a T1 measurement #
##############################################

# with StatusMessage('setting up the feature tree...', capture_io=False):


print('setting up the feature tree...'.ljust(48), end='')
# First, the spectrum measurement
qb_spec = include_feature(QubitSpectrum, 'qb_spec')
# Then the Rabi. Make sure it depends on the transition frequency measured by qb_spec!
qb_rabi = include_feature(QubitRabi, 'qb_rabi')
qb_rabi.parents['spec'] = qb_spec
cprint('done.\n', 'ok')

qb_rabi.tree()

# Then the T1
#qb_relax = include_feature(QubitRelaxation, 'qb_relax')
#qb_relax.parents['spec'] = qb_rabi
