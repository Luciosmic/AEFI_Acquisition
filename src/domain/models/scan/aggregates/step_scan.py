"""
Step Scan Aggregate

Responsibility:
- Aggregate Root for Step-by-Step Scans.
- Manages the collection of ScanPointResults.
- Ensures consistency of the scan data.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from domain.models.scan.aggregates.spatial_scan import SpatialScan
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.shared.events.domain_event import DomainEvent
from domain.models.scan.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled, ScanPaused, ScanResumed
from domain.models.scan.entities.atomic_motion import AtomicMotion

@dataclass
class StepScan(SpatialScan):
    """
    Aggregate Root for Step Scans.
    """
    
    _points: List[ScanPointResult] = field(default_factory=list)
    _motions: List[AtomicMotion] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        self.is_fly_scan = False
        self.scan_type = "step_scan"
        
    @property
    def points(self) -> List[ScanPointResult]:
        return list(self._points)
    
    @property
    def motions(self) -> List[AtomicMotion]:
        """Get list of atomic motions."""
        return list(self._motions)
        
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
        # Allow failing from RUNNING or PAUSED states
        if self.status not in (ScanStatus.RUNNING, ScanStatus.PAUSED):
            raise ValueError(f"Cannot fail scan in status {self.status}")
        super().fail(reason)
        self._domain_events.append(ScanFailed(scan_id=self.id, reason=reason))
        
    def cancel(self) -> None:
        """Cancel the scan (idempotent)."""
        # Idempotent: if already cancelled, do nothing
        if self.status == ScanStatus.CANCELLED:
            return
        super().cancel()
        self._domain_events.append(ScanCancelled(scan_id=self.id))
        
    def pause(self) -> None:
        """Pause the scan (idempotent)."""
        # Idempotent: if already paused, do nothing
        if self.status == ScanStatus.PAUSED:
            return
        # Cannot pause if already in final state
        if self.status.is_final():
            return  # Silently ignore instead of raising
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot pause scan when status is {self.status}")
        super().pause()
        current_index = len(self._points)
        self._domain_events.append(ScanPaused(scan_id=self.id, current_point_index=current_index))
        
    def resume(self) -> None:
        """Resume the scan execution after pause."""
        if self.status != ScanStatus.PAUSED:
            raise ValueError(f"Cannot resume scan when status is {self.status}")
        super().resume()
        resume_index = len(self._points)
        self._domain_events.append(ScanResumed(scan_id=self.id, resume_from_point_index=resume_index))
    
    def add_motions(self, motions: List[AtomicMotion]) -> None:
        """
        Add atomic motions to the scan.
        
        Args:
            motions: List of AtomicMotion entities
        """
        self._motions.extend(motions)
    
    def get_motion_by_execution_id(self, execution_motion_id: str) -> Optional[AtomicMotion]:
        """
        Find motion by execution motion ID.
        
        Args:
            execution_motion_id: Execution motion ID from events
            
        Returns:
            AtomicMotion if found, None otherwise
        """
        for motion in self._motions:
            if motion.execution_motion_id == execution_motion_id:
                return motion
        return None
