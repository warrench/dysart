# Add packages to test to the path
import env
# Add some helper packages
import numpy as np
import matplotlib.pyplot as plt
import Labber
# Add modules to test
import unittest as ut
import dysart.fitting.spectra as spectra
# Include sample data that is used

# Timing
from timeit import timeit

# SPECTRUM FITTING TESTS #


# Fixing random seed. There are a lot of pseudorandom tests in this module, so
# it is essential that you take care to ensure that (a) there is no particular
# sensitivity to the value of this seed, (b) that the seed is not changed
# arbitrarily from test to test, or better yet both.
np.random.seed(373432261)


class TestSpectrumFittingFunctions(ut.TestCase):

    def setUp(self):
        # Import sample spectrum data to be used in certain tests
        # data_file_name = 'BFC3-8B-spec_thru_Q1_at0Bobbin_rerun.hdf5'
        data_file_name = 'qubit_spectroscopy/20181005_DME_3x3qubits_v2/QBSpectro__TMM10_qu1vBobbin.hdf5'
        qubit_of_interest = 1
        channel_name = 'MQ PulseGen - Voltage, QB%d' % qubit_of_interest
        log_file = Labber.LogFile(env.data_file_path + data_file_name)
        (self.x, self.y) = log_file.getTraceXY(entry=-1, y_channel=channel_name)

        # Set a tolerable reduced-chi-squared limit for spectrum fits. This is a
        # magic constant that shouldn't be here in future versions.
        self.redchi_tolerance_absolute = 2e-9
        self.redchi_tolerance_relative = 1.1

    def test_recursive_linear_search_forward(self):
        """
        Check that recursive_linear_search reports that a linear space exceeds
        half its range at half its size.
        """
        lin = np.linspace(0, 1, 1000)
        index_guess = spectra.recursive_linear_search(lin, 0.5, forward_sense=True, step_size=1)
        self.assertEqual(index_guess, 500)

    def test_recursive_linear_search_forward_random_step(self):
        """
        Check that this doesn't depend on the initial step size
        """
        num_guesses = 20
        lin = np.linspace(0, 1, 1000)
        index_guesses = np.empty(num_guesses)
        for i in range(num_guesses):
            step_size = np.random.randint(1, 257)
            index_guesses[i] = spectra.recursive_linear_search(lin, 0.5, forward_sense=True, step_size=step_size)
        self.assertTrue((index_guesses == 500 * np.ones(num_guesses)).all())

    def test_recursive_linear_search_backward(self):
        """
        Check that recursive_linear_search reports that a linear space exceeds
        half its range at half its size, when searching backwards.
        """
        lin = np.linspace(1, 0, 1000)
        index_guess = spectra.recursive_linear_search(lin, 0.5, forward_sense=False, step_size=1)
        self.assertEqual(index_guess, 500)

    def test_recursive_linear_search_backward_random_step(self):
        """
        Check that this doesn't depend on the initial step size.
        """
        num_guesses = 20
        lin = np.linspace(0, 1, 1000)
        index_guesses = np.empty(num_guesses)
        for i in range(num_guesses):
            step_size = np.random.randint(1, 257)
            index_guesses[i] = spectra.recursive_linear_search(lin, 0.5, forward_sense=True, step_size=step_size)
        self.assertTrue((index_guesses == 500 * np.ones(num_guesses)).all())

    def test_fit_spectrum_on_exp_data(self):
        """
        A dummy function that checks whether fit_spectrum performs well on particular
        sample dataset. This is not all that meaningful in its own right, and should
        ultimately be deprecated. (Note the magic numbers.)
        """
        # Fit the data
        spectrum_fit_result = spectra.fit_spectrum(self.x, np.real(self.y), 2)
        # Check that the reduced-chi-squared statistic is tolerably small (TODO: make this meaningful)
        self.assertLess(spectrum_fit_result.redchi, self.redchi_tolerance_absolute)

    def test_SpectrumModel_eval(self):
        """
        TODO
        Verify SpectrumModel behavior by comparing the model function to a stored
        template.
        """
        # Check that the actual value is close to the model value
        self.assertLess(1, 2)

    def test_fit_spectrum_on_random_data(self):
        """
        This is the first `real` test. Generate lots of spectra with random resonance
        frequencies, linewidths, and amplitudes, and add varying amounts of noise.
        Verify that the chi-squared value is close to the noise std in every case,
        which means that the fit is essentially as good as possible.

        TODO: actually think carefully about possible edge cases. What happens if
        a resonance is at the edge of the domain? What happens if two almost
        perfectly overlap?
        """

        def make_spectrum_params(amplitudes, centers, sigmas):
            """Roll the spectrum parameters into a dict"""
            params = {'c': 0}
            # TODO: do this more pythonically with a comprehension or something
            for i in range(len(amplitudes)):
                params['_%s_amplitude' % i] = amplitudes[i]
                params['_%s_centers' % i] = centers[i]
                params['_%s_sigmas' % i] = sigmas[i]
            return params

        # Make the frequency-domain variable
        low_freq = 4.0e9
        high_freq = 5.0e9
        num_freqs = 1000
        freqs = np.linspace(low_freq, high_freq, num_freqs)

        # Narrowest and widest linewidths
        narrow_linewidth = 10e6
        wide_linewidth = 50e6

        # Loop variable
        num_noise_amplitudes = 5
        num_num_resonances = 8
        noise_amplitudes = np.logspace(-5, -1, num_noise_amplitudes)

        # Initialize chi-squared array
        redchi = np.empty([5, 8])

        # Now generate the random instances!
        for num_resonances in range(num_num_resonances):
            spectrum = spectra.SpectrumModel(num_resonances=num_resonances)
            for noise_index in range(num_noise_amplitudes):
                print((noise_index, num_resonances))
                # Make some random parameters
                amplitudes = np.random.uniform(0, 1e-3, num_resonances)
                centers = np.random.uniform(low_freq, high_freq, num_resonances)
                sigmas = np.random.uniform(narrow_linewidth, wide_linewidth, num_resonances)
                # Calculate the noiseless signal
                sig = spectrum.eval(x=freqs, **make_spectrum_params(amplitudes, centers, sigmas))
                # Add noise to the signal
                sig += np.random.normal(0, noise_amplitudes[noise_index], num_freqs)

                # Now fit the signal and extract the reduced-chi-squared statistic
                spectrum_fit_result = spectra.fit_spectrum(freqs, sig, num_resonances)
                redchi[noise_index][num_resonances] = spectrum_fit_result.redchi
                print("reduced chi is %f" % spectrum_fit_result.redchi + ", noise amplitude^2 is %f" % noise_amplitudes[noise_index]**2)
                print("ratio is %f" % (spectrum_fit_result.redchi / noise_amplitudes[noise_index]**2))
        # Check that the reduced-chi-squared statistic is tolerably small
        var_matrix = np.reshape(np.kron(noise_amplitudes**2, np.ones(num_num_resonances)), [5, 8])
        self.assertTrue((redchi < self.redchi_tolerance_relative * var_matrix).all())


if __name__ == '__main__':
    ut.main()
