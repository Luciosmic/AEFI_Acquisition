"""
Scan Queries - CQRS Query Side

Queries read scan state without modifying it.
Queries return data (DTOs, view models).

Responsibility:
- Provide read-only access to scan state
- Return optimized views for UI/reporting
- No side effects

Rationale:
- Separation of concerns (query vs mutation)
- Can be optimized independently (caching, read replicas)
- Clear intent (query = read data)

Design:
- Each query is a separate method
- Queries return DTOs (not entities)
- Queries never modify state
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..value_objects.scan.scan_status import ScanStatus
from ..value_objects.scan.scan_progress import ScanProgress
from ..entities.spatial_scan import SpatialScan


@dataclass
class ScanStatusDTO:
    """Data Transfer Object for scan status."""
    scan_id: str
    status: ScanStatus
    start_time: datetime
    end_time: Optional[datetime]
    is_paused: bool
    is_cancelled: bool


@dataclass
class ScanProgressDTO:
    """Data Transfer Object for scan progress."""
    scan_id: str
    total_points: int
    completed_points: int
    current_point_index: int
    progress_percentage: float
    estimated_time_remaining_seconds: Optional[float]


@dataclass
class ScanResultsDTO:
    """Data Transfer Object for scan results."""
    scan_id: str
    results: List[Dict[str, Any]]
    total_points: int


class ScanQueries:
    """
    Query side of scan service (CQRS).
    
    Handles all read-only operations on scan state.
    """
    
    def __init__(self, scan_state_provider):
        """
        Args:
            scan_state_provider: Object that provides access to scan state
                                 (could be the command side, or a read model)
        """
        self._state_provider = scan_state_provider
    
    def get_scan_status(self) -> Optional[ScanStatusDTO]:
        """
        Query: Get current scan status.
        
        Returns:
            ScanStatusDTO if scan exists, None otherwise
        """
        scan = self._state_provider._current_scan
        
        if scan is None:
            return None
        
        return ScanStatusDTO(
            scan_id=str(id(scan)),
            status=scan.status,
            start_time=scan.start_time,
            end_time=scan.end_time,
            is_paused=self._state_provider._paused,
            is_cancelled=self._state_provider._cancelled
        )
    
    def get_scan_progress(self) -> Optional[ScanProgressDTO]:
        """
        Query: Get current scan progress.
        
        Returns:
            ScanProgressDTO if scan exists, None otherwise
        """
        scan = self._state_provider._current_scan
        
        if scan is None:
            return None
        
        total_points = len(scan.results) + 1  # Simplified
        completed_points = len(scan.results)
        
        progress_pct = (completed_points / total_points * 100) if total_points > 0 else 0
        
        # Estimate time remaining (simplified)
        if completed_points > 0 and scan.start_time:
            elapsed = (datetime.now() - scan.start_time).total_seconds()
            time_per_point = elapsed / completed_points
            remaining_points = total_points - completed_points
            estimated_remaining = time_per_point * remaining_points
        else:
            estimated_remaining = None
        
        return ScanProgressDTO(
            scan_id=str(id(scan)),
            total_points=total_points,
            completed_points=completed_points,
            current_point_index=completed_points,
            progress_percentage=progress_pct,
            estimated_time_remaining_seconds=estimated_remaining
        )
    
    def get_scan_results(self) -> Optional[ScanResultsDTO]:
        """
        Query: Get scan results.
        
        Returns:
            ScanResultsDTO if scan exists, None otherwise
        """
        scan = self._state_provider._current_scan
        
        if scan is None:
            return None
        
        return ScanResultsDTO(
            scan_id=str(id(scan)),
            results=scan.results,
            total_points=len(scan.results)
        )
    
    def get_all_scans(self) -> List[ScanStatusDTO]:
        """
        Query: Get all scans (historical).
        
        This would query a repository in a real implementation.
        
        Returns:
            List of ScanStatusDTO
        """
        # TODO: Implement with repository
        return []
