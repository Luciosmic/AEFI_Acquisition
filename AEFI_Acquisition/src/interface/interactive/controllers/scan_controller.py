"""
Scan Interactive Controller

Handles scan-related user interactions.
Integrates with EventBus and CommandBus.
"""

from typing import Dict, Any, Optional
from domain.shared.events.i_domain_event_bus import IDomainEventBus
from interface.interactive.i_interactive_port import IInteractivePort, ICommandHandler, IEventPublisher
from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort
from application.dtos.scan_dtos import Scan2DConfigDTO
from domain.models.scan.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled, ScanPaused, ScanResumed


class ScanController(IInteractivePort, ICommandHandler, IEventPublisher):
    """
    Controller for scan operations.
    
    Responsibilities:
    - Handle scan commands (start, stop, pause, resume)
    - Subscribe to scan domain events
    - Present scan updates via output port
    """
    
    def __init__(
        self,
        scan_service: ScanApplicationService,
        output_port: Optional[IScanOutputPort] = None
    ):
        self._scan_service = scan_service
        self._output_port = output_port
        self._event_bus: Optional[IDomainEventBus] = None
        
        # Set output port if provided
        if output_port:
            self._scan_service.set_output_port(output_port)
    
    def initialize(self, event_bus: IDomainEventBus) -> None:
        """Subscribe to scan domain events."""
        self._event_bus = event_bus
        
        # Subscribe to scan events
        event_bus.subscribe("scanstarted", self._on_scan_started)
        event_bus.subscribe("scanpointacquired", self._on_scan_point_acquired)
        event_bus.subscribe("scancompleted", self._on_scan_completed)
        event_bus.subscribe("scanfailed", self._on_scan_failed)
        event_bus.subscribe("scancancelled", self._on_scan_cancelled)
        event_bus.subscribe("scanpaused", self._on_scan_paused)
        event_bus.subscribe("scanresumed", self._on_scan_resumed)
    
    def shutdown(self) -> None:
        """Unsubscribe from events."""
        if self._event_bus:
            self._event_bus.unsubscribe("scanstarted", self._on_scan_started)
            self._event_bus.unsubscribe("scanpointacquired", self._on_scan_point_acquired)
            self._event_bus.unsubscribe("scancompleted", self._on_scan_completed)
            self._event_bus.unsubscribe("scanfailed", self._on_scan_failed)
            self._event_bus.unsubscribe("scancancelled", self._on_scan_cancelled)
            self._event_bus.unsubscribe("scanpaused", self._on_scan_paused)
            self._event_bus.unsubscribe("scanresumed", self._on_scan_resumed)
    
    def get_controller_name(self) -> str:
        return "scan"
    
    # ==================================================================================
    # ICommandHandler Implementation
    # ==================================================================================
    
    def handle_command(self, command_type: str, command_data: Dict[str, Any]) -> None:
        """Handle scan commands."""
        if command_type == "scan_start":
            self._handle_scan_start(command_data)
        elif command_type == "scan_stop":
            self._handle_scan_stop()
        elif command_type == "scan_pause":
            self._handle_scan_pause()
        elif command_type == "scan_resume":
            self._handle_scan_resume()
        elif command_type == "flyscan_start":
            self._handle_flyscan_start(command_data)
        else:
            raise ValueError(f"Unknown scan command: {command_type}")
    
    def _handle_scan_start(self, command_data: Dict[str, Any]) -> None:
        """Handle scan start command."""
        dto = Scan2DConfigDTO(
            x_min=float(command_data["x_min"]),
            x_max=float(command_data["x_max"]),
            y_min=float(command_data["y_min"]),
            y_max=float(command_data["y_max"]),
            x_nb_points=int(command_data["x_nb_points"]),
            y_nb_points=int(command_data["y_nb_points"]),
            scan_pattern=command_data.get("scan_pattern", "SERPENTINE"),
            stabilization_delay_ms=int(command_data.get("stabilization_delay_ms", 300)),
            averaging_per_position=int(command_data.get("averaging_per_position", 10)),
            uncertainty_volts=float(command_data.get("uncertainty_volts", 0.001)),
            motion_speed_mm_s=command_data.get("motion_speed_mm_s")
        )
        self._scan_service.execute_scan(dto)
    
    def _handle_scan_stop(self) -> None:
        """Handle scan stop command."""
        self._scan_service.cancel_scan()
    
    def _handle_scan_pause(self) -> None:
        """Handle scan pause command."""
        self._scan_service.pause_scan()
    
    def _handle_scan_resume(self) -> None:
        """Handle scan resume command."""
        self._scan_service.resume_scan()
    
    def _handle_flyscan_start(self, command_data: Dict[str, Any]) -> None:
        """Handle FlyScan start command."""
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"scan_controller.py:115","message":"_handle_flyscan_start called","data":{"has_command_data":bool(command_data),"has_scan_zone":bool(command_data.get("scan_zone"))},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass  # Ignore log errors in tests
        # #endregion
        # Convert command_data to FlyScanConfig
        from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
        from domain.models.scan.value_objects.scan_zone import ScanZone
        from domain.models.scan.value_objects.scan_pattern import ScanPattern
        from domain.models.test_bench.value_objects.motion_profile import MotionProfile
        
        motion_profile = MotionProfile(
            min_speed=float(command_data["motion_profile"]["min_speed"]),
            target_speed=float(command_data["motion_profile"]["target_speed"]),
            acceleration=float(command_data["motion_profile"]["acceleration"]),
            deceleration=float(command_data["motion_profile"]["deceleration"])
        )
        
        config = FlyScanConfig(
            scan_zone=ScanZone(
                x_min=float(command_data["scan_zone"]["x_min"]),
                x_max=float(command_data["scan_zone"]["x_max"]),
                y_min=float(command_data["scan_zone"]["y_min"]),
                y_max=float(command_data["scan_zone"]["y_max"])
            ),
            x_nb_points=int(command_data["x_nb_points"]),
            y_nb_points=int(command_data["y_nb_points"]),
            scan_pattern=ScanPattern[command_data.get("scan_pattern", "SERPENTINE")],
            motion_profile=motion_profile,
            desired_acquisition_rate_hz=float(command_data.get("desired_acquisition_rate_hz", 100.0)),
            max_spatial_gap_mm=float(command_data.get("max_spatial_gap_mm", 0.5))
        )
        
        acquisition_rate_hz = float(command_data.get("acquisition_rate_hz", config.desired_acquisition_rate_hz))
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"scan_controller.py:146","message":"calling execute_fly_scan","data":{"has_service":bool(self._scan_service),"acquisition_rate_hz":acquisition_rate_hz},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass  # Ignore log errors in tests
        # #endregion
        self._scan_service.execute_fly_scan(config, acquisition_rate_hz)
    
    # ==================================================================================
    # IEventPublisher Implementation
    # ==================================================================================
    
    def publish_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish user interaction events to EventBus."""
        if self._event_bus:
            self._event_bus.publish(event_type, event_data)
    
    # ==================================================================================
    # Event Handlers (Domain Events from EventBus)
    # ==================================================================================
    
    def _on_scan_started(self, event: ScanStarted) -> None:
        """Handle scan started domain event."""
        # Forward to output port if available
        if self._output_port:
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
            
            self._output_port.present_scan_started(str(event.scan_id), {
                "pattern": event.config.scan_pattern.name,
                "points": points,
                "x_min": event.config.scan_zone.x_min,
                "x_max": event.config.scan_zone.x_max,
                "x_nb_points": event.config.x_nb_points,
                "y_min": event.config.scan_zone.y_min,
                "y_max": event.config.scan_zone.y_max,
                "y_nb_points": event.config.y_nb_points
            })
    
    def _on_scan_point_acquired(self, event: ScanPointAcquired) -> None:
        """Handle scan point acquired domain event."""
        if self._output_port:
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
            # Get total points from service (via public method if available, or from event)
            # For now, we'll use a reasonable default or get from service status
            total = getattr(self._scan_service, '_current_scan', None)
            total = total.expected_points if total else 0
            self._output_port.present_scan_progress(event.point_index, total, data)
    
    def _on_scan_completed(self, event: ScanCompleted) -> None:
        """Handle scan completed domain event."""
        if self._output_port:
            self._output_port.present_scan_completed(str(event.scan_id), event.total_points)
    
    def _on_scan_failed(self, event: ScanFailed) -> None:
        """Handle scan failed domain event."""
        if self._output_port:
            self._output_port.present_scan_failed(str(event.scan_id), event.reason)
    
    def _on_scan_cancelled(self, event: ScanCancelled) -> None:
        """Handle scan cancelled domain event."""
        if self._output_port:
            self._output_port.present_scan_cancelled(str(event.scan_id))
    
    def _on_scan_paused(self, event: ScanPaused) -> None:
        """Handle scan paused domain event."""
        if self._output_port:
            self._output_port.present_scan_paused(str(event.scan_id), event.current_point_index)
    
    def _on_scan_resumed(self, event: ScanResumed) -> None:
        """Handle scan resumed domain event."""
        if self._output_port:
            self._output_port.present_scan_resumed(str(event.scan_id), event.resume_from_point_index)

