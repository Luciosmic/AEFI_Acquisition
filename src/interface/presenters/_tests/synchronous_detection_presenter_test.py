"""Unit tests for SynchronousDetectionPresenter (see synchronous_detection_presenter.py)."""

import unittest

from interface.presenters.synchronous_detection_presenter import SynchronousDetectionPresenter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.synchronous_detection_service.i_api_synchronous_detection_service import (
    IApiSynchronousDetectionService,
)
from application.services.synchronous_detection_service.dtos.sphere_phases_dto import SpherePhasesDTO
from application.services.synchronous_detection_service.synchronous_detection_service import (
    SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC,
)
from domain.calibration.events.synchronous_detection_compensation_enabled_changed.synchronous_detection_compensation_enabled_changed import (
    SynchronousDetectionCompensationEnabledChanged,
)


class FakeSynchronousDetectionService(IApiSynchronousDetectionService):
    """Simple hand-written stub — not a Mock: lets tests assert on state,
    not on call interactions (per this repo's Fake-vs-Mock test standard)."""

    def __init__(self):
        self.sphere_phases = SpherePhasesDTO(
            s1_degrees=0.0,
            s2_degrees=180.0,
            s3_degrees=90.0,
            s4_degrees=0.0,
            delta_phi_corrige_degrees=12.5,
            quadrature_enforced=True,
            lock_in_gain_below_default=False,
        )
        self._compensation_enabled = False
        self.save_calibration_point_error: Exception | None = None
        self.save_calibration_point_calls = 0
        self.set_compensation_enabled_calls = []
        self.enable_lock_in_detection_calls = 0

    def get_sphere_phases(self) -> SpherePhasesDTO:
        return self.sphere_phases

    def save_calibration_point(self) -> None:
        self.save_calibration_point_calls += 1
        if self.save_calibration_point_error is not None:
            raise self.save_calibration_point_error

    def is_compensation_enabled(self) -> bool:
        return self._compensation_enabled

    def set_compensation_enabled(self, enabled: bool) -> None:
        self.set_compensation_enabled_calls.append(enabled)
        self._compensation_enabled = enabled

    def enable_lock_in_detection(self) -> None:
        self.enable_lock_in_detection_calls += 1


class TestSynchronousDetectionPresenter(unittest.TestCase):
    def setUp(self):
        self.service = FakeSynchronousDetectionService()
        self.event_bus = InMemoryEventBus()
        self.presenter = SynchronousDetectionPresenter(self.service, self.event_bus)
        self.received_sphere_phases = []
        self.received_compensation_states = []
        self.received_status_messages = []
        self.presenter.sphere_phases_updated.connect(
            lambda *args: self.received_sphere_phases.append(args)
        )
        self.presenter.compensation_state_changed.connect(self.received_compensation_states.append)
        self.presenter.status_message.connect(self.received_status_messages.append)

    def test_refresh_state_emits_both_signals_with_dto_values(self):
        self.presenter.refresh_state()

        self.assertEqual(
            self.received_sphere_phases,
            [(0.0, 180.0, 90.0, 0.0, 12.5, False)],
        )
        self.assertEqual(self.received_compensation_states, [False])

    def test_on_save_calibration_point_requested_catches_service_exception(self):
        self.service.save_calibration_point_error = ValueError("no active frequency")

        self.presenter.on_save_calibration_point_requested()

        self.assertEqual(self.service.save_calibration_point_calls, 1)
        self.assertEqual(len(self.received_status_messages), 1)
        self.assertIn("Erreur", self.received_status_messages[0])
        self.assertIn("no active frequency", self.received_status_messages[0])

    def test_on_save_calibration_point_requested_reports_success(self):
        self.presenter.on_save_calibration_point_requested()

        self.assertEqual(self.service.save_calibration_point_calls, 1)
        self.assertEqual(self.received_status_messages, ["Point de calibration enregistré"])

    def test_compensation_changed_event_reemits_flag_without_calling_service_again(self):
        self.event_bus.publish(
            SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC,
            SynchronousDetectionCompensationEnabledChanged(enabled=True),
        )

        self.assertEqual(self.received_compensation_states, [True])
        self.assertEqual(self.service.set_compensation_enabled_calls, [])

    def test_on_compensation_toggle_requested_calls_service(self):
        self.presenter.on_compensation_toggle_requested(True)

        self.assertEqual(self.service.set_compensation_enabled_calls, [True])

    def test_on_lock_in_detection_toggled_true_calls_service(self):
        self.presenter.on_lock_in_detection_toggled(True)

        self.assertEqual(self.service.enable_lock_in_detection_calls, 1)

    def test_on_lock_in_detection_toggled_false_is_a_no_op(self):
        self.presenter.on_lock_in_detection_toggled(False)

        self.assertEqual(self.service.enable_lock_in_detection_calls, 0)


if __name__ == "__main__":
    unittest.main()
