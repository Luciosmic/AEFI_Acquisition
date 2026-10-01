"""
Acquisition Snapshot Port Interface

Responsibility:
- Return the acquisition context as a flat dict of sections, for inclusion
  in the per-scan metadata JSON: the hardware configuration known to the
  domain (mounted boards and their characterization, sensor and source
  geometry calibrations, with the warnings of an incomplete configuration)
  and the last-applied hardware configs sitting on disk.

Rationale:
- AD9106/motion config have no in-memory getter today — the on-disk JSON
  files they're persisted to are the only accessible source of truth.
  Reading them from the application layer directly would violate the
  "no direct IO in Application services" rule, hence this port.

Design:
- Single read-only query method; no state, no configuration step.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IAcquisitionSnapshotPort(ABC):
    """Read-only snapshot of on-disk acquisition/hardware config sections."""

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Return available config sections, keyed by section name.

        Missing or unreadable files are simply omitted from the result —
        never raises.
        """
        pass
