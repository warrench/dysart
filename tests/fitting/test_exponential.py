# Put modules to test on the path
import env
# Add some helper packages
import numpy as np
# Add modules to test
import unittest as ut
import dysart.fitting.exponential as exponential


class TestExponentialFittingFunctions(ut.TestCase):

    def setUp(self):
        pass

    def test_fit_exponential(self):
        """
        Check that exponential fit works. This is a really silly test; it's
        here just to protect against regression.
        """
        x = np.linspace(0, 1, 101)
        y = np.exp(-x)
        fit_result = exponential.fit_exponential(x, y)
        self.assertAlmostEqual(fit_result.params['decay'], 1)
        self.assertAlmostEqual(fit_result.params['amplitude'], 1)


if __name__ == '__main__':
    ut.main()
