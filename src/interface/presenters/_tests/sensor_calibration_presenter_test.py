"""Unit tests for SensorCalibrationPresenter (see sensor_calibration_presenter.py)."""

import unittest
from datetime import datetime, timezone
from typing import Optional

from interface.presenters.sensor_calibration_presenter import SensorCalibrationPresenter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.sensor_calibration_service.i_api_sensor_calibration_service import (
    IApiSensorCalibrationService,
)
from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import (
    ActiveSensorRotationDTO,
    SensorCalibrationDTO,
)
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
    SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC,
)


class FakeSensorCalibrationService(IApiSensorCalibrationService):
    """Simple hand-written stub — not a Mock: lets tests assert on state,
    not on call interactions (per this repo's Fake-vs-Mock test standard)."""

    def __init__(self, event_bus: InMemoryEventBus):
        self._event_bus = event_bus
        self.latest: Optional[SensorCalibrationDTO] = None
        self.record_calibration_calls = []
        self.record_calibration_error: Exception | None = None
        self.preview_rotation_calls = []
        self.reset_to_default_calls = 0

    def preview_rotation(self, theta_x_degrees, theta_y_degrees, theta_z_degrees) -> None:
        self.preview_rotation_calls.append((theta_x_degrees, theta_y_degrees, theta_z_degrees))

    def reset_to_default(self) -> None:
        self.reset_to_default_calls += 1

    def record_calibration(self, theta_x_degrees, theta_y_degrees, theta_z_degrees) -> None:
        self.record_calibration_calls.append((theta_x_degrees, theta_y_degrees, theta_z_degrees))
        if self.record_calibration_error is not None:
            raise self.record_calibration_error
        self.latest = SensorCalibrationDTO(
            theta_x_degrees=theta_x_degrees,
            theta_y_degrees=theta_y_degrees,
            theta_z_degrees=theta_z_degrees,
            recorded_at=datetime.now(timezone.utc),
        )
        self._event_bus.publish(SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC, object())


    def get_latest_calibration(self) -> Optional[SensorCalibrationDTO]:
        return self.latest

    def get_active_rotation(self) -> ActiveSensorRotationDTO:
        if self.latest is None:
            return ActiveSensorRotationDTO(35.3, 45.0, 0.0, is_calibrated=False, is_trial=False, recorded_at=None)
        return ActiveSensorRotationDTO(
            self.latest.theta_x_degrees, self.latest.theta_y_degrees, self.latest.theta_z_degrees,
            is_calibrated=True, is_trial=False, recorded_at=self.latest.recorded_at,
        )


class TestSensorCalibrationPresenter(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = FakeSensorCalibrationService(self.event_bus)
        self.presenter = SensorCalibrationPresenter(self.service, self.event_bus)
        self.received_latest = []
        self.received_status_messages = []
        self.presenter.latest_calibration_updated.connect(self.received_latest.append)
        self.presenter.status_message.connect(self.received_status_messages.append)
        self.received_active = []
        self.presenter.active_rotation_updated.connect(self.received_active.append)

    def test_refresh_state_emits_ideal_active_rotation_when_nothing_recorded(self):
        self.presenter.refresh_state()

        self.assertEqual(len(self.received_active), 1)
        self.assertFalse(self.received_active[0].is_calibrated)
        self.assertEqual(self.received_active[0].theta_x_degrees, 35.3)

    def test_active_rotation_changed_event_refreshes_the_panel(self):
        """A source geometry change re-evaluates the active rotation without
        any record from this panel."""
        self.event_bus.publish(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, object())

        self.assertEqual(len(self.received_active), 1)

    def test_refresh_state_emits_none_when_nothing_recorded(self):
        self.presenter.refresh_state()

        self.assertEqual(self.received_latest, [None])

    def test_on_save_calibration_requested_calls_service_and_reports_success(self):
        self.presenter.on_save_calibration_requested(-1.84, 2.03, 1.27)

        self.assertEqual(self.service.record_calibration_calls, [(-1.84, 2.03, 1.27)])
        self.assertEqual(self.received_status_messages, ["Calibration enregistrée"])

    def test_on_save_calibration_requested_auto_refreshes_via_entry_added_event(self):
        self.presenter.on_save_calibration_requested(-1.84, 2.03, 1.27)

        self.assertEqual(len(self.received_latest), 1)
        self.assertEqual(self.received_latest[0].theta_x_degrees, -1.84)

    def test_on_save_calibration_requested_catches_service_exception(self):
        self.service.record_calibration_error = ValueError("boom")

        self.presenter.on_save_calibration_requested(0.0, 0.0, 0.0)

        self.assertEqual(len(self.received_status_messages), 1)
        self.assertIn("Erreur", self.received_status_messages[0])
        self.assertIn("boom", self.received_status_messages[0])
        self.assertEqual(self.received_latest, [])  # no entry-added event on failure

    def test_on_trial_rotation_requested_forwards_to_preview_rotation(self):
        self.presenter.on_trial_rotation_requested(36.0, 44.0, 1.0)

        self.assertEqual(self.service.preview_rotation_calls, [(36.0, 44.0, 1.0)])

    def test_on_reset_to_default_requested_forwards_to_service(self):
        self.presenter.on_reset_to_default_requested()

        self.assertEqual(self.service.reset_to_default_calls, 1)


if __name__ == "__main__":
    unittest.main()
