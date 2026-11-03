from abc import ABC, abstractmethod
from typing import List

from application.services.operator_service.dtos.operator_dto import OperatorDTO, OperatorRegistrationDTO
from application.services.operator_service.operator_service_errors import OperatorServiceError
from domain.shared_kernel.operation_result import OperationResult


class IApiOperatorService(ABC):
    """
    Responsibility:
    - Inbound contract of the operator use cases, for the presenters.

    Design:
    - Pure ABC. Expected refusals are results (OperatorServiceError union),
      never exceptions. Implemented by OperatorService.
    """

    @abstractmethod
    def list_operators(self) -> OperationResult[List[OperatorDTO], OperatorServiceError]:
        """Known operators, sorted by name."""

    @abstractmethod
    def register_operator(self, name: str) -> OperationResult[OperatorRegistrationDTO, OperatorServiceError]:
        """The operator of this name — the existing one if the spelling is
        already known (case and spacing insensitive), else a new one."""
