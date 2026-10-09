"""
Fly Scan Aggregate (transitional)

Responsibility:
- Step-scan lifecycle shell that, unlike StepScan, still holds its points.
- Auto-completes when the expected number of points is reached.

Transitional: the fly-scan keeps its points here until it gets its own
AefiLine-based flow (step 8 of the scan-domain refactoring).
"""

import logging
from dataclasses import dataclass, field
from typing import List

from domain.step_scan.step_scan import StepScan
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired

logger = logging.getLogger(__name__)


@dataclass
class FlyScan(StepScan):
    """Aggregate Root for fly scans: a StepScan that keeps its points."""

    _points: List[ScanPointResult] = field(default_factory=list)
    _expected_points: int = 0

    @property
    def points(self) -> List[ScanPointResult]:
        return list(self._points)

    @property
    def expected_points(self) -> int:
        return self._expected_points

    def start(self, config) -> None:
        super().start(config)
        self._expected_points = config.total_points()

    def add_point_result(self, result: ScanPointResult) -> None:
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot add result when scan is {self.status}")

        self._points.append(result)
        self._domain_events.append(ScanPointAcquired(
            scan_id=self.id,
            point_index=result.point_index,
            position=result.position,
            measurement=result.measurement,
            baseline_measurement=result.baseline_measurement,
        ))

        if self._expected_points > 0 and len(self._points) >= self._expected_points:
            logger.info("FlyScan: scan_id=%s reached %d expected points, completing", self.id, self._expected_points)
            self.complete()

    def complete(self, total_points: int = 0) -> bool:
        return super().complete(len(self._points))

    def pause(self, current_point_index: int = 0) -> None:
        super().pause(len(self._points))

    def resume(self, resume_from_point_index: int = 0) -> None:
        super().resume(len(self._points))
