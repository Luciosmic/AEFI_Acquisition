from abc import ABC, abstractmethod
from typing import Tuple

from .dtos.field_map_dto import FieldMapDTO
from .dtos.load_step_dto import LoadStepDTO
from .dtos.steps_request_dto import StepsRequestDTO


class IApiFieldMapService(ABC):
    """
    Responsibility:
    - Inbound contract of the field map use cases: which steps an acquisition holds, and one step as a map.

    Rationale:
    - The Map panel depends on this contract, never on the file format nor on the concrete service.

    Design:
    - Pure ABC. Steps come in processing order. An unreadable step raises; nothing is silently drawn from defaults except missing channel names.
    """

    @abstractmethod
    def list_steps(self, request: StepsRequestDTO) -> Tuple[str, ...]:
        """The stored steps of the acquisition, in processing order."""

    @abstractmethod
    def load_step(self, request: LoadStepDTO) -> FieldMapDTO:
        """The step as one 2D grid per channel, with its extent."""
