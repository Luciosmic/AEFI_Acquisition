from typing import Any, Dict

class IScanOutputPort:
    """
    Output Port for Scan Application Service.
    
    Responsibility:
    - Defines the contract for presenting scan updates to the user/system.
    - Implemented by Presenters (for UI) or CLI adapters.
    """
    
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        """Called when a scan successfully starts."""
        pass

    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        """
        Called when a new point is acquired.
        point_data: ScanPointResult or similar DTO.
        """
        pass

    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        """Called when the scan finishes successfully."""
        pass

    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        """Called when the scan fails."""
        pass

    def present_scan_cancelled(self, scan_id: str) -> None:
        """Called when the scan is cancelled/stopped."""
        pass

    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        """Called when the scan is paused."""
        pass

    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        """Called when the scan is resumed after pause."""
        pass
