from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Dict, Any, Optional
import threading

from application.services.scan_application_service.scan_application_service import (
    ScanApplicationService,
)
from application.dtos.scan_dtos import Scan2DConfigDTO, ExportConfigDTO
from application.services.scan_application_service.scan_export_service import (
    ScanExportService,
)
from domain.events.domain_event import DomainEvent
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed

from application.services.scan_application_service.i_scan_output_port import IScanOutputPort
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService

class ScanPresenter(QObject, IScanOutputPort):
    """
    Presenter for the Scan UI.
    Acts as a bridge between the View (Qt Widgets) and the Model (ScanApplicationService).
    Handles thread safety for UI updates.
    
    Implements IScanOutputPort to receive explicit updates from the Service.
    """
    
    # Signals for UI updates (emitted on main thread)
    scan_started = pyqtSignal(str, dict)  # scan_id, config_summary
    scan_point_acquired = pyqtSignal(dict) # point_data (x, y, value, etc.)
    scan_completed = pyqtSignal(str, int) # scan_id, total_points
    scan_failed = pyqtSignal(str, str)    # scan_id, reason
    scan_progress = pyqtSignal(float)     # percentage
    
    def __init__(
        self,
        scan_service: ScanApplicationService,
        hardware_config_service: HardwareConfigurationService,
        export_service: Optional[ScanExportService] = None,
    ):
        super().__init__()
        self._service = scan_service
        self._hardware_config_service = hardware_config_service
        self._export_service = export_service
        
        # NOTE: We no longer subscribe to events here. 
        # The Service will call present_* methods directly.
        
    def start_scan(self, params: Dict[str, Any]):
        """
        Start a scan with the given parameters.
        Runs the scan in a separate thread to avoid freezing the UI.
        """
        try:
            # 1. Parse Speed (if provided)
            # Param key from UI widget is 'motion_speed_mm_s' (was incorrectly cm_s)
            speed_mm_s = params.get('motion_speed_mm_s')
            motion_speed = float(speed_mm_s) if speed_mm_s else None
            
            # 2. Configure export (if service is available)
            if self._export_service is not None:
                export_enabled = bool(params.get("export_enabled", True))
                export_output_dir = str(params.get("export_output_directory", ""))
                export_filename_base = str(params.get("export_filename_base", "scan"))
                export_format = str(params.get("export_format", "CSV"))

                export_config = ExportConfigDTO(
                    enabled=export_enabled,
                    output_directory=export_output_dir,
                    filename_base=export_filename_base,
                    format=export_format,
                )
                self._export_service.configure_export(export_config)

            # 3. Create DTO from params
            config = Scan2DConfigDTO(
                x_min=float(params.get('x_min', 0)),
                x_max=float(params.get('x_max', 10)),
                x_nb_points=int(params.get('x_nb_points', 10)),
                y_min=float(params.get('y_min', 0)),
                y_max=float(params.get('y_max', 10)),
                y_nb_points=int(params.get('y_nb_points', 10)),
                scan_pattern=params.get('scan_pattern', 'RASTER'),
                stabilization_delay_ms=int(params.get('stabilization_delay_ms', 10)),
                averaging_per_position=int(params.get('averaging_per_position', 1)),
                uncertainty_volts=float(params.get('uncertainty_volts', 1e-6)),
                motion_speed_mm_s=motion_speed
            )
            
            # Run in background thread
            self._scan_thread = threading.Thread(target=self._execute_scan_thread, args=(config,))
            self._scan_thread.daemon = True
            self._scan_thread.start()
            
        except ValueError as e:
            self.scan_failed.emit("Pre-check", str(e))

    def stop_scan(self):
        """Request scan cancellation."""
        self._service.cancel_scan()

    def pause_scan(self):
        """Request scan pause."""
        self._service.pause_scan()

    def resume_scan(self):
        """Request scan resume."""
        self._service.resume_scan()

    def _execute_scan_thread(self, config: Scan2DConfigDTO):
        """Background thread execution."""
        # We now depend on the service being initialized with THIS PRESENTER as the output port.
        self._service.execute_scan(config)

    # ==================================================================================
    # IScanOutputPort Implementation
    # ==================================================================================

    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        """Called when a scan successfully starts."""
        self.scan_started.emit(scan_id, config)

    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        """Called when a new point is acquired."""
        # Flatten data for UI if necessary, or just pass simple dict
        # Assuming point_data matches the dict structure we want, or is the Result object
        # The service will now pass us the generic dict we prepared before, saving logic here.
        self.scan_point_acquired.emit(point_data)
        
        if total_points > 0:
            self.scan_progress.emit(current_point_index / total_points * 100.0)

    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        """Called when the scan finishes successfully."""
        self.scan_completed.emit(scan_id, total_points)

    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        """Called when the scan fails."""
        self.scan_failed.emit(scan_id, reason)

