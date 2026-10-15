import math
import unittest

from domain.calibration.value_objects.bar_point_reading.bar_point_reading import (
    BarPointClassification,
    BarPointReading,
)
from domain.shared_kernel.value_objects.lidar_distance.lidar_distance import LidarDistance

NO_RETURN = LidarDistance.no_return()


def _lidar(*distances):
    return [NO_RETURN if d is None else LidarDistance(d) for d in distances]


THRESHOLD = 750.0  # bar at 250 mm, floor at 1250 mm


class BarPointReadingTest(unittest.TestCase):
    def test_short_distance_is_on_the_bar(self):
        reading = BarPointReading.from_samples([251.0, 249.0, 250.0, 250.5])
        self.assertIs(reading.classify(THRESHOLD, k_sigma=3.0), BarPointClassification.ON_BAR)

    def test_long_distance_is_off_the_bar(self):
        reading = BarPointReading.from_samples([1249.0, 1251.0, 1250.0])
        self.assertIs(reading.classify(THRESHOLD, k_sigma=3.0), BarPointClassification.OFF_BAR)

    def test_mean_within_noise_of_threshold_is_undecidable(self):
        # spot half on the bar: mean 760, sigma 40, k=4 -> half width 3*40/2 = 60 > 10
        reading = BarPointReading(mean_distance_mm=760.0, std_distance_mm=40.0, sample_count=4)
        self.assertIs(reading.classify(THRESHOLD, k_sigma=3.0), BarPointClassification.UNDECIDABLE)

    def test_more_samples_shrink_the_undecidable_zone(self):
        few = BarPointReading(mean_distance_mm=760.0, std_distance_mm=40.0, sample_count=4)
        many = BarPointReading(mean_distance_mm=760.0, std_distance_mm=40.0, sample_count=400)
        self.assertIs(few.classify(THRESHOLD, 3.0), BarPointClassification.UNDECIDABLE)
        self.assertIs(many.classify(THRESHOLD, 3.0), BarPointClassification.OFF_BAR)
        self.assertAlmostEqual(many.undecidable_half_width_mm(3.0), 3.0 * 40.0 / math.sqrt(400))

    def test_exactly_on_threshold_without_noise_is_undecidable(self):
        reading = BarPointReading(mean_distance_mm=THRESHOLD, std_distance_mm=0.0, sample_count=5)
        self.assertIs(reading.classify(THRESHOLD, k_sigma=3.0), BarPointClassification.UNDECIDABLE)

    def test_needs_two_samples_for_a_spread(self):
        with self.assertRaises(ValueError):
            BarPointReading.from_samples([250.0])

    def test_no_return_is_never_averaged(self):
        reading = BarPointReading.from_lidar(_lidar(95.0, None, 97.0, None))
        self.assertEqual((reading.mean_distance_mm, reading.sample_count), (96.0, 2))

    def test_enough_valid_returns_are_classified_on_their_mean(self):
        samples = _lidar(1249.0, None, 1251.0, None, 1250.0)
        self.assertTrue(BarPointReading.has_enough_returns(samples, 3))
        verdict = BarPointReading.classify_lidar(samples, 3, THRESHOLD, 3.0)
        self.assertIs(verdict, BarPointClassification.OFF_BAR)

    def test_any_valid_return_is_the_bar_when_the_floor_gives_none(self):
        verdict = BarPointReading.classify_lidar(_lidar(95.0, 96.0, None, 94.5), 3, None, 3.0)
        self.assertIs(verdict, BarPointClassification.ON_BAR)

    def test_no_valid_return_is_off_the_bar(self):
        verdict = BarPointReading.classify_lidar([NO_RETURN] * 24, 6, None, 3.0)
        self.assertIs(verdict, BarPointClassification.OFF_BAR)

    def test_some_but_too_few_returns_are_undecidable(self):
        samples = _lidar(95.0, 96.0, *([None] * 20))
        self.assertFalse(BarPointReading.has_enough_returns(samples, 6))
        self.assertIs(BarPointReading.classify_lidar(samples, 6, None, 3.0), BarPointClassification.UNDECIDABLE)

    def test_a_point_without_any_sample_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            BarPointReading.classify_lidar([], 6, None, 3.0)

    def test_rejects_negative_k_sigma(self):
        reading = BarPointReading.from_samples([250.0, 251.0])
        with self.assertRaises(ValueError):
            reading.classify(THRESHOLD, k_sigma=-1.0)


if __name__ == "__main__":
    unittest.main()
