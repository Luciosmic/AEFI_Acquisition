"""
NoAcquisitionProvenanceReader - The provenance reader that knows no acquisition (see post_processing_service_intention.md).
"""

from typing import Optional

from .dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO
from .ports.i_acquisition_provenance_reader import IAcquisitionProvenanceReader


class NoAcquisitionProvenanceReader(IAcquisitionProvenanceReader):
    """Default of the service: no description of the acquisition is read, the source is recorded by its hash alone."""

    def read(self, csv_path: str) -> Optional[AcquisitionProvenanceDTO]:
        return None


NO_ACQUISITION_PROVENANCE = NoAcquisitionProvenanceReader()
