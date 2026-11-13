"""
Position Increments Port

Responsibility: tell the export, for a position in mm, the controller increments that were commanded,
and read the increments the controller reports now.

Rationale: a position in mm is only reproducible with the µm-per-increment factor in force, and that
factor has already been corrected once on the bench. The increment is the controller's own unit: a scan
exported with its increments can be replayed whatever the factor becomes. Two numbers are exported because
they answer two questions: what was asked (commanded) and where the controller says it was (read).

Design:
- `increments_of` uses the same arithmetic as the move command, so the exported number is the one that was
  sent. During a fly scan the mm position is itself derived from reports: the result is then within one
  increment of the true one.
- `read_increments` is instantaneous: meaningful only while the axes are at rest (step scan, after the
  settle delay), never during a fly sweep: the caller decides.
- Both return None when the mm conversion is not applied or the controller does not answer: the export
  leaves the cells empty, never a guess.
- Pure query side: no command, no event.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IPositionIncrementsPort(ABC):
    @abstractmethod
    def increments_of(self, x_mm: float, y_mm: float) -> Optional[Tuple[int, int]]:
        """Increments (x, y) the move command sends for this position, or None if the conversion is not applied."""

    @abstractmethod
    def read_increments(self) -> Optional[Tuple[int, int]]:
        """Increments (x, y) the controller reports now, or None if it does not answer."""
