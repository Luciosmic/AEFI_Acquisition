"""
Motion Synchronizer Error Union

Responsibility:
- Enumerate every terminal failure mode of `IMotionSynchronizer.wait_for_motion`.

Rationale:
- The scan loop needs to distinguish reasons a motion did not complete
  normally (timeout vs hardware failure vs emergency stop vs external stop)
  to decide whether to retry, cancel the scan, or fail it.
- Variants are named after the refused promise in ubiquitous language, not
  after the exception mechanism, per the error-taxonomy standard.

Design:
- Sealed-union pattern via a common base class + frozen dataclasses.
- Pattern-matchable with Python 3.10+ `match/case`.
- Immutable and stringly free: each variant carries the structured data
  callers need to log or translate further.
"""

from __future__ import annotations

from dataclasses import dataclass


class MotionSyncError:
    """
    Sealed union tag for motion synchronization failures.

    Do not instantiate directly; use one of the subclasses.
    """


@dataclass(frozen=True)
class MotionTimeout(MotionSyncError):
    """The requested motion did not reach a terminal state within the timeout."""

    motion_id: str
    timeout_seconds: float


@dataclass(frozen=True)
class MotionHardwareFailed(MotionSyncError):
    """The motion controller reported a hardware-level failure for this motion."""

    motion_id: str
    error_detail: str


@dataclass(frozen=True)
class EmergencyStop(MotionSyncError):
    """An emergency stop was triggered while this motion was pending."""


@dataclass(frozen=True)
class MotionStoppedExternally(MotionSyncError):
    """The motion was stopped by an external actor (user, safety loop, other service)."""

    motion_id: str
    reason: str
