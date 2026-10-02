"""
Scan Application Service

Responsibility:
- Orchestrate scan operations (Use Cases)
- Coordinate Hardware (Motion, Acquisition) and Infrastructure (Export)
- Use Domain Service for pure logic (Trajectory calculation, statistics)
- Manage scan lifecycle (Pause, Resume, Cancel)
- Run the step-scan acquisition loop in a background task

Rationale:
- Application Layer handles I/O orchestration and use-case logic.
- Domain Layer handles pure logic (aggregate invariants, trajectory, statistics).
- Infrastructure Layer provides task execution and motion synchronization primitives.
"""

from dataclasses import dataclass
from typing import Any, Optional, Callable, List, Dict, Union
import logging
import math
import queue
import time
from datetime import datetime

from .dtos.scan_dtos import Scan2DConfigDTO, LineScanConfigDTO, ScanStatusDTO
from domain.step_scan.services.scan_trajectory_factory.scan_trajectory_factory import ScanTrajectoryFactory
from domain.step_scan.services.line_scan_trajectory_factory.line_scan_trajectory_factory import LineScanTrajectoryFactory
from domain.step_scan.services.fly_scan_line_projector.fly_scan_line_projector import FlyScanLineProjector
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.services.measurement_statistics_service.measurement_statistics_service import MeasurementStatisticsService
from domain.electric_field_probe.services.field_measurement_statistics_service.field_measurement_statistics_service import FieldMeasurementStatisticsService
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.value_objects.scan_trajectory.scan_trajectory import ScanTrajectory

# Ports
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from .ports.i_motion_synchronizer import IMotionSynchronizer
from .ports.i_scan_output_port import IScanOutputPort
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import IElectricFieldProbePort
# ponytail: direct Application-Service-to-Application-Service dependency,
# same precedent as ScanExportService's excitation_service coupling (see
# that file's __init__ comment) — no domain event exists yet for
# "excitation control requested", so the scan loop calls mute()/unmute()
# directly. Replace with an event-driven handoff if that ever exists.
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService

# Continuous acquisition streams (scan is a subscriber, not a puller — the
# continuous worker owns the driver exclusively).
from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import IApiAefiAcquisitionService
from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.shared.exclusive_control.exclusive_control import take_all
from application.services.electric_field_probe_service.i_api_electric_field_probe_service import IApiElectricFieldProbeService
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import ElectricFieldProbeAcquisitionConfig
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import AefiVoltageSampleAcquired
from domain.shared_kernel.events.position_updated.position_updated import PositionUpdated

# Error union (cross-layer translation)
from .errors.motion_sync_error import (
    EmergencyStop,
    MotionHardwareFailed,
    MotionSyncError,
    MotionStoppedExternally,
    MotionTimeout,
)

logger = logging.getLogger(__name__)

# Owner name of the excitation and of the acquisition stream during a scan.
SCAN_EXCITATION_CONTROLLER = "scan"


def _drain_queue(q: "queue.Queue") -> None:
    """Discard whatever is currently buffered in `q` without blocking."""
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            return


def _motion_failure_reason(error: MotionSyncError, where: str) -> str:
    if isinstance(error, MotionTimeout):
        return f"Motion timeout ({error.timeout_seconds}s) at {where}"
    if isinstance(error, MotionHardwareFailed):
        return f"Motion hardware failure at {where}: {error.error_detail}"
    if isinstance(error, EmergencyStop):
        return f"Emergency stop at {where}"
    return f"Motion stopped externally at {where}: {error.reason}"  # type: ignore[union-attr]


from domain.step_scan.step_scan import StepScan
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.scan_paused.scan_paused import ScanPaused
from domain.step_scan.events.scan_resumed.scan_resumed import ScanResumed
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus


@dataclass
class AuxiliaryProbeChannel:
    """
    One auxiliary (non-primary) sample stream feeding the scan loop — e.g.
    the Narda EF probe, or any future secondary probe.

    Distinct from the primary AEFI/ADC channel (hardcoded in the loop):
    a primary result feeds scan.add_point_result() directly, while an
    auxiliary probe publishes its own per-point domain event via
    publish_point_result. All registered channels are blocking — conservative
    default, matching the original Narda-only invariant: if a channel fails
    to collect averaging_per_position samples for a point, the whole scan
    fails rather than publish an incomplete point. Making a given probe
    optional instead of blocking is a per-probe policy decision left for
    later, not something this registry decides on its own.

    service/acquisition_config are duck-typed on purpose: any service
    exposing start_acquisition(config)/stop_acquisition()/is_acquisition_running()
    fits (IApiAefiAcquisitionService and IApiElectricFieldProbeService
    already share that shape).
    """

    name: str
    event_topic: str
    service: Any
    acquisition_config: Any
    is_ready: Callable[[], bool]
    publish_point_result: Callable[[Any, int, Any, List, Optional[List]], None]


