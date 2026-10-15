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

    def test_undecidable_probe_becomes_the_noise_zone_and_refinement_goes_on(self):
        bracket = EdgeBracket(100, 0).narrowed(50, UNDECIDABLE)
        self.assertTrue(bracket.limited_by_lidar_noise)
        self.assertFalse(bracket.is_resolved)
        self.assertEqual(bracket.next_probe(), 75)  # bar side first: between a=100 and the zone
        bracket = bracket.narrowed(75, ON)
        self.assertEqual(bracket.next_probe(), 62)
        bracket = bracket.narrowed(62, UNDECIDABLE)  # zone grows toward the bar side
        self.assertEqual(bracket.undecidable_near_on, 62)

    def test_each_side_stops_one_increment_from_the_zone(self):
        bracket = EdgeBracket(on_bar_increment=60, off_bar_increment=40, undecidable_near_on=59,
                              undecidable_near_off=45)
        self.assertEqual(bracket.next_probe(), 42)  # bar side done, floor side goes on
        bracket = bracket.narrowed(42, OFF).narrowed(43, OFF)
        self.assertEqual(bracket.next_probe(), 44)
        bracket = bracket.narrowed(44, OFF)
        self.assertTrue(bracket.is_resolved)
        self.assertEqual((bracket.on_bar_increment, bracket.off_bar_increment), (60, 44))

    def test_noise_beyond_the_zone_recenters_the_bracket(self):
        bracket = EdgeBracket(100, 0, undecidable_near_on=50, undecidable_near_off=50)
        recentred = bracket.narrowed(25, ON)  # on the bar, but past the zone
        self.assertEqual(recentred, EdgeBracket(25, 0))
        self.assertFalse(recentred.limited_by_lidar_noise)
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

    def test_noisier_lidar_is_limited_by_noise_with_a_wider_bracket(self):
        # edge off the first midpoint (1000), where the spot is exactly half on the bar
        quiet, _ = _refine(EdgeBracket(1300, 700), random.Random(2), edge=1093.3, noise_mm=0.5, spot_width=0.2)
        noisy, _ = _refine(EdgeBracket(1300, 700), random.Random(2), edge=1093.3, noise_mm=300.0, k=4)
        self.assertLessEqual(quiet.width_increments, 2)
        self.assertTrue(noisy.limited_by_lidar_noise)
        self.assertGreater(noisy.width_increments, quiet.width_increments)
        self.assertLess(noisy.width_increments, 600)

    def test_first_probe_in_the_noise_zone_gives_half_the_zone_not_the_margin(self):
        """Edge exactly at the coarse front: the first probe is undecidable. The
        noise zone (|d̄ − s| < k_σ·σ/√k) is ±~5 increments wide here."""
        rng = random.Random(4)
        edge, margin = 5_000.0, 400
        final, probes = _refine(
            EdgeBracket.around(edge, on_bar_direction=+1, margin_increments=margin), rng, edge,
            k=10, k_sigma=3.0, spot_width=20.0, noise_mm=150.0,
        )
        self.assertTrue(final.limited_by_lidar_noise)
        self.assertLess(final.half_width_increments, 30)  # not ~400
        self.assertLessEqual(abs(final.center_increment - edge), final.half_width_increments + 1)
        self.assertLessEqual(probes, 25)


if __name__ == "__main__":
    unittest.main()
