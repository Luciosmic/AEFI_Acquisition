import unittest

from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention


class TestSensorRotationAngles(unittest.TestCase):
    def test_creates_with_all_fields(self):
        angles = SensorRotationAngles(theta_x_degrees=36.0, theta_y_degrees=44.0, theta_z_degrees=1.0)
        self.assertEqual(angles.theta_x_degrees, 36.0)
        self.assertEqual(angles.theta_y_degrees, 44.0)
        self.assertEqual(angles.theta_z_degrees, 1.0)

    def test_allows_zero_angles(self):
        angles = SensorRotationAngles(theta_x_degrees=0.0, theta_y_degrees=0.0, theta_z_degrees=0.0)
        self.assertEqual(angles.theta_x_degrees, 0.0)

    def test_is_immutable(self):
        angles = SensorRotationAngles(theta_x_degrees=0.0, theta_y_degrees=0.0, theta_z_degrees=0.0)
        with self.assertRaises(Exception):
            angles.theta_x_degrees = 10.0

    def test_equal_angles_compare_equal(self):
        angles_a = SensorRotationAngles(theta_x_degrees=-1.84, theta_y_degrees=2.03, theta_z_degrees=1.27)
        angles_b = SensorRotationAngles(theta_x_degrees=-1.84, theta_y_degrees=2.03, theta_z_degrees=1.27)
        self.assertEqual(angles_a, angles_b)

    def test_convention_defaults_to_standard(self):
        angles = SensorRotationAngles(theta_x_degrees=35.26, theta_y_degrees=45.0, theta_z_degrees=0.0)
        self.assertEqual(angles.convention, RotationConvention.standard())


if __name__ == "__main__":
    unittest.main()
