import unittest
from uuid import uuid4

from domain.calibration.events.sensor_calibration_entry_added.sensor_calibration_entry_added import (
    SensorCalibrationEntryAdded,
)
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)


def make_entry():
    return SensorCalibrationEntry.single(uuid4(), uuid4(), SensorRotationAngles(35.3, 45.0, 0.0))


class TestSensorCalibrationEntryAdded(unittest.TestCase):
    def test_carries_entry(self):
        entry = make_entry()
        event = SensorCalibrationEntryAdded(entry=entry)
        self.assertEqual(event.entry, entry)

    def test_is_frozen(self):
        event = SensorCalibrationEntryAdded(entry=make_entry())
        with self.assertRaises(Exception):
            event.entry = make_entry()


if __name__ == "__main__":
    unittest.main()
