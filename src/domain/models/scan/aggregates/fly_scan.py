"""
FlyScan Aggregate

Responsibility:
- Aggregate Root for Fly Scans (continuous motion with acquisition).
- Manages the collection of ScanPointResults acquired during motion.
- Ensures consistency of the scan data.

Key differences from StepScan:
- Acquires during motion, not at stops
- Uses AtomicMotion.calculate_acquisition_positions()
- Point count >> grid point count (continuous acquisition)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from domain.models.scan.aggregates.spatial_scan import SpatialScan
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.shared.events.domain_event import DomainEvent
from domain.models.scan.events.scan_events import (
    ScanStarted,
    ScanPointAcquired,
    ScanCompleted,
    ScanFailed,
    ScanCancelled,
    ScanPaused,
    ScanResumed
)
from domain.models.scan.entities.atomic_motion import AtomicMotion


@dataclass
class FlyScan(SpatialScan):
    """
    Aggregate Root for Fly Scans.

    Unlike StepScan which stops at each point, FlyScan acquires
    continuously during motion, resulting in many more data points.
    """

    _points: List[ScanPointResult] = field(default_factory=list)
    _motions: List[AtomicMotion] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list)
    _acquisition_rate_hz: float = 100.0  # Measured acquisition rate

    def __post_init__(self):
        self.is_fly_scan = True
        self.scan_type = "fly_scan"

    @property
    def points(self) -> List[ScanPointResult]:
        """Get immutable copy of scan points."""
        return list(self._points)

    @property
    def motions(self) -> List[AtomicMotion]:
        """Get immutable copy of atomic motions."""
        return list(self._motions)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    @property
    def expected_points(self) -> int:
        """
        Expected number of points (estimated, not exact for FlyScan).

        For FlyScan, this is an estimate based on trajectory and acquisition rate.
        """
        return self._expected_points

    @property
    def acquisition_rate_hz(self) -> float:
        """Get configured acquisition rate."""
        return self._acquisition_rate_hz

    _expected_points: int = 0

    def start(self, config, acquisition_rate_hz: float) -> None:
        """
        Start the fly scan.

        Args:
            config: FlyScanConfig or similar configuration
            acquisition_rate_hz: Measured acquisition rate capability
        """
        super().start()

        # Store acquisition rate
        self._acquisition_rate_hz = acquisition_rate_hz

        # Calculate expected points based on config
        if hasattr(config, 'estimate_total_points'):
            # FlyScanConfig has estimation method
            # Will be called by application layer with capability
            self._expected_points = 0  # Will be updated by executor
        elif hasattr(config, 'total_points'):
            self._expected_points = config.total_points()
        else:
            # Fallback calculation
            self._expected_points = config.x_nb_points * config.y_nb_points

        self._domain_events.append(ScanStarted(scan_id=self.id, config=config))

    def add_point_result(self, result: ScanPointResult) -> None:
        """
        Add a scan point result acquired during motion.

        For FlyScan, points are added continuously during motion,
        not just at grid positions.

        Args:
            result: ScanPointResult from acquisition
        """
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
        # (For FlyScan, this is less precise than StepScan)
        if self._expected_points > 0 and len(self._points) >= self._expected_points:
            self.complete()

    def complete(self) -> None:
        """Mark scan as completed."""
        if self.status == ScanStatus.COMPLETED:
            return  # Already completed

        super().complete()
        self._domain_events.append(ScanCompleted(scan_id=self.id, total_points=len(self._points)))

    def fail(self, reason: str) -> None:
        """
        Mark scan as failed.

        Args:
            reason: Failure reason
        """
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

    def set_expected_points(self, expected_points: int) -> None:
        """
        Set expected number of points (called by executor after estimation).

        Args:
            expected_points: Estimated total points
        """
        self._expected_points = expected_points
