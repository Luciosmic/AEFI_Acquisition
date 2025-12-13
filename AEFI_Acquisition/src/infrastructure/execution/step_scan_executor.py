from __future__ import annotations

from typing import List, Optional, Any
import time
import threading

from application.services.scan_application_service.i_scan_executor import IScanExecutor
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort

from domain.aggregates.step_scan import StepScan
from domain.events.domain_event import DomainEvent
from domain.events.i_domain_event_bus import IDomainEventBus
from domain.services.measurement_statistics_service import MeasurementStatisticsService
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_point_result import ScanPointResult
from domain.value_objects.scan.scan_status import ScanStatus
from domain.events.motion_events import MotionCompleted, MotionFailed


class StepScanExecutor(IScanExecutor):
    """
    Concrete scan executor for step‑scan strategy using event-based motion synchronization.

    Notes:
    - Decouples motion execution from scan logic via Domain Events.
    - Handles asynchronous motion hardware (like Arcus) correctly.
    - Allows responsive cancellation during motion wait.
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
        
        # State for event synchronization
        self._pending_motion_id: Optional[str] = None
        self._motion_completed_event = threading.Event()
        self._motion_error: Optional[str] = None
        self._current_scan: Optional[StepScan] = None

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
        Synchronous execution loop.
        """
        self._current_scan = scan
        try:
            return self._worker(scan, trajectory, config)
        finally:
            self._current_scan = None

    def cancel(self, scan: StepScan) -> None:
        """
        Mark scan as cancelled. Actual handling happens in _worker loop.
        """
        scan.cancel()
        self._publish_events(scan.domain_events)

    def pause(self, scan: StepScan) -> None:
        """
        Mark scan as paused. Actual handling happens in _worker loop.
        """
        scan.pause()
        self._publish_events(scan.domain_events)

    def resume(self, scan: StepScan) -> None:
        """
        Mark scan as resumed. Actual handling happens in _worker loop.
        """
        scan.resume()
        self._publish_events(scan.domain_events)

    # ------------------------------------------------------------------ #
    # Event Handlers
    # ------------------------------------------------------------------ #

    def _on_motion_completed(self, event: MotionCompleted) -> None:
        """Handler for motion completed event."""
        if self._pending_motion_id and event.motion_id == self._pending_motion_id:
            self._motion_completed_event.set()

    def _on_motion_failed(self, event: MotionFailed) -> None:
        """Handler for motion failed event."""
        if self._pending_motion_id and event.motion_id == self._pending_motion_id:
            self._motion_error = event.error
            self._motion_completed_event.set()

    def _on_emergency_stop_triggered(self, event: Any) -> None:
        """Handler for emergency stop event."""
        # Signal the wait loop to wake up and check cancellation/status
        self._motion_error = "Emergency Stop Triggered"
        
        # Cancel the scan immediately
        if self._current_scan:
            self._current_scan.cancel()
            
        self._motion_completed_event.set()

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
        Core execution loop using event-based motion synchronization.
        """
        # Subscribe to motion events
        self._event_bus.subscribe("motioncompleted", self._on_motion_completed)
        self._event_bus.subscribe("motionfailed", self._on_motion_failed)
        self._event_bus.subscribe("emergencystoptriggered", self._on_emergency_stop_triggered)

        try:
            for i, position in enumerate(trajectory):
                # Check for cancellation
                if scan.status == ScanStatus.CANCELLED:
                    return False

                # Check for pause - block until resumed or cancelled
                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)  # Wait for resume
                    # Check if cancelled during pause
                    if scan.status == ScanStatus.CANCELLED:
                        return False

                # A. Move (Event-Based)
                self._motion_error = None
                self._motion_completed_event.clear()
                
                # Start motion
                # print(f"[StepScanExecutor] Moving to {position}...")
                motion_id = self._motion_port.move_to(position)
                self._pending_motion_id = motion_id
                
                # Wait for completion (with cancellation check)
                timeout = 30.0 # TODO: Make configurable
                start_wait = time.time()
                
                while not self._motion_completed_event.is_set():
                    # Check cancellation during wait
                    if scan.status == ScanStatus.CANCELLED:
                        self._motion_port.stop(immediate=True)
                        return False
                    
                    # Check pause during wait
                    if scan.status == ScanStatus.PAUSED:
                        # Motion is already started, we should wait for it to complete
                        # but we can pause after motion completes
                        pass
                    
                    # Check timeout
                    if time.time() - start_wait > timeout:
                        raise RuntimeError(f"Motion timeout after {timeout}s")
                    
                    time.sleep(0.01) # Avoid CPU spin
                
                # Check for motion failure
                if self._motion_error:
                     raise RuntimeError(f"Motion failed: {self._motion_error}")

                # Check for pause AFTER motion completes (safe point)
                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)
                    if scan.status == ScanStatus.CANCELLED:
                        return False

                # B. Stabilize
                if config.stabilization_delay_ms > 0:
                    # print(f"[StepScanExecutor] Stabilizing for {config.stabilization_delay_ms}ms...")
                    time.sleep(config.stabilization_delay_ms / 1000.0)
                
                # Check for pause/cancel after stabilization (safe point)
                if scan.status == ScanStatus.CANCELLED:
                    return False
                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)
                    if scan.status == ScanStatus.CANCELLED:
                        return False

                # C. Acquire (Infrastructure)
                measurements = []
                for _ in range(config.averaging_per_position):
                    # Check cancellation during acquisition?
                    if scan.status == ScanStatus.CANCELLED:
                        return False
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
        finally:
            # Unsubscribe to avoid leaks
            self._event_bus.unsubscribe("motioncompleted", self._on_motion_completed)
            self._event_bus.unsubscribe("motionfailed", self._on_motion_failed)
            self._event_bus.unsubscribe("emergencystoptriggered", self._on_emergency_stop_triggered)

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #

    def _publish_events(self, events: List[DomainEvent]) -> None:
        for event in events:
            event_type = type(event).__name__.lower()
            self._event_bus.publish(event_type, event)
