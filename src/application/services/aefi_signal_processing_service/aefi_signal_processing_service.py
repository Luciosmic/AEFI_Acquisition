"""AefiSignalProcessingService (see aefi_signal_processing_service_intention.md)."""

import logging
from dataclasses import replace
from typing import Optional

from application.services.transformation_service.transformation_service import TransformationService
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.aefi_corrected_sample import AefiCorrectedSample
from domain.signal_processing.errors.signal_correction_calibration_missing_error import (
    SignalCorrectionCalibrationMissingError,
)
from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.events.aefi_signal_correction_calibration_updated.aefi_signal_correction_calibration_updated import (
    AefiSignalCorrectionCalibrationUpdated,
)
from domain.signal_processing.services.aefi_signal_correction_service.aefi_signal_correction_service import (
    AefiSignalCorrectionService,
)
from domain.signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import (
    AefiCorrectedFieldMeasurement,
)
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)

from .i_api_aefi_signal_processing_service import IApiAefiSignalProcessingService

logger = logging.getLogger(__name__)


class AefiSignalProcessingService(IApiAefiSignalProcessingService):
    """
    Orchestrates signal correction (noise/phase/primary) and the sensor -> source
    coordinate transform on the continuous acquisition stream.

    Delegates the correction invariant entirely to the AefiCorrectedSample
    aggregate: this service only collects and republishes the events the
    aggregate produces, then chains TransformationService.transform_sensor_to_source
    (existing, unmodified) to obtain the corrected field measurement.
    See intention.md.
    """

    def __init__(self, event_bus: IDomainEventBus, transformation_service: TransformationService):
        self._event_bus = event_bus
        self._transformation_service = transformation_service
        self._calibration = AefiSignalCorrectionCalibration()
        self._last_raw_sample: Optional[AefiVoltageMeasurement] = None
        event_bus.subscribe("aefivoltagesampleacquired", self._on_raw_sample)

    # ------------------------------------------------------------------ #
    # Reactive handler
    # ------------------------------------------------------------------ #

    def _on_raw_sample(self, event: AefiVoltageSampleAcquired) -> None:
        self._last_raw_sample = event.sample
        try:
            corrected_sample = AefiCorrectedSample.correct(
                event.sample, self._calibration, event.acquisition_id, event.sample_index
            )
        except SignalCorrectionCalibrationMissingError as error:
            logger.warning(
                "Correction rejected: %s (acquisition_id=%s, sample_index=%s)",
                error, event.acquisition_id, event.sample_index,
            )
            return  # No domain event on invariant rejection (cf. EventStore standard).

        for domain_event in corrected_sample.domain_events:
            self._event_bus.publish(type(domain_event).__name__.lower(), domain_event)

        corrected = corrected_sample.measurement
        v_in_phase = self._transformation_service.transform_sensor_to_source(
            (corrected.voltage_x_in_phase, corrected.voltage_y_in_phase, corrected.voltage_z_in_phase)
        )
        v_quadrature = self._transformation_service.transform_sensor_to_source(
            (corrected.voltage_x_quadrature, corrected.voltage_y_quadrature, corrected.voltage_z_quadrature)
        )
        field = AefiCorrectedFieldMeasurement(
            field_x_in_phase=v_in_phase[0], field_x_quadrature=v_quadrature[0],
            field_y_in_phase=v_in_phase[1], field_y_quadrature=v_quadrature[1],
            field_z_in_phase=v_in_phase[2], field_z_quadrature=v_quadrature[2],
            timestamp=corrected.timestamp,
        )
        self._event_bus.publish(
            "aeficorrectedfieldsampleacquired",
            AefiCorrectedFieldSampleAcquired(
                acquisition_id=event.acquisition_id,
                sample_index=event.sample_index,
                sample=field,
            ),
        )

    # ------------------------------------------------------------------ #
    # Commands
    # ------------------------------------------------------------------ #

    def calibrate_noise(self) -> None:
        logger.info("AefiSignalProcessingService: Command calibrate_noise")
        if self._last_raw_sample is None:
            logger.warning("calibrate_noise: no sample received yet. Doing nothing.")
            return
        self._calibration = AefiSignalCorrectionService.calibrate_noise(self._last_raw_sample, self._calibration)
        self._publish_calibration_updated()

    def calibrate_phase(self) -> None:
        logger.info("AefiSignalProcessingService: Command calibrate_phase")
        if self._last_raw_sample is None:
            logger.warning("calibrate_phase: no sample received yet. Doing nothing.")
            return
        # Recompute the pre-phase sample from the last raw sample: noise/primary
        # as currently configured, phase disabled (cf. aefi_signal_correction_service
        # intention — calibrate_phase expects a sample not yet phase-corrected).
        pre_phase_calibration = replace(self._calibration, phase_correction_enabled=False)
        pre_phase_sample = AefiSignalCorrectionService.apply(self._last_raw_sample, pre_phase_calibration)
        self._calibration = AefiSignalCorrectionService.calibrate_phase(pre_phase_sample, self._calibration)
        self._publish_calibration_updated()

    def calibrate_primary(self) -> None:
        logger.info("AefiSignalProcessingService: Command calibrate_primary")
        if self._last_raw_sample is None:
            logger.warning("calibrate_primary: no sample received yet. Doing nothing.")
            return
        fully_processed = AefiSignalCorrectionService.apply(self._last_raw_sample, self._calibration)
        self._calibration = AefiSignalCorrectionService.calibrate_primary(fully_processed, self._calibration)
        self._publish_calibration_updated()

    def reset_calibration(self) -> None:
        logger.info("AefiSignalProcessingService: Command reset_calibration")
        self._calibration = AefiSignalCorrectionCalibration()
        self._publish_calibration_updated()

    def set_noise_correction_enabled(self, enabled: bool) -> None:
        logger.info("AefiSignalProcessingService: Command set_noise_correction_enabled enabled=%s", enabled)
        self._calibration = replace(self._calibration, noise_correction_enabled=enabled)
        self._publish_calibration_updated()

    def set_phase_correction_enabled(self, enabled: bool) -> None:
        logger.info("AefiSignalProcessingService: Command set_phase_correction_enabled enabled=%s", enabled)
        self._calibration = replace(self._calibration, phase_correction_enabled=enabled)
        self._publish_calibration_updated()

    def set_primary_correction_enabled(self, enabled: bool) -> None:
        logger.info("AefiSignalProcessingService: Command set_primary_correction_enabled enabled=%s", enabled)
        self._calibration = replace(self._calibration, primary_correction_enabled=enabled)
        self._publish_calibration_updated()

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def get_calibration(self) -> AefiSignalCorrectionCalibration:
        return self._calibration

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _publish_calibration_updated(self) -> None:
        self._event_bus.publish(
            "aefisignalcorrectioncalibrationupdated",
            AefiSignalCorrectionCalibrationUpdated(calibration=self._calibration),
        )
