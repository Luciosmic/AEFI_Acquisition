"""
Inbound interface for the cube visualizer application service.

Consumed by primary adapters (Qt UI / Presenter) — i_api_ prefix = inbound.
"""
from abc import ABC, abstractmethod
from .dtos.update_angles_request_dto import UpdateAnglesRequestDto
from .dtos.sensor_orientation_dto import SensorOrientationDto


class IApiCubeVisualizerService(ABC):
    """Inbound port: contract exposed to the Interface/Presenter layer."""

    @abstractmethod
    def update_angles(self, request: UpdateAnglesRequestDto) -> SensorOrientationDto:
        """Update sensor orientation angles and return the new orientation."""
        ...

    @abstractmethod
    def reset_to_default(self) -> SensorOrientationDto:
        """Reset sensor orientation to default and return it."""
        ...

    @abstractmethod
    def get_current_orientation(self) -> SensorOrientationDto:
        """Query: return current orientation without side effects."""
        ...
