from abc import ABC, abstractmethod
from typing import List

from ..acquisition_record import AcquisitionRecord


class IAcquisitionRepository(ABC):
    """
    Responsibility:
    - List the acquisitions of an export folder, each with the dates of its scan file and of its steps file.

    Rationale:
    - The rule "to recalculate" belongs to the domain; where acquisitions live and how their dates are read does not.

    Design:
    - Read-only port: listing never creates nor modifies a file. A folder that does not exist holds no acquisition.
    - Acquisitions come sorted by folder name.
    """

    @abstractmethod
    def list_acquisitions(self, export_folder: str) -> List[AcquisitionRecord]:
        """The acquisitions found under the export folder."""
