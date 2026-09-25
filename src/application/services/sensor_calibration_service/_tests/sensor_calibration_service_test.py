import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from application.services.sensor_calibration_service.sensor_calibration_service import (
    SensorCalibrationService,
    SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC,
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
)
from application.services.source_geometry_calibration_service.source_geometry_calibration_service import (
    SourceGeometryCalibrationService,
)
from application.services.hardware_component_service.hardware_component_service import (
    HARDWARE_COMPONENT_MOUNTED_TOPIC,
)
from infrastructure.persistence.calibration.fake.fake_source_geometry_calibration_repository import (
    FakeSourceGeometryCalibrationRepository,
)
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentMounted,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_sensor_calibration_repository import (
    FakeSensorCalibrationRepository,
)
from tool.diagram_friendly_test import DiagramFriendlyTest


IDEAL_ANGLES = SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.0)


class TestSensorCalibrationService(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.sensor_mounting_id = uuid4()
        self.source_geometry_entry_id = uuid4()
        self.repository = FakeSensorCalibrationRepository()
        self.event_bus = InMemoryEventBus()
        self.service = self._make_service(self.sensor_mounting_id)

    def _make_service(self, sensor_mounting_id):
        return SensorCalibrationService(
            calibration_repository=self.repository,
            sensor_mounting_id=sensor_mounting_id,
            source_geometry_entry_id=self.source_geometry_entry_id,
            default_angles=IDEAL_ANGLES,
            event_bus=self.event_bus,
        )

    def _record(self, theta_x=1.0, theta_y=2.0, theta_z=3.0):
        self.service.record_calibration(theta_x_degrees=theta_x, theta_y_degrees=theta_y, theta_z_degrees=theta_z)

    def _mount(self, kind=HardwareComponentKind.SENSOR, name="v2b_SN-3"):
        """A new mounting (as HardwareComponentService publishes it); returns its identity."""
        mounting_id = uuid4()
        self.event_bus.publish(
            HARDWARE_COMPONENT_MOUNTED_TOPIC,
            HardwareComponentMounted(kind=kind, component_name=name, mounting_id=mounting_id),
        )
        return mounting_id

    def _record_source_geometry(self, diameter_s1: float):
        """Record a new source geometry entry; returns its identity."""
        geometry_service = SourceGeometryCalibrationService(
            calibration_repository=FakeSourceGeometryCalibrationRepository(), event_bus=self.event_bus
        )
        geometry_service.record_calibration(
            sphere_diameters_m=[diameter_s1, 0.0196, 0.0195, 0.0195],
            pairwise_distances_ext_m=[0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450],
        )
        return geometry_service.get_current_entry_id()

    def _collect_active_rotation_events(self):
        received = []
        self.event_bus.subscribe(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, received.append)
        return received

    # -- record_calibration -----------------------------------------------------

    def test_record_calibration_references_sensor_mounting_and_geometry(self):
        self._record(theta_x=-1.84, theta_y=2.03, theta_z=1.27)

        (entry,) = self.repository.find_all()
        self.assertEqual(entry.sensor_mounting_id, self.sensor_mounting_id)
        self.assertEqual(entry.source_geometry_entry_id, self.source_geometry_entry_id)
        self.assertEqual(
            (entry.angles.theta_x_degrees, entry.angles.theta_y_degrees, entry.angles.theta_z_degrees),
            (-1.84, 2.03, 1.27),
        )

    def test_record_calibration_publishes_entry_added_event(self):
        received = []
        self.event_bus.subscribe(SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC, received.append)

        self._record()

        self.assertEqual(len(received), 1)

    def test_no_sensor_mounted_refuses_angle_calibration(self):
        self.service = self._make_service(sensor_mounting_id=None)

        with self.assertRaises(ValueError):
            self._record()
        self.assertEqual(self.repository.find_all(), [])
        self.assertFalse(self.service.get_active_rotation().is_calibrated)

    # -- get_latest_calibration ---------------------------------------------------

    def test_get_latest_calibration_returns_none_when_nothing_recorded(self):
        self.assertIsNone(self.service.get_latest_calibration())

    def test_get_latest_calibration_returns_dto_for_current_mounting_and_geometry(self):
        self._record(theta_x=-1.84, theta_y=2.03, theta_z=1.27)

        dto = self.service.get_latest_calibration()

        self.assertEqual((dto.theta_x_degrees, dto.theta_y_degrees, dto.theta_z_degrees), (-1.84, 2.03, 1.27))

    def test_get_latest_calibration_ignores_other_mountings_and_geometries(self):
        for mounting, geometry in ((uuid4(), self.source_geometry_entry_id), (self.sensor_mounting_id, uuid4())):
            self.repository.add(
                SensorCalibrationEntry(
                    entry_id=uuid4(),
                    sensor_mounting_id=mounting,
                    source_geometry_entry_id=geometry,
                    angles=SensorRotationAngles(99.0, 99.0, 99.0),
                    recorded_at=datetime.now(timezone.utc),
                )
            )

        self.assertIsNone(self.service.get_latest_calibration())

    def test_get_latest_calibration_picks_most_recent_entry(self):
        for theta, month in ((1.0, 1), (2.0, 6)):
            self.repository.add(
                SensorCalibrationEntry(
                    entry_id=uuid4(),
                    sensor_mounting_id=self.sensor_mounting_id,
                    source_geometry_entry_id=self.source_geometry_entry_id,
                    angles=SensorRotationAngles(theta, theta, theta),
                    recorded_at=datetime(2024, month, 1, tzinfo=timezone.utc),
                )
            )

        self.assertEqual(self.service.get_latest_calibration().theta_x_degrees, 2.0)

    # -- sensor mounting ------------------------------------------------------------

    def test_remounting_the_sensor_falls_back_to_ideal_angles(self):
        """The angles belong to one mounting: a new mounting (even of the same
        sensor) must be calibrated again."""
        self._record(theta_x=36.0)
        received = self._collect_active_rotation_events()

        self._mount(name="v2b_SN-3")

        self.assertFalse(self.service.get_active_rotation().is_calibrated)
        self.assertEqual(received[-1].angles, IDEAL_ANGLES)

    def test_next_calibration_references_the_new_mounting(self):
        new_mounting = self._mount()

        self._record(theta_x=36.0)

        self.assertEqual(self.repository.find_all()[-1].sensor_mounting_id, new_mounting)
        self.assertTrue(self.service.get_active_rotation().is_calibrated)

    def test_mounting_another_component_kind_is_ignored(self):
        self._record(theta_x=36.0)
        received = self._collect_active_rotation_events()

        self._mount(kind=HardwareComponentKind.ADC, name="ADS131A04")

        self.assertEqual(received, [])
        self.assertTrue(self.service.get_active_rotation().is_calibrated)

    def test_sensor_mounted_at_runtime_enables_calibration(self):
        self.service = self._make_service(sensor_mounting_id=None)

        new_mounting = self._mount()
        self._record()

        self.assertEqual(self.repository.find_all()[-1].sensor_mounting_id, new_mounting)

    # -- active rotation (applied to sensor readings) -------------------------------

    def test_active_rotation_is_the_ideal_default_when_nothing_recorded(self):
        dto = self.service.get_active_rotation()

        self.assertEqual((dto.theta_x_degrees, dto.theta_y_degrees, dto.theta_z_degrees), (35.3, 45.0, 0.0))
        self.assertFalse(dto.is_calibrated)
        self.assertIsNone(dto.recorded_at)

    def test_active_rotation_is_the_latest_calibration_for_the_current_mounting(self):
        self._record(theta_x=36.0, theta_y=44.0, theta_z=1.0)

        dto = self.service.get_active_rotation()

        self.assertEqual((dto.theta_x_degrees, dto.theta_y_degrees, dto.theta_z_degrees), (36.0, 44.0, 1.0))
        self.assertTrue(dto.is_calibrated)

    def test_record_calibration_publishes_active_rotation_changed(self):
        received = self._collect_active_rotation_events()

        self._record(theta_x=36.0)

        self.assertEqual(len(received), 1)
        self.assertTrue(received[0].is_calibrated)
        self.assertEqual(received[0].angles.theta_x_degrees, 36.0)

    def test_new_source_geometry_falls_back_to_ideal_angles(self):
        self._record(theta_x=36.0)
        received = self._collect_active_rotation_events()

        self._record_source_geometry(diameter_s1=0.0200)

        self.assertFalse(self.service.get_active_rotation().is_calibrated)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].angles, IDEAL_ANGLES)

    def test_new_source_geometry_is_referenced_by_the_next_calibration(self):
        new_geometry_entry_id = self._record_source_geometry(diameter_s1=0.0200)

        self._record(theta_x=36.0)

        self.assertEqual(self.repository.find_all()[-1].source_geometry_entry_id, new_geometry_entry_id)
        self.assertTrue(self.service.get_active_rotation().is_calibrated)

    def test_same_geometry_entry_does_not_republish(self):
        received = self._collect_active_rotation_events()

        self.event_bus.publish(
            "sourcegeometrycalibrationentryadded",
            SimpleNamespace(entry=SimpleNamespace(entry_id=self.source_geometry_entry_id)),
        )

        self.assertEqual(received, [])

    def test_re_measured_geometry_with_same_values_is_a_new_reference(self):
        """Identity, not values: a new caliper measurement is a new geometry
        entry, even if its values are unchanged."""
        self._record(theta_x=36.0)

        self._record_source_geometry(diameter_s1=0.0196)

        self.assertFalse(self.service.get_active_rotation().is_calibrated)

    # -- trial rotation (live trial-and-error tuning, not persisted) -----------------

    def test_preview_rotation_publishes_and_reports_trial_angles(self):
        received = self._collect_active_rotation_events()

        self.service.preview_rotation(36.0, 44.0, 1.0)

        self.assertEqual(len(received), 1)
        self.assertTrue(received[0].is_trial)
        dto = self.service.get_active_rotation()
        self.assertEqual((dto.theta_x_degrees, dto.theta_y_degrees, dto.theta_z_degrees), (36.0, 44.0, 1.0))
        self.assertTrue(dto.is_trial)
        self.assertEqual(self.repository.find_all(), [])  # not persisted

    def test_reset_to_default_takes_ideal_angles_as_trial(self):
        self._record(theta_x=36.0, theta_y=44.0, theta_z=1.0)

        self.service.reset_to_default()

        dto = self.service.get_active_rotation()
        self.assertEqual((dto.theta_x_degrees, dto.theta_y_degrees, dto.theta_z_degrees), (35.3, 45.0, 0.0))
        self.assertTrue(dto.is_trial)

    def test_record_calibration_ends_the_trial(self):
        self.service.preview_rotation(36.0, 44.0, 1.0)

        self._record(theta_x=36.0, theta_y=44.0, theta_z=1.0)

        dto = self.service.get_active_rotation()
        self.assertFalse(dto.is_trial)
        self.assertTrue(dto.is_calibrated)

    def test_source_geometry_change_discards_the_trial(self):
        self.service.preview_rotation(36.0, 44.0, 1.0)

        self._record_source_geometry(diameter_s1=0.0200)

        self.assertFalse(self.service.get_active_rotation().is_trial)


if __name__ == "__main__":
    unittest.main()
