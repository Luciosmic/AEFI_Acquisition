"""
Step Scan Aggregate

Responsibility:
- Aggregate Root for Step-by-Step Scans.
- Manages the collection of ScanPointResults.
- Ensures consistency of the scan data.
"""

from dataclasses import dataclass, field
from typing import List
from ..entities.spatial_scan import SpatialScan
from ..value_objects.scan.scan_point_result import ScanPointResult
from ..value_objects.scan.scan_status import ScanStatus

@dataclass
class StepScan(SpatialScan):
    """
    Aggregate Root for Step Scans.
    
    Inherits identity and lifecycle from SpatialScan.
    Specializes in holding strongly-typed ScanPointResults.
    """
    
    # Typed results list (shadows the generic results from parent if needed, 
    # or we just use a specific field)
    _points: List[ScanPointResult] = field(default_factory=list)
    
    def __post_init__(self):
        # Ensure correct type
        self.is_fly_scan = False
        self.scan_type = "step_scan"
        
    @property
    def points(self) -> List[ScanPointResult]:
        """Get read-only list of points."""
        return list(self._points)
        
    def add_point_result(self, result: ScanPointResult) -> None:
        """
        Add a point result to the scan.
        
        Invariant: Can only add results when RUNNING.
        """
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot add result when scan is {self.status}")
            
        self._points.append(result)
        # We could also update the generic results list for compatibility if needed
        # self.results.append(asdict(result))
