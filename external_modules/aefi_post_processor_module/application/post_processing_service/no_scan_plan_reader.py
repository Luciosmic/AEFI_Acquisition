"""
NoScanPlanReader - The scan plan reader that knows no plan (see post_processing_service_intention.md).
"""

from typing import Optional

from ...domain.processing.planned_scan_grid.planned_scan_grid import PlannedScanGrid
from .ports.i_scan_plan_reader import IScanPlanReader


class NoScanPlanReader(IScanPlanReader):
    """Default of the service: no description of the acquisition is read, every scan gets the square grid."""

    def planned_grid(self, csv_path: str) -> Optional[PlannedScanGrid]:
        return None


NO_SCAN_PLAN = NoScanPlanReader()
