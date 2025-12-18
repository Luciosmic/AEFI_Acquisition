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
    
    def present_motion_progress(
        self,
        motion_index: int,
        total_motions: int,
        motion_dto: Any  # AtomicMotionDTO
    ) -> None:
        """
        Called when a motion progresses (started, executing, completed).
        
        Args:
            motion_index: Index of the motion (0-based)
            total_motions: Total number of motions in trajectory
            motion_dto: AtomicMotionDTO with current state
        """
        pass
    
    def present_motion_profile_applied(
        self,
        motion_id: str,
        profile_dto: Any  # MotionProfileDTO
    ) -> None:
        """
        Called when a motion profile is applied to hardware.
        
        Args:
            motion_id: ID of the motion
            profile_dto: MotionProfileDTO that was applied
        """
        pass
    
    # ==================================================================================
    # FlyScan-specific methods
    # ==================================================================================
    
    def present_flyscan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        """
        Called when a FlyScan successfully starts.
        
        Args:
            scan_id: Scan ID
            config: FlyScan configuration dictionary
        """
        pass
    
    def present_flyscan_progress(
        self,
        current_point_index: int,
        total_points: int,
        point_data: Any
    ) -> None:
        """
        Called when a new point is acquired during FlyScan.
        
        Args:
            current_point_index: Current point index
            total_points: Estimated total points
            point_data: ScanPointResult or similar DTO
        """
        pass
    
    def present_flyscan_completed(self, scan_id: str, total_points: int) -> None:
        """Called when FlyScan finishes successfully."""
        pass
    
    def present_flyscan_failed(self, scan_id: str, reason: str) -> None:
        """Called when FlyScan fails."""
        pass
    
    def present_flyscan_cancelled(self, scan_id: str) -> None:
        """Called when FlyScan is cancelled/stopped."""
        pass