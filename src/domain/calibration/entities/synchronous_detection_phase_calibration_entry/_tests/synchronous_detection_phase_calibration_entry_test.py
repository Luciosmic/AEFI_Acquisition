import unittest
from datetime import datetime, timezone
from uuid import UUID

from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)


def make_hardware_signature(**overrides):
    defaults = dict(
        excitation_electronics_board_name="v1.2",
        conditioning_electronics_board_name="v2.0",
        sensor_name="v3.1_SN-001",
    )
    defaults.update(overrides)
    return HardwareSignature(**defaults)


class TestSynchronousDetectionPhaseCalibrationEntry(unittest.TestCase):
    def test_creates_with_required_fields(self):
        signature = make_hardware_signature()
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)
        entry_id = UUID("12345678-1234-5678-1234-567812345678")
        recorded_at = datetime.now(timezone.utc)

        entry = SynchronousDetectionPhaseCalibrationEntry(
            entry_id=entry_id,
            hardware_signature=signature,
            points=(point,),
            recorded_at=recorded_at,
        )

        self.assertEqual(entry.entry_id, entry_id)
        self.assertEqual(entry.hardware_signature, signature)
        self.assertEqual(entry.points, (point,))
        self.assertEqual(entry.recorded_at, recorded_at)

    def test_is_immutable(self):
        signature = make_hardware_signature()
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)
        entry = SynchronousDetectionPhaseCalibrationEntry(
            entry_id=UUID("12345678-1234-5678-1234-567812345678"),
            hardware_signature=signature,
            points=(point,),
            recorded_at=datetime.now(timezone.utc),
        )
        with self.assertRaises(Exception):
            entry.points = ()

    def test_rejects_empty_points(self):
        signature = make_hardware_signature()
        with self.assertRaises(ValueError):
            SynchronousDetectionPhaseCalibrationEntry(
                entry_id=UUID("12345678-1234-5678-1234-567812345678"),
                hardware_signature=signature,
                points=(),
                recorded_at=datetime.now(timezone.utc),
            )

    def test_single_factory_wraps_one_point(self):
        signature = make_hardware_signature()
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)

        entry = SynchronousDetectionPhaseCalibrationEntry.single(signature, point)

        self.assertEqual(entry.points, (point,))
        self.assertEqual(entry.hardware_signature, signature)

    def test_single_factory_mints_fresh_uuid_and_utc_timestamp(self):
        signature = make_hardware_signature()
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)

        entry_a = SynchronousDetectionPhaseCalibrationEntry.single(signature, point)
        entry_b = SynchronousDetectionPhaseCalibrationEntry.single(signature, point)

        self.assertIsInstance(entry_a.entry_id, UUID)
        self.assertNotEqual(entry_a.entry_id, entry_b.entry_id)
        self.assertIsNotNone(entry_a.recorded_at.tzinfo)


if __name__ == "__main__":
    unittest.main()
