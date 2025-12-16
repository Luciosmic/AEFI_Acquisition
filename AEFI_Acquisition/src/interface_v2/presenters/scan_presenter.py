from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any

from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.i_scan_output_port import IScanOutputPort
from application.services.scan_application_service.scan_export_service import ScanExportService
from application.dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO
from domain.events.i_domain_event_bus import IDomainEventBus

class ScanPresenter(QObject, IScanOutputPort):
    """
    Presenter for the Scan feature.
    
    Responsibility:
    - Acts as the Output Port for ScanApplicationService (receives updates).
    - Handles user interactions from ScanControlPanel.
    - Updates ScanControlPanel and ScanVisualizationPanel via signals.
    """
    
    # Signals to update Views
    scan_started = Signal(str, dict) # scan_id, config
    scan_progress = Signal(int, int, dict) # current, total, point_data
    scan_completed = Signal(int) # total_points
    scan_failed = Signal(str) # reason
    scan_cancelled = Signal(str) # scan_id
    scan_paused = Signal(str, int) # scan_id, current_point_index
    scan_resumed = Signal(str, int) # scan_id, resume_from_point_index
    status_updated = Signal(str) # status message
    
    def __init__(self, service: ScanApplicationService, export_service: ScanExportService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self._export_service = export_service
        self._event_bus = event_bus
        
        # Register myself as the output port
        self._service.set_output_port(self)
        
    # ==================================================================================
    # IScanOutputPort Implementation (Service -> Presenter)
    # ==================================================================================
    
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        self.scan_started.emit(scan_id, config)
        self.status_updated.emit(f"Scan started (ID: {scan_id})")
        
    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self.scan_progress.emit(current_point_index, total_points, point_data)
        percentage = (current_point_index / total_points * 100) if total_points > 0 else 0
        self.status_updated.emit(f"Progress: {current_point_index}/{total_points} ({percentage:.1f}%)")
        
    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        self.scan_completed.emit(total_points)
        self.status_updated.emit("Scan completed successfully.")
        
    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        self.scan_failed.emit(reason)
        self.status_updated.emit(f"Scan failed: {reason}")

    def present_scan_cancelled(self, scan_id: str) -> None:
        self.scan_cancelled.emit(scan_id)
        self.status_updated.emit("Scan cancelled.")

    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        self.scan_paused.emit(scan_id, current_point_index)
        self.status_updated.emit(f"Scan paused at point {current_point_index}.")

    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        self.scan_resumed.emit(scan_id, resume_from_point_index)
        self.status_updated.emit(f"Scan resumed from point {resume_from_point_index}.")

    # ==================================================================================
    # User Actions (View -> Presenter)
    # ==================================================================================

    @Slot(dict)
    def on_scan_start_requested(self, params: dict):
        """
        Handle start request from View.
        Converts raw dict params to DTO and calls service.
        """
        try:
            # Parse parameters
            dto = Scan2DConfigDTO(
                x_min=float(params.get("x_min", 600)),
                x_max=float(params.get("x_max", 800)),
                x_nb_points=int(params.get("x_nb_points", 41)),
                y_min=float(params.get("y_min", 600)),
                y_max=float(params.get("y_max", 800)),
                y_nb_points=int(params.get("y_nb_points", 41)),
                scan_pattern=params.get("scan_pattern", "SERPENTINE"),
                motion_speed_mm_s=float(params.get("motion_speed_mm_s", 10.0)),
                stabilization_delay_ms=int(params.get("stabilization_delay_ms", 300)),
                averaging_per_position=int(params.get("averaging_per_position", 10)),
                uncertainty_volts=0.001     # Default
            )
            
            # Configure Export
            export_dto = ExportConfigDTO(
                enabled=params.get("export_enabled", False),
                output_directory=params.get("export_output_directory", ""),
                filename_base=params.get("export_filename_base", "scan"),
                format=params.get("export_format", "CSV")
            )
            self._export_service.configure_export(export_dto)
            
            success = self._service.execute_scan(dto)
            if not success:
                self.status_updated.emit("Failed to start scan (check logs).")
                
        except ValueError as e:
            self.status_updated.emit(f"Invalid parameters: {e}")
        except Exception as e:
            self.status_updated.emit(f"Error starting scan: {e}")

    @Slot()
    def on_scan_stop_requested(self):
        self._service.cancel_scan()
        # Don't set status here - wait for ScanCancelled event

    @Slot()
    def on_scan_pause_requested(self):
        self._service.pause_scan()
        # Don't set status here - wait for ScanPaused event

    @Slot()
    def on_scan_resume_requested(self):
        self._service.resume_scan()
        # Don't set status here - wait for ScanResumed event
