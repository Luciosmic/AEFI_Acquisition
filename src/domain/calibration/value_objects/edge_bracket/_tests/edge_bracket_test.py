import math
import random
import unittest

from domain.calibration.value_objects.bar_point_reading.bar_point_reading import (
    BarPointClassification,
    BarPointReading,
)
from domain.calibration.value_objects.edge_bracket.edge_bracket import EdgeBracket

ON, OFF, UNDECIDABLE = (
    BarPointClassification.ON_BAR,
    BarPointClassification.OFF_BAR,
    BarPointClassification.UNDECIDABLE,
)


def _noisy_edge_distance(rng, n, edge, on_bar_direction, spot_width=6.0, noise_mm=4.0):
    """Synthetic LIDAR: bar at 250 mm, floor at 1250 mm, front softened by the
    spot (logistic of width `spot_width` increments), Gaussian noise."""
    x = on_bar_direction * (n - edge) / spot_width
    coverage = 1.0 / (1.0 + math.exp(-x)) if x > -50 else 0.0
    return 1250.0 - 1000.0 * coverage + rng.gauss(0.0, noise_mm)


def _refine(bracket, rng, edge, k=10, k_sigma=3.0, **noise):
    probes = 0
    while not bracket.is_resolved:
        probe = bracket.next_probe()
        reading = BarPointReading.from_samples(
            [_noisy_edge_distance(rng, probe, edge, bracket.on_bar_direction, **noise) for _ in range(k)]
        )
        bracket = bracket.narrowed(probe, reading.classify(750.0, k_sigma))
        probes += 1
    return bracket, probes


class EdgeBracketTest(unittest.TestCase):
    def test_coarse_bracket_puts_the_bar_side_on_the_given_direction(self):
        rising = EdgeBracket.around(1000.4, on_bar_direction=+1, margin_increments=50)
        self.assertEqual((rising.on_bar_increment, rising.off_bar_increment), (1050, 950))
        falling = EdgeBracket.around(5000.0, on_bar_direction=-1, margin_increments=50)
        self.assertEqual((falling.on_bar_increment, falling.off_bar_increment), (4950, 5050))
        self.assertEqual(falling.on_bar_direction, -1)

    def test_next_probe_is_strictly_inside(self):
        for on, off in ((10, 13), (13, 10), (10, 12), (12, 10), (-7, 4)):
            probe = EdgeBracket(on, off).next_probe()
            self.assertTrue(min(on, off) < probe < max(on, off), (on, off, probe))

    def test_narrowing_moves_the_side_matching_the_classification(self):
        bracket = EdgeBracket(on_bar_increment=100, off_bar_increment=0)
        self.assertEqual(bracket.narrowed(50, ON), EdgeBracket(50, 0))
        self.assertEqual(bracket.narrowed(50, OFF), EdgeBracket(100, 50))

    def test_undecidable_probe_stops_without_narrowing(self):
        bracket = EdgeBracket(100, 0).narrowed(50, UNDECIDABLE)
        self.assertTrue(bracket.is_resolved)
        self.assertIsNone(bracket.next_probe())
        self.assertEqual((bracket.on_bar_increment, bracket.off_bar_increment), (100, 0))
        self.assertEqual(bracket.center_increment, 50.0)
        self.assertEqual(bracket.half_width_increments, 50.0)

    def test_one_increment_wide_is_the_motor_resolution(self):
        bracket = EdgeBracket(11, 10)
        self.assertTrue(bracket.is_resolved)
        self.assertEqual(bracket.center_increment, 10.5)
        self.assertEqual(bracket.half_width_increments, 0.5)

    def test_probe_outside_the_bracket_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            EdgeBracket(100, 0).narrowed(100, ON)

    def test_widening_pushes_each_side_away(self):
        self.assertEqual(EdgeBracket(10, 0).widened(5), EdgeBracket(15, -5))
        self.assertEqual(EdgeBracket(0, 10).widened(5), EdgeBracket(-5, 15))

    def test_dichotomy_on_a_noisy_edge_brackets_the_true_edge(self):
        rng = random.Random(1)
        for direction, edge in ((+1, 18_345.3), (-1, 41_120.8)):
            bracket = EdgeBracket.around(edge + 37 * direction, on_bar_direction=direction, margin_increments=300)
            final, probes = _refine(bracket, rng, edge)
            self.assertLessEqual(probes, 11)
            self.assertLessEqual(abs(final.center_increment - edge), final.half_width_increments + 1.0)
            self.assertLess(final.half_width_increments, 20.0)

    def test_noisier_lidar_stops_earlier_with_a_wider_bracket(self):
        # edge off the first midpoint (1000), where the spot is exactly half on the bar
        quiet, _ = _refine(EdgeBracket(1300, 700), random.Random(2), edge=1093.3, noise_mm=0.5, spot_width=0.2)
        noisy, _ = _refine(EdgeBracket(1300, 700), random.Random(2), edge=1093.3, noise_mm=300.0, k=4)
        self.assertLessEqual(quiet.width_increments, 2)
        self.assertTrue(noisy.stopped_undecidable)
        self.assertGreater(noisy.width_increments, quiet.width_increments)


if __name__ == "__main__":
    unittest.main()
