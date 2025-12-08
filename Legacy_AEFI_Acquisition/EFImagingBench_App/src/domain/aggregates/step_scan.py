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
from ..events.domain_event import DomainEvent
from ..events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled

@dataclass
class StepScan(SpatialScan):
    """
    Aggregate Root for Step Scans.
    """
    
    _points: List[ScanPointResult] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        self.is_fly_scan = False
        self.scan_type = "step_scan"
        
    @property
    def points(self) -> List[ScanPointResult]:
        return list(self._points)
        
    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
        
    @property
    def expected_points(self) -> int:
        return self._expected_points

    _expected_points: int = 0
    
    def start(self, config) -> None: # Added config for event
        super().start()
        # Calculate expected points based on config
        # Assuming config has total_points() method or we calculate it
        if hasattr(config, 'total_points'):
             self._expected_points = config.total_points()
        else:
             # Fallback calculation if method doesn't exist directly on config object passed
             self._expected_points = config.x_nb_points * config.y_nb_points
             
        self._domain_events.append(ScanStarted(scan_id=self.id, config=config))
        
    def add_point_result(self, result: ScanPointResult) -> None:
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot add result when scan is {self.status}")
            
        self._points.append(result)
        self._domain_events.append(ScanPointAcquired(
            scan_id=self.id,
            point_index=result.point_index,
            position=result.position,
            measurement=result.measurement
        ))
        
        # Auto-complete if we reached expected points
        if self._expected_points > 0 and len(self._points) >= self._expected_points:
            self.complete()
            
    def complete(self) -> None:
        if self.status == ScanStatus.COMPLETED:
            return # Already completed
            
        super().complete()
        self._domain_events.append(ScanCompleted(scan_id=self.id, total_points=len(self._points)))
        
    def fail(self, reason: str) -> None:
        super().fail(reason)
        self._domain_events.append(ScanFailed(scan_id=self.id, reason=reason))
        
    def cancel(self) -> None:
        super().cancel()
        self._domain_events.append(ScanCancelled(scan_id=self.id))
