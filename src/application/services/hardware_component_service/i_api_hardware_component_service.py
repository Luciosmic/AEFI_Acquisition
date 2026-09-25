from abc import ABC, abstractmethod
from typing import Any, List, Mapping, Optional

from application.services.hardware_component_service.dtos.hardware_component_dto import (
    HardwareComponentDTO,
    HardwareComponentKindDTO,
)


class IApiHardwareComponentService(ABC):
    """
    Responsibility:
    - Inbound API contract for HardwareComponentService.

    Rationale:
    - Lets presenters depend on a contract, and be tested against a stub.

    Design:
    - Pure ABC. Kinds are designated by their string key (see `list_kinds`).
    """

    @abstractmethod
    def list_kinds(self) -> List[HardwareComponentKindDTO]: ...

    @abstractmethod
    def record_characterization(self, kind_key: str, component_name: str, values: Mapping[str, Any]) -> None:
        """Quantities left out or None are recorded as not characterized.
        Recording under an existing name completes that component's history."""

    @abstractmethod
    def mount_component(self, kind_key: str, component_name: str) -> None:
        """Declare the (already characterized) component mounted on the bench."""

    @abstractmethod
    def list_components(self, kind_key: str) -> List[HardwareComponentDTO]:
        """Every known component of that kind, current characterization, by name."""

    @abstractmethod
    def get_mounted_component(self, kind_key: str) -> Optional[HardwareComponentDTO]:
        """The mounted component's current characterization, None if none mounted."""
