from abc import ABC, abstractmethod
from typing import Optional


class IApiInertialSensorService(ABC):
    """
    Responsibility:
    - Inbound API contract for InertialSensorService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters -> Application) from outbound
      ports (Application -> Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by InertialSensorService.
    """

    @abstractmethod
    def connect_sensor(self) -> None:
        """Connect to the board. Never raises — reports outcome via domain event."""

    @abstractmethod
    def disconnect_sensor(self) -> None:
        """Stop any acquisition, then close the link (stream stop sent to the board)."""

    @abstractmethod
    def start_acquisition(self) -> None:
        """Start the continuous acquisition on the configured channels (non-blocking)."""

    @abstractmethod
    def stop_acquisition(self) -> None: ...

    @abstractmethod
    def is_acquisition_running(self) -> bool: ...

    @abstractmethod
    def get_control_refusal(self) -> Optional[str]:
        """Why the panel may not start or disconnect the stream now (another owner,
        e.g. the bar calibration, holds it); None when it may."""

    @abstractmethod
    def shutdown(self) -> None:
        """
        Safety stop for application exit: stop the acquisition and close the
        link, which sends the stream stop to the board (it keeps its stream
        active with the port closed). Never raises.
        """
