"""Unit tests for SourceGeometryCalibrationPresenter (see source_geometry_calibration_presenter.py)."""

import unittest
from datetime import datetime, timezone
from typing import List, Optional

from interface.presenters.source_geometry_calibration_presenter import SourceGeometryCalibrationPresenter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.source_geometry_calibration_service.i_api_source_geometry_calibration_service import (
    IApiSourceGeometryCalibrationService,
)
from application.services.source_geometry_calibration_service.dtos.source_geometry_calibration_dto import (
    SourceGeometryCalibrationDTO,
)
from application.services.source_geometry_calibration_service.source_geometry_calibration_service import (
    SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC,
)

_DIAMETERS_M = [0.0196, 0.0196, 0.0195, 0.0195]
_DISTANCES_M = [0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450]


class FakeSourceGeometryCalibrationService(IApiSourceGeometryCalibrationService):
    """Simple hand-written stub — not a Mock: lets tests assert on state,
    not on call interactions (per this repo's Fake-vs-Mock test standard)."""

    def __init__(self, event_bus: InMemoryEventBus):
        self._event_bus = event_bus
        self.latest: Optional[SourceGeometryCalibrationDTO] = None
        self.record_calibration_calls = []
        self.record_calibration_error: Exception | None = None

    def record_calibration(
        self,
        sphere_diameters_m: List[float],
        pairwise_distances_ext_m: List[float],
        resolution_m: float = 0.00002,
        k: float = 2.0,
    ) -> None:
        self.record_calibration_calls.append((sphere_diameters_m, pairwise_distances_ext_m))
        if self.record_calibration_error is not None:
            raise self.record_calibration_error
        self.latest = SourceGeometryCalibrationDTO(
            sphere_diameters_m=tuple(sphere_diameters_m),
            sphere_diameters_uncertainty_m=(1.15e-5,) * 4,
            pairwise_distances_ext_m=tuple(pairwise_distances_ext_m),
            pairwise_distances_ext_uncertainty_m=(1.15e-5,) * 6,
            k=k,
            recorded_at=datetime.now(timezone.utc),
        )
        self._event_bus.publish(SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC, object())

    def get_latest_calibration(self) -> Optional[SourceGeometryCalibrationDTO]:
        return self.latest


class TestSourceGeometryCalibrationPresenter(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = FakeSourceGeometryCalibrationService(self.event_bus)
        self.presenter = SourceGeometryCalibrationPresenter(self.service, self.event_bus)
        self.received_latest = []
        self.received_status_messages = []
        self.presenter.latest_calibration_updated.connect(self.received_latest.append)
        self.presenter.status_message.connect(self.received_status_messages.append)

    def test_refresh_state_emits_none_when_nothing_recorded(self):
        self.presenter.refresh_state()

        self.assertEqual(self.received_latest, [None])

    def test_on_save_calibration_requested_calls_service_and_reports_success(self):
        self.presenter.on_save_calibration_requested(_DIAMETERS_M, _DISTANCES_M)

        self.assertEqual(self.service.record_calibration_calls, [(_DIAMETERS_M, _DISTANCES_M)])
        self.assertEqual(self.received_status_messages, ["Calibration enregistrée"])

    def test_on_save_calibration_requested_auto_refreshes_via_entry_added_event(self):
        self.presenter.on_save_calibration_requested(_DIAMETERS_M, _DISTANCES_M)

        self.assertEqual(len(self.received_latest), 1)
        self.assertEqual(self.received_latest[0].sphere_diameters_m, tuple(_DIAMETERS_M))

    def test_on_save_calibration_requested_catches_service_exception(self):
        self.service.record_calibration_error = ValueError("boom")

        self.presenter.on_save_calibration_requested(_DIAMETERS_M, _DISTANCES_M)

        self.assertEqual(len(self.received_status_messages), 1)
        self.assertIn("Erreur", self.received_status_messages[0])
        self.assertIn("boom", self.received_status_messages[0])
        self.assertEqual(self.received_latest, [])  # no entry-added event on failure


if __name__ == "__main__":
    unittest.main()
