from abc import ABC, abstractmethod
from typing import Tuple

from .dtos.acquisition_outcome_dto import AcquisitionOutcomeDTO
from .dtos.acquisition_status_dto import AcquisitionStatusDTO
from .dtos.list_acquisitions_dto import ListAcquisitionsDTO


class IApiAcquisitionCatalogService(ABC):
    """
    Responsibility:
    - Inbound contract of the catalog use cases: the acquisitions of an export with their processing state, and the outcome of a processing.

    Rationale:
    - The Acquisitions panel shows states at opening without computing anything; it reads the catalog and reports each outcome back.

    Design:
    - Pure ABC. Listing never writes. A failure reported for an acquisition is kept in memory for the session, until a success is reported for it.
    """

    @abstractmethod
    def list_acquisitions(self, request: ListAcquisitionsDTO) -> Tuple[AcquisitionStatusDTO, ...]:
        """The acquisitions of the export folder, each processed, to recompute or failed."""

    @abstractmethod
    def report_outcome(self, outcome: AcquisitionOutcomeDTO) -> None:
        """Remember a failure (with its message) or forget it after a success."""
