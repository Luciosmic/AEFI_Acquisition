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
from typing import Any, Optional, Callable, List
import logging
import queue
import time
from datetime import datetime

from .dtos.scan_dtos import Scan2DConfigDTO, ScanStatusDTO
from domain.step_scan.services.scan_trajectory_factory.scan_trajectory_factory import ScanTrajectoryFactory
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
from application._shared.ports.i_async_task_runner import IAsyncTaskRunner
from .ports.i_motion_synchronizer import IMotionSynchronizer
from .ports.i_scan_output_port import IScanOutputPort
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import IElectricFieldProbePort

# Continuous acquisition streams (scan is a subscriber, not a puller — the
# continuous worker owns the driver exclusively).
from application.services.continuous_acquisition_service.i_api_continuous_acquisition_service import IApiContinuousAcquisitionService
from application.services.continuous_acquisition_service.dtos.continuous_acquisition_dtos import ContinuousAcquisitionConfig
from application.services.electric_field_probe_service.i_api_electric_field_probe_service import IApiElectricFieldProbeService
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import ElectricFieldProbeAcquisitionConfig
from domain.shared_kernel.events.continuous_acquisition_sample_acquired.continuous_acquisition_sample_acquired import ContinuousAcquisitionSampleAcquired

# Error union (cross-layer translation)
from .errors.motion_sync_error import (
    EmergencyStop,
    MotionHardwareFailed,
    MotionSyncError,
    MotionStoppedExternally,
    MotionTimeout,
)

logger = logging.getLogger(__name__)


