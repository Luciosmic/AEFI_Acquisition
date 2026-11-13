"""
Frequency Sweep Service

See frequency_sweep_service_intention.md.
"""

import logging
import queue
import threading
from dataclasses import replace
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple
from uuid import uuid4

from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import IApiAefiAcquisitionService
# ponytail: direct Application-Service-to-Application-Service dependency,
# same precedent as ScanApplicationService and the throughput characterization.
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
    FrequencySweepActivityDTO,
    SweptExcitationDTO,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencyPointDTO,
    FrequencySweepRequestDTO,
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.services.frequency_sweep_service.i_api_frequency_sweep_service import IApiFrequencySweepService
from application.services.frequency_sweep_service.ports.i_frequency_sweep_export_port import IFrequencySweepExportPort
from application.services.frequency_sweep_service.ports.i_frequency_sweep_output_port import IFrequencySweepOutputPort
from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    ExportedFileDTO,
    SoftwareProvenanceDTO,
)
from application.shared.acquisition_parameters.i_acquisition_conditions_port import IAcquisitionConditionsPort
from application.shared.acquisition_parameters.i_software_provenance_port import ISoftwareProvenancePort
from application.shared.acquisition_parameters.i_usb_latency_timer_port import IUsbLatencyTimerPort
from application.shared.exclusive_control.exclusive_control import take_all
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from application.shared.settled_sample_collection.settled_sample_collection import collect_settled_samples
from domain.frequency_sweep.frequency_sweep import FrequencySweep
from domain.frequency_sweep.value_objects.frequency_grid.frequency_grid import FrequencyGrid
from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId
from domain.frequency_sweep.value_objects.frequency_sweep_role.frequency_sweep_role import FrequencySweepRole
from domain.frequency_sweep.value_objects.table_height.table_height import TableHeight
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle

AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC = "aefivoltagesampleacquired"
# Owner name of the excitation and the acquisition stream while sweeping.
CONTROLLER = "balayage en fréquence"
MIN_SAMPLES_PER_FREQUENCY = 3

logger = logging.getLogger(__name__)


class _SweepAborted(Exception):
    """Internal: an expected failure of the sweep (reason for the operator)."""


