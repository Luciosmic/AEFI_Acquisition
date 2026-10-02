"""
Acquisition Throughput Characterization Service

See acquisition_throughput_characterization_service_intention.md.
"""

import logging
import queue
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputPointDTO,
    AcquisitionThroughputRequestDTO,
    AcquisitionThroughputSampleDTO,
)
from application.services.acquisition_throughput_characterization_service.i_api_acquisition_throughput_characterization_service import (
    IApiAcquisitionThroughputCharacterizationService,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_averaging_port import (
    IAcquisitionAveragingPort,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_export_port import (
    IAcquisitionThroughputExportPort,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_output_port import (
    IAcquisitionThroughputOutputPort,
)
from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import (
    IApiAefiAcquisitionService,
)
# ponytail: direct Application-Service-to-Application-Service dependency,
# same precedent as ScanApplicationService and SensorCalibrationService.
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.hardware_configuration_service.i_api_hardware_configuration_service import (
    IApiHardwareConfigurationService,
)
from application.shared.exclusive_control.exclusive_control import take_all
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from application.shared.settled_sample_collection.settled_sample_collection import collect_settled_samples
from domain.calibration.services.acquisition_throughput_analysis.acquisition_throughput_analysis import (
    characterize_acquisition_throughput,
    characterize_point,
)
from domain.calibration.value_objects.acquisition_throughput_characterization.acquisition_throughput_characterization import (
    AcquisitionThroughputPoint,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC = "aefivoltagesampleacquired"
# Owner name of the excitation, the acquisition stream and the n_avg / OSR configuration.
CONTROLLER = "caractérisation débit MCU"
EXCITATION_CONDITION = "coupée"
MIN_SAMPLES_PER_POINT = 3

logger = logging.getLogger(__name__)


class _CharacterizationAborted(Exception):
    """Internal: an expected failure of the sweep (reason for the operator)."""


class AcquisitionThroughputCharacterizationService(IApiAcquisitionThroughputCharacterizationService):
    """Sweeps the MCU averaging n_avg, excitation cut, and characterizes the
    acquisition throughput and noise for each value."""

    def __init__(
        self,
        excitation_service: ExcitationConfigurationService,
        acquisition_service: IApiAefiAcquisitionService,
        averaging_port: IAcquisitionAveragingPort,
        export_port: IAcquisitionThroughputExportPort,
        task_runner: IAsyncTaskRunner,
        event_bus: IDomainEventBus,
        hardware_configuration: IApiHardwareConfigurationService,
        settle_delay_s: float = 0.5,
        sample_timeout_s: float = 60.0,
    ) -> None:
        """`settle_delay_s`: wait after each change (excitation cut, n_avg)
        before a sample counts; `sample_timeout_s`: budget per n_avg.
        `hardware_configuration`: locks the n_avg / OSR settings of the
        Hardware Advanced Config panel during the sweep."""
        self._excitation_service = excitation_service
        self._acquisition_service = acquisition_service
        self._hardware_configuration = hardware_configuration
        self._releases: List = []
        self._averaging = averaging_port
        self._export = export_port
        self._task_runner = task_runner
        self._event_bus = event_bus
        self._settle_delay_s = settle_delay_s
        self._sample_timeout_s = sample_timeout_s
        self._output_port: Optional[IAcquisitionThroughputOutputPort] = None
        self._running = False

    def set_output_port(self, output_port: IAcquisitionThroughputOutputPort) -> None:
        self._output_port = output_port

    # -- commands -----------------------------------------------------------------

    def start_characterization(self, request: AcquisitionThroughputRequestDTO) -> None:
        logger.info(
            "AcquisitionThroughputCharacterizationService: Command start_characterization n_avg_values=%s "
            "samples_per_point=%s excitation=%s",
            request.n_avg_values, request.samples_per_point, EXCITATION_CONDITION,
        )
        if self._running:
            logger.info("AcquisitionThroughputCharacterizationService: already running. Doing nothing.")
            return
        refusal = self._validate(request)
        if refusal is not None:
            self._fail(refusal)
            return
        # Everything the sweep depends on, held until it ends: excitation (cut),
        # the acquisition stream (no Stop under its feet), and the Hardware
        # Advanced Config of n_avg / OSR. Refused during a scan or a calibration.
        takes = [
            (lambda: self._excitation_service.take_control(CONTROLLER),
             lambda: self._excitation_service.release_control(CONTROLLER)),
            (lambda: self._acquisition_service.take_control(CONTROLLER),
             lambda: self._acquisition_service.release_control(CONTROLLER)),
        ] + [
            (lambda hw=hw: self._hardware_configuration.take_control(hw, CONTROLLER),
             lambda hw=hw: self._hardware_configuration.release_control(hw, CONTROLLER))
            for hw in self._averaging.get_configuration_hardware_ids()
        ]
        taken = take_all(takes)
        if taken.is_failure:
            self._fail(taken.error)
            return
        self._releases = taken.value
        self._running = True
        self._task_runner.submit(lambda: self._run(request))

    def _validate(self, request: AcquisitionThroughputRequestDTO) -> Optional[str]:
        low, high = self._averaging.get_n_avg_range()
        out_of_range = [n for n in request.n_avg_values if not low <= n <= high]
        if out_of_range:
            return f"n_avg hors bornes du MCU ({low}-{high}) : {out_of_range}"
        if len(set(request.n_avg_values)) < 2:
            return "au moins 2 valeurs de n_avg distinctes sont nécessaires pour ajuster T(n)"
        if request.samples_per_point < MIN_SAMPLES_PER_POINT:
            return f"au moins {MIN_SAMPLES_PER_POINT} échantillons par point sont nécessaires"
        return None

    def _run(self, request: AcquisitionThroughputRequestDTO) -> None:
        try:
            try:
                points, samples, oversampling_ratio = self._sweep(request)
            except _CharacterizationAborted as error:
                self._fail(str(error))
                return
            characterization = characterize_acquisition_throughput(points)
            logger.info(
                "AcquisitionThroughputCharacterizationService: result overhead=%.4fs adc_output_rate=%sHz "
                "fit_max_relative_residual=%.3f recommended_n_avg=%d osr=%d excitation=%s",
                characterization.overhead_s, characterization.adc_output_rate_hz,
                characterization.fit_max_relative_residual, characterization.recommended_n_avg,
                oversampling_ratio, EXCITATION_CONDITION,
            )
            point_dtos = tuple(_to_point_dto(p) for p in characterization.points)
            result = AcquisitionThroughputCharacterizationDTO(
                points=point_dtos,
                overhead_s=characterization.overhead_s,
                adc_output_rate_hz=characterization.adc_output_rate_hz,
                fit_max_relative_residual=characterization.fit_max_relative_residual,
                recommended_n_avg=characterization.recommended_n_avg,
                noise_relative_uncertainty=characterization.noise_relative_uncertainty,
                oversampling_ratio=oversampling_ratio,
                excitation=EXCITATION_CONDITION,
                export_path=None,
                component_values={
                    # Keys of HardwareComponentKind.MICROCONTROLLER's quantities.
                    "max_acquisition_rate_per_s": max(p.sample_rate_per_s for p in point_dtos),
                    "optimal_acquisition_rate_per_s": tuple((p.n_avg, p.sample_rate_per_s) for p in point_dtos),
                },
            )
            exported = self._export.export(result, samples)
            if exported.is_success:
                logger.info("AcquisitionThroughputCharacterizationService: exported to %s", exported.value)
                result = _with_export_path(result, exported.value)
            else:
                logger.warning("AcquisitionThroughputCharacterizationService: export failed: %s", exported.error)
            if self._output_port is not None:
                self._output_port.present_throughput_characterization_succeeded(result)
        finally:
            for release in self._releases:
                release()
            self._releases = []
            self._running = False

    def _sweep(
        self, request: AcquisitionThroughputRequestDTO
    ) -> Tuple[List[AcquisitionThroughputPoint], List[AcquisitionThroughputSampleDTO], int]:
        """One point per n_avg, excitation cut. Restores the operator's n_avg,
        excitation and acquisition stream whatever happens."""
        previous_n_avg = self._averaging.get_n_avg()
        oversampling_ratio = self._averaging.get_oversampling_ratio()
        events: "queue.Queue" = queue.Queue()

        def _on_sample(event) -> None:
            events.put(event)

        self._event_bus.subscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
        started_here = not self._acquisition_service.is_acquisition_running()
        if started_here:
            self._acquisition_service.start_acquisition(AefiAcquisitionConfig(), controller=CONTROLLER)
        self._excitation_service.mute()
        points: List[AcquisitionThroughputPoint] = []
        samples: List[AcquisitionThroughputSampleDTO] = []
        try:
            for n_avg in request.n_avg_values:
                point, point_samples = self._measure_point(events, n_avg, request.samples_per_point)
                points.append(point)
                samples.extend(point_samples)
        finally:
            self._event_bus.unsubscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
            if started_here:
                self._acquisition_service.stop_acquisition(controller=CONTROLLER)
            restored = self._averaging.set_n_avg(previous_n_avg)
            if restored.is_failure:
                logger.error(
                    "AcquisitionThroughputCharacterizationService: could not restore n_avg=%d: %s",
                    previous_n_avg, restored.error,
                )
            self._excitation_service.unmute()
            logger.info(
                "AcquisitionThroughputCharacterizationService: restored n_avg=%d and the operator's excitation",
                previous_n_avg,
            )
        return points, samples, oversampling_ratio

    def _measure_point(
        self, events: "queue.Queue", n_avg: int, count: int
    ) -> Tuple[AcquisitionThroughputPoint, List[AcquisitionThroughputSampleDTO]]:
        if self._output_port is not None:
            self._output_port.present_throughput_characterization_step(f"Mesure n_avg={n_avg}…")
        applied = self._averaging.set_n_avg(n_avg)
        if applied.is_failure:
            raise _CharacterizationAborted(f"n_avg={n_avg} non appliqué : {applied.error}")
        settled_at = datetime.now() + timedelta(seconds=self._settle_delay_s)
        kept, rejected = collect_settled_samples(events, count, settled_at, self._settle_delay_s + self._sample_timeout_s)
        if len(kept) < count:
            raise _CharacterizationAborted(
                f"acquisition : {len(kept)}/{count} échantillons reçus en {self._sample_timeout_s:.0f} s "
                f"pour n_avg={n_avg}"
            )
        # Kept events are consecutive in the stream: each timestamp gap is one full round-trip.
        periods = [
            (later.sample.timestamp - earlier.sample.timestamp).total_seconds()
            for earlier, later in zip(kept, kept[1:])
        ]
        rows = [_channel_values(event.sample) for event in kept]
        point = characterize_point(n_avg, periods, rows)
        logger.info(
            "AcquisitionThroughputCharacterizationService: n_avg=%d period=%.4fs rate=%.1f/s adc_conversions=%.0f/s "
            "noise_in_one_second=%.3gV rejected=%d",
            n_avg, point.sample_period_s, point.sample_rate_per_s, point.adc_conversions_per_s,
            point.noise_in_one_second_v, rejected,
        )
        if self._output_port is not None:
            self._output_port.present_throughput_point_measured(_to_point_dto(point))
        samples = [
            AcquisitionThroughputSampleDTO(
                n_avg=n_avg, sample_index=event.sample_index, timestamp=event.sample.timestamp, values_v=row
            )
            for event, row in zip(kept, rows)
        ]
        return point, samples

    def _fail(self, reason: str) -> None:
        logger.warning("AcquisitionThroughputCharacterizationService: characterization failed: %s", reason)
        if self._output_port is not None:
            self._output_port.present_throughput_characterization_failed(reason)


def _channel_values(sample) -> Tuple[float, ...]:
    return (
        sample.voltage_x_in_phase, sample.voltage_y_in_phase, sample.voltage_z_in_phase,
        sample.voltage_x_quadrature, sample.voltage_y_quadrature, sample.voltage_z_quadrature,
    )


def _to_point_dto(point: AcquisitionThroughputPoint) -> AcquisitionThroughputPointDTO:
    return AcquisitionThroughputPointDTO(
        n_avg=point.n_avg,
        sample_period_s=point.sample_period_s,
        sample_rate_per_s=point.sample_rate_per_s,
        adc_conversions_per_s=point.adc_conversions_per_s,
        noise_v_rms=point.noise_v_rms,
        noise_rms_v=point.noise_rms_v,
        noise_in_one_second_v=point.noise_in_one_second_v,
    )


def _with_export_path(
    result: AcquisitionThroughputCharacterizationDTO, export_path: str
) -> AcquisitionThroughputCharacterizationDTO:
    from dataclasses import replace

    return replace(result, export_path=export_path)
