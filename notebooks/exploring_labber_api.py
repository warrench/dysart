import os, io
import numbers
import numpy as np
import matplotlib.pyplot as plt
import Labber

sample_data_directory   = 'sample_data/'
sample_data_path        = os.path.join(sample_data_directory,
                                       'rabi_scan',
                                       '20181005_DME_3x3qubits_v2',
                                       'TMM10_qu1_rabi.hdf5')

def modify_voltages(path, voltage=np.array([0.]), **kwargs):
    lf = Labber.LogFile(path)
    if isinstance(voltage, numbers.Number) :

    return lf


lf = Labber.LogFile(os.path.abspath(sample_data_path))
lf.getNumberOfEntries()

lf.getStepChannel()

for channel in lf.getStepChannels():
    print(channel.name)
