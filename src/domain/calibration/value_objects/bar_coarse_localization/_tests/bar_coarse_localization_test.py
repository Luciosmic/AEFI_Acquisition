import unittest

from domain.calibration.value_objects.bar_coarse_localization.bar_coarse_localization import (
    BarCoarseLocalization,
)


def make(on=250.0, off=1250.0, first=100.0, second=900.0):
    return BarCoarseLocalization(
        on_bar_distance_mm=on,
        off_bar_distance_mm=off,
        plateau_noise_mm=2.0,
        first_front_increment=first,
        second_front_increment=second,
        profile_point_count=50,
    )


class BarCoarseLocalizationTest(unittest.TestCase):
    def test_threshold_is_midway_between_plateaus(self):
        located = make()
        self.assertEqual(located.threshold_mm, 750.0)
        self.assertEqual(located.contrast_mm, 1000.0)
        self.assertEqual(located.bar_length_increments, 800.0)

    def test_refuses_a_bar_farther_than_the_floor(self):
        with self.assertRaises(ValueError):
            make(on=1250.0, off=250.0)

    def test_refuses_fronts_in_the_wrong_order(self):
        with self.assertRaises(ValueError):
            make(first=900.0, second=100.0)


if __name__ == "__main__":
    unittest.main()
