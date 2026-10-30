import unittest

from domain.detection_devices.lidar.lidar_distance.lidar_distance import LidarDistance


class LidarDistanceTest(unittest.TestCase):
    def test_raw_zero_is_no_return_never_a_distance_of_zero(self):
        distance = LidarDistance.from_raw(0, 1.0)
        self.assertFalse(distance.has_return)
        self.assertIsNone(distance.distance_mm)
        self.assertEqual(distance, LidarDistance.no_return())

    def test_positive_raw_is_a_valid_return_in_mm(self):
        distance = LidarDistance.from_raw(95, 1.0)
        self.assertTrue(distance.has_return)
        self.assertEqual(distance.distance_mm, 95.0)
        self.assertEqual(LidarDistance.from_raw(10, 2.5).distance_mm, 25.0)

    def test_negative_raw_is_no_return(self):
        self.assertFalse(LidarDistance.from_raw(-3, 1.0).has_return)

    def test_a_valid_distance_is_always_positive_and_finite(self):
        for invalid in (0.0, -1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                LidarDistance(invalid)

    def test_refuses_a_meaningless_conversion_factor(self):
        with self.assertRaises(ValueError):
            LidarDistance.from_raw(95, 0.0)

    def test_is_immutable(self):
        with self.assertRaises(Exception):
            LidarDistance(95.0).distance_mm = 1.0


if __name__ == "__main__":
    unittest.main()
