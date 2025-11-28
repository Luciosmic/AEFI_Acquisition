"""
Domain: Scan execution metadata value object.

Responsibility:
    Represent execution-related metadata for a scan.
    Captures wall-clock timing (start, end, duration) of the scan lifecycle.

Rationale:
    A Scan has a lifecycle (PENDING -> RUNNING -> COMPLETED).
    We need to track when these transitions happened and how long the scan took
    in "wall-clock" time.

Design:
    - Immutable value object
    - No infrastructure dependencies (datetime objects passed in)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ScanExecutionMetadata:
    """Domain concept: execution metadata for a scan.
    
    Attributes
    ----------
    start_time : datetime | None
        When the scan transitioned to RUNNING.
    end_time : datetime | None
        When the scan transitioned to COMPLETED (or FAILED).
    total_duration_seconds : float | None
        Total wall-clock duration (end_time - start_time).
        Can be None if scan is not finished.
    """
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None

    def with_start_time(self, start_time: datetime) -> ScanExecutionMetadata:
        """Return a new instance with start_time set."""
        return ScanExecutionMetadata(
            start_time=start_time,
            end_time=self.end_time,
            total_duration_seconds=self.total_duration_seconds
        )

    def with_completion(self, end_time: datetime) -> ScanExecutionMetadata:
        """Return a new instance with end_time and duration set."""
        duration = None
        if self.start_time:
            duration = (end_time - self.start_time).total_seconds()
            
        return ScanExecutionMetadata(
            start_time=self.start_time,
            end_time=end_time,
            total_duration_seconds=duration
        )
