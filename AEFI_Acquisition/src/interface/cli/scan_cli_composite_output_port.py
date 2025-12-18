"""
Composite Output Port that forwards to both CLI and UI presenters.
Implements the pattern: Controller CLI → Presenter CLI → Presenter UI → View UI
"""

from typing import Dict, Any, Optional
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort


class ScanCLICompositeOutputPort(IScanOutputPort):
    """
    Composite output port that forwards events to both CLI and UI presenters.
    
    Pattern: Controller CLI → Presenter CLI → (this) → Presenter UI → View UI
    """
    
    def __init__(
        self,
        cli_output_port: IScanOutputPort,
        ui_output_port: Optional[IScanOutputPort] = None
    ):
        self._cli_output_port = cli_output_port
        self._ui_output_port = ui_output_port
    
    def set_ui_output_port(self, ui_output_port: IScanOutputPort) -> None:
        """Set the UI output port (can be set later)."""
        self._ui_output_port = ui_output_port
    
    # Scan methods
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        self._cli_output_port.present_scan_started(scan_id, config)
        if self._ui_output_port:
            self._ui_output_port.present_scan_started(scan_id, config)
    
    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self._cli_output_port.present_scan_progress(current_point_index, total_points, point_data)
        if self._ui_output_port:
            self._ui_output_port.present_scan_progress(current_point_index, total_points, point_data)
    
    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        self._cli_output_port.present_scan_completed(scan_id, total_points)
        if self._ui_output_port:
            self._ui_output_port.present_scan_completed(scan_id, total_points)
    
    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        self._cli_output_port.present_scan_failed(scan_id, reason)
        if self._ui_output_port:
            self._ui_output_port.present_scan_failed(scan_id, reason)
    
    def present_scan_cancelled(self, scan_id: str) -> None:
        self._cli_output_port.present_scan_cancelled(scan_id)
        if self._ui_output_port:
            self._ui_output_port.present_scan_cancelled(scan_id)
    
    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        self._cli_output_port.present_scan_paused(scan_id, current_point_index)
        if self._ui_output_port:
            self._ui_output_port.present_scan_paused(scan_id, current_point_index)
    
    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        self._cli_output_port.present_scan_resumed(scan_id, resume_from_point_index)
        if self._ui_output_port:
            self._ui_output_port.present_scan_resumed(scan_id, resume_from_point_index)
    
    # FlyScan methods
    def present_flyscan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"scan_cli_composite_output_port.py:66","message":"present_flyscan_started called","data":{"scan_id":scan_id,"has_cli_port":bool(self._cli_output_port),"has_ui_port":bool(self._ui_output_port)},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass  # Ignore log errors in tests
        # #endregion
        self._cli_output_port.present_flyscan_started(scan_id, config)
        if self._ui_output_port:
            self._ui_output_port.present_flyscan_started(scan_id, config)
    
    def present_flyscan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        # #region agent log
        try:
            with open('/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/AEFI_Acquisition/AEFI_Acquisition/.cursor/debug.log', 'a') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"scan_cli_composite_output_port.py:71","message":"present_flyscan_progress called","data":{"current":current_point_index,"total":total_points,"has_ui_port":bool(self._ui_output_port)},"timestamp":__import__('time').time()*1000}) + '\n')
        except (PermissionError, OSError):
            pass  # Ignore log errors in tests
        # #endregion
        self._cli_output_port.present_flyscan_progress(current_point_index, total_points, point_data)
        if self._ui_output_port:
            self._ui_output_port.present_flyscan_progress(current_point_index, total_points, point_data)
    
    def present_flyscan_completed(self, scan_id: str, total_points: int) -> None:
        self._cli_output_port.present_flyscan_completed(scan_id, total_points)
        if self._ui_output_port:
            self._ui_output_port.present_flyscan_completed(scan_id, total_points)
    
    def present_flyscan_failed(self, scan_id: str, reason: str) -> None:
        self._cli_output_port.present_flyscan_failed(scan_id, reason)
        if self._ui_output_port:
            self._ui_output_port.present_flyscan_failed(scan_id, reason)
    
    def present_flyscan_cancelled(self, scan_id: str) -> None:
        self._cli_output_port.present_flyscan_cancelled(scan_id)
        if self._ui_output_port:
            self._ui_output_port.present_flyscan_cancelled(scan_id)

