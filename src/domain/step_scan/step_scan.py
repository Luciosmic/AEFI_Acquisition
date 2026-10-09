"""
Step Scan Aggregate

Responsibility:
- Aggregate Root for the lifecycle of step-by-step (and line) scans.
- Does NOT hold its points: the scan is a tracing artifact, the points live in
  AefiPoint and the thin Scan references them by identity.
- Emits the lifecycle events; ScanCompleted is emitted by the thin Scan, not here.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from domain.step_scan.entities.spatial_scan.spatial_scan import SpatialScan
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.scan_paused.scan_paused import ScanPaused
from domain.step_scan.events.scan_resumed.scan_resumed import ScanResumed

logger = logging.getLogger(__name__)

@dataclass
class StepScan(SpatialScan):
    """
    Aggregate Root for Step Scans.
    """
    
    _domain_events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        self.is_fly_scan = False
        self.scan_type = "step_scan"
        
    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
        
    def start(self, config) -> None:
        super().start()
        self._domain_events.append(ScanStarted(scan_id=self.id, config=config))

    def point_acquired(self, result: ScanPointResult) -> None:
        """Queue ScanPointAcquired for a point; nothing is stored."""
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot add result when scan is {self.status}")

        self._domain_events.append(ScanPointAcquired(
            scan_id=self.id,
            point_index=result.point_index,
            position=result.position,
            measurement=result.measurement,
            baseline_measurement=result.baseline_measurement,
        ))

    def mark_completed(self) -> bool:
        """Follow the thin Scan's completion: COMPLETED, no event (the thin Scan's
        ScanCompleted is the one that went out). Returns False if there was nothing to do."""
        if self.status not in (ScanStatus.RUNNING, ScanStatus.PAUSED):
            logger.info("StepScan: scan_id=%s is %s, completion ignored. Doing nothing.", self.id, self.status)
            return False
        self.status = ScanStatus.COMPLETED
        self.end_time = datetime.now()
        return True

    def complete(self, total_points: int = 0) -> bool:
        """Complete the scan. Returns False (no-op, idempotent) if already
        completed — a caller that doesn't pre-check status can log this
        instead of it passing silently (see ODD: idempotence is a log, not
        a domain event)."""
        if self.status == ScanStatus.COMPLETED:
            return False

        super().complete()
        self._domain_events.append(ScanCompleted(scan_id=self.id, total_points=total_points))
        return True
        
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
        
    def pause(self, current_point_index: int = 0) -> None:
        """Pause the scan (idempotent only for the already-PAUSED case —
        pausing a scan in a final status (COMPLETED/FAILED/CANCELLED) is an
        invariant rejection, not idempotence, and must raise like
        resume()/fail()/SpatialScan.cancel() already do for the equivalent
        case — an operator's "Pause" click racing scan completion must be
        observable to the caller, not silently swallowed."""
        # Idempotent: if already paused, do nothing
        if self.status == ScanStatus.PAUSED:
            return
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot pause scan when status is {self.status}")
        super().pause()
        self._domain_events.append(ScanPaused(scan_id=self.id, current_point_index=current_point_index))
        
    def resume(self, resume_from_point_index: int = 0) -> None:
        """Resume the scan execution after pause."""
        if self.status != ScanStatus.PAUSED:
            raise ValueError(f"Cannot resume scan when status is {self.status}")
        super().resume()
        self._domain_events.append(ScanResumed(scan_id=self.id, resume_from_point_index=resume_from_point_index))
