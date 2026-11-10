"""
Inertial Probe Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution of the
  inertial probe.

Rationale:
- The application layer depends on this port instead of direct threading code.
  Infrastructure implements the worker (same role as
  IElectricFieldProbeAcquisitionExecutor for the field probe).

Design:
- Abstract Base Class (ABC), pure interface.
- start() must not block the caller: stream_port.start_stream() blocks ~0.5 s
  on the real board and has to run in the worker thread, never in the Qt thread.
"""

from abc import ABC, abstractmethod

from application.services.inertial_probe_service.dtos.inertial_probe_dtos import (
    InertialProbeAcquisitionConfig,
)
from application.services.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)


class IInertialProbeAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous inertial probe acquisition."""

    @abstractmethod
    def start(
        self,
        config: InertialProbeAcquisitionConfig,
        stream_port: IInertialProbeStreamPort,
    ) -> None:
        """Start continuous acquisition (non-blocking from the caller perspective)."""

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop; the worker stops the stream on the board."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""
