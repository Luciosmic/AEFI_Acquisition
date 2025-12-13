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

from application.dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO, ScanStatusDTO
from domain.services.scan_trajectory_factory import ScanTrajectoryFactory
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.scan.scan_pattern import ScanPattern
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.value_objects.scan.scan_status import ScanStatus
from domain.value_objects.scan.scan_progress import ScanProgress
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement

# Ports
from application.services.motion_control_service.i_motion_port import IMotionPort
from .i_acquisition_port import IAcquisitionPort
from .i_scan_export_port import IScanExportPort
from .i_scan_executor import IScanExecutor

logger = logging.getLogger(__name__)

from domain.aggregates.step_scan import StepScan
from domain.value_objects.scan.scan_point_result import ScanPointResult
from .i_scan_output_port import IScanOutputPort
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed
from domain.events.domain_event import DomainEvent
from domain.events.i_domain_event_bus import IDomainEventBus

# ...

class ScanApplicationService:
    """
    Application Service for Scan Operations.
    """
    
    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort,
        event_bus: IDomainEventBus,
        scan_executor: IScanExecutor,
        output_port: Optional[IScanOutputPort] = None, # Optional for backward compat/tests
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._event_bus = event_bus
        self._scan_executor = scan_executor
        self._output_port = output_port
        
        self._current_scan: Optional[StepScan] = None
        self._status = ScanStatus.PENDING
        self._paused = False
        self._cancelled = False
        
        # Subscribe myself to the bus to forward events to the output port
        # This ensures that even events from the Executor (which talks to the bus) get forwarded
        self._event_bus.subscribe("scanstarted", self._on_domain_event)
        self._event_bus.subscribe("scanpointacquired", self._on_domain_event)
        self._event_bus.subscribe("scancompleted", self._on_domain_event)
        self._event_bus.subscribe("scanfailed", self._on_domain_event)


    def set_output_port(self, output_port: IScanOutputPort) -> None:
        """
        Set the output port (Presenter) after initialization.
        Useful for circular dependencies (Presenter <-> Service).
        """
        self._output_port = output_port

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

            # 0. Configure Motion Speed (if provided)
            if scan_dto.motion_speed_mm_s is not None:
                print(f"[ScanApplicationService] Setting motion speed to {scan_dto.motion_speed_mm_s} mm/s")
                self._motion_port.set_speed(scan_dto.motion_speed_mm_s)

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
            self._publish_events(scan.domain_events)
            
            # 3. Generate Trajectory (Domain - Pure Calculation)
            print(f"[ScanApplicationService] Generating trajectory...")
            trajectory = ScanTrajectoryFactory.create_trajectory(config)
            total_points = len(trajectory)
            print(f"[ScanApplicationService] Trajectory generated with {total_points} points.")
            
            # 4. Delegate execution to ScanExecutor (Infrastructure)
            print(f"[ScanApplicationService] Delegating execution to ScanExecutor...")
            success = self._scan_executor.execute(scan, trajectory, config)
            if not success:
                raise RuntimeError("Scan execution failed in ScanExecutor")
            
            # Status will be COMPLETED if executor reached the end
            self._status = ScanStatus.COMPLETED
            print(f"[ScanApplicationService] Scan completed successfully.")
            
            return True
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            print(f"[ScanApplicationService] Scan failed: {e}")
            if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
                # Ne marquer comme failed que si le scan est encore en cours
                # (évite double appel si l'executor a déjà géré l'erreur)
                self._current_scan.fail(str(e))
                self._publish_events(self._current_scan.domain_events)
            self._status = ScanStatus.FAILED
            return False

    def pause_scan(self) -> None:
        self._paused = True
        
    def resume_scan(self) -> None:
        self._paused = False
        
    def cancel_scan(self) -> None:
        self._cancelled = True

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
    # SUBSCRIPTIONS (Events)
    # ==================================================================================

    def subscribe_to_scan_updates(self, callback: Callable[[DomainEvent], None]) -> None:
        """Subscribe to scan point acquired events."""
        self._event_bus.subscribe("scanpointacquired", callback)
        self._event_bus.subscribe("scanstarted", callback)

    def subscribe_to_scan_completion(self, callback: Callable[[DomainEvent], None]) -> None:
        """Subscribe to scan completion events."""
        self._event_bus.subscribe("scancompleted", callback)

    def _on_domain_event(self, event: DomainEvent):
        """
        Forward events from the EventBus to the OutputPort.
        This provides the Strict Contract on top of the Loose Events.
        """
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
                "y_nb_points": event.config.y_nb_points
            })

        elif isinstance(event, ScanPointAcquired):
            # Flatten data for UI
            data = {
                "x": event.position.x,
                "y": event.position.y,
                "value": {
                    "x_in_phase": event.measurement.voltage_x_in_phase,
                    "x_quadrature": event.measurement.voltage_x_quadrature,
                    "y_in_phase": event.measurement.voltage_y_in_phase,
                    "y_quadrature": event.measurement.voltage_y_quadrature,
                    "z_in_phase": event.measurement.voltage_z_in_phase,
                    "z_quadrature": event.measurement.voltage_z_quadrature
                },
                "index": event.point_index
            }
            # We assume total_points is available via current scan or we pass 0 if unknown
            total = self._current_scan.expected_points if self._current_scan else 0
            self._output_port.present_scan_progress(event.point_index, total, data)

        elif isinstance(event, ScanCompleted):
            self._output_port.present_scan_completed(str(event.scan_id), event.total_points)

        elif isinstance(event, ScanFailed):
            self._output_port.present_scan_failed(str(event.scan_id), event.reason)
    
    # ... rest of methods ...

    def _publish_events(self, events: List[DomainEvent]) -> None:
        """Publish domain events to EventBus."""
        for event in events:
            event_type = type(event).__name__.lower()  # e.g., 'scanstarted'
            self._event_bus.publish(event_type, event)


    def _to_domain_config(self, dto: Scan2DConfigDTO) -> StepScanConfig:
        return StepScanConfig(
            scan_zone=ScanZone(x_min=dto.x_min, x_max=dto.x_max, y_min=dto.y_min, y_max=dto.y_max),
            x_nb_points=dto.x_nb_points,
            y_nb_points=dto.y_nb_points,
            scan_pattern=ScanPattern[dto.scan_pattern],
            stabilization_delay_ms=dto.stabilization_delay_ms,
            averaging_per_position=dto.averaging_per_position,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=dto.uncertainty_volts)
        )

    def _extract_metadata(self, dto: Scan2DConfigDTO) -> dict:
        return {"mode": dto.scan_pattern}
