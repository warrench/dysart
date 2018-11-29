import numpy as np
from lmfit.models import ConstantModel, LorentzianModel, GaussianModel

# SPECTRUM FITTING #
# Contains tools for fitting resonance spectra. The idea of this module is to
# implement some fitting routines more `intelligently' and simply than spectra.py
# by taking full advantage of the lmfit API for guessing, hypothesis testing,
# and so on.
# As in spectrum.py, this is a module that is worth getting Right with a capital
# 'R', and since a lot of people have reinvented this wheel before, it would
# behoove me to review prior art. In particular, it's likely that there are
# standard algorithms and hypothesis tests that are well-known in the NMR, HEP,
# and astronomy communities. Check out any CERN docs on spectrum-fitting;
# they're probably the gold standard.
