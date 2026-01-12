"""
FlyScan Executor Port Interface

Responsibility:
- Abstract interface for executing fly scans
- Enables hexagonal architecture with pluggable implementations
"""

from abc import ABC, abstractmethod
from typing import List

from domain.models.scan.aggregates.fly_scan import FlyScan
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort


class IFlyScanExecutor(ABC):
    """Port for executing fly scans with continuous motion and acquisition."""

    @abstractmethod
    def execute(
        self,
        fly_scan: FlyScan,
        motions: List[AtomicMotion],
        config: FlyScanConfig,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort
    ) -> bool:
        """
        Execute fly scan with continuous motion and acquisition.

        Args:
            fly_scan: FlyScan aggregate to populate
            motions: List of AtomicMotion entities for the trajectory
            config: FlyScan configuration
            motion_port: Motion control port
            acquisition_port: Acquisition port

        Returns:
            True if execution started successfully
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of running fly scan."""
        pass
