from typing import List, Dict, Any
from datetime import datetime
from ...application.ports.i_motion_port import IMotionPort
from ...application.ports.i_acquisition_port import IAcquisitionPort
from ...application.ports.i_export_port import IExportPort
from ...domain.value_objects.geometric.position_2d import Position2D
from ...domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from ...domain.value_objects.measurement_uncertainty import MeasurementUncertainty

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
