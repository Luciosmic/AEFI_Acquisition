from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
import unittest

from domain.test_bench_calibration.calibration import Calibration
from domain.test_bench_configuration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.test_bench_calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.test_bench_calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.test_bench_calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)
from domain.test_bench_calibration.events.synchronous_detection_phase_calibration_entry_added.synchronous_detection_phase_calibration_entry_added import (
    SynchronousDetectionPhaseCalibrationEntryAdded,
)
from domain.test_bench_calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.test_bench_calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.test_bench_calibration.events.sensor_calibration_entry_added.sensor_calibration_entry_added import (
    SensorCalibrationEntryAdded,
)
from domain.test_bench_calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.test_bench_calibration.errors.source_geometry_inconsistent_error import SourceGeometryInconsistentError
from domain.test_bench_calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.test_bench_calibration.events.source_geometry_calibration_entry_added.source_geometry_calibration_entry_added import (
    SourceGeometryCalibrationEntryAdded,
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

    def test_record_source_geometry_refuses_a_geometry_the_spheres_cannot_take(self):
        """No overlap, but S3 cannot reach both S1 and S2: nothing recorded."""
        calibration = Calibration()
        measure = lambda values: tuple(CaliperMeasurement.from_resolution(v) for v in values)

        with self.assertRaises(SourceGeometryInconsistentError):
            calibration.record_source_geometry_calibration_entry(
                measure((0.02,) * 4), measure((0.11, 0.11, 0.04, 0.08, 0.04, 0.08))
            )
        self.assertEqual(calibration.domain_events, [])

    def test_record_mechanical_transmission_entry_returns_entry_and_emits_event(self):
        from domain.test_bench_calibration.events.mechanical_transmission_calibration_entry_added.mechanical_transmission_calibration_entry_added import (
            MechanicalTransmissionCalibrationEntryAdded,
        )
        calibration = Calibration()
        motor, driver = uuid4(), uuid4()

        entry = calibration.record_mechanical_transmission_calibration_entry(motor, driver, 16, 3.5, 4.0, 21.11)

        self.assertEqual((entry.motor_mounting_id, entry.stepper_driver_mounting_id), (motor, driver))
        (event,) = calibration.domain_events
        self.assertIsInstance(event, MechanicalTransmissionCalibrationEntryAdded)
        self.assertEqual(event.entry, entry)

    def test_record_mechanical_transmission_entry_requires_mounted_motor_and_driver(self):
        calibration = Calibration()

        for motor, driver in ((None, uuid4()), (uuid4(), None)):
            with self.assertRaises(ValueError):
                calibration.record_mechanical_transmission_calibration_entry(motor, driver, 16, 3.5, 4.0, 21.11)
        self.assertEqual(calibration.domain_events, [])

    def test_current_mechanical_transmission_is_latest_for_the_mounted_motor_and_driver(self):
        calibration = Calibration()
        motor, driver, other_driver = uuid4(), uuid4(), uuid4()
        record = calibration.record_mechanical_transmission_calibration_entry
        old = record(motor, driver, 8, 3.5, 4.0, 21.11)
        new = record(motor, driver, 16, 3.5, 4.0, 21.11)
        swapped = record(motor, other_driver, 16, 3.5, 4.0, 21.11)
        entries = [old, new, swapped]

        self.assertEqual(Calibration.current_mechanical_transmission(entries, motor, driver), new)
        self.assertEqual(Calibration.current_mechanical_transmission(entries, motor, other_driver), swapped)
        self.assertIsNone(Calibration.current_mechanical_transmission(entries, uuid4(), driver))

    def test_reconstitute_restores_exact_state(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertTrue(calibration.synchronous_detection_compensation_enabled)

    def test_reconstitute_does_not_emit_any_domain_event(self):
        calibration = Calibration.reconstitute(synchronous_detection_compensation_enabled=True)

        self.assertEqual(calibration.domain_events, [])


if __name__ == "__main__":
    unittest.main()
