"""
Domain: Scan status enumeration.

Responsibility:
    Define the lifecycle states of a scan.
    Universal concept applicable to all scan types (spatial, frequency, etc.).

Rationale:
    Using an enum makes state transitions explicit and prevents invalid
    states. The lifecycle is: PENDING → RUNNING → (COMPLETED | FAILED | CANCELLED)

Design:
    - Enum for type safety
    - Clear state names matching business terminology
    - No infrastructure dependencies
    - Universal: used by all scan types
"""

from __future__ import annotations

from enum import Enum


class ScanStatus(Enum):
    """Lifecycle states of a scan.

    Universal lifecycle applicable to all scan types.

    States
    ------
    PENDING : str
        Scan is created but not yet started.
    RUNNING : str
        Scan execution is in progress.
    COMPLETED : str
        Scan finished successfully with results.
    FAILED : str
        Scan execution failed with an error.
    CANCELLED : str
        Scan was cancelled before completion.

    State Transitions
    -----------------
    Valid transitions:
    - PENDING → RUNNING (scan starts)
    - RUNNING → COMPLETED (scan succeeds)
    - RUNNING → FAILED (scan fails)
    - PENDING → CANCELLED (user cancels before start)
    - RUNNING → CANCELLED (user cancels during execution)

    Invalid transitions:
    - COMPLETED → * (final state)
    - FAILED → * (final state, except retry would create new scan)
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_final(self) -> bool:
        """Check if this status is a final state.

        Returns
        -------
        bool
            True if status is COMPLETED, FAILED, or CANCELLED.
        """
        return self in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED)

    def is_active(self) -> bool:
        """Check if this status represents an active scan.

        Returns
        -------
        bool
            True if status is PENDING or RUNNING.
        """
        return self in (ScanStatus.PENDING, ScanStatus.RUNNING)
