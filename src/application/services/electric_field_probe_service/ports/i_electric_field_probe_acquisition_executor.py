"""
Electric Field Probe Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution from
  an electric field probe.

Rationale:
- Application layer depends on this port instead of direct threading or
  hardware code — mirrors IContinuousAcquisitionExecutor, kept separate to
  avoid coupling electric_field_probe to VoltageMeasurement.
"""

from abc import ABC, abstractmethod

from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)


class IElectricFieldProbeAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous acquisition from a probe."""

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
    def update_config(self, config: ElectricFieldProbeAcquisitionConfig) -> None:
        """Dynamically update configuration of running acquisition."""
