import unittest

from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement


class TestCaliperMeasurement(unittest.TestCase):
    def test_creates_with_all_fields(self):
        measurement = CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=2.0)
        self.assertEqual(measurement.value_m, 0.0196)
        self.assertEqual(measurement.uncertainty_expanded_m, 1.15e-5)
        self.assertEqual(measurement.k, 2.0)

    def test_is_immutable(self):
        measurement = CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=2.0)
        with self.assertRaises(Exception):
            measurement.value_m = 0.02

    def test_rejects_zero_value(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement(value_m=0.0, uncertainty_expanded_m=1.15e-5, k=2.0)

    def test_rejects_negative_value(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement(value_m=-0.01, uncertainty_expanded_m=1.15e-5, k=2.0)

    def test_rejects_negative_uncertainty(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=-1.0, k=2.0)

    def test_rejects_zero_k(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=0.0)

    def test_equal_measurements_compare_equal(self):
        a = CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=2.0)
        b = CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=2.0)
        self.assertEqual(a, b)

    # -- from_resolution: GUM formula --------------------------------------------

    def test_from_resolution_reproduces_existing_json_uncertainty(self):
        """
        Default resolution (0.02mm vernier) and k=2 must reproduce the
        expanded uncertainty already hand-written throughout
        config_templates/aefi_device_config.json (1.15e-5 m).
        """
        measurement = CaliperMeasurement.from_resolution(value_m=0.0196)

        self.assertAlmostEqual(measurement.uncertainty_expanded_m, 1.15e-5, delta=1e-7)
        self.assertEqual(measurement.value_m, 0.0196)
        self.assertEqual(measurement.k, 2.0)

    def test_from_resolution_uses_gum_formula(self):
        resolution_m = 0.0001
        k = 3.0

        measurement = CaliperMeasurement.from_resolution(value_m=0.05, resolution_m=resolution_m, k=k)

        expected_u_c = resolution_m / (2 * (3 ** 0.5))
        self.assertAlmostEqual(measurement.uncertainty_expanded_m, k * expected_u_c)

    def test_from_resolution_zero_resolution_yields_zero_uncertainty(self):
        measurement = CaliperMeasurement.from_resolution(value_m=0.05, resolution_m=0.0)

        self.assertEqual(measurement.uncertainty_expanded_m, 0.0)


if __name__ == "__main__":
    unittest.main()
