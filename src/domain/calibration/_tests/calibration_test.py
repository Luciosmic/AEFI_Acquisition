import unittest

from domain.calibration.calibration import Calibration
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)
from domain.calibration.events.synchronous_detection_phase_calibration_entry_added.synchronous_detection_phase_calibration_entry_added import (
    SynchronousDetectionPhaseCalibrationEntryAdded,
)


def make_hardware_signature(**overrides):
    defaults = dict(
        excitation_board_version="v1.2",
        conditioning_board_version="v2.0",
        sensor_version="v3.1",
        sensor_serial_number="SN-001",
    )
    defaults.update(overrides)
    return HardwareSignature(**defaults)


class TestCalibration(unittest.TestCase):
    def test_default_compensation_is_disabled(self):
        calibration = Calibration()
        self.assertFalse(calibration.synchronous_detection_compensation_enabled)

    def test_set_compensation_enabled_updates_state_and_emits_event(self):
        calibration = Calibration()

        calibration.set_synchronous_detection_compensation_enabled(True)

        self.assertTrue(calibration.synchronous_detection_compensation_enabled)
        events = calibration.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SynchronousDetectionCompensationEnabledChanged)
        self.assertTrue(events[0].enabled)

    def test_set_compensation_enabled_is_idempotent_no_event_when_unchanged(self):
        calibration = Calibration()

        calibration.set_synchronous_detection_compensation_enabled(False)

        self.assertFalse(calibration.synchronous_detection_compensation_enabled)
        self.assertEqual(calibration.domain_events, [])

    def test_set_compensation_enabled_no_duplicate_event_on_repeated_call(self):
        calibration = Calibration()
        calibration.set_synchronous_detection_compensation_enabled(True)
        calibration.domain_events  # drain

        calibration.set_synchronous_detection_compensation_enabled(True)

        self.assertEqual(calibration.domain_events, [])

    def test_domain_events_drains(self):
        calibration = Calibration()
        calibration.set_synchronous_detection_compensation_enabled(True)

        first_read = calibration.domain_events
        second_read = calibration.domain_events

        self.assertEqual(len(first_read), 1)
        self.assertEqual(second_read, [])

    def test_record_synchronous_detection_phase_entry_returns_entry_and_emits_event(self):
        calibration = Calibration()
        signature = make_hardware_signature()
        point = SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=5.0)

        entry = calibration.record_synchronous_detection_phase_entry(signature, point)

        self.assertIsInstance(entry, SynchronousDetectionPhaseCalibrationEntry)
        self.assertEqual(entry.hardware_signature, signature)
        self.assertEqual(entry.points, (point,))

        events = calibration.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SynchronousDetectionPhaseCalibrationEntryAdded)
        self.assertEqual(events[0].entry, entry)

    def test_reconstitute_restores_exact_state(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertTrue(calibration.synchronous_detection_compensation_enabled)

    def test_reconstitute_does_not_emit_any_domain_event(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertEqual(calibration.domain_events, [])


if __name__ == "__main__":
    unittest.main()
