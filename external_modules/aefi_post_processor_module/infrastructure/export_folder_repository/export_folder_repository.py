"""
ExportFolderRepository - The acquisitions of an export folder, at any depth, described by their acquisition
parameters file (see export_folder_repository_intention.md).
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import h5py

from ...domain.acquisition_record.acquisition_record import AcquisitionRecord
from ...domain.acquisition_record.repositories.i_acquisition_repository import IAcquisitionRepository
from ...domain.processing.processing_steps.processing_steps import PREPROCESSED
from ..hdf5_step_format.hdf5_step_format import processing_store_path, step_group_name
from .acl.acquisition_parameters_translator import NOT_A_SCAN, ParametersDescription, describe

logger = logging.getLogger(__name__)

# Step scans (measurements) and fly scans (exploration maps): same files, same processing.
KINDS = ("stepScan", "flyScan")
CSV_SUFFIX = "_aefi.csv"
PARAMETERS_SUFFIX = "_acquisition-parameters.json"
_UNKNOWN = ParametersDescription(None, None, None, None, None)


def _holds_preprocessed(steps_file: str) -> bool:
    """Read-only look into the steps file; one that cannot be opened holds nothing."""
    try:
        with h5py.File(steps_file, 'r') as h5:
            return step_group_name(PREPROCESSED) in h5
    except OSError:
        return False


def _description(folder: Path) -> ParametersDescription:
    """The acquisition as its parameters file describes it; unknown without a readable one."""
    files = sorted(folder.glob(f"*{PARAMETERS_SUFFIX}"))
    if not files:
        return _UNKNOWN
    try:
        return describe(json.loads(files[0].read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("catalog.parameters_unreadable file=%s error_type=%s error=%s", files[0], type(e).__name__, e)
        return _UNKNOWN


def _kind_from_name(name: str) -> Optional[str]:
    """Legacy: exports without parameters, or from before schema 1.4, are told apart by their name only."""
    return next((kind for kind in KINDS if f"_{kind}_" in f"{name}_"), None)


class ExportFolderRepository(IAcquisitionRepository):
    def list_acquisitions(self, export_folder: str) -> List[AcquisitionRecord]:
        root = Path(export_folder)
        if not root.exists():
            return []
        records = []
        for csv_path in sorted(root.rglob(f"*{CSV_SUFFIX}")):
            folder = csv_path.parent
            if folder == root:
                continue
            name = folder.name
            description = _description(folder)
            kind = description.kind
            if kind is None:
                kind = _kind_from_name(name)
                if kind is not None:
                    logger.info("catalog.kind_from_name scan=%s kind=%s schema=%s", name, kind, description.schema_version)
            if kind is None or kind == NOT_A_SCAN:
                continue
            acquisition_file = str(folder / f"{name}.h5")
            steps_file = processing_store_path(acquisition_file)
            steps_exist = os.path.exists(steps_file)
            group = folder.parent.relative_to(root).as_posix()
            records.append(AcquisitionRecord(
                name=name,
                kind=kind,
                folder=str(folder),
                csv_file=str(csv_path),
                acquisition_file=acquisition_file,
                csv_modified_at=csv_path.stat().st_mtime,
                steps_modified_at=os.stat(steps_file).st_mtime if steps_exist else None,
                steps_hold_preprocessed=steps_exist and _holds_preprocessed(steps_file),
                group="" if group == "." else group,
                acquired_at=description.acquired_at,
                measured_object=description.measured_object,
                lift_off_mm=description.lift_off_mm,
            ))
        return sorted(records, key=lambda record: record.name)
