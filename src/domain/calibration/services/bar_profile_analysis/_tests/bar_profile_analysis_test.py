import random
import unittest

from domain.calibration.errors.bar_profile_unusable_error import BarProfileUnusableError
from domain.calibration.services.bar_profile_analysis.bar_profile_analysis import (
    locate_bar,
    pair_by_reception_time,
)
from domain.shared_kernel.value_objects.lidar_distance.lidar_distance import LidarDistance

NO_RETURN = LidarDistance.no_return()

BAR_START, BAR_END = 18_349, 41_284  # 400..900 mm at 21.8 µm/increment
TRAVEL = 58_257


def _fly_profile(rng, bar=(BAR_START, BAR_END), step=32, noise_mm=3.0, latency_increments=0, travel=TRAVEL):
    """Synthetic fly scan: one LIDAR point every `step` increments, bar at 250 mm,
    floor at 1250 mm, sharp edges, Gaussian noise; latency shifts what is seen."""
    profile = []
    for n in range(0, travel, step):
        seen = n - latency_increments
        on_bar = any(start <= seen <= end for start, end in ([bar] if isinstance(bar[0], int) else bar))
        profile.append((float(n), LidarDistance((250.0 if on_bar else 1250.0) + rng.gauss(0.0, noise_mm))))
    return profile


def _out_of_range_floor_profile(rng, dropout=0.0, bar=(BAR_START, BAR_END), step=32):
    """Bench case (2026-10-15): bar at ~95 mm with sporadic dropouts, floor out of
    LIDAR range (no return at all)."""
    profile = []
    for n in range(0, TRAVEL, step):
        on_bar = bar[0] <= n <= bar[1] and rng.random() >= dropout
        profile.append((float(n), LidarDistance(95.0 + rng.gauss(0.0, 1.0)) if on_bar else NO_RETURN))
    return profile


class PairByReceptionTimeTest(unittest.TestCase):
    def test_interpolates_the_position_at_each_sample_time(self):
        positions = [(0.0, 0.0), (1.0, 800.0), (2.0, 1600.0)]
        floor, bar = LidarDistance(1250.0), LidarDistance(250.0)
        samples = [(0.5, floor), (1.25, bar), (1.5, NO_RETURN)]
        self.assertEqual(
            pair_by_reception_time(positions, samples), [(400.0, floor), (1000.0, bar), (1200.0, NO_RETURN)]
        )

    def test_drops_samples_outside_the_positions_time_span(self):
        positions = [(1.0, 0.0), (2.0, 100.0)]
        samples = [(0.9, LidarDistance(1.0)), (2.1, LidarDistance(2.0)), (2.0, LidarDistance(3.0))]
        self.assertEqual(pair_by_reception_time(positions, samples), [(100.0, LidarDistance(3.0))])

    def test_unordered_positions_are_sorted_by_time(self):
        five = LidarDistance(5.0)
        self.assertEqual(pair_by_reception_time([(2.0, 20.0), (0.0, 0.0)], [(1.0, five)]), [(10.0, five)])


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
        profile[10] = (profile[10][0], LidarDistance(240.0))  # one spike on the floor plateau
        located = locate_bar(profile)
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=32)

    def test_floor_without_return_is_the_off_bar_plateau(self):
        located = locate_bar(_out_of_range_floor_profile(random.Random(9)))
        self.assertAlmostEqual(located.on_bar_distance_mm, 95.0, delta=1.0)
        self.assertIsNone(located.off_bar_distance_mm)
        self.assertIsNone(located.threshold_mm)
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=32)
        self.assertAlmostEqual(located.second_front_increment, BAR_END, delta=32)

    def test_sporadic_dropouts_on_the_bar_do_not_create_fronts(self):
        located = locate_bar(_out_of_range_floor_profile(random.Random(10), dropout=0.2))
        # A dropout on the last sample of the bar moves a coarse front by one sample, no more.
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=2 * 32)
        self.assertAlmostEqual(located.second_front_increment, BAR_END, delta=2 * 32)
        self.assertAlmostEqual(located.bar_length_increments, BAR_END - BAR_START, delta=3 * 32)

    def test_samples_without_return_count_as_off_the_bar_between_valid_plateaus(self):
        rng = random.Random(11)
        profile = [(n, NO_RETURN if d.distance_mm > 750.0 and rng.random() < 0.3 else d)
                   for n, d in _fly_profile(rng)]
        located = locate_bar(profile)
        self.assertAlmostEqual(located.off_bar_distance_mm, 1250.0, delta=1.0)
        self.assertAlmostEqual(located.first_front_increment, BAR_START, delta=32)

    def test_refuses_a_profile_without_any_valid_return(self):
        with self.assertRaisesRegex(BarProfileUnusableError, "aucun retour valide"):
            locate_bar([(float(n), NO_RETURN) for n in range(100)])

    def test_refuses_a_profile_without_contrast(self):
        with self.assertRaises(BarProfileUnusableError):
            locate_bar([(float(n), LidarDistance(1250.0 + (n % 3))) for n in range(100)])

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
            locate_bar([(0.0, LidarDistance(1250.0)), (1.0, LidarDistance(250.0))])


if __name__ == "__main__":
    unittest.main()