class FrequencySweepService(IApiFrequencySweepService):
    """Applies each frequency of a grid with the operator's excitation, and
    records the averaged I/Q response per axis at each one."""

    def __init__(
        self,
        excitation_service: ExcitationConfigurationService,
        acquisition_service: IApiAefiAcquisitionService,
        export_port: IFrequencySweepExportPort,
        task_runner: IAsyncTaskRunner,
        event_bus: IDomainEventBus,
        conditions_port: IAcquisitionConditionsPort,
        software_provenance_port: ISoftwareProvenancePort,
        usb_latency_timer_port: IUsbLatencyTimerPort,
        settle_delay_s: float = 0.5,
        frequency_timeout_s: float = 60.0,
    ) -> None:
        """`settle_delay_s`: wait after each frequency change before a sample
        counts; `frequency_timeout_s`: budget per frequency."""
        self._excitation_service = excitation_service
        self._acquisition_service = acquisition_service
        self._export = export_port
        self._task_runner = task_runner
        self._event_bus = event_bus
        self._conditions = conditions_port
        self._software_provenance = software_provenance_port
        self._usb_latency_timer = usb_latency_timer_port
        self._settle_delay_s = settle_delay_s
        self._frequency_timeout_s = frequency_timeout_s
        self._output_port: Optional[IFrequencySweepOutputPort] = None
        self._running = False
        self._stop_requested = threading.Event()
        self._releases: List = []
        self._held_controls: Tuple[str, ...] = ()
        # The sweep in progress, as recorded in its acquisition parameters.
        self._activity: Optional[FrequencySweepActivityDTO] = None
        self._activity_conditions = AcquisitionConditionsDTO()
        self._activity_software: Optional[SoftwareProvenanceDTO] = None
        self._export_location: Optional[str] = None

    def set_output_port(self, output_port: IFrequencySweepOutputPort) -> None:
        self._output_port = output_port

    # -- commands -----------------------------------------------------------------

    def start_sweep(self, request: FrequencySweepRequestDTO) -> None:
        logger.info(
            "FrequencySweepService: Command start_sweep role=%s start_hz=%s stop_hz=%s frequency_count=%s "
            "samples_per_frequency=%s table_height_mm=%s",
            request.role, request.start_hz, request.stop_hz, request.frequency_count,
            request.samples_per_frequency, request.table_height_mm,
        )
        if self._running:
            logger.info("FrequencySweepService: already running. Doing nothing.")
            return
        sweep_or_refusal = self._new_sweep(request)
        if isinstance(sweep_or_refusal, str):
            self._fail(sweep_or_refusal)
            return
        sweep = sweep_or_refusal
        # Everything the sweep depends on, held until it ends: the excitation
        # (frequency changed at each step) and the acquisition stream (no Stop
        # under its feet). Refused during a scan or a calibration.
        taken = take_all([
            (lambda: self._excitation_service.take_control(CONTROLLER),
             lambda: self._excitation_service.release_control(CONTROLLER)),
            (lambda: self._acquisition_service.take_control(CONTROLLER),
             lambda: self._acquisition_service.release_control(CONTROLLER)),
        ])
        if taken.is_failure:
            self._fail(taken.error)
            return
        self._releases = taken.value
        self._held_controls = ("excitation", "acquisition_stream")
        self._running = True
        self._stop_requested.clear()
        self._task_runner.submit(lambda: self._run(sweep, request))

    def stop_sweep(self) -> None:
        if not self._running:
            logger.info("FrequencySweepService: Command stop_sweep but no sweep running. Doing nothing.")
            return
        logger.info("FrequencySweepService: Command stop_sweep (after the frequency being acquired)")
        self._stop_requested.set()

    def _new_sweep(self, request: FrequencySweepRequestDTO):
        """The sweep to run, or the reason it is refused."""
        try:
            role = FrequencySweepRole(request.role)
        except ValueError:
            return f"rôle de balayage inconnu : {request.role!r}"
        if request.table_height_mm is None:
            return "hauteur de la table non saisie : elle conditionne la réutilisation du fond"
        if request.samples_per_frequency < MIN_SAMPLES_PER_FREQUENCY:
            return f"au moins {MIN_SAMPLES_PER_FREQUENCY} échantillons par fréquence sont nécessaires"
        excitation = self._excitation_service.get_current_parameters()
        if excitation.mode == ExcitationMode.CUSTOM:
            return (
                "excitation en mode personnalisé : choisir une direction (X, Y, circulaire) dans le panneau "
                "Excitation, sinon chaque changement de fréquence réécrirait les phases"
            )
        if excitation.level_s1_s2.value <= 0 and excitation.level_s3_s4.value <= 0:
            return "excitation éteinte : régler un niveau dans le panneau Excitation"
        try:
            grid = FrequencyGrid.logarithmic(request.start_hz, request.stop_hz, request.frequency_count)
            table_height = TableHeight(request.table_height_mm)
        except ValueError as error:
            return f"grille ou hauteur invalide : {error}"
        return FrequencySweep(
            FrequencySweepId(uuid4()), role, grid, table_height, samples_per_frequency=request.samples_per_frequency
        )

    # -- the sweep (background task) ----------------------------------------------

    def _run(self, sweep: FrequencySweep, request: FrequencySweepRequestDTO) -> None:
        self._activity = None
        self._export_location = None
        points: List[FrequencyPointDTO] = []
        samples: List[FrequencySweepSampleDTO] = []
        try:
            try:
                self._sweep(sweep, request, points, samples)
            except _SweepAborted as error:
                self._finish(sweep, "failed", str(error), points, samples)
                self._fail(str(error))
                return
            status = "completed" if sweep.is_completed else "cancelled"
            result = self._finish(sweep, status, None, points, samples)
            if self._output_port is not None:
                self._output_port.present_frequency_sweep_ended(result)
        finally:
            for release in self._releases:
                release()
            self._releases = []
            self._running = False

    def _sweep(
        self,
        sweep: FrequencySweep,
        request: FrequencySweepRequestDTO,
        points: List[FrequencyPointDTO],
        samples: List[FrequencySweepSampleDTO],
    ) -> None:
        """One point per grid frequency, with the operator's mode and levels.
        Restores the operator's frequency and the acquisition stream whatever happens."""
        started_at = _now()
        operator = self._excitation_service.get_current_parameters()
        events: "queue.Queue" = queue.Queue()

        def _on_sample(event) -> None:
            events.put(event)

        self._event_bus.subscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
        started_here = not self._acquisition_service.is_acquisition_running()
        if started_here:
            self._acquisition_service.start_acquisition(AefiAcquisitionConfig(), controller=CONTROLLER)
        excitation_restored = False
        try:
            self._begin_activity(sweep, request, started_at, operator, started_here)
            for index, frequency_hz in enumerate(sweep.grid.frequencies_hz):
                if self._stop_requested.is_set():
                    logger.info(
                        "FrequencySweepService: sweep_id=%s stop requested after %d/%d frequencies",
                        sweep.id, index, len(sweep.grid),
                    )
                    break
                point, point_samples = self._measure_frequency(sweep, events, operator, index, frequency_hz)
                points.append(point)
                samples.extend(point_samples)
                if self._output_port is not None:
                    self._output_port.present_frequency_point_measured(point)
        finally:
            self._event_bus.unsubscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
            if started_here:
                self._acquisition_service.stop_acquisition(controller=CONTROLLER)
            restored = self._excitation_service.set_excitation(
                operator.mode, operator.level_s1_s2.value, operator.level_s3_s4.value, operator.frequency,
                controller=CONTROLLER,
            )
            excitation_restored = restored.is_success
            if restored.is_failure:
                logger.error(
                    "FrequencySweepService: sweep_id=%s operator frequency %s Hz NOT restored: %s",
                    sweep.id, operator.frequency, restored.error,
                )
            else:
                logger.info("FrequencySweepService: sweep_id=%s operator frequency %s Hz restored", sweep.id, operator.frequency)
            self._end_activity(excitation_restored, len(points))

    def _measure_frequency(
        self, sweep: FrequencySweep, events: "queue.Queue", operator, index: int, frequency_hz: float
    ) -> Tuple[FrequencyPointDTO, List[FrequencySweepSampleDTO]]:
        count = sweep.samples_per_frequency
        if self._output_port is not None:
            self._output_port.present_frequency_sweep_step(
                f"Fréquence {index + 1}/{len(sweep.grid)} : {frequency_hz:g} Hz…"
            )
        applied = self._excitation_service.set_excitation(
            operator.mode, operator.level_s1_s2.value, operator.level_s3_s4.value, frequency_hz, controller=CONTROLLER,
        )
        if applied.is_failure:
            raise _SweepAborted(f"fréquence {frequency_hz:g} Hz non appliquée : {applied.error}")
        settled_at = datetime.now() + timedelta(seconds=self._settle_delay_s)
        kept, rejected = collect_settled_samples(events, count, settled_at, self._settle_delay_s + self._frequency_timeout_s)
        if len(kept) < count:
            raise _SweepAborted(
                f"acquisition : {len(kept)}/{count} échantillons reçus en {self._frequency_timeout_s:.0f} s "
                f"à {frequency_hz:g} Hz"
            )
        measurement = sweep.record_frequency_point(frequency_hz, [event.sample for event in kept])
        for domain_event in sweep.domain_events:
            self._event_bus.publish(type(domain_event).__name__.lower(), domain_event)
        phase_offset = self._reference_phase_offset_deg()
        logger.info(
            "FrequencySweepService: sweep_id=%s role=%s frequency_hz=%s x_i=%.4gV x_q=%.4gV rejected=%d "
            "reference_phase_offset_deg=%s",
            sweep.id, sweep.role.value, frequency_hz, measurement.voltage_x_in_phase,
            measurement.voltage_x_quadrature, rejected, phase_offset,
        )
        point = FrequencyPointDTO(
            frequency_index=index,
            frequency_hz=frequency_hz,
            samples_count=count,
            mean_v=_values(measurement),
            std_v=(
                measurement.std_dev_x_in_phase, measurement.std_dev_y_in_phase, measurement.std_dev_z_in_phase,
                measurement.std_dev_x_quadrature, measurement.std_dev_y_quadrature, measurement.std_dev_z_quadrature,
            ),
            reference_phase_offset_deg=phase_offset,
        )
        point_samples = [
            FrequencySweepSampleDTO(
                frequency_hz=frequency_hz, sample_index=event.sample_index,
                timestamp=event.sample.timestamp, values_v=_values(event.sample),
            )
            for event in kept
        ]
        return point, point_samples

    def _reference_phase_offset_deg(self) -> Optional[float]:
        """Phase of the synchronous detection reference relative to the
        excitation (DDS4 − DDS1), as written on the chip at this frequency —
        the compensation picks the calibration point nearest in frequency."""
        chip = self._conditions.read_conditions().signal_generation
        if chip is None or not {"1", "4"} <= set(chip.channels):
            return None
        offset = PhaseAngle.from_register(chip.channels["4"].phase_code).difference_from(
            PhaseAngle.from_register(chip.channels["1"].phase_code)
        )
        return round(offset, 6)

    # -- acquisition parameters (what influenced the sweep) ------------------------

    def _begin_activity(
        self, sweep: FrequencySweep, request: FrequencySweepRequestDTO, started_at: datetime, operator,
        stream_started_here: bool,
    ) -> None:
        conditions = self._conditions.read_conditions()
        position = self._conditions.read_bench_position()
        latency_ms, latency_unknown = self._read_usb_latency(conditions.host_link.serial_port)
        self._activity_conditions = conditions
        self._activity_software = self._software_provenance.read()
        self._activity = FrequencySweepActivityDTO(
            activity_id=str(sweep.id),
            started_at=started_at,
            status="running",
            role=sweep.role.value,
            frequencies_hz=sweep.grid.frequencies_hz,
            samples_per_frequency=sweep.samples_per_frequency,
            table_height_mm=sweep.table_height.millimetres,
            settle_delay_s=self._settle_delay_s,
            frequency_timeout_s=self._frequency_timeout_s,
            controller=CONTROLLER,
            held_controls=self._held_controls,
            excitation=SweptExcitationDTO(
                mode=operator.mode.name,
                level_s1_s2_percent=operator.level_s1_s2.value,
                level_s3_s4_percent=operator.level_s3_s4.value,
                operator_frequency_hz=operator.frequency,
            ),
            stream_started_here=stream_started_here,
            operator_name=request.operator_name,
            operator_id=request.operator_id,
            bench_position_start=position.value if position.is_success else None,
            bench_position_unknown_reason=None if position.is_success else position.error,
            usb_latency_timer_ms=latency_ms,
            usb_latency_unknown_reason=latency_unknown,
        )
        logger.info(
            "FrequencySweepService: sweep_id=%s started role=%s frequencies=%d table_height_mm=%s "
            "stream_started_here=%s commit=%s dirty=%s",
            sweep.id, sweep.role.value, len(sweep.grid), sweep.table_height.millimetres, stream_started_here,
            self._activity_software.commit, self._activity_software.dirty,
        )
        opened = self._export.open_export(sweep.role.value, sweep.table_height.millimetres)
        if opened.is_failure:
            logger.warning("FrequencySweepService: sweep_id=%s no export location: %s", sweep.id, opened.error)
            return
        self._export_location = opened.value
        self._write_acquisition_parameters()

    def _read_usb_latency(self, serial_port: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        if serial_port is None:
            return None, "port série du MCU inconnu (non connecté ou transport simulé)"
        latency = self._usb_latency_timer.read_latency_timer_ms(serial_port)
        return (latency.value, None) if latency.is_success else (None, latency.error)

    def _end_activity(self, excitation_restored: bool, acquired: int) -> None:
        if self._activity is None:
            return
        position = self._conditions.read_bench_position()
        self._activity = replace(
            self._activity,
            ended_at=_now(),
            excitation_restored=excitation_restored,
            acquired_frequency_count=acquired,
            bench_position_end=position.value if position.is_success else None,
        )

    def _finish(
        self,
        sweep: FrequencySweep,
        status: str,
        failure_reason: Optional[str],
        points: Sequence[FrequencyPointDTO],
        samples: Sequence[FrequencySweepSampleDTO],
    ) -> FrequencySweepResultDTO:
        """Export what was acquired (even partial: the parameters say so) and
        write the final acquisition parameters."""
        result = FrequencySweepResultDTO(
            sweep_id=str(sweep.id), role=sweep.role.value, table_height_mm=sweep.table_height.millimetres,
            status=status, points=tuple(points), export_path=None,
        )
        logger.info(
            "FrequencySweepService: sweep_id=%s ended status=%s acquired=%d/%d reason=%s",
            sweep.id, status, len(points), len(sweep.grid), failure_reason,
        )
        if self._activity is None:
            logger.info("FrequencySweepService: sweep_id=%s no activity started. Nothing to record.", sweep.id)
            return result
        files: Tuple[ExportedFileDTO, ...] = ()
        if self._export_location is not None:
            exported = self._export.export(self._export_location, result, samples)
            if exported.is_success:
                files = exported.value
                result = replace(result, export_path=self._export_location)
                logger.info("FrequencySweepService: sweep_id=%s exported to %s", sweep.id, self._export_location)
            else:
                logger.warning("FrequencySweepService: sweep_id=%s export failed: %s", sweep.id, exported.error)
        self._activity = replace(self._activity, status=status, failure_reason=failure_reason)
        self._write_acquisition_parameters(files)
        return result

    def _write_acquisition_parameters(self, files: Sequence[ExportedFileDTO] = ()) -> None:
        if self._export_location is None:
            logger.warning(
                "FrequencySweepService: sweep_id=%s status=%s parameters not written (no export location)",
                self._activity.activity_id, self._activity.status,
            )
            return
        written = self._export.write_acquisition_parameters(
            self._export_location,
            FrequencySweepAcquisitionParametersDTO(
                activity=self._activity,
                conditions=self._activity_conditions,
                software=self._activity_software,
                files=tuple(files),
            ),
        )
        if written.is_success:
            logger.info(
                "FrequencySweepService: sweep_id=%s status=%s acquisition parameters written",
                self._activity.activity_id, self._activity.status,
            )
        else:
            logger.warning(
                "FrequencySweepService: sweep_id=%s acquisition parameters not written: %s",
                self._activity.activity_id, written.error,
            )

    def _fail(self, reason: str) -> None:
        logger.warning("FrequencySweepService: sweep failed: %s", reason)
        if self._output_port is not None:
            self._output_port.present_frequency_sweep_failed(reason)


def _values(measurement) -> Tuple[float, ...]:
    return (
        measurement.voltage_x_in_phase, measurement.voltage_y_in_phase, measurement.voltage_z_in_phase,
        measurement.voltage_x_quadrature, measurement.voltage_y_quadrature, measurement.voltage_z_quadrature,
    )


def _now() -> datetime:
    """Local time with its offset (ISO 8601 with offset in the export)."""
    return datetime.now().astimezone()
