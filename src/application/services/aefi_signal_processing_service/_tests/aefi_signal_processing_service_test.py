from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

from application.services.aefi_signal_processing_service.aefi_signal_processing_service import (
    AefiSignalProcessingService,
)
from application.services.transformation_service.transformation_service import TransformationService

from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.events.aefi_sample_corrected.aefi_sample_corrected import AefiSampleCorrected
from domain.signal_processing.events.aefi_signal_correction_calibration_updated.aefi_signal_correction_calibration_updated import (
    AefiSignalCorrectionCalibrationUpdated,
)

TIMESTAMP = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_raw(v: float = 1.0) -> AefiVoltageMeasurement:
    return AefiVoltageMeasurement(v, v, v, v, v, v, timestamp=TIMESTAMP)


class TestAefiSignalProcessingService(DiagramFriendlyTest):
    """Diagram-friendly test: AefiSignalProcessingService reacts to raw samples,
    delegates the correction invariant to AefiCorrectedSample, and republishes
    its events + the sensor->source transform, using a real InMemoryEventBus
    and a real TransformationService."""

    def setUp(self) -> None:
        super().setUp()
        self.event_bus = InMemoryEventBus()
        self.transformation_service = TransformationService()
        self.service = AefiSignalProcessingService(self.event_bus, self.transformation_service)

        self.corrected_events: List[AefiSampleCorrected] = []
        self.field_events: List[AefiCorrectedFieldSampleAcquired] = []
        self.calibration_events: List[AefiSignalCorrectionCalibrationUpdated] = []
        self.event_bus.subscribe("aefisamplecorrected", self.corrected_events.append)
        self.event_bus.subscribe("aeficorrectedfieldsampleacquired", self.field_events.append)
        self.event_bus.subscribe("aefisignalcorrectioncalibrationupdated", self.calibration_events.append)

    def test_raw_sample_with_calibration_disabled_is_corrected_and_republished(self):
        self.log_divider("Accepted correction")
        acquisition_id = uuid4()
        event = AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=0, sample=make_raw(1.0))

        self.log_interaction("Test", "PUBLISH", "EventBus", "Publish AefiVoltageSampleAcquired")
        self.event_bus.publish("aefivoltagesampleacquired", event)

        self.assertEqual(len(self.corrected_events), 1)
        self.assertEqual(len(self.field_events), 1)
        self.assertEqual(self.field_events[0].acquisition_id, acquisition_id)
        self.assertEqual(self.field_events[0].sample_index, 0)
        # TransformationService disabled by default -> values pass through unchanged.
        self.assertAlmostEqual(self.field_events[0].sample.field_x_in_phase, 1.0)

    def test_phase_enabled_without_calibration_rejects_silently(self):
        self.log_divider("Rejected correction")
        self.service.set_phase_correction_enabled(True)
        self.calibration_events.clear()  # discard the toggle's own AefiSignalCorrectionCalibrationUpdated
        event = AefiVoltageSampleAcquired(acquisition_id=uuid4(), sample_index=0, sample=make_raw(1.0))

        self.log_interaction("Test", "PUBLISH", "EventBus", "Publish AefiVoltageSampleAcquired (phase uncalibrated)")
        self.event_bus.publish("aefivoltagesampleacquired", event)

        self.assertEqual(self.corrected_events, [])
        self.assertEqual(self.field_events, [])

    def test_calibrate_noise_uses_last_raw_sample_and_publishes_update(self):
        event = AefiVoltageSampleAcquired(acquisition_id=uuid4(), sample_index=0, sample=make_raw(0.5))
        self.event_bus.publish("aefivoltagesampleacquired", event)
        self.calibration_events.clear()

        self.service.calibrate_noise()

        calibration = self.service.get_calibration()
        self.assertTrue(calibration.noise_correction_enabled)
        self.assertEqual(calibration.noise_offset["x"], (0.5, 0.5))
        self.assertEqual(len(self.calibration_events), 1)

    def test_calibrate_phase_computes_angle_from_last_raw_sample(self):
        # Equal I/Q on every axis -> angle = atan2(1, 1) = pi/4.
        event = AefiVoltageSampleAcquired(acquisition_id=uuid4(), sample_index=0, sample=make_raw(1.0))
        self.event_bus.publish("aefivoltagesampleacquired", event)

        self.service.calibrate_phase()

        calibration = self.service.get_calibration()
        self.assertTrue(calibration.phase_correction_enabled)
        self.assertAlmostEqual(calibration.phase_angles["x"], 0.7853981633974483)

    def test_calibrate_primary_uses_fully_processed_sample(self):
        event = AefiVoltageSampleAcquired(acquisition_id=uuid4(), sample_index=0, sample=make_raw(2.0))
        self.event_bus.publish("aefivoltagesampleacquired", event)

        self.service.calibrate_primary()

        calibration = self.service.get_calibration()
        self.assertTrue(calibration.primary_correction_enabled)
        self.assertEqual(calibration.primary_offset["x"], (2.0, 2.0))

    def test_reset_calibration_clears_state_and_publishes_update(self):
        self.service.set_noise_correction_enabled(True)
        self.calibration_events.clear()

        self.service.reset_calibration()

        self.assertEqual(self.service.get_calibration().noise_offset, {})
        self.assertFalse(self.service.get_calibration().noise_correction_enabled)
        self.assertEqual(len(self.calibration_events), 1)
