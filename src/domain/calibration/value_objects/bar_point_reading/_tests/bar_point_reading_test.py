import math
import unittest

from domain.calibration.value_objects.bar_point_reading.bar_point_reading import (
    BarPointClassification,
    BarPointReading,
)

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

    def test_rejects_negative_k_sigma(self):
        reading = BarPointReading.from_samples([250.0, 251.0])
        with self.assertRaises(ValueError):
            reading.classify(THRESHOLD, k_sigma=-1.0)


if __name__ == "__main__":
    unittest.main()
