import random
import unittest

from domain.calibration.errors.bar_profile_unusable_error import BarProfileUnusableError
from domain.calibration.services.bar_profile_analysis.bar_profile_analysis import (
    locate_bar,
    pair_by_reception_time,
)

BAR_START, BAR_END = 18_349, 41_284  # 400..900 mm at 21.8 µm/increment
TRAVEL = 58_257


def _fly_profile(rng, bar=(BAR_START, BAR_END), step=32, noise_mm=3.0, latency_increments=0, travel=TRAVEL):
    """Synthetic fly scan: one LIDAR point every `step` increments, bar at 250 mm,
    floor at 1250 mm, sharp edges, Gaussian noise; latency shifts what is seen."""
    profile = []
    for n in range(0, travel, step):
        seen = n - latency_increments
        on_bar = any(start <= seen <= end for start, end in ([bar] if isinstance(bar[0], int) else bar))
        profile.append((float(n), (250.0 if on_bar else 1250.0) + rng.gauss(0.0, noise_mm)))
    return profile


class PairByReceptionTimeTest(unittest.TestCase):
    def test_interpolates_the_position_at_each_sample_time(self):
        positions = [(0.0, 0.0), (1.0, 800.0), (2.0, 1600.0)]
        samples = [(0.5, 1250.0), (1.25, 250.0)]
        self.assertEqual(pair_by_reception_time(positions, samples), [(400.0, 1250.0), (1000.0, 250.0)])

    def test_drops_samples_outside_the_positions_time_span(self):
        positions = [(1.0, 0.0), (2.0, 100.0)]
        samples = [(0.9, 1.0), (2.1, 2.0), (2.0, 3.0)]
        self.assertEqual(pair_by_reception_time(positions, samples), [(100.0, 3.0)])

    def test_unordered_positions_are_sorted_by_time(self):
        self.assertEqual(pair_by_reception_time([(2.0, 20.0), (0.0, 0.0)], [(1.0, 5.0)]), [(10.0, 5.0)])


class LocateBarTest(unittest.TestCase):
    def test_noisy_square_wave_gives_plateaus_threshold_and_fronts(self):
        located = locate_bar(_fly_profile(random.Random(3)))
        self.assertAlmostEqual(located.on_bar_distance_mm, 250.0, delta=1.0)
        self.assertAlmostEqual(located.off_bar_distance_mm, 1250.0, delta=1.0)
        self.assertAlmostEqual(located.threshold_mm, 750.0, delta=1.0)
        self.assertAlmostEqual(located.plateau_noise_mm, 3.0, delta=1.0)
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=32)
        self.assertAlmostEqual(located.second_front_increment, BAR_END, delta=32)

    def test_latency_shifts_both_fronts_but_not_the_length(self):
        located = locate_bar(_fly_profile(random.Random(4), latency_increments=200))
        self.assertAlmostEqual(located.first_front_increment, BAR_START + 200, delta=32)
        self.assertAlmostEqual(located.bar_length_increments, BAR_END - BAR_START, delta=64)

    def test_isolated_noise_flips_do_not_create_a_front(self):
        profile = _fly_profile(random.Random(5))
        profile[10] = (profile[10][0], 240.0)  # one spike on the floor plateau
        located = locate_bar(profile)
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=32)

    def test_refuses_a_profile_without_contrast(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar([(float(n), 1250.0 + (n % 3)) for n in range(100)])

    def test_refuses_a_bar_touching_the_origin(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar(_fly_profile(random.Random(6), bar=(0, 30_000)))

    def test_refuses_a_bar_reaching_the_opposite_limit(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar(_fly_profile(random.Random(7), bar=(30_000, TRAVEL)))

    def test_refuses_two_short_zones(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar(_fly_profile(random.Random(8), bar=((5_000, 20_000), (30_000, 45_000))))

    def test_refuses_a_too_short_profile(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar([(0.0, 1250.0), (1.0, 250.0)])


if __name__ == "__main__":
    unittest.main()
