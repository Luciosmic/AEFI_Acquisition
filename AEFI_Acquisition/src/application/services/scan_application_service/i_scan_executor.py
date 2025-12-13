"""
Scan Execution Port Interface

Responsibility:
- Define the abstract interface for executing a scan trajectory with hardware.

Rationale:
- Hexagonal architecture / Port pattern.
- Decouples scan orchestration (Application layer) from execution strategy
  (step‑scan vs fly‑scan vs simulation).

Design:
- Strategy pattern: different implementations can be swapped without
  changing the Application code.
- Works with existing domain model: StepScan aggregate + ScanTrajectory
  + StepScanConfig.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from domain.aggregates.step_scan import StepScan
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig


class IScanExecutor(ABC):
    """
    Port interface for scan execution.

    This interface is implemented in the infrastructure layer and encapsulates
    all concerns related to:
    - motion control timing (move / wait)
    - acquisition timing (averaging, sampling)
    - threading / background workers
    - event publication during execution
    """

    @abstractmethod
    def execute(
        self,
        scan: StepScan,
        trajectory: ScanTrajectory,
        config: StepScanConfig,
    ) -> bool:
        """
        Execute the scan trajectory.

        For the first implementation we keep this method **blocking** and
        return a simple success flag so that existing tests remain valid.

        Later, this contract can evolve to non‑blocking execution while
        preserving the same high‑level port.
        """

    @abstractmethod
    def cancel(self, scan: StepScan) -> None:
        """Request cancellation of an active scan (if supported by executor)."""


