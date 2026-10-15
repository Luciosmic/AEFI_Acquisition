"""Unit tests for AefiContinuousReadingPresenter (see aefi_continuous_reading_presenter.py).

Covers the refactoring that moved signal correction out of the presenter and
into AefiSignalProcessingService: the presenter must now be a pure
event -> view-model translator (sample_acquired) and a pure command delegator
(calibrate_*/on_*_toggled), with calibration feedback (correction_states_updated)
driven reactively by AefiSignalCorrectionCalibrationUpdated."""

import unittest
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import (
    IApiAefiAcquisitionService,
)
from application.services.aefi_signal_processing_service.i_api_aefi_signal_processing_service import (
    IApiAefiSignalProcessingService,
)
from domain.shared_kernel.operation_result import OperationResult
from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.events.aefi_signal_correction_calibration_updated.aefi_signal_correction_calibration_updated import (
    AefiSignalCorrectionCalibrationUpdated,
)
from domain.signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import (
    AefiCorrectedFieldMeasurement,
)
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)
from application.services.transformation_service.transformation_service import TransformationService
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from interface.presenters.aefi_continuous_reading_presenter import AefiContinuousReadingPresenter
from interface.view_models.aefi_continuous_reading_sample_view_model import (
    AefiContinuousReadingSampleViewModel,
)

TIMESTAMP = datetime(2026, 10, 9, tzinfo=timezone.utc)


class FakeAefiAcquisitionService(IApiAefiAcquisitionService):
    """Hand-written stub (not a Mock): the presenter's own acquisition commands
    are not this refactoring's focus, only the fields it reads/calls."""

    def __init__(self):
        self.controller: Optional[str] = None
        self.running = False
        self.start_result = OperationResult.ok(None)
        self.stop_result = OperationResult.ok(None)

    def take_control(self, controller: str) -> OperationResult:
        self.controller = controller
        return OperationResult.ok(None)

    def release_control(self, controller: str) -> None:
        if self.controller == controller:
            self.controller = None

    def get_controller(self) -> Optional[str]:
        return self.controller

    def start_acquisition(self, config) -> OperationResult:
        return self.start_result

    def stop_acquisition(self, controller: Optional[str] = None) -> OperationResult:
        return self.stop_result

    def is_acquisition_running(self) -> bool:
        return self.running


class FakeSignalProcessingService(IApiAefiSignalProcessingService):
    """Hand-written stub tracking calls — lets the presenter test assert pure
    delegation, per this repo's Fake-vs-Mock test standard."""

    def __init__(self):
        self.calibrate_noise_calls = 0
        self.calibrate_phase_calls = 0
        self.calibrate_primary_calls = 0
        self.reset_calibration_calls = 0
        self.noise_enabled_calls = []
        self.phase_enabled_calls = []
        self.primary_enabled_calls = []
        self._calibration = AefiSignalCorrectionCalibration()

    def calibrate_noise(self) -> None:
        self.calibrate_noise_calls += 1

    def calibrate_phase(self) -> None:
        self.calibrate_phase_calls += 1

    def calibrate_primary(self) -> None:
        self.calibrate_primary_calls += 1

    def reset_calibration(self) -> None:
        self.reset_calibration_calls += 1

    def set_noise_correction_enabled(self, enabled: bool) -> None:
        self.noise_enabled_calls.append(enabled)

    def set_phase_correction_enabled(self, enabled: bool) -> None:
        self.phase_enabled_calls.append(enabled)

    def set_primary_correction_enabled(self, enabled: bool) -> None:
        self.primary_enabled_calls.append(enabled)

    def get_calibration(self) -> AefiSignalCorrectionCalibration:
        return self._calibration


class FakeScanExportService:
    """Only the one method the presenter calls on acquisition start."""

    def __init__(self):
        self.configure_calls = []

    def configure_time_series_export(self, dto) -> None:
        self.configure_calls.append(dto)


def make_field_sample(value: float = 1.0) -> AefiCorrectedFieldMeasurement:
    return AefiCorrectedFieldMeasurement(
        field_x_in_phase=value, field_x_quadrature=value + 1,
        field_y_in_phase=value + 2, field_y_quadrature=value + 3,
        field_z_in_phase=value + 4, field_z_quadrature=value + 5,
        timestamp=TIMESTAMP,
    )


