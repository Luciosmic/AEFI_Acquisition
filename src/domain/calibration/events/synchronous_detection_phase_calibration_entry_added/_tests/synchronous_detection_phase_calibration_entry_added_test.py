import unittest
from datetime import datetime, timezone
from uuid import uuid4

from domain.calibration.events.synchronous_detection_phase_calibration_entry_added.synchronous_detection_phase_calibration_entry_added import (
    SynchronousDetectionPhaseCalibrationEntryAdded,
)
from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)


def make_entry():
    signature = HardwareSignature(
        excitation_board_version="v1.2",
        conditioning_board_version="v2.0",
        sensor_version="v3.1",
        sensor_serial_number=None,
    )
    point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)
    return SynchronousDetectionPhaseCalibrationEntry(
        entry_id=uuid4(),
        hardware_signature=signature,
        points=(point,),
        recorded_at=datetime.now(timezone.utc),
    )


class TestSynchronousDetectionPhaseCalibrationEntryAdded(unittest.TestCase):
    def test_carries_entry(self):
        entry = make_entry()
        event = SynchronousDetectionPhaseCalibrationEntryAdded(entry=entry)
        self.assertEqual(event.entry, entry)

    def test_is_frozen(self):
        entry = make_entry()
        event = SynchronousDetectionPhaseCalibrationEntryAdded(entry=entry)
        with self.assertRaises(Exception):
            event.entry = make_entry()


if __name__ == "__main__":
    unittest.main()
