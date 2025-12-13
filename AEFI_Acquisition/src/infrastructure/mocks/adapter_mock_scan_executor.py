from typing import List, Dict, Any
from application.services.scan_application_service.i_scan_executor import IScanExecutor
from domain.aggregates.step_scan import StepScan
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig

class MockScanExecutor(IScanExecutor):
    """
    Simple mock implementation of IScanExecutor.

    Responsibility:
    - Record calls to `execute` and `cancel` without touching hardware.
    - Allow tests to assert that the Application layer delegates correctly
      to the scan executor port.
    """

    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.executions: List[Dict[str, Any]] = []
        self.cancelled_scan_ids: List[str] = []

    def execute(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> bool:
        """Record the execution parameters and return the configured result."""
        info: Dict[str, Any] = {
            "scan_id": str(scan.id),
            "total_points": len(trajectory),
            "pattern": config.scan_pattern.name,
            "x_nb_points": config.x_nb_points,
            "y_nb_points": config.y_nb_points,
        }
        print(f"[MockScanExecutor] EXECUTE called with: {info}")
        self.executions.append(info)
        return self.should_succeed

    def cancel(self, scan: StepScan) -> None:
        """Record that cancellation was requested."""
        scan_id = str(scan.id)
        print(f"[MockScanExecutor] CANCEL called for scan_id={scan_id}")
        self.cancelled_scan_ids.append(scan_id)