class TestAefiContinuousReadingPresenter(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.acquisition_service = FakeAefiAcquisitionService()
        self.signal_processing_service = FakeSignalProcessingService()
        self.transformation_service = TransformationService()
        self.export_service = FakeScanExportService()
        self.presenter = AefiContinuousReadingPresenter(
            self.acquisition_service, self.event_bus, self.transformation_service,
            self.signal_processing_service, export_service=self.export_service,
        )
        self.received_samples = []
        self.received_correction_states = []
        self.received_acquisition_started = []
        self.presenter.sample_acquired.connect(self.received_samples.append)
        self.presenter.correction_states_updated.connect(
            lambda *args: self.received_correction_states.append(args)
        )
        self.presenter.acquisition_started.connect(self.received_acquisition_started.append)

    def _publish_corrected_sample(self, acquisition_id, sample_index: int = 0, value: float = 1.0):
        self.event_bus.publish(
            "aeficorrectedfieldsampleacquired",
            AefiCorrectedFieldSampleAcquired(
                acquisition_id=acquisition_id, sample_index=sample_index, sample=make_field_sample(value)
            ),
        )

    # ------------------------------------------------------------------ #
    # Sample translation: event -> view model, no correction logic here.
    # ------------------------------------------------------------------ #

    def test_corrected_sample_event_emits_view_model_with_translated_fields(self):
        acquisition_id = uuid4()
        self._publish_corrected_sample(acquisition_id, sample_index=3, value=1.0)

        self.assertEqual(len(self.received_samples), 1)
        vm = self.received_samples[0]
        self.assertIsInstance(vm, AefiContinuousReadingSampleViewModel)
        self.assertEqual(vm.acquisition_id, str(acquisition_id))
        self.assertEqual(vm.sample_index, 3)
        self.assertEqual(vm.timestamp_iso, TIMESTAMP.isoformat())
        self.assertEqual(vm.ux_in_phase, 1.0)
        self.assertEqual(vm.ux_quadrature, 2.0)
        self.assertEqual(vm.uy_in_phase, 3.0)
        self.assertEqual(vm.uy_quadrature, 4.0)
        self.assertEqual(vm.uz_in_phase, 5.0)
        self.assertEqual(vm.uz_quadrature, 6.0)

    def test_first_corrected_sample_of_an_acquisition_emits_acquisition_started(self):
        acquisition_id = uuid4()
        self._publish_corrected_sample(acquisition_id, sample_index=0)
        self._publish_corrected_sample(acquisition_id, sample_index=1)

        self.assertEqual(self.received_acquisition_started, [str(acquisition_id)])

    # ------------------------------------------------------------------ #
    # Calibration: pure delegation, feedback is event-driven.
    # ------------------------------------------------------------------ #

    def test_calibrate_slots_delegate_purely_to_signal_processing_service(self):
        self.presenter.calibrate_noise()
        self.presenter.calibrate_phase()
        self.presenter.calibrate_primary()
        self.presenter.reset_calibration()

        self.assertEqual(self.signal_processing_service.calibrate_noise_calls, 1)
        self.assertEqual(self.signal_processing_service.calibrate_phase_calls, 1)
        self.assertEqual(self.signal_processing_service.calibrate_primary_calls, 1)
        self.assertEqual(self.signal_processing_service.reset_calibration_calls, 1)

    def test_toggle_slots_delegate_purely_to_signal_processing_service(self):
        self.presenter.on_noise_toggled(True)
        self.presenter.on_phase_toggled(True)
        self.presenter.on_primary_toggled(False)

        self.assertEqual(self.signal_processing_service.noise_enabled_calls, [True])
        self.assertEqual(self.signal_processing_service.phase_enabled_calls, [True])
        self.assertEqual(self.signal_processing_service.primary_enabled_calls, [False])

    def test_calibration_updated_event_is_formatted_and_emitted(self):
        calibration = AefiSignalCorrectionCalibration(
            noise_offset={"x": (0.001, 0.002), "y": (0.0, 0.0), "z": (0.0, 0.0)},
            noise_correction_enabled=True,
        )

        self.event_bus.publish(
            "aefisignalcorrectioncalibrationupdated",
            AefiSignalCorrectionCalibrationUpdated(calibration=calibration),
        )

        self.assertEqual(len(self.received_correction_states), 1)
        noise, phase, primary, noise_str, phase_str, primary_str = self.received_correction_states[0]
        self.assertTrue(noise)
        self.assertFalse(phase)
        self.assertFalse(primary)
        self.assertIn("X=", noise_str)
        self.assertEqual(phase_str, "—")
        self.assertEqual(primary_str, "—")

    # ------------------------------------------------------------------ #
    # Shutdown: unsubscribes from the new topics.
    # ------------------------------------------------------------------ #

    def test_shutdown_unsubscribes_corrected_sample_and_calibration_topics(self):
        self.presenter.shutdown()
        self.received_samples.clear()
        self.received_correction_states.clear()

        self._publish_corrected_sample(uuid4())
        self.event_bus.publish(
            "aefisignalcorrectioncalibrationupdated",
            AefiSignalCorrectionCalibrationUpdated(calibration=AefiSignalCorrectionCalibration()),
        )

        self.assertEqual(self.received_samples, [])
        self.assertEqual(self.received_correction_states, [])


if __name__ == "__main__":
    unittest.main()
