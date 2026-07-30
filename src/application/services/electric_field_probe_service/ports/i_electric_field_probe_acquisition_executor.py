"""
Electric Field Probe Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution of an
  electric field probe.

Rationale:
- Application layer depends on this port instead of direct threading code.
  Infrastructure implements the actual worker (mirrors
  IAefiAcquisitionExecutor / AefiAcquisitionExecutor for the AEFI channel).

Design:
- Abstract Base Class (ABC), pure interface.
- start()/stop()/is_running() — same shape as IAefiAcquisitionExecutor so
  both continuous-acquisition channels read the same way.
"""

from abc import ABC, abstractmethod

from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)


class IElectricFieldProbeAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous electric field probe acquisition."""

    @abstractmethod
    def start(
        self,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        """Start continuous acquisition (non-blocking from the caller perspective)."""

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of the continuous acquisition."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""
