from abc import ABC, abstractmethod
from typing import Optional

from ....domain.processing.planned_scan_grid.planned_scan_grid import PlannedScanGrid


class IScanPlanReader(ABC):
    """
    Responsibility:
    - Give the grid the acquisition planned for a scan, from the description the acquisition wrote next to it.

    Rationale:
    - The measured points do not tell an interrupted scan from a rectangular one; the description of the
      acquisition does. The service must not know where that description lives nor its format.

    Design:
    - Outbound port, pure ABC. None when no description says the planned grid (no file, a scan that is not
      from the acquisition, an unreadable or incomplete description): the service then keeps the square grid.
    """

    @abstractmethod
    def planned_grid(self, csv_path: str) -> Optional[PlannedScanGrid]:
        """The planned grid of the scan whose points are in `csv_path`, or None when it is not known."""
