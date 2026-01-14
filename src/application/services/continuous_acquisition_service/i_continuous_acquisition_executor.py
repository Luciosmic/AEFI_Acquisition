"""
Continuous Acquisition Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution.

Rationale:
- Application layer depends on this port instead of direct threading or
  hardware code. Infrastructure implements the actual worker.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort


@dataclass
class ContinuousAcquisitionConfig:
    """
    Configuration for continuous acquisition.

    - sample_rate_hz: target acquisition rate.
    - max_duration_s: optional duration limit; None means until explicit stop.
    - target_uncertainty: optional measurement quality target.
    """

    sample_rate_hz: Optional[float] = None
    max_duration_s: Optional[float] = None
    target_uncertainty: Optional[MeasurementUncertainty] = None


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


