from abc import ABC, abstractmethod
from typing import Optional

from ..dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO


class IAcquisitionProvenanceReader(ABC):
    """
    Responsibility:
    - Give the activity id and the CSV hash the acquisition recorded for a scan, from the description it wrote next to it.

    Rationale:
    - The HDF5 file the processing creates must say which acquisition its points come from and whether the CSV is still
      the one the acquisition closed. The service must not know where that description lives nor its format.

    Design:
    - Outbound port, pure ABC. None when no description says anything (no file, a scan that is not from the
      acquisition, an unreadable description); a description that lacks one of the two facts gives it as None.
    """

    @abstractmethod
    def read(self, csv_path: str) -> Optional[AcquisitionProvenanceDTO]:
        """The provenance recorded for the scan whose points are in `csv_path`, or None when it is not known."""
