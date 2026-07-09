from abc import ABC, abstractmethod
from typing import Tuple


class IApiTransformationService(ABC):
    """
    Responsibility:
    - Inbound API contract for TransformationService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by TransformationService.
    """

    @abstractmethod
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float) -> None: ...

    @abstractmethod
    def get_rotation_angles(self) -> Tuple[float, float, float]: ...

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def is_enabled(self) -> bool: ...

    @abstractmethod
    def transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]: ...

    @abstractmethod
    def transform_source_to_sensor(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]: ...

    @abstractmethod
    def force_transform_sensor_to_source(self, vector: Tuple[float, float, float]) -> Tuple[float, float, float]: ...
