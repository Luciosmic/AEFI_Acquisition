from typing import List, Dict, Any
from time import sleep
import threading
from application.services.scan_application_service.i_scan_executor import IScanExecutor
from domain.aggregates.step_scan import StepScan
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_status import ScanStatus
from domain.value_objects.scan.scan_point_result import ScanPointResult
from domain.value_objects.acquisition.acquisition_sample import AcquisitionSample
from domain.events.i_domain_event_bus import IDomainEventBus

class MockScanExecutor(IScanExecutor):
    """
    Enhanced mock implementation of IScanExecutor with pause/resume/cancel support.

    Responsibility:
    - Simulate realistic scan execution with controllable timing
    - Support pause/resume/cancel during execution
    - Support failure injection at specific points
    - Emit proper events through event bus during execution
    - Record all interactions for test assertions
    """

    def __init__(
        self,
        event_bus: IDomainEventBus,
        should_succeed: bool = True,
        point_delay_ms: float = 10,
        fail_at_point: int = -1
    ):
        """
        Args:
            event_bus: Event bus for publishing domain events
            should_succeed: Whether execution should succeed or fail
            point_delay_ms: Delay between points (simulates acquisition time)
            fail_at_point: Point index at which to inject failure (-1 for no failure)
        """
        self.event_bus = event_bus
        self.should_succeed = should_succeed
        self.point_delay_ms = point_delay_ms
        self.fail_at_point = fail_at_point
        
        # Execution tracking
        self.executions: List[Dict[str, Any]] = []
        self.cancelled_scan_ids: List[str] = []
        self.paused_scan_ids: List[str] = []
        self.resumed_scan_ids: List[str] = []
        
        # Current execution state
        self._is_executing = False
        self._current_thread: threading.Thread | None = None

    def execute(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> bool:
        """Execute the scan trajectory with realistic point-by-point simulation."""
        info: Dict[str, Any] = {
            "scan_id": str(scan.id),
            "total_points": len(trajectory),
            "pattern": config.scan_pattern.name,
            "x_nb_points": config.x_nb_points,
            "y_nb_points": config.y_nb_points,
        }
        print(f"[MockScanExecutor] EXECUTE called with: {info}")
        self.executions.append(info)
        
        self._is_executing = True
        
        try:
            # Simulate point-by-point execution
            for i, position in enumerate(trajectory):
                # Check for cancellation
                if scan.status == ScanStatus.CANCELLED:
                    print(f"[MockScanExecutor] Scan cancelled at point {i}")
                    self._is_executing = False
                    return False
                
                # Check for pause - block until resumed or cancelled
                while scan.status == ScanStatus.PAUSED:
                    sleep(0.05)  # Wait for resume
                    if scan.status == ScanStatus.CANCELLED:
                        print(f"[MockScanExecutor] Scan cancelled during pause at point {i}")
                        self._is_executing = False
                        return False
                
                # Inject failure if requested
                if self.fail_at_point == i:
                    raise RuntimeError(f"Injected failure at point {i}")
                
                # Simulate acquisition with delay
                if self.point_delay_ms > 0:
                    sleep(self.point_delay_ms / 1000.0)
                
                # Final check before adding point (prevents race condition)
                if scan.status == ScanStatus.CANCELLED:
                    print(f"[MockScanExecutor] Scan cancelled before adding point {i}")
                    self._is_executing = False
                    return False
                
                # If paused, wait here before adding the point
                while scan.status == ScanStatus.PAUSED:
                    sleep(0.05)
                    if scan.status == ScanStatus.CANCELLED:
                        print(f"[MockScanExecutor] Scan cancelled during pause before adding point {i}")
                        self._is_executing = False
                        return False
                
                # Create mock measurement
                measurement = AcquisitionSample(
                    voltage_x_in_phase=float(i),
                    voltage_x_quadrature=0.0,
                    voltage_y_in_phase=0.0,
                    voltage_y_quadrature=0.0,
                    voltage_z_in_phase=0.0,
                    voltage_z_quadrature=0.0,
                    timestamp=float(i)
                )
                
                # Add point to scan (now guaranteed to be RUNNING)
                point_result = ScanPointResult(
                    position=position,
                    measurement=measurement,
                    point_index=i
                )
                scan.add_point_result(point_result)
                
                # Publish events
                self._publish_events(scan.domain_events)
            
            # Complete scan if not already completed
            if scan.status != ScanStatus.COMPLETED:
                scan.complete()
                self._publish_events(scan.domain_events)
            
            self._is_executing = False
            return self.should_succeed
            
        except Exception as exc:
            print(f"[MockScanExecutor] Execution failed: {exc}")
            scan.fail(str(exc))
            self._publish_events(scan.domain_events)
            self._is_executing = False
            return False

    def cancel(self, scan: StepScan) -> None:
        """Record that cancellation was requested."""
        scan_id = str(scan.id)
        print(f"[MockScanExecutor] CANCEL called for scan_id={scan_id}")
        self.cancelled_scan_ids.append(scan_id)
        scan.cancel()
        self._publish_events(scan.domain_events)

    def pause(self, scan: StepScan) -> None:
        """Record that pause was requested."""
        scan_id = str(scan.id)
        print(f"[MockScanExecutor] PAUSE called for scan_id={scan_id}")
        self.paused_scan_ids.append(scan_id)
        scan.pause()
        self._publish_events(scan.domain_events)

    def resume(self, scan: StepScan) -> None:
        """Record that resume was requested."""
        scan_id = str(scan.id)
        print(f"[MockScanExecutor] RESUME called for scan_id={scan_id}")
        self.resumed_scan_ids.append(scan_id)
        scan.resume()
        self._publish_events(scan.domain_events)

    def _publish_events(self, events):
        """Publish domain events to the event bus."""
        for event in events:
            event_type = type(event).__name__.lower()
            self.event_bus.publish(event_type, event)