def _drain_queue(q: "queue.Queue") -> None:
    """Discard whatever is currently buffered in `q` without blocking."""
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            return


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
    fits (IApiContinuousAcquisitionService and IApiElectricFieldProbeService
    already share that shape).
    """

    name: str
    event_topic: str
    service: Any
    acquisition_config: Any
    is_ready: Callable[[], bool]
    publish_point_result: Callable[[Any, int, Any, List], None]


def make_electric_field_probe_channel(
    probe_port: IElectricFieldProbePort,
    probe_service: IApiElectricFieldProbeService,
    event_bus: IDomainEventBus,
    sample_rate_hz: float,
) -> AuxiliaryProbeChannel:
    """Build the Narda EF probe's auxiliary channel registration."""

    def _publish(scan: StepScan, point_index: int, position, samples: List) -> None:
        field_measurement = FieldMeasurementStatisticsService.calculate_statistics(samples)
        event_bus.publish(
            "electricfieldscanpointacquired",
            ElectricFieldScanPointAcquired(
                scan_id=scan.id,
                point_index=point_index,
                position=position,
                field_measurement=field_measurement,
            ),
        )

    return AuxiliaryProbeChannel(
        name="Narda probe",
        event_topic="fieldsampleacquired",
        service=probe_service,
        acquisition_config=ElectricFieldProbeAcquisitionConfig(sample_rate_hz=sample_rate_hz),
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

    # Ceiling above the Narda probe's fastest filter response (~33 Hz at F1;
    # RECOMMENDED_FILTER=F4/F5 in driver_narda_ep601.py is slower). The
    # continuous worker's inter-sample sleep barely adds delay once real
    # acquire latency dominates — this is a safe upper bound, not a tuned rate.
    NARDA_CONTINUOUS_SAMPLE_RATE_HZ = 50.0

    # Total budget to collect one point's averaging window from a sample
    # stream (ADC or EF probe) before giving up. Same order of magnitude as
    # the existing motion timeout (wait_for_motion(timeout_seconds=30.0)) —
    # "hardware should have responded by now".
    POINT_ACQUISITION_TIMEOUT_S = 30.0

    def __init__(
        self,
        motion_port: IMotionPort,
        continuous_acquisition_service: IApiContinuousAcquisitionService,
        event_bus: IDomainEventBus,
        task_runner: IAsyncTaskRunner,
        motion_sync: IMotionSynchronizer,
        auxiliary_probes: Optional[List[AuxiliaryProbeChannel]] = None,
        output_port: Optional[IScanOutputPort] = None,
    ):
        self._motion_port = motion_port
        self._continuous_acquisition_service = continuous_acquisition_service
        self._event_bus = event_bus
        self._task_runner = task_runner
        self._motion_sync = motion_sync
        self._auxiliary_probes: List[AuxiliaryProbeChannel] = list(auxiliary_probes or [])
        self._output_port = output_port

        self._current_scan: Optional[StepScan] = None

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
        try:
            config = self._to_domain_config(scan_dto)

            validation = config.validate()
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {validation.errors}")

            scan = StepScan()
            scan.start(config)
            self._current_scan = scan
            self._publish_events(scan.domain_events)

            trajectory = ScanTrajectoryFactory.create_trajectory(config)

            self._task_runner.submit(
                lambda: self._execute_scan_loop(scan, trajectory, config)
            )
            return True

        except Exception as e:
            logger.error(f"Scan failed to start: {e}")
            if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
                self._current_scan.fail(str(e))
                self._publish_events(self._current_scan.domain_events)
            return False

    def pause_scan(self) -> None:
        if self._current_scan:
            self._current_scan.pause()
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
        config: StepScanConfig,
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

        def _on_adc_sample(event: ContinuousAcquisitionSampleAcquired) -> None:
            adc_queue.put(event.sample)

        self._event_bus.subscribe("continuousacquisitionsampleacquired", _on_adc_sample)

        # Only start what isn't already running, and only stop what we
        # started — a live-view session running before the scan keeps
        # running, untouched, after it.
        adc_started_by_scan = not self._continuous_acquisition_service.is_acquisition_running()
        if adc_started_by_scan:
            self._continuous_acquisition_service.start_acquisition(
                ContinuousAcquisitionConfig(sample_rate_hz=None)
            )

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

        try:
            for i, position in enumerate(trajectory):
                if scan.status == ScanStatus.CANCELLED:
                    return

                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)
                    if scan.status == ScanStatus.CANCELLED:
                        return

                # --- Motion ---
                motion_id = self._motion_port.move_to(position)
                sync_result = self._motion_sync.wait_for_motion(motion_id, timeout_seconds=30.0)

                if sync_result.is_failure:
                    error = sync_result.error
                    if isinstance(error, MotionTimeout):
                        reason = f"Motion timeout ({error.timeout_seconds}s) at point {i}"
                    elif isinstance(error, MotionHardwareFailed):
                        reason = f"Motion hardware failure at point {i}: {error.error_detail}"
                    elif isinstance(error, EmergencyStop):
                        reason = f"Emergency stop at point {i}"
                    else:
                        reason = f"Motion stopped externally at point {i}: {error.reason}"  # type: ignore[union-attr]
                    scan.fail(reason)
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
                        self._publish_events(scan.domain_events)
                        return

                    channel.publish_point_result(scan, i, position, channel_samples)

                # --- Add result to aggregate ---
                point_result = ScanPointResult(
                    position=position,
                    measurement=averaged_measurement,
                    point_index=i,
                )
                scan.add_point_result(point_result)
                self._publish_events(scan.domain_events)

            # --- Finalize ---
            if scan.status != ScanStatus.COMPLETED:
                scan.complete()
                self._publish_events(scan.domain_events)

        except Exception as exc:
            logger.error("Scan loop raised unexpectedly: %s", exc)
            scan.fail(str(exc))
            self._publish_events(scan.domain_events)

        finally:
            self._event_bus.unsubscribe("continuousacquisitionsampleacquired", _on_adc_sample)
            for topic, handler in channel_handlers:
                self._event_bus.unsubscribe(topic, handler)
            if adc_started_by_scan:
                self._continuous_acquisition_service.stop_acquisition()
            for channel in channels_started_by_scan:
                channel.service.stop_acquisition()

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

        if isinstance(event, ScanStarted):
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
            data = {
                "x": event.position.x,
                "y": event.position.y,
                "value": {
                    "x_in_phase": event.measurement.voltage_x_in_phase,
                    "x_quadrature": event.measurement.voltage_x_quadrature,
                    "y_in_phase": event.measurement.voltage_y_in_phase,
                    "y_quadrature": event.measurement.voltage_y_quadrature,
                    "z_in_phase": event.measurement.voltage_z_in_phase,
                    "z_quadrature": event.measurement.voltage_z_quadrature,
                },
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
            value = {f"component_{i}": c for i, c in enumerate(fm.components)}
            value["norm"] = fm.norm
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
        return StepScanConfig(
            scan_zone=ScanZone(x_min=dto.x_min, x_max=dto.x_max, y_min=dto.y_min, y_max=dto.y_max),
            x_nb_points=dto.x_nb_points,
            y_nb_points=dto.y_nb_points,
            scan_pattern=ScanPattern[dto.scan_pattern],
            stabilization_delay_ms=dto.stabilization_delay_ms,
            averaging_per_position=dto.averaging_per_position,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=dto.uncertainty_volts),
            scan_axis=ScanAxis[dto.scan_axis],
        )

    def _extract_metadata(self, dto: Scan2DConfigDTO) -> dict:
        return {"mode": dto.scan_pattern, "axis": dto.scan_axis}
