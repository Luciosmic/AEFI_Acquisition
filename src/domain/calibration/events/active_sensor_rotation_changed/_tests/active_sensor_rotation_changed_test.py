import unittest

from domain.calibration.events.active_sensor_rotation_changed.active_sensor_rotation_changed import (
    ActiveSensorRotationChanged,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)


class TestActiveSensorRotationChanged(unittest.TestCase):
    def test_carries_angles_and_origin(self):
        angles = SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.0)
        event = ActiveSensorRotationChanged(angles=angles, is_calibrated=False, recorded_at=None)
        self.assertEqual(event.angles, angles)
        self.assertFalse(event.is_calibrated)
        self.assertIsNone(event.recorded_at)

    def test_is_trial_defaults_to_false(self):
        angles = SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.0)
        event = ActiveSensorRotationChanged(angles=angles, is_calibrated=False, recorded_at=None)
        self.assertFalse(event.is_trial)

    def test_is_frozen(self):
        angles = SensorRotationAngles(theta_x_degrees=0.0, theta_y_degrees=0.0, theta_z_degrees=0.0)
        event = ActiveSensorRotationChanged(angles=angles, is_calibrated=False, recorded_at=None)
        with self.assertRaises(Exception):
            event.is_calibrated = True


if __name__ == "__main__":
    unittest.main()
