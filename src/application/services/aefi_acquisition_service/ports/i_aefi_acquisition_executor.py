"""
Continuous Acquisition Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution.

Rationale:
- Application layer depends on this port instead of direct threading or
  hardware code. Infrastructure implements the actual worker.
"""

from abc import ABC, abstractmethod

from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort

# Re-export so existing callers that imported from here continue to work
__all__ = ["IAefiAcquisitionExecutor", "AefiAcquisitionConfig"]


class IAefiAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous acquisition."""

    @abstractmethod
    def start(self, config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Start continuous acquisition (non‑blocking from the caller perspective).
        """

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of the continuous acquisition."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""


