import unittest
from dataclasses import replace

from domain.calibration.value_objects.axis_bar_transmission_measurement.axis_bar_transmission_measurement import (
    AxisBarTransmissionMeasurement,
)
from domain.calibration.value_objects.bar_transmission_mean.bar_transmission_mean import BarTransmissionMean
from domain.calibration.value_objects.edge_bracket.edge_bracket import EdgeBracket


def make_axis(axis, second_center, half_width=1):
    return AxisBarTransmissionMeasurement(
        axis=axis,
        bar_length_mm=500.0,
        bar_length_uncertainty_mm=0.0,
        first_front=EdgeBracket(1000 + half_width, 1000 - half_width),
        second_front=EdgeBracket(second_center - half_width, second_center + half_width),
        full_steps_per_revolution=200,
        microsteps=16,
    )


class BarTransmissionMeanTest(unittest.TestCase):
    def test_mean_and_deviation(self):
        x, y = make_axis("X", 23_936), make_axis("Y", 23_900)
        mean = BarTransmissionMean(x, y)
        self.assertAlmostEqual(
            mean.travel_per_motor_revolution_mm,
            (x.travel_per_motor_revolution_mm + y.travel_per_motor_revolution_mm) / 2,
        )
        self.assertAlmostEqual(
            mean.travel_per_motor_revolution_uncertainty_mm,
            (x.travel_per_motor_revolution_uncertainty_mm + y.travel_per_motor_revolution_uncertainty_mm) / 2,
        )
        self.assertAlmostEqual(mean.deviation_mm, x.travel_per_motor_revolution_mm - y.travel_per_motor_revolution_mm)
        self.assertLess(mean.deviation_mm, 0)  # Y has fewer increments for the same bar
        self.assertAlmostEqual(mean.relative_deviation, mean.deviation_mm / mean.travel_per_motor_revolution_mm)

    def test_axes_agree_within_their_uncertainties(self):
        self.assertTrue(BarTransmissionMean(make_axis("X", 23_936, 20), make_axis("Y", 23_920, 20)).axes_agree)
        self.assertFalse(BarTransmissionMean(make_axis("X", 23_936, 1), make_axis("Y", 23_800, 1)).axes_agree)

    def test_refuses_two_measurements_of_the_same_axis(self):
        with self.assertRaises(ValueError):
            BarTransmissionMean(make_axis("X", 23_936), make_axis("X", 23_936))

    def test_refuses_different_chain_settings(self):
        with self.assertRaises(ValueError):
            BarTransmissionMean(make_axis("X", 23_936), replace(make_axis("Y", 23_936), microsteps=8))


if __name__ == "__main__":
    unittest.main()
