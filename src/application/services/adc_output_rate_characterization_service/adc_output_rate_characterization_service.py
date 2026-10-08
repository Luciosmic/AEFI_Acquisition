"""
ADC Output Rate Characterization Service

See adc_output_rate_characterization_service_intention.md.
"""

import logging
import time
from dataclasses import replace
from typing import List, Optional, Tuple

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    AdcOutputRatePointDTO,
    AdcOutputRateRequestDTO,
    DrdyCaptureDTO,
    DrdyCaptureRequestDTO,
)
from application.services.adc_output_rate_characterization_service.i_api_adc_output_rate_characterization_service import (
    IApiAdcOutputRateCharacterizationService,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_export_port import (
    IAdcOutputRateExportPort,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_output_port import (
    IAdcOutputRateOutputPort,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_oversampling_port import (
    IAdcOversamplingPort,
)
from application.services.adc_output_rate_characterization_service.ports.i_drdy_capture_port import IDrdyCapturePort
from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import IApiAefiAcquisitionService
from application.services.hardware_configuration_service.i_api_hardware_configuration_service import (
    IApiHardwareConfigurationService,
)
from application.shared.exclusive_control.exclusive_control import take_all
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from domain.calibration.services.adc_output_rate_analysis.adc_output_rate_analysis import (
    characterize_output_rate,
    measure_output_rate,
)
from domain.calibration.value_objects.adc_output_rate_characterization.adc_output_rate_characterization import (
    AdcOutputRateMeasurement,
)

CONTROLLER = "caractérisation ODR (DRDY)"
# Only to choose the oscilloscope timebase (result independent of it): f_MOD
# measured on the bench 2026-10-02 (DRDY 1000,000 us at OSR 4096), then
# replaced by each measurement's implied f_MOD.
INITIAL_MODULATOR_FREQUENCY_ESTIMATE_HZ = 4.096e6
MIN_PERIODS_PER_CAPTURE = 3

logger = logging.getLogger(__name__)


class _CharacterizationAborted(Exception):
    """Internal: an expected failure (reason for the operator)."""


class AdcOutputRateCharacterizationService(IApiAdcOutputRateCharacterizationService):
    def __init__(
        self,
        oversampling_port: IAdcOversamplingPort,
        capture_port: IDrdyCapturePort,
        export_port: IAdcOutputRateExportPort,
        acquisition_service: IApiAefiAcquisitionService,
        hardware_configuration: IApiHardwareConfigurationService,
        task_runner: IAsyncTaskRunner,
        settle_delay_s: float = 0.05,
    ) -> None:
        """`settle_delay_s`: wait after an OSR write before capturing."""
        self._osr = oversampling_port
        self._capture = capture_port
        self._export = export_port
        self._acquisition = acquisition_service
        self._hardware_configuration = hardware_configuration
        self._task_runner = task_runner
        self._settle_delay_s = settle_delay_s
        self._output_port: Optional[IAdcOutputRateOutputPort] = None
        self._running = False
        self._releases: List = []

    def set_output_port(self, output_port: IAdcOutputRateOutputPort) -> None:
        self._output_port = output_port

    def get_allowed_oversampling_ratios(self) -> Tuple[int, ...]:
        return self._osr.get_allowed_oversampling_ratios()

    # -- commands -----------------------------------------------------------------

    def start_characterization(self, request: AdcOutputRateRequestDTO) -> None:
        logger.info(
            "AdcOutputRateCharacterizationService: Command start_characterization channel=%s probe=%s osr=%s periods=%s",
            request.scope_channel, request.probe_ratio, request.oversampling_ratios or "current",
            request.periods_per_capture,
        )
        if self._running:
            logger.info("AdcOutputRateCharacterizationService: already running. Doing nothing.")
            return
        refusal = self._validate(request)
        if refusal is not None:
            self._fail(refusal)
            return
        adc_id = self._osr.get_configuration_hardware_id()
        taken = take_all([
            (lambda: self._hardware_configuration.take_control(adc_id, CONTROLLER),
             lambda: self._hardware_configuration.release_control(adc_id, CONTROLLER)),
            (lambda: self._acquisition.take_control(CONTROLLER),
             lambda: self._acquisition.release_control(CONTROLLER)),
        ])
        if taken.is_failure:
            self._fail(taken.error)
            return
        current = self._osr.get_oversampling_ratio()
        if any(osr != current for osr in request.oversampling_ratios) and self._acquisition.is_acquisition_running():
            for release in taken.value:
                release()
            self._fail("arrêter la lecture continue avant un balayage de l'OSR (ses données seraient faussées)")
            return
        self._releases = taken.value
        self._running = True
        self._task_runner.submit(lambda: self._run(request))

    def _validate(self, request: AdcOutputRateRequestDTO) -> Optional[str]:
        if request.scope_channel not in (1, 2, 3, 4):
            return f"voie d'oscilloscope invalide : {request.scope_channel} (1 à 4)"
        if request.probe_ratio <= 0:
            return f"rapport de sonde invalide : {request.probe_ratio}"
        allowed = self._osr.get_allowed_oversampling_ratios()
        refused = [osr for osr in request.oversampling_ratios if osr not in allowed]
        if refused:
            return f"OSR non accepté(s) par l'ADC : {refused} (valeurs possibles : {list(allowed)})"
        if request.periods_per_capture < MIN_PERIODS_PER_CAPTURE:
            return f"au moins {MIN_PERIODS_PER_CAPTURE} périodes par capture sont nécessaires"
        return None

    def _run(self, request: AdcOutputRateRequestDTO) -> None:
        original = self._osr.get_oversampling_ratio()
        try:
            try:
                measurements, captures = self._measure_all(request, original)
            except _CharacterizationAborted as error:
                self._fail(str(error))
                return
            finally:
                restored = self._osr.set_oversampling_ratio(original)
                if restored.is_failure:
                    logger.error("AdcOutputRateCharacterizationService: OSR %d not restored: %s", original, restored.error)
                else:
                    logger.info("AdcOutputRateCharacterizationService: OSR restored to %d", original)
            characterization = characterize_output_rate(measurements)
            points = tuple(_to_point_dto(m) for m in characterization.measurements)
            logger.info(
                "AdcOutputRateCharacterizationService: result f_MOD=%.1f Hz max_deviation=%.2e over %d OSR",
                characterization.mean_modulator_frequency_hz,
                characterization.max_modulator_frequency_relative_deviation, len(points),
            )
            result = AdcOutputRateCharacterizationDTO(
                points=points,
                mean_modulator_frequency_hz=characterization.mean_modulator_frequency_hz,
                max_modulator_frequency_relative_deviation=characterization.max_modulator_frequency_relative_deviation,
                restored_oversampling_ratio=original,
                instrument=captures[0][1].instrument,
                export_path=None,
                component_values=_component_values(points, characterization.mean_modulator_frequency_hz),
            )
            exported = self._export.export(result, captures)
            if exported.is_success:
                result = replace(result, export_path=exported.value)
            else:
                logger.warning("AdcOutputRateCharacterizationService: export failed: %s", exported.error)
            if self._output_port is not None:
                self._output_port.present_output_rate_characterization_succeeded(result)
        finally:
            for release in self._releases:
                release()
            self._releases = []
            self._running = False

    def _measure_all(
        self, request: AdcOutputRateRequestDTO, original: int
    ) -> Tuple[List[AdcOutputRateMeasurement], List[Tuple[int, DrdyCaptureDTO]]]:
        f_mod_estimate = INITIAL_MODULATOR_FREQUENCY_ESTIMATE_HZ
        measurements, captures = [], []
        for osr in request.oversampling_ratios or (original,):
            self._step(f"Mesure de DRDY à OSR {osr}…")
            if osr != self._osr.get_oversampling_ratio():
                written = self._osr.set_oversampling_ratio(osr)
                if written.is_failure:
                    raise _CharacterizationAborted(f"OSR {osr} non écrit : {written.error}")
                time.sleep(self._settle_delay_s)
            window = request.periods_per_capture * osr / f_mod_estimate
            captured = self._capture.capture_falling_edges(
                DrdyCaptureRequestDTO(request.scope_channel, request.probe_ratio, window)
            )
            if captured.is_failure:
                raise _CharacterizationAborted(f"capture DRDY à OSR {osr} : {captured.error}")
            if len(captured.value.falling_edge_times_s) < MIN_PERIODS_PER_CAPTURE:
                raise _CharacterizationAborted(
                    f"OSR {osr} : {len(captured.value.falling_edge_times_s)} front(s) descendant(s) capturé(s) — "
                    "vérifier la voie et le branchement sur DRDY"
                )
            measurement = measure_output_rate(osr, captured.value.falling_edge_times_s)
            f_mod_estimate = measurement.implied_modulator_frequency_hz
            logger.info(
                "AdcOutputRateCharacterizationService: OSR=%d ODR=%.4f Hz std=%.3e s regular=%d irregular=%d f_MOD=%.1f Hz",
                osr, measurement.output_rate_hz, measurement.interval_std_s, measurement.regular_interval_count,
                measurement.irregular_interval_count, measurement.implied_modulator_frequency_hz,
            )
            measurements.append(measurement)
            captures.append((osr, captured.value))
            if self._output_port is not None:
                self._output_port.present_output_rate_point_measured(_to_point_dto(measurement))
        return measurements, captures

    def _step(self, message: str) -> None:
        if self._output_port is not None:
            self._output_port.present_output_rate_step(message)

    def _fail(self, reason: str) -> None:
        logger.warning("AdcOutputRateCharacterizationService: characterization failed: %s", reason)
        if self._output_port is not None:
            self._output_port.present_output_rate_characterization_failed(reason)


def _to_point_dto(m: AdcOutputRateMeasurement) -> AdcOutputRatePointDTO:
    return AdcOutputRatePointDTO(
        oversampling_ratio=m.oversampling_ratio,
        regular_interval_count=m.regular_interval_count,
        irregular_interval_count=m.irregular_interval_count,
        median_interval_s=m.median_interval_s,
        mean_interval_s=m.mean_interval_s,
        interval_std_s=m.interval_std_s,
        output_rate_hz=m.output_rate_hz,
        implied_modulator_frequency_hz=m.implied_modulator_frequency_hz,
    )


def _component_values(points, mean_modulator_frequency_hz: float) -> dict:
    """Keys of HardwareComponentKind.ADC's quantities."""
    return {
        "modulator_frequency_hz": mean_modulator_frequency_hz,
        "output_data_rate_hz": tuple((p.oversampling_ratio, p.output_rate_hz) for p in points),
    }
