from abc import ABC, abstractmethod
from typing import List

from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO, MeasuredObjectRegistrationDTO
from application.measured_object_registry.measured_object_service.measured_object_service_errors import MeasuredObjectServiceError
from domain.shared_kernel.operation_result import OperationResult


class IApiMeasuredObjectService(ABC):
    """
    Responsibility:
    - Inbound contract of the measured_object use cases, for the presenters.

    Rationale:
    - Hexagonal inbound port: presenters depend on this inbound port, never on the concrete service, so the UI layer does not import the application implementation.

    Design:
    - Pure ABC. Expected refusals are results (MeasuredObjectServiceError union),
      never exceptions. Implemented by MeasuredObjectService.
    """

    @abstractmethod
    def list_measured_objects(self) -> OperationResult[List[MeasuredObjectDTO], MeasuredObjectServiceError]:
        """Known measured_objects, sorted by name."""

    @abstractmethod
    def register_measured_object(self, name: str) -> OperationResult[MeasuredObjectRegistrationDTO, MeasuredObjectServiceError]:
        """The measured_object of this name — the existing one if the spelling is
        already known (case and spacing insensitive), else a new one."""

    @abstractmethod
    def rename_measured_object(self, measured_object_id: str, name: str) -> OperationResult[MeasuredObjectDTO, MeasuredObjectServiceError]:
        """The measured_object under its new name — same identity; refused if another
        measured_object already has this spelling."""

    @abstractmethod
    def delete_measured_object(self, measured_object_id: str) -> OperationResult[MeasuredObjectDTO, MeasuredObjectServiceError]:
        """Remove the measured_object from the registry; returns what was removed.
        Exports already written keep its identity and name."""
