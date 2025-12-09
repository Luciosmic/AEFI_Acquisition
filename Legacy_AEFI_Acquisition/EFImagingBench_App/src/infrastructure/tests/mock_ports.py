from typing import List, Dict, Any
from datetime import datetime

from application.ports.i_motion_port import IMotionPort
from application.ports.i_acquisition_port import IAcquisitionPort
from application.ports.i_export_port import IExportPort
from application.ports.i_scan_executor import IScanExecutor

from domain.aggregates.step_scan import StepScan
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig

class MockMotionPort(IMotionPort):
    def __init__(self):
        self.move_history: List[Position2D] = []
        self._current_pos = Position2D(0, 0)
        
    def move_to(self, position: Position2D) -> None:
        print(f"[MockMotionPort] Moving to {position}")
        self.move_history.append(position)
        self._current_pos = position
        
    def get_current_position(self) -> Position2D:
        return self._current_pos
        
    def is_moving(self) -> bool:
        return False
        
    def wait_until_stopped(self) -> None:
        pass

class MockAcquisitionPort(IAcquisitionPort):
    def __init__(self):
        self.acquire_count = 0
        
    def acquire_sample(self) -> VoltageMeasurement:
        self.acquire_count += 1
        print(f"[MockAcquisitionPort] Acquiring sample #{self.acquire_count}")
        # Return synthetic data based on count
        return VoltageMeasurement(
            voltage_x_in_phase=0.1 * self.acquire_count,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.2 * self.acquire_count,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now(),
            uncertainty_estimate_volts=None
        )
        
    def configure_for_uncertainty(self, uncertainty: MeasurementUncertainty) -> None:
        pass
        
    def is_ready(self) -> bool:
        return True

class MockExportPort(IExportPort):
    def __init__(self):
        self.points: List[Dict[str, Any]] = []
        self.is_open = False
        
    def configure(self, directory: str, filename: str, metadata: Dict[str, Any]) -> None:
        pass
        
    def start(self) -> None:
        self.is_open = True
        
    def write_point(self, data: Dict[str, Any]) -> None:
        if not self.is_open:
            # In a real scenario this might raise, but for simple mock we can just track it
            # or we can enforce start() being called.
            pass 
        self.points.append(data)
        
    def stop(self) -> None:
        self.is_open = False


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