def make_electric_field_probe_channel(
    probe_port: IElectricFieldProbePort,
    probe_service: IApiElectricFieldProbeService,
    event_bus: IDomainEventBus,
) -> AuxiliaryProbeChannel:
    """Build the Narda EF probe's auxiliary channel registration."""

    def _publish(
        scan: StepScan, point_index: int, position, samples: List, baseline_samples: Optional[List] = None
    ) -> None:
        field_measurement = FieldMeasurementStatisticsService.calculate_statistics(samples)
        baseline_field_measurement = (
            FieldMeasurementStatisticsService.calculate_statistics(baseline_samples)
            if baseline_samples
            else None
        )
        probe = probe_port.get_probe()
        event_bus.publish(
            "electricfieldscanpointacquired",
            ElectricFieldScanPointAcquired(
                scan_id=scan.id,
                point_index=point_index,
                position=position,
                field_measurement=field_measurement,
                baseline_field_measurement=baseline_field_measurement,
                axis_labels=probe.axis_labels if probe is not None else None,
            ),
        )

    return AuxiliaryProbeChannel(
        name="Narda probe",
        event_topic="fieldsampleacquired",
        service=probe_service,
        acquisition_config=ElectricFieldProbeAcquisitionConfig(),
        is_ready=probe_port.is_ready,
        publish_point_result=_publish,
    )


