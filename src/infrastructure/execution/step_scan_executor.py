from __future__ import annotations

from typing import List, Optional, Any
import time
import threading

from src.application.services.scan_application_service.ports.i_scan_executor import IScanExecutor
from application.services.motion_control_service.i_motion_port import IMotionPort
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort

from domain.models.scan.aggregates.step_scan import StepScan
from domain.shared.events.domain_event import DomainEvent
from domain.shared.events.i_domain_event_bus import IDomainEventBus
from domain.models.aefi_device.services.measurement_statistics_service import MeasurementStatisticsService
from domain.models.scan.value_objects.scan_trajectory import ScanTrajectory
from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.models.scan.events.motion_events import MotionCompleted, MotionFailed, MotionStopped, MotionStarted
from domain.models.scan.services.motion_state_tracker import MotionStateTracker
from infrastructure.execution.motion_adapter_service import MotionAdapterService


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
        
        # Motion adapter for executing AtomicMotions
        self._motion_adapter = MotionAdapterService(motion_port)
        
        # State tracker for AtomicMotions
        self._motion_tracker = MotionStateTracker()
        
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
        
        # Register motions for tracking if they exist
        if scan._motions:
            for motion in scan._motions:
                self._motion_tracker.register_motion(motion)
        
        # Run worker in a separate thread to avoid blocking the caller (UI)
        thread = threading.Thread(
            target=self._worker,
            args=(scan, trajectory, config),
            daemon=True
        )
        thread.start()
        
        # Return True immediately to indicate "Started"
        return True

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
            # Track completion with actual duration
            duration_seconds = event.duration_ms / 1000.0
            self._motion_tracker.track_motion_completed(event.motion_id, duration_seconds)
            self._motion_completed_event.set()

    def _on_motion_failed(self, event: MotionFailed) -> None:
        """Handler for motion failed event."""
        if self._pending_motion_id and event.motion_id == self._pending_motion_id:
            self._motion_tracker.track_motion_failed(event.motion_id, event.error)
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

    def _on_motion_started(self, event: MotionStarted) -> None:
        """Handler for motion started event."""
        # Motion start is tracked in worker when using AtomicMotion
        pass
    
    def _on_motion_stopped(self, event: MotionStopped) -> None:
        """Handler for regular motion stop event."""
        # Similar to emergency stop but less severe
        self._motion_error = f"Motion stopped: {event.reason}"
        # Wake up the wait loop
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
        Now uses AtomicMotion entities when available, falls back to direct move_to otherwise.
        """
        # Subscribe to motion events
        self._event_bus.subscribe("motionstarted", self._on_motion_started)
        self._event_bus.subscribe("motioncompleted", self._on_motion_completed)
        self._event_bus.subscribe("motionfailed", self._on_motion_failed)
        self._event_bus.subscribe("motionstopped", self._on_motion_stopped)
        self._event_bus.subscribe("emergencystoptriggered", self._on_emergency_stop_triggered)

        try:
            positions = list(trajectory.points)
            motions = scan._motions if scan._motions else []
            
            # If no motions, generate them on the fly (fallback for backward compatibility)
            if not motions:
                from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
                from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
                selector = MotionProfileSelector()
                motions = ScanTrajectoryFactory.create_motions(positions, selector)
                scan.add_motions(motions)
                # Register generated motions
                for motion in motions:
                    self._motion_tracker.register_motion(motion)
            
            current_position = self._motion_port.get_current_position()
            
            # Process each position
            # Note: positions[i] corresponds to motion[i-1] (first position has no motion)
            for i, position in enumerate(positions):
                # Check for cancellation
                if scan.status == ScanStatus.CANCELLED:
                    return False

                # Check for pause - block until resumed or cancelled
                while scan.status == ScanStatus.PAUSED:
                    time.sleep(0.1)  # Wait for resume
                    # Check if cancelled during pause
                    if scan.status == ScanStatus.CANCELLED:
                        return False

                # A. Move (Event-Based, using AtomicMotion if available)
                self._motion_error = None
                self._motion_completed_event.clear()
                
                # Execute motion only if not first position (first position is already at target)
                if i > 0:
                    # Use AtomicMotion via adapter
                    motion = motions[i - 1]  # Motion index is i-1
                    motion_index = i - 1
                    print(f"[StepScanExecutor] Executing motion {motion_index+1}/{len(motions)} (position {i+1}/{len(positions)})")
                    motion_id = self._motion_adapter.execute_atomic_motion(
                        motion,
                        current_position
                    )
                    self._pending_motion_id = motion_id
                    
                    # Track motion start
                    self._motion_tracker.track_motion_started(motion_id, motion)
                    
                    # Wait for completion (with cancellation check)
                    timeout = 30.0 # TODO: Make configurable
                    start_wait = time.time()
                    
                    while not self._motion_completed_event.is_set():
                        # Check cancellation during wait
                        if scan.status == ScanStatus.CANCELLED:
                            self._motion_port.stop()  # Regular stop with deceleration
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
                    
                    # Update current position
                    current_position = self._motion_port.get_current_position()
                else:
                    # First position: no motion needed, but we still need to set pending_motion_id
                    # to None to avoid issues with event handlers
                    self._pending_motion_id = None

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
            self._current_scan = None
            # Unsubscribe to avoid leaks
            self._event_bus.unsubscribe("motionstarted", self._on_motion_started)
            self._event_bus.unsubscribe("motioncompleted", self._on_motion_completed)
            self._event_bus.unsubscribe("motionfailed", self._on_motion_failed)
            self._event_bus.unsubscribe("motionstopped", self._on_motion_stopped)
            self._event_bus.unsubscribe("emergencystoptriggered", self._on_emergency_stop_triggered)

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #

    def _publish_events(self, events: List[DomainEvent]) -> None:
        for event in events:
            event_type = type(event).__name__.lower()
            self._event_bus.publish(event_type, event)
