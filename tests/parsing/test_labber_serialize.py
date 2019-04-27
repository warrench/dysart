import env
import unittest
import os
import shutil
import numpy as np
from dysart.parsing.labber_serialize import (
    load_labber_scenario_as_dict, save_labber_scenario_from_dict)


class SaneEqualityArray(np.ndarray):
    """Enable equality checking for numpy arrays"""

    def __eq__(self, other):
        return (
            isinstance(other, np.ndarray) and self.shape == other.shape and
            np.allclose(self, other))


def update_np_array_eq_func(d):
    """Update np array equality function to work in testing"""
    if isinstance(d, np.ndarray):
        return SaneEqualityArray(d.shape, d.dtype, d)
    if isinstance(d, (list, tuple)):
        return [update_np_array_eq_func(x) for x in d]
    if isinstance(d, dict):
        for key in d.keys():
            d[key] = update_np_array_eq_func(d[key])
    return d


class ConversionTest(unittest.TestCase):
    """Tests for converting between dict and hdf5 configurations"""

    def setUp(self):
        # set up output folder
        self.output_folder = os.path.join(os.getcwd(), '_out')
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder, ignore_errors=True)
        os.mkdir(self.output_folder)

    def tearDown(self):
        # remove temporary files
        try:
            if os.path.exists(self.output_folder):
                shutil.rmtree(self.output_folder, ignore_errors=True)
        except Exception:
            pass

    def test_compare_json(self):
        # file names
        file_org = os.path.join(
            env.data_file_path, 'labber_examples',
            'Spectroscopy_vsFlux.labber')
        file_new_json = os.path.join(self.output_folder, '_out.json')

        # load scenario from disk (binary)
        cfg = load_labber_scenario_as_dict(file_org)

        # save and reload config as json
        save_labber_scenario_from_dict(file_new_json, cfg)
        cfg2 = load_labber_scenario_as_dict(file_new_json)

        # update numpy arrays to enable automated tests
        cfg2 = update_np_array_eq_func(cfg2)

        # check that configs are the same
        self.assertEqual(cfg2, cfg)

    def test_compare_binary(self):
        # file names
        file_org = os.path.join(
            env.data_file_path, 'labber_examples',
            'Spectroscopy_vsFlux.json')
        file_new_bin = os.path.join(self.output_folder, '_out.labber')

        # load scenario from disk (binary)
        cfg = load_labber_scenario_as_dict(file_org)

        # save and reload config as json
        save_labber_scenario_from_dict(file_new_bin, cfg)
        cfg2 = load_labber_scenario_as_dict(file_new_bin)

        # update numpy arrays to enable automated tests
        cfg2 = update_np_array_eq_func(cfg2)

        # check that configs are the same
        self.assertEqual(cfg2, cfg)

if __name__ == '__main__':
    unittest.main()
