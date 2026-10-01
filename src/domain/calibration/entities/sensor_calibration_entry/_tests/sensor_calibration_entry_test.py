import unittest
from datetime import datetime
from uuid import UUID, uuid4

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)

SENSOR_MOUNTING = uuid4()
SOURCE_GEOMETRY = uuid4()


class TestSensorCalibrationEntry(unittest.TestCase):
    def test_single_mints_entry_referencing_mounting_and_geometry(self):
        angles = SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.0)
        entry = SensorCalibrationEntry.single(SENSOR_MOUNTING, SOURCE_GEOMETRY, angles)

        self.assertIsInstance(entry.entry_id, UUID)
        self.assertIsInstance(entry.recorded_at, datetime)
        self.assertEqual(entry.sensor_mounting_id, SENSOR_MOUNTING)
        self.assertEqual(entry.source_geometry_entry_id, SOURCE_GEOMETRY)
        self.assertEqual(entry.angles, angles)

    def test_is_immutable(self):
        entry = SensorCalibrationEntry.single(
            SENSOR_MOUNTING, SOURCE_GEOMETRY, SensorRotationAngles(0.0, 0.0, 0.0)
        )
        with self.assertRaises(Exception):
            entry.angles = None

    def test_successive_entries_get_distinct_ids(self):
        angles = SensorRotationAngles(0.0, 0.0, 0.0)
        entry_a = SensorCalibrationEntry.single(SENSOR_MOUNTING, SOURCE_GEOMETRY, angles)
        entry_b = SensorCalibrationEntry.single(SENSOR_MOUNTING, SOURCE_GEOMETRY, angles)
        self.assertNotEqual(entry_a.entry_id, entry_b.entry_id)


if __name__ == "__main__":
    unittest.main()
