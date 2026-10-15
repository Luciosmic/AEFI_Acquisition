import unittest

from domain.calibration.value_objects.axis_bar_transmission_measurement.axis_bar_transmission_measurement import (
    AxisBarTransmissionMeasurement,
)
from domain.calibration.value_objects.edge_bracket.edge_bracket import EdgeBracket


def make_measurement(axis="X", length=500.0, length_uncertainty=0.0, first=(1001, 1000), second=(23_936, 23_937)):
    return AxisBarTransmissionMeasurement(
        axis=axis,
        bar_length_mm=length,
        bar_length_uncertainty_mm=length_uncertainty,
        first_front=EdgeBracket(*first),
        second_front=EdgeBracket(*second),
        full_steps_per_revolution=200,
        microsteps=16,
    )


class AxisBarTransmissionMeasurementTest(unittest.TestCase):
    def test_n_is_the_distance_between_bracket_centers_plus_minus_half_widths(self):
        m = make_measurement(first=(1010, 1000), second=(23_930, 23_940))
        self.assertEqual(m.increments_between_fronts, 22_930.0)
        self.assertEqual(m.increments_uncertainty, 10.0)

    def test_travel_per_revolution_from_length_and_n(self):
        m = make_measurement()  # N = 22936 for 500 mm -> 21.8 µm/increment
        self.assertAlmostEqual(m.travel_per_motor_revolution_mm, 500.0 * 3200 / 22_936)
        self.assertAlmostEqual(m.travel_per_motor_revolution_mm, 69.76, places=2)
        self.assertAlmostEqual(m.microns_per_pulse, 21.8, places=2)

    def test_uncertainty_adds_bar_length_and_n_relative_bounds(self):
        m = make_measurement(length_uncertainty=0.5, first=(1010, 1000), second=(23_930, 23_940))
        expected_relative = 0.5 / 500.0 + 10.0 / 22_930.0
        self.assertAlmostEqual(m.relative_uncertainty, expected_relative)
        self.assertAlmostEqual(
            m.travel_per_motor_revolution_uncertainty_mm, m.travel_per_motor_revolution_mm * expected_relative
        )

    def test_without_length_uncertainty_only_n_counts(self):
        m = make_measurement()
        self.assertAlmostEqual(m.relative_uncertainty, 1.0 / 22_936)

    def test_rejects_unknown_axis_and_bad_length(self):
        with self.assertRaises(ValueError):
            make_measurement(axis="Z")
        with self.assertRaises(ValueError):
            make_measurement(length=0.0)
        with self.assertRaises(ValueError):
            make_measurement(length_uncertainty=-1.0)

    def test_rejects_fronts_that_overlap(self):
        with self.assertRaises(ValueError):
            make_measurement(first=(1000, 0), second=(1500, 500))


if __name__ == "__main__":
    unittest.main()
