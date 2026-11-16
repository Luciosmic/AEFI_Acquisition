"""
FakeAcquisitionParametersScanPlanReader - Planned grids in memory (see fake_acquisition_parameters_scan_plan_reader_intention.md).
"""

from typing import Dict, Optional

from ....application.post_processing_service.ports.i_scan_plan_reader import IScanPlanReader
from ....domain.processing.planned_scan_grid.planned_scan_grid import PlannedScanGrid


class FakeAcquisitionParametersScanPlanReader(IScanPlanReader):
    def __init__(self) -> None:
        self._plans: Dict[str, PlannedScanGrid] = {}

    def add_plan(self, csv_path: str, plan: PlannedScanGrid) -> None:
        self._plans[csv_path] = plan

    def planned_grid(self, csv_path: str) -> Optional[PlannedScanGrid]:
        return self._plans.get(csv_path)
