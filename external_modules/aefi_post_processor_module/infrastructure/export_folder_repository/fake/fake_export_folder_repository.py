"""
FakeExportFolderRepository - Acquisitions held in memory (see fake_export_folder_repository_intention.md).
"""

from typing import Dict, List

from ....domain.acquisition_record.acquisition_record import AcquisitionRecord
from ....domain.acquisition_record.repositories.i_acquisition_repository import IAcquisitionRepository


class FakeExportFolderRepository(IAcquisitionRepository):
    def __init__(self) -> None:
        self._by_folder: Dict[str, List[AcquisitionRecord]] = {}

    def add(self, export_folder: str, record: AcquisitionRecord) -> None:
        self._by_folder.setdefault(export_folder, []).append(record)

    def list_acquisitions(self, export_folder: str) -> List[AcquisitionRecord]:
        return sorted(self._by_folder.get(export_folder, []), key=lambda record: record.name)
