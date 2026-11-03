from abc import ABC, abstractmethod

from application.services.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO


class IMotionConversionStatusPort(ABC):
    """
    Responsibility:
    - Say whether the bench has its mm/pulse conversion and, if not, what is
      missing and where to enter it.

    Rationale:
    - MotionControlService must explain a refusal without calling another
      application service (mechanical transmission calibration): the
      explanation is handed to it through this port.

    Design:
    - Read-only query, no state change.
    - Implemented by MotionConversionHandler.
    """

    @abstractmethod
    def get_status(self) -> MotionConversionStatusDTO: ...
