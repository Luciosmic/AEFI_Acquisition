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

from typing import Optional, Callable, List, Dict, Any
import logging
import time
from datetime import datetime

from application.dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO, ScanStatusDTO
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.models.scan.value_objects.scan_progress import ScanProgress
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from application.services.motion_control_service.i_motion_port import IMotionPort
from .ports.i_acquisition_port import IAcquisitionPort
from .ports.i_scan_export_port import IScanExportPort
from .ports.i_scan_executor import IScanExecutor
from .ports.i_fly_scan_executor import IFlyScanExecutor

from domain.models.scan.aggregates.step_scan import StepScan
from domain.models.scan.aggregates.fly_scan import FlyScan
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from .ports.i_scan_output_port import IScanOutputPort
from domain.models.scan.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled, ScanPaused, ScanResumed
from domain.shared.events.domain_event import DomainEvent
from domain.shared.events.i_domain_event_bus import IDomainEventBus

# Ports

logger = logging.getLogger(__name__)

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
        fly_scan_executor: Optional[IFlyScanExecutor] = None,  # Optional FlyScan support
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._event_bus = event_bus
        self._scan_executor = scan_executor
        self._fly_scan_executor = fly_scan_executor
        self._output_port = output_port

        self._current_scan: Optional[StepScan] = None
        self._current_fly_scan: Optional[FlyScan] = None
        self._status = ScanStatus.PENDING
        self._paused = False
        self._cancelled = False
        
        # Subscribe myself to the bus to forward events to the output port
        # This ensures that even events from the Executor (which talks to the bus) get forwarded
        self._event_bus.subscribe("scanstarted", self._on_domain_event)
        self._event_bus.subscribe("scanpointacquired", self._on_domain_event)
        self._event_bus.subscribe("scancompleted", self._on_domain_event)
        self._event_bus.subscribe("scanfailed", self._on_domain_event)
        self._event_bus.subscribe("scancancelled", self._on_domain_event)
        self._event_bus.subscribe("scanpaused", self._on_domain_event)
        self._event_bus.subscribe("scanresumed", self._on_domain_event)


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
            # 0. Configure Motion Speed (if provided)
            # if scan_dto.motion_speed_mm_s is not None:
            #     print(f"[ScanApplicationService] Setting motion speed to {scan_dto.motion_speed_mm_s} mm/s")
            #     self._motion_port.set_speed(scan_dto.motion_speed_mm_s)

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
            
            # 3.5. Generate AtomicMotions (Domain - Pure Calculation)
            from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
            positions = list(trajectory.points)
            profile_selector = MotionProfileSelector()  # Use default profiles
            motions = ScanTrajectoryFactory.create_motions(positions, profile_selector)
            scan.add_motions(motions)
            print(f"[ScanApplicationService] Generated {len(motions)} AtomicMotions.")
            
            # 4. Delegate execution to ScanExecutor (Infrastructure)
            # The executor is responsible for running this asynchronously (if needed)
            print(f"[ScanApplicationService] Delegating execution to ScanExecutor...")
            success = self._scan_executor.execute(scan, trajectory, config)
            
            if not success:
                # If it failed to start
                self._status = ScanStatus.FAILED
                return False
            
            # Scan started successfully (RUNNING)
            # Completion will be handled via events
            return True
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            print(f"[ScanApplicationService] Scan failed: {e}")
            if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
                self._current_scan.fail(str(e))
                self._publish_events(self._current_scan.domain_events)
            self._status = ScanStatus.FAILED
            return False

    def pause_scan(self) -> None:
        """Request pause of the current scan."""
        if self._current_scan:
            self._paused = True
            self._scan_executor.pause(self._current_scan)
        
    def resume_scan(self) -> None:
        """Request resume of the current scan."""
        if self._current_scan:
            self._paused = False
            self._scan_executor.resume(self._current_scan)
        
    def cancel_scan(self) -> None:
        """Request cancellation of the current scan."""
        self._cancelled = True
        if self._current_scan:
            self._scan_executor.cancel(self._current_scan)

    # ==================================================================================
    # QUERIES (Read-Only)
    # ==================================================================================

    def get_status(self) -> ScanStatusDTO:
        current_idx = 0
        total_pts = 0
        
        # Use scan's status if available, otherwise use service's internal status
        status = self._status
        if self._current_scan:
            current_idx = len(self._current_scan.points)
            total_pts = self._current_scan.expected_points
            # Sync with scan's actual status
            status = self._current_scan.status

        return ScanStatusDTO(
            status=status.value,
            is_running=status == ScanStatus.RUNNING,
            is_paused=status == ScanStatus.PAUSED,
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
        Also update internal service state.
        """
        # Update internal state based on events
        if isinstance(event, ScanCompleted):
            self._status = ScanStatus.COMPLETED
            self._paused = False
        elif isinstance(event, ScanFailed):
            self._status = ScanStatus.FAILED
            self._paused = False
        elif isinstance(event, ScanCancelled):
            self._status = ScanStatus.CANCELLED
            self._paused = False
        elif isinstance(event, ScanPaused):
            self._status = ScanStatus.PAUSED
            self._paused = True
        elif isinstance(event, ScanResumed):
            self._status = ScanStatus.RUNNING
            self._paused = False
            
        if not self._output_port:
            return

        if isinstance(event, ScanStarted):
            # Handle both StepScanConfig and FlyScanConfig
            from domain.models.scan.value_objects.step_scan_config import StepScanConfig
            from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
            
            if isinstance(event.config, FlyScanConfig):
                # FlyScanConfig uses total_grid_points() instead of total_points()
                points = event.config.total_grid_points()
            elif isinstance(event.config, StepScanConfig):
                # StepScanConfig has total_points()
                points = event.config.total_points()
            else:
                # Fallback
                points = getattr(event.config, 'total_points', lambda: 0)()
            
            # Build CLI-standardized structure (all presenters receive same structure)
            cli_event = self._build_cli_event_structure(
                "scan_started",
                str(event.scan_id),
                config={
                    "pattern": event.config.scan_pattern.name,
                    "points": points,
                    "x_min": event.config.scan_zone.x_min,
                    "x_max": event.config.scan_zone.x_max,
                    "x_nb_points": event.config.x_nb_points,
                    "y_min": event.config.scan_zone.y_min,
                    "y_max": event.config.scan_zone.y_max,
                    "y_nb_points": event.config.y_nb_points
                }
            )
            # Extract scan_id and config for backward compatibility with IScanOutputPort signature
            self._output_port.present_scan_started(cli_event["scan_id"], cli_event["config"])

        elif isinstance(event, ScanPointAcquired):
            # Build CLI-standardized structure
            point_data = {
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
            total = self._current_scan.expected_points if self._current_scan else 0
            # Pass CLI structure (backward compatible with IScanOutputPort signature)
            self._output_port.present_scan_progress(event.point_index, total, point_data)

        elif isinstance(event, ScanCompleted):
            self._output_port.present_scan_completed(str(event.scan_id), event.total_points)

        elif isinstance(event, ScanFailed):
            self._output_port.present_scan_failed(str(event.scan_id), event.reason)

        elif isinstance(event, ScanCancelled):
            self._output_port.present_scan_cancelled(str(event.scan_id))

        elif isinstance(event, ScanPaused):
            self._output_port.present_scan_paused(str(event.scan_id), event.current_point_index)

        elif isinstance(event, ScanResumed):
            self._output_port.present_scan_resumed(str(event.scan_id), event.resume_from_point_index)
    
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

    # ==================================================================================
    # CLI Structure Helpers (Pattern: All presenters use CLI structure)
    # ==================================================================================
    
    def _build_cli_event_structure(self, event_name: str, scan_id: str, **kwargs) -> Dict[str, Any]:
        """
        Build CLI-standardized event structure.
        All presenters receive the same structure (CLI JSON format).
        
        Args:
            event_name: Event type (e.g., "scan_started", "scan_progress")
            scan_id: Scan ID
            **kwargs: Additional event-specific data
        
        Returns:
            Dict with structure: {"event": ..., "scan_id": ..., "timestamp": ..., ...kwargs}
        """
        return {
            "event": event_name,
            "scan_id": scan_id,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

    # ==================================================================================
    # FLYSCAN EXECUTION
    # ==================================================================================

    def execute_fly_scan(
        self,
        config: FlyScanConfig,
        acquisition_rate_hz: float
    ) -> bool:
        """
        Execute a fly scan with continuous motion and acquisition.

        Args:
            config: FlyScan configuration (already validated)
            acquisition_rate_hz: Measured acquisition rate capability

        Returns:
            True if execution started successfully
        """
        if self._fly_scan_executor is None:
            print("[ScanApplicationService] FlyScan not supported (no executor)")
            return False

        try:
            print(f"[ScanApplicationService] Starting FlyScan execution...")

            # Create FlyScan aggregate
            fly_scan = FlyScan()
            fly_scan.start(config, acquisition_rate_hz)
            self._current_fly_scan = fly_scan

            # Generate trajectory
            trajectory = ScanTrajectoryFactory.create_trajectory(config)

            # Create motions from trajectory
            from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
            profile_selector = MotionProfileSelector()
            motions = ScanTrajectoryFactory.create_motions(
                list(trajectory.points),
                profile_selector
            )

            # Add motions to aggregate
            fly_scan.add_motions(motions)

            # Estimate and set expected points
            from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
            capability = AcquisitionRateCapability(
                measured_rate_hz=acquisition_rate_hz,
                measured_std_dev_hz=0.0,
                measurement_timestamp=datetime.now(),
                measurement_duration_s=1.0,
                sample_count=100
            )
            estimated_points = config.estimate_total_points(capability)
            fly_scan.set_expected_points(estimated_points)

            # Publish domain events
            events = fly_scan.domain_events
            self._publish_events(events)
            
            # Notify output port (CLI-standardized structure)
            if self._output_port:
                flyscan_config = {
                    "pattern": config.scan_pattern.name,
                    "estimated_points": estimated_points,
                    "x_min": config.scan_zone.x_min,
                    "x_max": config.scan_zone.x_max,
                    "x_nb_points": config.x_nb_points,
                    "y_min": config.scan_zone.y_min,
                    "y_max": config.scan_zone.y_max,
                    "y_nb_points": config.y_nb_points,
                    "motion_profile": {
                        "min_speed": config.motion_profile.min_speed,
                        "target_speed": config.motion_profile.target_speed,
                        "acceleration": config.motion_profile.acceleration,
                        "deceleration": config.motion_profile.deceleration
                    },
                    "desired_acquisition_rate_hz": config.desired_acquisition_rate_hz,
                    "max_spatial_gap_mm": config.max_spatial_gap_mm
                }
            # Pass CLI structure (backward compatible)
            # #region agent log
            try:
                with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                    import json
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"scan_application_service.py:431","message":"calling present_flyscan_started","data":{"has_output_port":bool(self._output_port),"fly_scan_id":str(fly_scan.id)},"timestamp":__import__('time').time()*1000}) + '\n')
            except (PermissionError, OSError):
                pass  # Ignore log errors in tests
            # #endregion
            if self._output_port:
                self._output_port.present_flyscan_started(str(fly_scan.id), flyscan_config)

            # Subscribe to FlyScan events
            self._event_bus.subscribe("scanpointacquired", self._on_flyscan_event)
            self._event_bus.subscribe("scancompleted", self._on_flyscan_event)
            self._event_bus.subscribe("scanfailed", self._on_flyscan_event)
            self._event_bus.subscribe("scancancelled", self._on_flyscan_event)

            # Execute via executor
            success = self._fly_scan_executor.execute(
                fly_scan,
                motions,
                config,
                self._motion_port,
                self._acquisition_port
            )

            if success:
                self._status = ScanStatus.RUNNING
                print(f"[ScanApplicationService] FlyScan started (estimated {estimated_points} points)")

            return success

        except Exception as e:
            print(f"[ScanApplicationService] FlyScan execution failed: {e}")
            if self._current_fly_scan:
                self._current_fly_scan.fail(str(e))
                events = self._current_fly_scan.domain_events
                self._publish_events(events)
            return False
    
    def _on_flyscan_event(self, event: DomainEvent):
        """
        Handle FlyScan domain events and forward to output port.
        """
        if not self._output_port or not self._current_fly_scan:
            return
        
        if isinstance(event, ScanPointAcquired):
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
            total = self._current_fly_scan.expected_points if self._current_fly_scan else 0
            self._output_port.present_flyscan_progress(event.point_index, total, data)
        
        elif isinstance(event, ScanCompleted):
            self._status = ScanStatus.COMPLETED
            self._output_port.present_flyscan_completed(str(event.scan_id), event.total_points)
            # Unsubscribe from events
            self._event_bus.unsubscribe("scanpointacquired", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancompleted", self._on_flyscan_event)
            self._event_bus.unsubscribe("scanfailed", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancancelled", self._on_flyscan_event)
        
        elif isinstance(event, ScanFailed):
            self._status = ScanStatus.FAILED
            self._output_port.present_flyscan_failed(str(event.scan_id), event.reason)
            # Unsubscribe from events
            self._event_bus.unsubscribe("scanpointacquired", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancompleted", self._on_flyscan_event)
            self._event_bus.unsubscribe("scanfailed", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancancelled", self._on_flyscan_event)
        
        elif isinstance(event, ScanCancelled):
            self._status = ScanStatus.CANCELLED
            self._output_port.present_flyscan_cancelled(str(event.scan_id))
            # Unsubscribe from events
            self._event_bus.unsubscribe("scanpointacquired", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancompleted", self._on_flyscan_event)
            self._event_bus.unsubscribe("scanfailed", self._on_flyscan_event)
            self._event_bus.unsubscribe("scancancelled", self._on_flyscan_event)
