# TESTING NOTEBOOK #
# Informal tests exploring APIs and data from Morten. After I start to get a
# handle on things and this starts to look less hacky (and needs to be integrated
# with other modules), these will gradually be replaced by real unit tests.
# This notebook is intended to be used for checking the
# Best viewed with Hydrogen in Atom.

import os
import numpy as np
import matplotlib.pyplot as plt
import Labber
from lmfit.models import ConstantModel, LorentzianModel, GaussianModel
from dysart.fitting.spectra import *


# Fixing random seed
np.random.seed(373432261)

# Location of data file(s)
sample_data_path = 'sample_data/'
# os.readlink(os.path.expanduser('~') + '/EQuS') + '/data/'
file_name = 'qubit_spectroscopy/20181005_DME_3x3qubits_v2/QBSpectro_TMM10_qu1vBobbin.hdf5'
#'BFC3-8B-spec_thru_Q1_at0Bobbin_rerun.hdf5'

# Import the data file 
log_file = Labber.LogFile(os.path.abspath(sample_data_path + file_name))

# Create test plot, find a minimum
qubit_number = 1
channel_name = 'MQ PulseGen - Voltage, QB%d' % qubit_number
(x, y) = log_file.getTraceXY(entry=-1, y_channel=channel_name)

plt.subplot(111)
plt.plot(x,np.real(y))
plt.show()


spectrum_fit_result = fit_spectrum(x, np.real(y), 2)
plt.subplot(111)
plt.plot(x, np.real(y))
plt.plot(x, spectrum_fit_result.init_fit)
plt.show()


baseline_guess = guess_baseline(np.real(y))
baseline_guess

peak_index_guess = guess_peak_index(np.real(y))
peak_index_guess

hwhm_guess = guess_hwhm(x, np.real(y), peak_index_guess, baseline_guess, initial_step_size=1)
hwhm_guess

amplitude_guess = np.pi * hwhm_guess * (np.real(y)[peak_index_guess] - baseline_guess)
amplitude_guess

(baseline_guess + np.real(y)[peak_index_guess]) / 2
res1 = find_resonance(x, np.real(y))
# res2 = find_resonance(x, np.real(y) - res1.best_fit)

baseline_guess2 = guess_baseline(np.real(y) - res1.best_fit)
baseline_guess2
peak_index_guess2 = guess_peak_index(np.real(y) - res1.best_fit)
peak_index_guess2
# hwhm_guess2 = hwhm_guess = guess_hwhm(x, np.real(y) - res1.best_fit, peak_index_guess, baseline_guess, initial_step_size=1)

a = np.real(y) - res1.best_fit
np.argmin(a)
a[30]

plt.subplot(111)
plt.plot(x, np.real(y))
np.argmin(np.real(y))
plt.plot(x, np.real(y) - res1.best_fit, 'r-')
plt.show()
res2 = find_resonance(x, np.real(y) - res1.best_fit)

fit_result.params['c'].value

for i in range(1, N_QUBITS + 1):
    channel_name = 'MQ PulseGen - Voltage, QB%d' % i
    (x, y) = log_file.getTraceXY(entry=-1, y_channel=channel_name)
