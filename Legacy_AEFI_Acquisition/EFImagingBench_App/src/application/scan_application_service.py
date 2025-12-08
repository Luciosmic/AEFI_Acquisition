"""
Scan Application Service

Responsibility:
- Orchestrate scan operations (Use Cases)
- Coordinate Hardware (Motion, Acquisition) and Infrastructure (Export)
- Use Domain Service for pure logic (Trajectory calculation)
- Manage scan lifecycle (Pause, Resume, Cancel)

Rationale:
- Application Layer handles I/O and orchestration.
- Domain Layer handles pure logic.
"""

from typing import Optional, Callable, List
import logging
import time
from datetime import datetime

from .dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO, ScanStatusDTO
from ..domain.services.scan_trajectory_factory import ScanTrajectoryFactory
from ..domain.value_objects.scan.step_scan_config import StepScanConfig
from ..domain.value_objects.scan.scan_zone import ScanZone
from ..domain.value_objects.scan.scan_mode import ScanMode
from ..domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from ..domain.value_objects.scan.scan_status import ScanStatus
from ..domain.value_objects.scan.scan_progress import ScanProgress
from ..domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement

# Ports
from ..domain.ports.i_motion_port import IMotionPort
from ..domain.ports.i_acquisition_port import IAcquisitionPort
from ..domain.ports.i_export_port import IExportPort

logger = logging.getLogger(__name__)

from ..domain.aggregates.step_scan import StepScan
from ..domain.value_objects.scan.scan_point_result import ScanPointResult

# ... imports ...

class ScanApplicationService:
    """
    Application Service for Scan Operations.
    
    Orchestrates the scanning process:
    1. Get trajectory from Domain (ScanTrajectoryFactory)
    2. Loop through points:
       - Command Motion Port
       - Command Acquisition Port
       - Command Export Port
    """
    
    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort,
        export_port: Optional[IExportPort] = None
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._export_port = export_port
    
    def execute_scan(self, scan_dto: Scan2DConfigDTO, export_dto: ExportConfigDTO) -> bool:
        try:
            # ... setup ...
            
            # 1. Create Aggregate
            scan = StepScan()
            scan.start(config)
            self._current_scan = scan # Keep track of aggregate
            
            # Convert DTO to Domain Config
            config = self._to_domain_config(scan_dto)

            # 2. Validate (Domain)
            validation = config.validate()
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {validation.errors}")
            
            # 3. Generate Trajectory (Domain - Pure Calculation)
            trajectory = ScanTrajectoryFactory.create_trajectory(config)
            total_points = len(trajectory)
            
            # ... loop ...
            for i, position in enumerate(trajectory):
                # ... lifecycle checks ...
                
                # ... move & acquire ...
                
                # D. Average
                averaged_measurement = self._average_measurements(measurements)
                
                # Create Value Object
                point_result = ScanPointResult(
                    position=position,
                    measurement=averaged_measurement,
                    point_index=i
                )
                
                # Add to Aggregate
                scan.add_point_result(point_result)
                
                # E. Export (Infrastructure)
                if export_dto.enabled and self._export_port:
                    # Map VO to dict for export port
                    self._export_port.write_point({
                        "x": point_result.position.x,
                        "y": point_result.position.y,
                        "index": point_result.point_index,
                        "voltage_x_in_phase": point_result.measurement.voltage_x_in_phase,
                        # ... map other fields ...
                    })
            
            # Finalize
            if self._status != ScanStatus.CANCELLED:
                scan.complete()
                self._status = ScanStatus.COMPLETED
            else:
                scan.cancel()
                
            # ... stop export ...
            
            return True
            
        except Exception as e:
            if 'scan' in locals():
                scan.fail(str(e))
            self._status = ScanStatus.FAILED
            # ... error handling ...
            
    def pause_scan(self) -> None:
        self._paused = True
        
    def resume_scan(self) -> None:
        self._paused = False
        
    def cancel_scan(self) -> None:
        self._cancelled = True
        
    def get_status(self) -> Optional[ScanStatusDTO]:
        return ScanStatusDTO(
            status=self._status.value,
            is_running=self._status == ScanStatus.RUNNING,
            is_paused=self._paused,
            current_point_index=self._current_progress.current_point if self._current_progress else 0,
            total_points=self._current_progress.total_points if self._current_progress else 0,
            progress_percentage=0.0,
            estimated_remaining_seconds=0.0
        )

    def _average_measurements(self, measurements: List[VoltageMeasurement]) -> VoltageMeasurement:
        """Simple averaging helper."""
        if not measurements:
            raise ValueError("No measurements to average")
        n = len(measurements)
        # Simplified averaging for brevity
        return measurements[0] # Placeholder for actual averaging logic

    def _to_domain_config(self, dto: Scan2DConfigDTO) -> StepScanConfig:
        return StepScanConfig(
            scan_zone=ScanZone(x_min=dto.x_min, x_max=dto.x_max, y_min=dto.y_min, y_max=dto.y_max),
            x_nb_points=dto.x_nb_points,
            y_nb_points=dto.y_nb_points,
            scan_mode=ScanMode[dto.scan_mode],
            stabilization_delay_ms=dto.stabilization_delay_ms,
            averaging_per_scan_point=dto.averaging_per_point,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=dto.uncertainty_volts)
        )

    def _extract_metadata(self, dto: Scan2DConfigDTO) -> dict:
        return {"mode": dto.scan_mode}
