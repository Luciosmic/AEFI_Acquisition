import unittest

from domain.test_bench_calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement


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

    # -- from_uniform_half_width: u = a / sqrt(3) ---------------------------------

    def test_from_uniform_half_width_uses_a_over_sqrt3(self):
        measurement = CaliperMeasurement.from_uniform_half_width(value_m=0.103, half_width_m=0.00025, k=2.0)

        self.assertAlmostEqual(measurement.uncertainty_expanded_m / measurement.k, 0.00025 / 3 ** 0.5, delta=1e-15)
        self.assertEqual(measurement.uniform_half_width_m, 0.00025)

    def test_default_half_width_gives_the_same_standard_uncertainty_as_the_vernier_resolution(self):
        """0.01 mm half-width = 0.02 mm resolution / 2: past calibrations keep their uncertainty."""
        from_half_width = CaliperMeasurement.from_uniform_half_width(value_m=0.0196)
        from_resolution = CaliperMeasurement.from_resolution(value_m=0.0196)

        self.assertEqual(CaliperMeasurement.DEFAULT_UNIFORM_HALF_WIDTH_M, 0.00001)
        self.assertAlmostEqual(from_half_width.uncertainty_expanded_m, 2.0 * 0.00002 / (2 * 3 ** 0.5), delta=1e-15)
        self.assertAlmostEqual(from_half_width.uncertainty_expanded_m, from_resolution.uncertainty_expanded_m, delta=1e-15)
        self.assertAlmostEqual(from_resolution.uniform_half_width_m, 0.00001, delta=1e-15)

    def test_rejects_negative_half_width(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement.from_uniform_half_width(value_m=0.05, half_width_m=-0.00001)

    def test_rejects_a_half_width_inconsistent_with_the_uncertainty(self):
        with self.assertRaises(ValueError):
            CaliperMeasurement(value_m=0.05, uncertainty_expanded_m=1.15e-5, k=2.0, uniform_half_width_m=0.00025)

    def test_half_width_is_optional_for_a_directly_given_uncertainty(self):
        measurement = CaliperMeasurement(value_m=0.0196, uncertainty_expanded_m=1.15e-5, k=2.0)

        self.assertIsNone(measurement.uniform_half_width_m)


if __name__ == "__main__":
    unittest.main()
