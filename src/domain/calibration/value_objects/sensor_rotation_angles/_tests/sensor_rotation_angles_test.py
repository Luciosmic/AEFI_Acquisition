import unittest

import numpy as np

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

    def test_mounting_matrix_is_p_of_the_reference_convention(self):
        # Reference: scipy 'XYZ' UPPERCASE (rotation_convention_intention.md)
        from scipy.spatial.transform import Rotation

        angles = SensorRotationAngles(theta_x_degrees=35.26, theta_y_degrees=45.0, theta_z_degrees=12.0)
        expected = Rotation.from_euler("XYZ", [35.26, 45.0, 12.0], degrees=True).as_matrix()
        np.testing.assert_allclose(angles.mounting_matrix(), expected, atol=1e-12)

    def test_mounting_matrix_columns_are_sensor_axes_in_sources_frame(self):
        angles = SensorRotationAngles(theta_x_degrees=0.0, theta_y_degrees=0.0, theta_z_degrees=90.0)
        np.testing.assert_allclose(angles.mounting_matrix()[:, 0], [0.0, 1.0, 0.0], atol=1e-12)


if __name__ == "__main__":
    unittest.main()
