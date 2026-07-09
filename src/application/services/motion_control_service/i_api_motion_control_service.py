from abc import ABC, abstractmethod

from domain.shared.operation_result import OperationResult


class IApiMotionControlService(ABC):
    """
    Responsibility:
    - Inbound API contract for MotionControlService.
    - Defines what UI adapters and controllers may call on this service.

    Rationale:
    - Distinguishes inbound callers (Adapters → Application) from outbound ports
      (Application → Infrastructure) which use the i_ prefix.

    Design:
    - Pure ABC, no state.
    - Implemented by MotionControlService.
    """

    @abstractmethod
    def move_relative(self, dx: float, dy: float) -> OperationResult: ...

    @abstractmethod
    def move_absolute(self, x: float, y: float) -> OperationResult: ...

    @abstractmethod
    def move_absolute_x(self, target_x: float) -> OperationResult: ...

    @abstractmethod
    def move_absolute_y(self, target_y: float) -> OperationResult: ...

    @abstractmethod
    def home_x(self) -> OperationResult: ...

    @abstractmethod
    def home_y(self) -> OperationResult: ...

    @abstractmethod
    def home_xy(self) -> OperationResult: ...

    @abstractmethod
    def stop(self) -> OperationResult: ...

    @abstractmethod
    def emergency_stop(self) -> OperationResult: ...

    @abstractmethod
    def set_reference(self, axis: str, position: float = 0.0) -> OperationResult: ...

    @abstractmethod
    def get_axis_limits(self) -> tuple[float, float]: ...