class ScanApplicationService:
    """
    Application Service for Scan Operations.

    Receives IAsyncTaskRunner + IMotionSynchronizer from the infrastructure layer
    to avoid owning threading primitives.  The scan loop lives here (use-case
    logic); the task runner and motion synchronizer are thin infrastructure
    adapters that own only concurrency/protocol concerns.
    """

    # Total budget to collect one point's averaging window from a sample
    # stream (ADC or EF probe) before giving up. Same order of magnitude as
    # the existing motion timeout (wait_for_motion(timeout_seconds=30.0)) —
    # "hardware should have responded by now".
    POINT_ACQUISITION_TIMEOUT_S = 30.0

    def __init__(
        self,
        motion_port: IMotionPort,
        aefi_acquisition_service: IApiAefiAcquisitionService,
        event_bus: IDomainEventBus,
        task_runner: IAsyncTaskRunner,
        motion_sync: IMotionSynchronizer,
        auxiliary_probes: Optional[List[AuxiliaryProbeChannel]] = None,
        output_port: Optional[IScanOutputPort] = None,
        excitation_service: Optional[ExcitationConfigurationService] = None,
    ):
        self._motion_port = motion_port
        self._aefi_acquisition_service = aefi_acquisition_service
        self._event_bus = event_bus
        self._task_runner = task_runner
        self._motion_sync = motion_sync
        self._auxiliary_probes: List[AuxiliaryProbeChannel] = list(auxiliary_probes or [])
        self._output_port = output_port
        self._excitation_service = excitation_service

        self._current_scan: Optional[StepScan] = None
        self._control_releases: List = []  # excitation + acquisition stream, held while a scan runs

        # Subscribe to forward events to the output port.
        self._event_bus.subscribe("scanstarted", self._on_domain_event)
        self._event_bus.subscribe("scanpointacquired", self._on_domain_event)
        self._event_bus.subscribe("scancompleted", self._on_domain_event)
        self._event_bus.subscribe("scanfailed", self._on_domain_event)
        self._event_bus.subscribe("scancancelled", self._on_domain_event)
        self._event_bus.subscribe("scanpaused", self._on_domain_event)
        self._event_bus.subscribe("scanresumed", self._on_domain_event)
        self._event_bus.subscribe("electricfieldscanpointacquired", self._on_domain_event)

    def set_output_port(self, output_port: IScanOutputPort) -> None:
        self._output_port = output_port

    # ==================================================================================
    # COMMANDS (State Mutators)
    # ==================================================================================

    def execute_scan(self, scan_dto: Scan2DConfigDTO) -> bool:
        def build() -> StepScanConfig:
            config = self._to_domain_config(scan_dto)
            validation = config.validate()
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {validation.errors}")
            return config

        return self._start_scan(build, ScanTrajectoryFactory.create_trajectory)

    def execute_line_scan(self, scan_dto: LineScanConfigDTO) -> bool:
        logger.info(
            "ScanApplicationService: Command execute_line_scan — center=(%s, %s) length_mm=%s n_points=%s theta_deg=%s",
            scan_dto.center_x, scan_dto.center_y, scan_dto.length_mm, scan_dto.n_points, scan_dto.theta_deg,
        )
        return self._start_scan(
            lambda: self._to_line_domain_config(scan_dto), LineScanTrajectoryFactory.create_trajectory
        )

    def _start_scan(self, build_config: Callable[[], Any], create_trajectory: Callable[[Any], ScanTrajectory]) -> bool:
        """Shared start for every scan shape: same aggregate, same loop —
        only the config type and its trajectory factory differ."""
        try:
            config = build_config()

            if config.differential_mode and self._excitation_service is None:
                raise ValueError("differential_mode requires an ExcitationConfigurationService")
            # The excitation is a measurement condition of every point, and the
            # acquisition stream feeds every point: both held for the whole scan
            # (refused if e.g. the automatic sensor calibration drives them;
            # Continuous Reading cannot Stop the stream under the scan).
            # Released with the streams.
            takes = [
                (lambda: self._aefi_acquisition_service.take_control(SCAN_EXCITATION_CONTROLLER),
                 lambda: self._aefi_acquisition_service.release_control(SCAN_EXCITATION_CONTROLLER)),
            ]
            if self._excitation_service is not None:
                takes.insert(0, (
                    lambda: self._excitation_service.take_control(SCAN_EXCITATION_CONTROLLER),
                    lambda: self._excitation_service.release_control(SCAN_EXCITATION_CONTROLLER),
                ))
            taken = take_all(takes)
            if taken.is_failure:
                logger.warning("ScanApplicationService: scan refused — %s", taken.error)
                return False
            self._control_releases = taken.value

            scan = StepScan()
            scan.start(config)
            self._current_scan = scan
            self._publish_events(scan.domain_events)

            trajectory = create_trajectory(config)

            # Only the grid config knows fly scan (LineScanConfig has no such field).
            run_loop = self._execute_fly_scan_loop if getattr(config, "fly_scan", False) else self._execute_scan_loop
            self._task_runner.submit(
                lambda: run_loop(scan, trajectory, config)
            )
            return True

        except Exception as e:
            logger.error(f"Scan failed to start: {e}")
            self._release_controls()
            if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
                self._current_scan.fail(str(e))
                self._publish_events(self._current_scan.domain_events)
            return False

    def _release_controls(self) -> None:
        """Give back the excitation and the acquisition stream (idempotent)."""
        releases, self._control_releases = self._control_releases, []
        for release in releases:
            release()

    def pause_scan(self) -> None:
        if not self._current_scan:
            return
        try:
            self._current_scan.pause()
        except ValueError as e:
            logger.warning("ScanApplicationService: pause_scan rejected — %s", e)
            return
        self._publish_events(self._current_scan.domain_events)

    def resume_scan(self) -> None:
        if self._current_scan:
            self._current_scan.resume()
            self._publish_events(self._current_scan.domain_events)

    def cancel_scan(self) -> None:
        if self._current_scan:
            self._current_scan.cancel()
            self._publish_events(self._current_scan.domain_events)

    # ==================================================================================
    # QUERIES (Read-Only)
    # ==================================================================================

    def get_status(self) -> ScanStatusDTO:
        if self._current_scan:
            status = self._current_scan.status
            current_idx = len(self._current_scan.points)
            total_pts = self._current_scan.expected_points
        else:
            status = ScanStatus.PENDING
            current_idx = 0
            total_pts = 0

        return ScanStatusDTO(
            status=status.value,
            is_running=status == ScanStatus.RUNNING,
            is_paused=status == ScanStatus.PAUSED,
            current_point_index=current_idx,
            total_points=total_pts,
            progress_percentage=(current_idx / total_pts * 100.0) if total_pts > 0 else 0.0,
            estimated_remaining_seconds=0.0,
        )

    # ==================================================================================
    # SUBSCRIPTIONS (Events)
    # ==================================================================================

    def subscribe_to_scan_updates(self, callback: Callable[[DomainEvent], None]) -> None:
        self._event_bus.subscribe("scanpointacquired", callback)

    def subscribe_to_scan_completion(self, callback: Callable[[DomainEvent], None]) -> None:
        self._event_bus.subscribe("scancompleted", callback)

    # ==================================================================================
    # SCAN LOOP (runs inside a background task submitted to IAsyncTaskRunner)
    # ==================================================================================

    def _execute_scan_loop(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: Union[StepScanConfig, LineScanConfig],
    ) -> None:
        """
        Core step-scan acquisition loop.

        Runs inside a task submitted to IAsyncTaskRunner.  All state mutations
        go through the StepScan aggregate; pause/cancel signals arrive via the
        aggregate's status field (set by pause_scan/cancel_scan on the service).

        Acquisition is subscription-based, not pulled: the ADC and every
        registered auxiliary probe (self._auxiliary_probes) are driven by
        their own continuous-acquisition worker (started here if not already
        running elsewhere, e.g. a live-view panel), and this loop just
        collects samples off the event bus per point. This keeps a single
        owner of each driver at all times.
        """
        adc_queue: "queue.Queue" = queue.Queue()

        def _on_adc_sample(event: AefiVoltageSampleAcquired) -> None:
            adc_queue.put(event.sample)

        self._event_bus.subscribe("aefivoltagesampleacquired", _on_adc_sample)

        # Only start what isn't already running, and only stop what we
        # started — a live-view session running before the scan keeps
        # running, untouched, after it.
        adc_started_by_scan = not self._aefi_acquisition_service.is_acquisition_running()
        if adc_started_by_scan:
            self._aefi_acquisition_service.start_acquisition(AefiAcquisitionConfig(), controller=SCAN_EXCITATION_CONTROLLER)

        # Active auxiliary channels: (channel, its queue). A channel that
        # isn't ready (probe not connected) is simply skipped for this scan.
        active_channels: List[tuple] = []
        channel_handlers: List[tuple] = []
        channels_started_by_scan: List[AuxiliaryProbeChannel] = []

        for channel in self._auxiliary_probes:
            if not channel.is_ready():
                continue

            channel_queue: "queue.Queue" = queue.Queue()

            def _make_handler(q: "queue.Queue") -> Callable:
                def _handler(event: Any) -> None:
                    q.put(event.sample)
                return _handler

            handler = _make_handler(channel_queue)
            self._event_bus.subscribe(channel.event_topic, handler)
            channel_handlers.append((channel.event_topic, handler))
            active_channels.append((channel, channel_queue))

            if not channel.service.is_acquisition_running():
                channel.service.start_acquisition(channel.acquisition_config)
                channels_started_by_scan.append(channel)

        def _release_streams() -> None:
            # Called before every terminal event publication (as well as in
            # `finally`, as a safety net — idempotent, safe to call twice):
            # an observer reacting to scancompleted/scanfailed must never see
            # a stream this scan owns still running.
            self._event_bus.unsubscribe("aefivoltagesampleacquired", _on_adc_sample)
            for topic, handler in channel_handlers:
                self._event_bus.unsubscribe(topic, handler)
            if adc_started_by_scan:
                self._aefi_acquisition_service.stop_acquisition(controller=SCAN_EXCITATION_CONTROLLER)
            for channel in channels_started_by_scan:
                channel.service.stop_acquisition()
            self._release_controls()

        try:
            for i, position in enumerate(trajectory):
                if scan.status == ScanStatus.CANCELLED:
                    return

                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)
                    if scan.status == ScanStatus.CANCELLED:
                        return

                # --- Differential baseline (excitation muted) ---
                # Mute is electronic and shared: toggled once per point, not
                # once per channel — the primary ADC and every active
                # auxiliary probe read their baseline window off the same
                # muted excitation state.
                #
                # Muted *before* motion starts rather than after stabilization:
                # motion + stabilization normally take far longer than the DDS
                # needs to settle at 0 gain, so the baseline window is already
                # stable by the time we'd collect it — the settle delay below
                # becomes a no-op floor instead of dead time. The try/finally
                # now spans motion too, so a motion failure/cancel while muted
                # still restores excitation before this point gives up.
                baseline_measurement = None
                channel_baseline_samples: Dict[str, List] = {}
                if config.differential_mode:
                    self._excitation_service.mute()

                try:
                    # --- Motion ---
                    motion_id = self._motion_port.move_to(position)
                    sync_result = self._motion_sync.wait_for_motion(motion_id, timeout_seconds=30.0)

                    if sync_result.is_failure:
                        scan.fail(_motion_failure_reason(sync_result.error, f"point {i}"))
                        _release_streams()
                        self._publish_events(scan.domain_events)
                        return

                    # Safe pause point after motion completes
                    while scan.status == ScanStatus.PAUSED:
                        time.sleep(0.1)
                        if scan.status == ScanStatus.CANCELLED:
                            return

                    # --- Stabilization ---
                    if config.stabilization_delay_ms > 0:
                        time.sleep(config.stabilization_delay_ms / 1000.0)

                    if scan.status == ScanStatus.CANCELLED:
                        return
                    while scan.status == ScanStatus.PAUSED:
                        time.sleep(0.1)
                        if scan.status == ScanStatus.CANCELLED:
                            return

                    if config.differential_mode:
                        if config.differential_settle_delay_ms > 0:
                            time.sleep(config.differential_settle_delay_ms / 1000.0)

                        if scan.status == ScanStatus.CANCELLED:
                            return
                        while scan.status == ScanStatus.PAUSED:
                            time.sleep(0.1)
                            if scan.status == ScanStatus.CANCELLED:
                                return

                        _drain_queue(adc_queue)
                        baseline_samples = self._collect_samples(adc_queue, config.averaging_per_position, scan)
                        if baseline_samples is None:
                            return
                        if len(baseline_samples) < config.averaging_per_position:
                            scan.fail(
                                f"AEFI baseline acquisition: point {i} timed out after "
                                f"{self.POINT_ACQUISITION_TIMEOUT_S}s "
                                f"({len(baseline_samples)}/{config.averaging_per_position} samples)"
                            )
                            _release_streams()
                            self._publish_events(scan.domain_events)
                            return
                        baseline_measurement = MeasurementStatisticsService.calculate_statistics(baseline_samples)

                        for channel, channel_queue in active_channels:
                            _drain_queue(channel_queue)
                            samples = self._collect_samples(channel_queue, config.averaging_per_position, scan)
                            if samples is None:
                                return
                            if len(samples) < config.averaging_per_position:
                                scan.fail(
                                    f"{channel.name} baseline: point {i} timed out after "
                                    f"{self.POINT_ACQUISITION_TIMEOUT_S}s "
                                    f"({len(samples)}/{config.averaging_per_position} samples) "
                                    "— aborting scan rather than validating an incomplete point"
                                )
                                _release_streams()
                                self._publish_events(scan.domain_events)
                                return
                            channel_baseline_samples[channel.name] = samples
                finally:
                    # Always restore the pre-scan excitation state, even on a
                    # failure/cancel return above (including a motion failure
                    # while still muted).
                    if config.differential_mode:
                        self._excitation_service.unmute()

                if config.differential_mode:
                    if config.differential_settle_delay_ms > 0:
                        time.sleep(config.differential_settle_delay_ms / 1000.0)
                    if scan.status == ScanStatus.CANCELLED:
                        return
                    while scan.status == ScanStatus.PAUSED:
                        time.sleep(0.1)
                        if scan.status == ScanStatus.CANCELLED:
                            return

                # --- AEFI Acquisition ---
                # Samples accumulated in the queue while moving/stabilizing
                # don't correspond to the settled position — drop them before
                # collecting this point's averaging window.
                _drain_queue(adc_queue)
                measurements = self._collect_samples(adc_queue, config.averaging_per_position, scan)
                if measurements is None:
                    return
                if len(measurements) < config.averaging_per_position:
                    scan.fail(
                        f"AEFI acquisition: point {i} timed out after "
                        f"{self.POINT_ACQUISITION_TIMEOUT_S}s "
                        f"({len(measurements)}/{config.averaging_per_position} samples)"
                    )
                    _release_streams()
                    self._publish_events(scan.domain_events)
                    return

                averaged_measurement = MeasurementStatisticsService.calculate_statistics(measurements)

                # --- Auxiliary probes ---
                # Invariant: a point is not validated on partial data from any
                # registered channel — the whole scan fails rather than
                # publish an incomplete point. All channels are blocking
                # (conservative default); making a probe optional instead is
                # a per-probe policy decision, not made here.
                for channel, channel_queue in active_channels:
                    _drain_queue(channel_queue)
                    channel_samples = self._collect_samples(
                        channel_queue, config.averaging_per_position, scan
                    )
                    if channel_samples is None:
                        return
                    if len(channel_samples) < config.averaging_per_position:
                        scan.fail(
                            f"{channel.name}: point {i} timed out after "
                            f"{self.POINT_ACQUISITION_TIMEOUT_S}s "
                            f"({len(channel_samples)}/{config.averaging_per_position} samples) "
                            "— aborting scan rather than validating an incomplete point"
                        )
                        _release_streams()
                        self._publish_events(scan.domain_events)
                        return

                    channel.publish_point_result(
                        scan, i, position, channel_samples, channel_baseline_samples.get(channel.name)
                    )

                # --- Add result to aggregate ---
                point_result = ScanPointResult(
                    position=position,
                    measurement=averaged_measurement,
                    point_index=i,
                    baseline_measurement=baseline_measurement,
                )
                scan.add_point_result(point_result)
                # add_point_result() auto-completes the aggregate (and queues
                # a ScanCompleted event) once the last point is in — release
                # streams *before* publishing so an observer reacting to
                # ScanCompleted never sees a stream this scan owns still
                # running. The Finalize check below is then a no-op for the
                # common case; it stays as a fallback for the (defensive)
                # scenario where the aggregate didn't auto-complete.
                if scan.status == ScanStatus.COMPLETED:
                    _release_streams()
                self._publish_events(scan.domain_events)

            # --- Finalize ---
            if scan.status != ScanStatus.COMPLETED:
                scan.complete()
                _release_streams()
                self._publish_events(scan.domain_events)

        except Exception as exc:
            logger.error("Scan loop raised unexpectedly: %s", exc)
            scan.fail(str(exc))
            _release_streams()
            self._publish_events(scan.domain_events)

        finally:
            # Safety net for the cancel-return paths above (which don't
            # publish a terminal event themselves) and any path we didn't
            # anticipate. Idempotent — a harmless no-op if _release_streams()
            # already ran for this scan.
            _release_streams()

    # ==================================================================================
    # FLY SCAN LOOP (quick exploration — same background task mechanism)
    # ==================================================================================

    # Polling period of the motion completion while samples are placed.
    FLY_MOTION_POLL_S = 0.02

    def _execute_fly_scan_loop(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> None:
        """
        Fly-scan loop: each line of the grid is swept in one go while the ADC
        stream keeps running. The positions the motion controller reports
        while it moves (PositionUpdated, ~every 150 ms) give the instant each
        grid point is crossed; the samples are read at that instant
        (FlyScanLineProjector). Grid points are emitted live, as soon as
        they are passed — never in a burst at the end of the line.

        Software synchronization (reception timestamps in Python), accepted:
        an exploration before a step scan, no stabilization, no averaging.
        Same grid, aggregate and events as the step scan.
        """
        adc_queue: "queue.Queue" = queue.Queue()
        position_queue: "queue.Queue" = queue.Queue()

        def _on_adc_sample(event: AefiVoltageSampleAcquired) -> None:
            adc_queue.put((time.monotonic(), event.sample))

        def _on_position(event: PositionUpdated) -> None:
            position_queue.put((time.monotonic(), event.position))

        self._event_bus.subscribe("aefivoltagesampleacquired", _on_adc_sample)
        self._event_bus.subscribe("positionupdated", _on_position)

        # Same ownership rule as the step loop: only stop what we started.
        adc_started_by_scan = not self._aefi_acquisition_service.is_acquisition_running()
        if adc_started_by_scan:
            self._aefi_acquisition_service.start_acquisition(AefiAcquisitionConfig())

        def _release_streams() -> None:
            self._event_bus.unsubscribe("aefivoltagesampleacquired", _on_adc_sample)
            self._event_bus.unsubscribe("positionupdated", _on_position)
            if adc_started_by_scan:
                self._aefi_acquisition_service.stop_acquisition()

        def _fail(reason: str) -> None:
            # A cancel can land while a line is being swept — nothing left to fail then.
            if scan.status in (ScanStatus.RUNNING, ScanStatus.PAUSED):
                scan.fail(reason)
            _release_streams()
            self._publish_events(scan.domain_events)

        def _may_continue() -> bool:
            while scan.status == ScanStatus.PAUSED:
                time.sleep(0.1)
            return scan.status == ScanStatus.RUNNING

        # Points passed while the scan is paused mid-line wait here: the
        # aggregate only takes results while RUNNING, the line goes on anyway.
        pending: List[ScanPointResult] = []

        def _emit(line_index: int, line: List[Position2D], grid_points) -> None:
            for k, measurement in grid_points:
                pending.append(ScanPointResult(
                    position=line[k], measurement=measurement, point_index=line_index * n + k,
                ))
            if scan.status != ScanStatus.RUNNING:
                return
            while pending:
                scan.add_point_result(pending.pop(0))
                # Same rule as the step loop: streams released before
                # ScanCompleted is published.
                if scan.status == ScanStatus.COMPLETED:
                    _release_streams()
                self._publish_events(scan.domain_events)

        points = list(trajectory)
        n = config.points_per_line()
        lines = [points[i:i + n] for i in range(0, len(points), n)]
        logger.info(
            "ScanApplicationService: fly scan loop started scan_id=%s lines=%d points_per_line=%d",
            scan.id, len(lines), n,
        )
        # ponytail: AEFI stream only — an auxiliary probe (Narda, ~50 Hz) is
        # too slow to be swept; give it its own projector if a fly map of the
        # field probe is ever wanted.
        ignored = [channel.name for channel in self._auxiliary_probes if channel.is_ready()]
        if ignored:
            logger.warning("ScanApplicationService: fly scan scan_id=%s ignores auxiliary probes %s", scan.id, ignored)

        try:
            for line_index, line in enumerate(lines):
                if not _may_continue():
                    return

                # Reach the line start and stop there, then sweep to its end.
                sync_result = self._motion_sync.wait_for_motion(self._motion_port.move_to(line[0]), timeout_seconds=30.0)
                if sync_result.is_failure:
                    _fail(_motion_failure_reason(sync_result.error, f"start of fly line {line_index}"))
                    return
                if not _may_continue():
                    return

                start, end = line[0], line[-1]
                length_mm = math.hypot(end.x - start.x, end.y - start.y)
                ux, uy = (end.x - start.x) / length_mm, (end.y - start.y) / length_mm

                def _abscissa(position: Position2D) -> float:
                    return (position.x - start.x) * ux + (position.y - start.y) * uy

                projector = FlyScanLineProjector(n, length_mm)
                counts = {"samples": 0, "positions": 0, "live": 0}

                def _drain(t_max: float = math.inf) -> None:
                    for source, add, key in (
                        (position_queue, lambda t, p: projector.add_position(t, _abscissa(p)), "positions"),
                        (adc_queue, projector.add_sample, "samples"),
                    ):
                        while True:
                            try:
                                t, item = source.get_nowait()
                            except queue.Empty:
                                break
                            if t > t_max:
                                continue
                            counts[key] += 1
                            passed = add(t, item)
                            counts["live"] += len(passed)
                            _emit(line_index, line, passed)

                # Only the speed setting, for the time budget of the line:
                # placement comes from the reported positions.
                speed_mm_s = self._motion_port.get_cruise_speed_mm_s()
                _drain_queue(adc_queue)
                _drain_queue(position_queue)
                t_start = time.monotonic()
                motion_id = self._motion_port.move_to(end)
                deadline = t_start + 2 * length_mm / speed_mm_s + 10.0

                while True:
                    _drain()
                    if scan.status == ScanStatus.CANCELLED:
                        return
                    sync_result = self._motion_sync.wait_for_motion(motion_id, timeout_seconds=self.FLY_MOTION_POLL_S)
                    if sync_result.is_success:
                        break
                    if not isinstance(sync_result.error, MotionTimeout):
                        _fail(_motion_failure_reason(sync_result.error, f"fly line {line_index}"))
                        return
                    if time.monotonic() > deadline:
                        _fail(
                            f"Motion timeout at fly line {line_index}: still moving after "
                            f"{deadline - t_start:.1f}s ({length_mm:.0f} mm at {speed_mm_s:.1f} mm/s)"
                        )
                        return

                t_end = time.monotonic()
                _drain(t_max=t_end)  # what was queued before the completion was seen
                # The motor is at the end now: close the trace there.
                counts["live"] += len(passed := projector.add_position(t_end, _abscissa(self._motion_port.get_current_position())))
                _emit(line_index, line, passed)

                if counts["samples"] == 0:
                    _fail(f"Fly line {line_index}: no AEFI sample in {t_end - t_start:.2f}s — nothing to place")
                    return
                filled = projector.finish()
                logger.info(
                    "ScanApplicationService: fly line swept scan_id=%s line=%d/%d samples=%d positions=%d "
                    "points_live=%d points_at_end=%d duration_s=%.2f",
                    scan.id, line_index + 1, len(lines), counts["samples"], counts["positions"],
                    counts["live"], len(filled), t_end - t_start,
                )
                _emit(line_index, line, filled)
                if not _may_continue():
                    return
                _emit(line_index, line, [])  # flush points held by a pause

        except Exception as exc:
            logger.error("Fly scan loop raised unexpectedly: scan_id=%s error=%s", scan.id, exc)
            _fail(str(exc))

        finally:
            _release_streams()

    def _collect_samples(
        self, sample_queue: "queue.Queue", count: int, scan: StepScan
    ) -> Optional[List]:
        """
        Collect `count` samples from `sample_queue`, bounded by
        POINT_ACQUISITION_TIMEOUT_S total.

        Polls with a short timeout so a cancel signal is noticed promptly
        instead of blocking for the whole budget. Returns whatever was
        collected (possibly short, if the budget ran out) — the caller
        decides whether that's a failure — or None if the scan was cancelled
        mid-collection.
        """
        samples: List = []
        deadline = time.monotonic() + self.POINT_ACQUISITION_TIMEOUT_S
        while len(samples) < count:
            if scan.status == ScanStatus.CANCELLED:
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                samples.append(sample_queue.get(timeout=min(remaining, 0.2)))
            except queue.Empty:
                continue
        return samples

    # ==================================================================================
    # EVENT ROUTING
    # ==================================================================================

    def _on_domain_event(self, event: DomainEvent) -> None:
        """Forward domain events from the bus to the output port."""
        if not self._output_port:
            return

        if isinstance(event, ScanStarted) and isinstance(event.config, LineScanConfig):
            cfg = event.config
            start, end = cfg.endpoints()
            self._output_port.present_scan_started(str(event.scan_id), {
                "scan_kind": "line",
                "points": cfg.total_points(),
                "n_points": cfg.n_points,
                "center_x": cfg.center.x,
                "center_y": cfg.center.y,
                "length_mm": cfg.length_mm,
                "theta_deg": cfg.theta_deg,
                "start_x": start.x,
                "start_y": start.y,
                "end_x": end.x,
                "end_y": end.y,
            })

        elif isinstance(event, ScanStarted):
            self._output_port.present_scan_started(str(event.scan_id), {
                "pattern": event.config.scan_pattern.name,
                "points": event.config.total_points(),
                "x_min": event.config.scan_zone.x_min,
                "x_max": event.config.scan_zone.x_max,
                "x_nb_points": event.config.x_nb_points,
                "y_min": event.config.scan_zone.y_min,
                "y_max": event.config.scan_zone.y_max,
                "y_nb_points": event.config.y_nb_points,
            })

        elif isinstance(event, ScanPointAcquired):
            value = {
                "x_in_phase": event.measurement.voltage_x_in_phase,
                "x_quadrature": event.measurement.voltage_x_quadrature,
                "y_in_phase": event.measurement.voltage_y_in_phase,
                "y_quadrature": event.measurement.voltage_y_quadrature,
                "z_in_phase": event.measurement.voltage_z_in_phase,
                "z_quadrature": event.measurement.voltage_z_quadrature,
            }
            b = event.baseline_measurement
            if b is not None:
                # Differential mode only — exposed as its own channel so the
                # live plot shows the excitation-muted sample too, not just
                # the excited one (mute/unmute is too fast to see on hardware
                # otherwise, see _system/ops/tasks.md "Mesure différentielle").
                value.update({
                    "baseline_x_in_phase": b.voltage_x_in_phase,
                    "baseline_x_quadrature": b.voltage_x_quadrature,
                    "baseline_y_in_phase": b.voltage_y_in_phase,
                    "baseline_y_quadrature": b.voltage_y_quadrature,
                    "baseline_z_in_phase": b.voltage_z_in_phase,
                    "baseline_z_quadrature": b.voltage_z_quadrature,
                })
            data = {
                "x": event.position.x,
                "y": event.position.y,
                "value": value,
                "index": event.point_index,
            }
            total = self._current_scan.expected_points if self._current_scan else 0
            self._output_port.present_scan_progress(event.point_index, total, data)

        elif isinstance(event, ScanCompleted):
            self._output_port.present_scan_completed(str(event.scan_id), event.total_points)

        elif isinstance(event, ScanFailed):
            self._output_port.present_scan_failed(str(event.scan_id), event.reason)

        elif isinstance(event, ScanCancelled):
            self._output_port.present_scan_cancelled(str(event.scan_id))

        elif isinstance(event, ScanPaused):
            self._output_port.present_scan_paused(str(event.scan_id), event.current_point_index)

        elif isinstance(event, ScanResumed):
            self._output_port.present_scan_resumed(str(event.scan_id), event.resume_from_point_index)

        elif isinstance(event, ElectricFieldScanPointAcquired):
            fm = event.field_measurement
            labels = event.axis_labels or tuple(str(i) for i in range(len(fm.components)))
            value = {f"field_{label.lower()}": c for label, c in zip(labels, fm.components)}
            value["norm"] = fm.norm
            bfm = event.baseline_field_measurement
            if bfm is not None:
                value.update(
                    {f"baseline_field_{label.lower()}": c for label, c in zip(labels, bfm.components)}
                )
            data = {
                "x": event.position.x,
                "y": event.position.y,
                "value": value,
                "index": event.point_index,
            }
            total = self._current_scan.expected_points if self._current_scan else 0
            self._output_port.present_field_scan_progress(event.point_index, total, data)

    def _publish_events(self, events: List[DomainEvent]) -> None:
        for event in events:
            event_type = type(event).__name__.lower()
            self._event_bus.publish(event_type, event)

    def _to_domain_config(self, dto: Scan2DConfigDTO) -> StepScanConfig:
        measurement_uncertainty = MeasurementUncertainty(max_uncertainty_volts=dto.uncertainty_volts)
        for warning in measurement_uncertainty.warnings:
            logger.warning("ScanApplicationService: uncertainty_volts=%s — %s", dto.uncertainty_volts, warning)

        return StepScanConfig(
            scan_zone=ScanZone(x_min=dto.x_min, x_max=dto.x_max, y_min=dto.y_min, y_max=dto.y_max),
            x_nb_points=dto.x_nb_points,
            y_nb_points=dto.y_nb_points,
            scan_pattern=ScanPattern[dto.scan_pattern],
            stabilization_delay_ms=dto.stabilization_delay_ms,
            averaging_per_position=dto.averaging_per_position,
            measurement_uncertainty=measurement_uncertainty,
            scan_axis=ScanAxis[dto.scan_axis],
            differential_mode=dto.differential_mode,
            differential_settle_delay_ms=dto.differential_settle_delay_ms,
            fly_scan=dto.fly_scan,
        )

    def _to_line_domain_config(self, dto: LineScanConfigDTO) -> LineScanConfig:
        return LineScanConfig(
            center=Position2D(x=dto.center_x, y=dto.center_y),
            length_mm=dto.length_mm,
            n_points=dto.n_points,
            theta_deg=dto.theta_deg,
            stabilization_delay_ms=dto.stabilization_delay_ms,
            averaging_per_position=dto.averaging_per_position,
            differential_mode=dto.differential_mode,
            differential_settle_delay_ms=dto.differential_settle_delay_ms,
        )

    def _extract_metadata(self, dto: Scan2DConfigDTO) -> dict:
        return {"mode": dto.scan_pattern, "axis": dto.scan_axis}
