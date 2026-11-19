"""
FakeAcquisitionProvenanceReader - Provenances in memory (see fake_acquisition_provenance_reader_intention.md).
"""

from typing import Dict, Optional

from ....application.post_processing_service.dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO
from ....application.post_processing_service.ports.i_acquisition_provenance_reader import IAcquisitionProvenanceReader


class FakeAcquisitionProvenanceReader(IAcquisitionProvenanceReader):
    def __init__(self) -> None:
        self._provenances: Dict[str, AcquisitionProvenanceDTO] = {}

    def add_provenance(self, csv_path: str, provenance: AcquisitionProvenanceDTO) -> None:
        self._provenances[csv_path] = provenance

    def read(self, csv_path: str) -> Optional[AcquisitionProvenanceDTO]:
        return self._provenances.get(csv_path)
