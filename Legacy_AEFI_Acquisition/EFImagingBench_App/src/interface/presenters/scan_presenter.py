from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Dict, Any
import threading

from application.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from domain.events.domain_event import DomainEvent
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed

class ScanPresenter(QObject):
    """
    Presenter for the Scan UI.
    Acts as a bridge between the View (Qt Widgets) and the Model (ScanApplicationService).
    Handles thread safety for UI updates.
    """
    
    # Signals for UI updates (emitted on main thread)
    scan_started = pyqtSignal(str, dict)  # scan_id, config_summary
    scan_point_acquired = pyqtSignal(dict) # point_data (x, y, value, etc.)
    scan_completed = pyqtSignal(str, int) # scan_id, total_points
    scan_failed = pyqtSignal(str, str)    # scan_id, reason
    scan_progress = pyqtSignal(float)     # percentage
    
    def __init__(self, scan_service: ScanApplicationService):
        super().__init__()
        self._service = scan_service
        
        # Subscribe to service events
        self._service.subscribe_to_scan_updates(self._on_domain_event)
        self._service.subscribe_to_scan_completion(self._on_domain_event)
        
    def start_scan(self, params: Dict[str, Any]):
        """
        Start a scan with the given parameters.
        Runs the scan in a separate thread to avoid freezing the UI.
        """
        try:
            # Create DTO from params
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
                uncertainty_volts=float(params.get('uncertainty_volts', 1e-6))
            )
            
            # Run in background thread
            thread = threading.Thread(target=self._execute_scan_thread, args=(config,))
            thread.daemon = True
            thread.start()
            
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
        self._service.execute_scan(config)

    def _on_domain_event(self, event: DomainEvent):
        """
        Handle domain events from the service.
        This method is called from the service thread (background).
        We emit Qt signals to update the UI on the main thread.
        """
        if isinstance(event, ScanStarted):
            self.scan_started.emit(str(event.scan_id), {
                "pattern": event.config.scan_pattern.name,
                "points": event.config.total_points
            })
            
        elif isinstance(event, ScanPointAcquired):
            # Flatten data for UI
            data = {
                "x": event.position.x,
                "y": event.position.y,
                "value": event.measurement.voltage_x_in_phase, # Default visualization channel
                "index": event.point_index
            }
            self.scan_point_acquired.emit(data)
            
        elif isinstance(event, ScanCompleted):
            self.scan_completed.emit(str(event.scan_id), event.total_points)
            
        elif isinstance(event, ScanFailed):
            self.scan_failed.emit(str(event.scan_id), event.reason)
