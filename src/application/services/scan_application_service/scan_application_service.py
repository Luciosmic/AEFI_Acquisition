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

from typing import Optional, Callable, List
import logging
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
from domain.shared_kernel.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.step_scan.value_objects.scan_trajectory.scan_trajectory import ScanTrajectory

# Ports
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application._shared.ports.i_async_task_runner import IAsyncTaskRunner
from .ports.i_acquisition_port import IAcquisitionPort
from .ports.i_motion_synchronizer import IMotionSynchronizer
from .ports.i_scan_output_port import IScanOutputPort
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import IElectricFieldProbePort

# Error union (cross-layer translation)
from .errors.motion_sync_error import (
    EmergencyStop,
    MotionHardwareFailed,
    MotionSyncError,
    MotionStoppedExternally,
    MotionTimeout,
)

logger = logging.getLogger(__name__)

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


class ScanApplicationService:
    """
    Application Service for Scan Operations.

    Receives IAsyncTaskRunner + IMotionSynchronizer from the infrastructure layer
    to avoid owning threading primitives.  The scan loop lives here (use-case
    logic); the task runner and motion synchronizer are thin infrastructure
    adapters that own only concurrency/protocol concerns.
    """

    # Retry budget for a single EF probe sample acquisition.
    # Applicative rule: transient USB/serial errors on the Narda probe are
    # retried before abandoning the sample (not a hardware invariant → belongs
    # here, not in infrastructure).
    FIELD_SAMPLE_MAX_RETRIES = 2

    # Retry budget for a whole point's worth of EF probe samples.
    # Applicative rule: the Narda probe is less robust than the AEFI ADC path,
    # so a point is never validated on partial field data — we keep sampling
    # at the same point (extra passes over the averaging window) rather than
    # advance with a gap. Expressed as "extra passes" so the bound scales with
    # averaging_per_position instead of being a fixed sample count.
    FIELD_POINT_MAX_RETRY_PASSES = 3

    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort,
        event_bus: IDomainEventBus,
        task_runner: IAsyncTaskRunner,
        motion_sync: IMotionSynchronizer,
        field_probe_port: Optional[IElectricFieldProbePort] = None,
        output_port: Optional[IScanOutputPort] = None,
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._event_bus = event_bus
        self._task_runner = task_runner
        self._motion_sync = motion_sync
        self._field_probe_port = field_probe_port
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
        """
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
                measurements = []
                for _ in range(config.averaging_per_position):
                    if scan.status == ScanStatus.CANCELLED:
                        return
                    measurements.append(self._acquisition_port.acquire_sample())

                averaged_measurement = MeasurementStatisticsService.calculate_statistics(measurements)

                # --- EF Probe (optional) ---
                # Invariant: a point is not validated on partial field data.
                # Each sample gets its own retry budget (FIELD_SAMPLE_MAX_RETRIES);
                # the point itself stays "in progress" (index does not advance,
                # add_point_result is not called) until the full averaging
                # window is collected or the point-level retry budget
                # (FIELD_POINT_MAX_RETRY_PASSES) is exhausted, in which case the
                # whole scan fails rather than publishing an incomplete point.
                field_measurement = None
                if self._field_probe_port is not None and self._field_probe_port.is_ready():
                    field_measurements = self._acquire_field_samples_until_complete(
                        scan, i, config.averaging_per_position
                    )
                    if scan.status == ScanStatus.CANCELLED:
                        return
                    if field_measurements is None:
                        scan.fail(
                            f"Narda probe: point {i} never reached "
                            f"{config.averaging_per_position} samples — aborting scan "
                            f"rather than validating an incomplete point"
                        )
                        self._publish_events(scan.domain_events)
                        return

                    field_measurement = FieldMeasurementStatisticsService.calculate_statistics(
                        field_measurements
                    )
                    ef_event = ElectricFieldScanPointAcquired(
                        scan_id=scan.id,
                        point_index=i,
                        position=position,
                        field_measurement=field_measurement,
                    )
                    self._event_bus.publish("electricfieldscanpointacquired", ef_event)

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

    def _acquire_field_sample_with_retry(self, point_index: int):
        """
        Acquire one EF probe sample, retrying on transient failures.

        Returns the sample, or None once the retry budget is exhausted, so the
        caller can keep whatever other samples in the averaging window succeeded.
        """
        for attempt in range(self.FIELD_SAMPLE_MAX_RETRIES + 1):
            try:
                return self._field_probe_port.acquire_sample()
            except Exception as e:
                logger.warning(
                    "Field probe sample failed at point %d (attempt %d/%d): %s",
                    point_index,
                    attempt + 1,
                    self.FIELD_SAMPLE_MAX_RETRIES + 1,
                    e,
                )
        return None

    def _acquire_field_samples_until_complete(
        self, scan: StepScan, point_index: int, required_samples: int
    ) -> Optional[List]:
        """
        Keep sampling the EF probe at the current point until `required_samples`
        have been collected, bounded by FIELD_POINT_MAX_RETRY_PASSES extra
        passes over the averaging window.

        Returns the list of samples, or None if the scan was cancelled or the
        retry budget was exhausted before reaching `required_samples`.
        """
        samples: List = []
        max_attempts = required_samples * (self.FIELD_POINT_MAX_RETRY_PASSES + 1)
        attempts = 0
        while len(samples) < required_samples and attempts < max_attempts:
            if scan.status == ScanStatus.CANCELLED:
                return None
            attempts += 1
            sample = self._acquire_field_sample_with_retry(point_index)
            if sample is not None:
                samples.append(sample)

        if len(samples) < required_samples:
            logger.warning(
                "Narda probe: point %d incomplete (%d/%d samples) after %d attempts, giving up",
                point_index,
                len(samples),
                required_samples,
                attempts,
            )
            return None
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
