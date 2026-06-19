"""
Continuous Acquisition Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution.

Rationale:
- Application layer depends on this port instead of direct threading or
  hardware code. Infrastructure implements the actual worker.
"""

from abc import ABC, abstractmethod

from application.services.continuous_acquisition_service.dtos.continuous_acquisition_dtos import ContinuousAcquisitionConfig
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort

# Re-export so existing callers that imported from here continue to work
__all__ = ["IContinuousAcquisitionExecutor", "ContinuousAcquisitionConfig"]


class IContinuousAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous acquisition."""

    @abstractmethod
    def start(self, config: ContinuousAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Start continuous acquisition (non‑blocking from the caller perspective).
        """

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of the continuous acquisition."""

    @abstractmethod
    def update_config(self, config: ContinuousAcquisitionConfig) -> None:
        """
        Dynamically update configuration of running acquisition.
        """


