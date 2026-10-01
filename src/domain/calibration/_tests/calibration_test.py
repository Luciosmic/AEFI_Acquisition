from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
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
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.events.sensor_calibration_entry_added.sensor_calibration_entry_added import (
    SensorCalibrationEntryAdded,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.events.source_geometry_calibration_entry_added.source_geometry_calibration_entry_added import (
    SourceGeometryCalibrationEntryAdded,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.calibration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentCharacterized,
    HardwareComponentMounted,
)


def make_hardware_signature(**overrides):
    defaults = dict(
        excitation_electronics_board_name="v1.2",
        conditioning_electronics_board_name="v2.0",
        sensor_name="v3.1_SN-001",
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

    def test_record_sensor_calibration_entry_returns_entry_and_emits_event(self):
        calibration = Calibration()
        sensor_mounting = uuid4()  # identity of the sensor's current mounting
        geometry = uuid4()  # identity of a source geometry entry
        angles = SensorRotationAngles(theta_x_degrees=-1.84, theta_y_degrees=2.03, theta_z_degrees=1.27)

        entry = calibration.record_sensor_calibration_entry(sensor_mounting, geometry, angles)

        self.assertIsInstance(entry, SensorCalibrationEntry)
        self.assertEqual(entry.sensor_mounting_id, sensor_mounting)
        self.assertEqual(entry.source_geometry_entry_id, geometry)
        self.assertEqual(entry.angles, angles)

        events = calibration.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SensorCalibrationEntryAdded)
        self.assertEqual(events[0].entry, entry)

    def test_record_sensor_calibration_entry_requires_a_mounted_sensor(self):
        calibration = Calibration()
        angles = SensorRotationAngles(theta_x_degrees=0.0, theta_y_degrees=0.0, theta_z_degrees=0.0)

        with self.assertRaises(ValueError):
            calibration.record_sensor_calibration_entry(None, uuid4(), angles)
        self.assertEqual(calibration.domain_events, [])

    def test_mounting_gets_its_own_identity_carried_by_the_event(self):
        calibration = Calibration()

        selection = calibration.mount_hardware_component(HardwareComponentKind.SENSOR, "v2b_SN-3", {"v2b_SN-3"}, None)

        (event,) = calibration.domain_events
        self.assertEqual(event.mounting_id, selection.mounting_id)

    def test_record_source_geometry_calibration_entry_returns_entry_and_emits_event(self):
        calibration = Calibration()
        sphere_diameters = tuple(
            CaliperMeasurement.from_resolution(v) for v in (0.0196, 0.0196, 0.0195, 0.0195)
        )
        pairwise_distances_ext = tuple(
            CaliperMeasurement.from_resolution(v)
            for v in (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)
        )

        entry = calibration.record_source_geometry_calibration_entry(
            sphere_diameters, pairwise_distances_ext
        )

        self.assertIsInstance(entry, SourceGeometryCalibrationEntry)
        self.assertEqual(entry.sphere_diameters, sphere_diameters)
        self.assertEqual(entry.pairwise_distances_ext, pairwise_distances_ext)

        events = calibration.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SourceGeometryCalibrationEntryAdded)
        self.assertEqual(events[0].entry, entry)

    def test_record_hardware_component_characterization_emits_event(self):
        calibration = Calibration()

        entry = calibration.record_hardware_component_characterization(
            HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD, "AmpliHT_v2", {"bandwidth_hz": 1e6}
        )

        self.assertEqual(entry.component_name, "AmpliHT_v2")
        self.assertEqual(entry.characterization.uncharacterized(), ["gain"])
        (event,) = calibration.domain_events
        self.assertIsInstance(event, HardwareComponentCharacterized)

    def test_mount_hardware_component_records_selection_and_emits_event(self):
        calibration = Calibration()

        selection = calibration.mount_hardware_component(HardwareComponentKind.ADC, "B", {"A", "B"}, "A")

        self.assertEqual(selection.component_name, "B")
        (event,) = calibration.domain_events
        self.assertIsInstance(event, HardwareComponentMounted)

    def test_mount_refuses_uncharacterized_component(self):
        calibration = Calibration()
        with self.assertRaises(ValueError):
            calibration.mount_hardware_component(HardwareComponentKind.ADC, "Unknown", {"A"}, None)
        self.assertEqual(calibration.domain_events, [])

    def test_mount_already_mounted_component_is_a_logged_no_op(self):
        calibration = Calibration()
        with self.assertLogs("domain.calibration.calibration", level="INFO") as logs:
            self.assertIsNone(calibration.mount_hardware_component(HardwareComponentKind.ADC, "A", {"A"}, "A"))
        self.assertEqual(calibration.domain_events, [])
        self.assertIn("already mounted", logs.output[0])

    def test_mounted_component_is_latest_selection(self):
        from datetime import datetime, timezone
        from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
            HardwareComponentSelection,
        )
        kind = HardwareComponentKind.MOTORS
        selections = [
            HardwareComponentSelection(kind, "B", datetime(2026, 6, 1, tzinfo=timezone.utc), uuid4()),
            HardwareComponentSelection(kind, "A", datetime(2026, 1, 1, tzinfo=timezone.utc), uuid4()),
        ]
        self.assertEqual(Calibration.mounted_component_name(selections), "B")
        self.assertIsNone(Calibration.mounted_component_name([]))

    def test_current_characterization_is_latest_entry_of_that_component(self):
        record = Calibration().record_hardware_component_characterization
        kind = HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD
        first = record(kind, "A", {})
        completed = record(kind, "A", {"gain": 20.0})
        other = record(kind, "B", {})

        self.assertEqual(Calibration.current_characterization([first, completed, other], "A"), completed)
        self.assertIsNone(Calibration.current_characterization([first], None))

    def test_resolve_current_hardware_signature_warns_per_board_kind_not_mounted(self):
        fallback = make_hardware_signature()

        with self.assertLogs("domain.calibration.calibration", level="WARNING") as logs:
            resolved = Calibration.resolve_current_hardware_signature(fallback, None, None, None)

        self.assertEqual(resolved, fallback)
        self.assertEqual(len(logs.records), 3)  # sensor + both boards on the template

    def test_resolve_current_hardware_signature_uses_mounted_board_names(self):
        resolved = Calibration.resolve_current_hardware_signature(
            make_hardware_signature(), "cond_X", "exc_Y", "sensor_Z"
        )

        self.assertEqual(resolved.conditioning_electronics_board_name, "cond_X")
        self.assertEqual(resolved.excitation_electronics_board_name, "exc_Y")
        self.assertEqual(resolved.sensor_name, "sensor_Z")

    def test_reconstitute_restores_exact_state(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertTrue(calibration.synchronous_detection_compensation_enabled)

    def test_reconstitute_does_not_emit_any_domain_event(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertEqual(calibration.domain_events, [])


if __name__ == "__main__":
    unittest.main()
