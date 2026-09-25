import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.source_geometry_calibration_service.source_geometry_calibration_service import (
    SourceGeometryCalibrationService,
    SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_source_geometry_calibration_repository import (
    FakeSourceGeometryCalibrationRepository,
)
from tool.diagram_friendly_test import DiagramFriendlyTest

_DIAMETERS_M = [0.0196, 0.0196, 0.0195, 0.0195]
_DISTANCES_M = [0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450]


def make_entry(diameters_m=_DIAMETERS_M, distances_m=_DISTANCES_M, recorded_at=None) -> SourceGeometryCalibrationEntry:
    entry = SourceGeometryCalibrationEntry.single(
        sphere_diameters=tuple(CaliperMeasurement.from_resolution(v) for v in diameters_m),
        pairwise_distances_ext=tuple(CaliperMeasurement.from_resolution(v) for v in distances_m),
    )
    if recorded_at is not None:
        entry = SourceGeometryCalibrationEntry(
            entry_id=entry.entry_id,
            sphere_diameters=entry.sphere_diameters,
            pairwise_distances_ext=entry.pairwise_distances_ext,
            recorded_at=recorded_at,
        )
    return entry


class TestSourceGeometryCalibrationService(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.repository = FakeSourceGeometryCalibrationRepository()
        self.event_bus = InMemoryEventBus()
        self.service = SourceGeometryCalibrationService(
            calibration_repository=self.repository, event_bus=self.event_bus
        )

    # -- record_calibration -----------------------------------------------------

    def test_record_calibration_persists_entry_with_gum_uncertainty(self):
        self.service.record_calibration(
            sphere_diameters_m=_DIAMETERS_M, pairwise_distances_ext_m=_DISTANCES_M
        )

        entries = self.repository.find_all()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual([m.value_m for m in entry.sphere_diameters], _DIAMETERS_M)
        self.assertEqual([m.value_m for m in entry.pairwise_distances_ext], _DISTANCES_M)
        self.assertAlmostEqual(entry.sphere_diameters[0].uncertainty_expanded_m, 1.15e-5, delta=1e-7)
        self.assertEqual(entry.sphere_diameters[0].k, 2.0)

    def test_record_calibration_publishes_entry_added_event(self):
        received = []
        self.event_bus.subscribe(SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC, lambda e: received.append(e))

        self.service.record_calibration(
            sphere_diameters_m=_DIAMETERS_M, pairwise_distances_ext_m=_DISTANCES_M
        )

        self.assertEqual(len(received), 1)

    def test_record_calibration_honors_custom_resolution_and_k(self):
        self.service.record_calibration(
            sphere_diameters_m=_DIAMETERS_M,
            pairwise_distances_ext_m=_DISTANCES_M,
            resolution_m=0.0001,
            k=3.0,
        )

        entry = self.repository.find_all()[0]
        expected_u_c = 0.0001 / (2 * (3 ** 0.5))
        self.assertAlmostEqual(entry.sphere_diameters[0].uncertainty_expanded_m, 3.0 * expected_u_c)
        self.assertEqual(entry.sphere_diameters[0].k, 3.0)

    # -- get_latest_calibration ---------------------------------------------------

    def test_get_latest_calibration_returns_none_when_nothing_recorded(self):
        self.assertIsNone(self.service.get_latest_calibration())

    def test_get_latest_calibration_returns_dto_after_record(self):
        self.service.record_calibration(
            sphere_diameters_m=_DIAMETERS_M, pairwise_distances_ext_m=_DISTANCES_M
        )

        dto = self.service.get_latest_calibration()

        self.assertIsNotNone(dto)
        self.assertEqual(dto.sphere_diameters_m, tuple(_DIAMETERS_M))
        self.assertEqual(dto.pairwise_distances_ext_m, tuple(_DISTANCES_M))
        self.assertAlmostEqual(dto.sphere_diameters_uncertainty_m[0], 1.15e-5, delta=1e-7)
        self.assertEqual(dto.k, 2.0)

    def test_get_latest_calibration_picks_most_recent_entry(self):
        older_entry = make_entry(diameters_m=[0.01, 0.01, 0.01, 0.01], recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
        newer_entry = make_entry(diameters_m=[0.02, 0.02, 0.02, 0.02], recorded_at=datetime(2024, 6, 1, tzinfo=timezone.utc))
        self.repository.add(older_entry)
        self.repository.add(newer_entry)

        dto = self.service.get_latest_calibration()

        self.assertEqual(dto.sphere_diameters_m, (0.02, 0.02, 0.02, 0.02))
        self.assertEqual(dto.recorded_at, newer_entry.recorded_at)

    # -- get_current_entry_id -----------------------------------------------------

    def test_get_current_entry_id_raises_when_registry_empty(self):
        with self.assertRaises(ValueError):
            self.service.get_current_entry_id()

    def test_get_current_entry_id_is_the_latest_entry_identity(self):
        self.service.record_calibration(
            sphere_diameters_m=_DIAMETERS_M, pairwise_distances_ext_m=_DISTANCES_M
        )

        (entry,) = self.repository.find_all()
        self.assertEqual(self.service.get_current_entry_id(), entry.entry_id)


if __name__ == "__main__":
    unittest.main()
