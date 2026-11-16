"""
ExportFolderRepository - The acquisitions of an export folder, read from its sub-folders (see export_folder_repository_intention.md).
"""

import os
from pathlib import Path
from typing import List, Tuple

from ...domain.acquisition_record.acquisition_record import AcquisitionRecord
from ...domain.acquisition_record.repositories.i_acquisition_repository import IAcquisitionRepository
from ..hdf5_step_format.hdf5_step_format import processing_store_path

# Step scans (measurements) and fly scans (exploration maps): same files, same processing.
KINDS = ("stepScan", "flyScan")


class ExportFolderRepository(IAcquisitionRepository):
    def list_acquisitions(self, export_folder: str) -> List[AcquisitionRecord]:
        root = Path(export_folder)
        if not root.exists():
            return []
        found: List[Tuple[Path, str]] = sorted(
            (path, kind) for kind in KINDS for path in root.glob(f"*_{kind}_*/*_aefi.csv")
        )
        records = []
        for csv_path, kind in found:
            name = csv_path.parent.name
            acquisition_file = str(csv_path.parent / f"{name}.h5")
            steps_file = processing_store_path(acquisition_file)
            records.append(AcquisitionRecord(
                name=name,
                kind=kind,
                folder=str(csv_path.parent),
                csv_file=str(csv_path),
                acquisition_file=acquisition_file,
                csv_modified_at=csv_path.stat().st_mtime,
                steps_modified_at=os.stat(steps_file).st_mtime if os.path.exists(steps_file) else None,
            ))
        return records
