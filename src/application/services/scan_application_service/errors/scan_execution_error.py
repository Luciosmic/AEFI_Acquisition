"""
Scan Execution Use-Case Error Union

Responsibility:
- Enumerate every terminal failure mode a caller of the scan execution use case
  must be prepared to distinguish.

Rationale:
- Application services translate infrastructure errors (MotionSyncError,
  probe/acquisition failures) into use-case-level outcomes named in the
  ubiquitous language of the scan use case. The caller (Presenter, tests)
  depends only on this union, not on the underlying port errors.
- This is the single cross-layer translation site, per the error-taxonomy
  standard.

Design:
- Sealed-union pattern via base class + frozen dataclasses.
- Each variant maps to a specific translation origin so the presenter can
  build a meaningful user-facing message without inspecting port errors.
"""

from __future__ import annotations

from dataclasses import dataclass


class ScanExecutionError:
    """
    Sealed union tag for scan execution failures visible to the use-case caller.
    """


@dataclass(frozen=True)
class MotionTimeoutDuringScan(ScanExecutionError):
    """A motion segment exceeded the allowed duration; the scan cannot continue."""

    point_index: int
    motion_id: str
    timeout_seconds: float


@dataclass(frozen=True)
class MotionFailedDuringScan(ScanExecutionError):
    """The motion controller reported a hardware failure during the scan."""

    point_index: int
    motion_id: str
    error_detail: str


@dataclass(frozen=True)
class EmergencyStopDuringScan(ScanExecutionError):
    """An emergency stop occurred during scan execution."""

    point_index: int


@dataclass(frozen=True)
class AcquisitionFailedDuringScan(ScanExecutionError):
    """A sample acquisition raised at the given scan point."""

    point_index: int
    error_detail: str


@dataclass(frozen=True)
class FieldProbeAcquisitionFailedDuringScan(ScanExecutionError):
    """An EF probe acquisition raised at the given scan point (probe branch enabled)."""

    point_index: int
    error_detail: str
