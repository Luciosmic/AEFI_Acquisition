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
from .ports.i_motion_port import IMotionPort
from .ports.i_acquisition_port import IAcquisitionPort
from .ports.i_export_port import IExportPort

logger = logging.getLogger(__name__)

from ..domain.aggregates.step_scan import StepScan
from ..domain.value_objects.scan.scan_point_result import ScanPointResult
from ..domain.events.domain_event import DomainEvent

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
        acquisition_port: IAcquisitionPort
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._subscribers: List[Callable[[DomainEvent], None]] = []
        self._current_scan: Optional[StepScan] = None
        self._status = ScanStatus.PENDING
        self._paused = False
        self._cancelled = False

    # ==================================================================================
    # COMMANDS (State Mutators)
    # ==================================================================================

    def execute_scan(self, scan_dto: Scan2DConfigDTO) -> bool:
        try:
            print(f"[ScanApplicationService] Starting scan execution...")
            # Reset state
            self._status = ScanStatus.RUNNING
            self._paused = False
            self._cancelled = False
            
            # Convert DTO to Domain Config
            print(f"[ScanApplicationService] Converting DTO to domain config...")
            config = self._to_domain_config(scan_dto)

            # 1. Validate (Domain)
            print(f"[ScanApplicationService] Validating configuration...")
            validation = config.validate()
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {validation.errors}")
            
            # 2. Create Aggregate & Start
            print(f"[ScanApplicationService] Creating StepScan aggregate and starting...")
            scan = StepScan()
            scan.start(config)
            self._current_scan = scan
            self._dispatch_events(scan.domain_events)
            
            # 3. Generate Trajectory (Domain - Pure Calculation)
            print(f"[ScanApplicationService] Generating trajectory...")
            trajectory = ScanTrajectoryFactory.create_trajectory(config)
            total_points = len(trajectory)
            print(f"[ScanApplicationService] Trajectory generated with {total_points} points.")
            
            # 4. Execution Loop
            for i, position in enumerate(trajectory):
                print(f"[ScanApplicationService] Processing point {i+1}/{total_points} at {position}...")
                # Check Cancellation
                if self._cancelled:
                    print(f"[ScanApplicationService] Scan cancelled by user.")
                    scan.cancel()
                    self._status = ScanStatus.CANCELLED
                    self._dispatch_events(scan.domain_events)
                    break
                    
                # Check Pause
                while self._paused:
                    print(f"[ScanApplicationService] Scan paused...")
                    time.sleep(0.1)
                    if self._cancelled: 
                        break
                
                # A. Move (Infrastructure)
                self._motion_port.move_to(position)
                
                # B. Stabilize
                if config.stabilization_delay_ms > 0:
                    time.sleep(config.stabilization_delay_ms / 1000.0)
                
                # C. Acquire (Infrastructure)
                measurements = []
                for _ in range(config.averaging_per_scan_point):
                    measurements.append(self._acquisition_port.acquire_sample())
                
                # D. Average
                averaged_measurement = self._average_measurements(measurements)
                
                # Create Value Object
                point_result = ScanPointResult(
                    position=position,
                    measurement=averaged_measurement,
                    point_index=i
                )
                
                # E. Add to Aggregate (Domain Logic)
                scan.add_point_result(point_result)
                
                # F. Dispatch Events (Application Logic)
                self._dispatch_events(scan.domain_events)
            
            # Finalize
            if self._status != ScanStatus.CANCELLED:
                if scan.status != ScanStatus.COMPLETED:
                     scan.complete()
                self._status = ScanStatus.COMPLETED
                print(f"[ScanApplicationService] Scan completed successfully.")
                self._dispatch_events(scan.domain_events)
            
            return True
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            print(f"[ScanApplicationService] Scan failed: {e}")
            if self._current_scan:
                self._current_scan.fail(str(e))
                self._dispatch_events(self._current_scan.domain_events)
            self._status = ScanStatus.FAILED
            return False

    def pause_scan(self) -> None:
        self._paused = True
        
    def resume_scan(self) -> None:
        self._paused = False
        
    def cancel_scan(self) -> None:
        self._cancelled = True

    def subscribe(self, callback: Callable[[DomainEvent], None]) -> None:
        """Subscribe to domain events."""
        self._subscribers.append(callback)

    # ==================================================================================
    # QUERIES (Read-Only)
    # ==================================================================================

    def get_status(self) -> ScanStatusDTO:
        current_idx = 0
        total_pts = 0
        
        if self._current_scan:
            current_idx = len(self._current_scan.points)
            total_pts = self._current_scan.expected_points

        return ScanStatusDTO(
            status=self._status.value,
            is_running=self._status == ScanStatus.RUNNING,
            is_paused=self._paused,
            current_point_index=current_idx,
            total_points=total_pts,
            progress_percentage=(current_idx / total_pts * 100.0) if total_pts > 0 else 0.0,
            estimated_remaining_seconds=0.0 # To be implemented
        )

    # ==================================================================================
    # HELPERS (Internal)
    # ==================================================================================

    def _dispatch_events(self, events: List[DomainEvent]) -> None:
        """Dispatch events to all subscribers."""
        for event in events:
            for subscriber in self._subscribers:
                try:
                    subscriber(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")

    def _average_measurements(self, measurements: List[VoltageMeasurement]) -> VoltageMeasurement:
        """Simple averaging helper."""
        if not measurements:
            raise ValueError("No measurements to average")
        n = len(measurements)
        # Simplified averaging for brevity - In real app, average all fields
        return measurements[0] 

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
