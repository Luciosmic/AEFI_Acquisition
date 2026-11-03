"""
Inertial Sensor Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution of the
  inertial sensor.

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

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorAcquisitionConfig,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)


class IInertialSensorAcquisitionExecutor(ABC):
    """Port for starting / stopping continuous inertial sensor acquisition."""

    @abstractmethod
    def start(
        self,
        config: InertialSensorAcquisitionConfig,
        stream_port: IInertialSensorStreamPort,
    ) -> None:
        """Start continuous acquisition (non-blocking from the caller perspective)."""

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop; the worker stops the stream on the board."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""
