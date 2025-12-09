"""
StepScanExecutor

Responsibility:
- Execute a step‑and‑settle scan:
  move → optional wait → acquire N samples → average → add result to aggregate
  → publish domain events via the event bus.

Rationale:
- Move the heavy execution loop out of the Application service into an
  Infrastructure adapter implementing the `IScanExecutor` port.
- First implementation stays synchronous (blocking) but the logic is
  encapsulated in a `_worker` method to allow an easy migration to
  background threads later.
"""

from __future__ import annotations

from typing import List
import time

from application.ports.i_scan_executor import IScanExecutor
from application.ports.i_motion_port import IMotionPort
from application.ports.i_acquisition_port import IAcquisitionPort

from domain.aggregates.step_scan import StepScan
from domain.events.domain_event import DomainEvent
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.services.measurement_statistics_service import MeasurementStatisticsService
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_point_result import ScanPointResult
from domain.value_objects.scan.scan_status import ScanStatus


class StepScanExecutor(IScanExecutor):
    """
    Concrete scan executor for step‑scan strategy.

    Notes:
    - Uses the same logic as the previous `ScanApplicationService.execute_scan`
      loop, but moved here and grouped in `_worker`.
    - Execution is currently **blocking**; callers can wrap this in their
      own thread / task if needed.
    """

    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort,
        event_bus: IDomainEventBus,
    ) -> None:
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._event_bus = event_bus

    # ------------------------------------------------------------------ #
    # IScanExecutor implementation
    # ------------------------------------------------------------------ #

    def execute(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> bool:
        """
        Synchronous execution for now; returns True on success, False on failure.
        """
        return self._worker(scan, trajectory, config)

    def cancel(self, scan: StepScan) -> None:
        """
        Basic cancellation: mark the aggregate as cancelled and publish events.
        More advanced executors could honour a cancellation flag during execution.
        """
        scan.cancel()
        self._publish_events(scan.domain_events)

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> bool:
        """
        Core execution loop, extracted from `ScanApplicationService.execute_scan`.
        """
        try:
            total_points = len(trajectory)

            for i, position in enumerate(trajectory):
                # A. Move (Infrastructure)
                self._motion_port.move_to(position)

                # B. Stabilize
                if config.stabilization_delay_ms > 0:
                    time.sleep(config.stabilization_delay_ms / 1000.0)

                # C. Acquire (Infrastructure)
                measurements = []
                for _ in range(config.averaging_per_position):
                    measurements.append(self._acquisition_port.acquire_sample())

                # D. Average (Domain Service)
                averaged_measurement = MeasurementStatisticsService.calculate_statistics(measurements)

                # E. Create value object and add to aggregate
                point_result = ScanPointResult(
                    position=position,
                    measurement=averaged_measurement,
                    point_index=i,
                )
                scan.add_point_result(point_result)

                # F. Publish domain events
                self._publish_events(scan.domain_events)

            # Finalize if not already completed by domain
            if scan.status != ScanStatus.COMPLETED:
                scan.complete()
                self._publish_events(scan.domain_events)

            return True

        except Exception as exc:
            # On failure, mark aggregate and publish events
            scan.fail(str(exc))
            self._publish_events(scan.domain_events)
            return False

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #

    def _publish_events(self, events: List[DomainEvent]) -> None:
        for event in events:
            event_type = type(event).__name__.lower()
            self._event_bus.publish(event_type, event)


