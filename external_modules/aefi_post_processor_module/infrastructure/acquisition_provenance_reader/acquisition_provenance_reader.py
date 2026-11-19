"""
AcquisitionProvenanceReader - The activity id and the CSV hash of a scan, from the acquisition parameters file
the acquisition writes next to it (see acquisition_provenance_reader_intention.md).
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from ...application.post_processing_service.dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO
from ...application.post_processing_service.ports.i_acquisition_provenance_reader import IAcquisitionProvenanceReader
from ..acquisition_parameters_scan_plan_reader.acquisition_parameters_scan_plan_reader import parameters_path_of

logger = logging.getLogger(__name__)


def _get(mapping: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(mapping, dict):
            return None
        mapping = mapping.get(key)
    return mapping


def _text(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


class AcquisitionProvenanceReader(IAcquisitionProvenanceReader):
    def read(self, csv_path: str) -> Optional[AcquisitionProvenanceDTO]:
        parameters_path = parameters_path_of(csv_path)
        if parameters_path is None or not parameters_path.is_file():
            logger.info("provenance.unknown csv=%s reason=no acquisition parameters file", csv_path)
            return None
        try:
            description = json.loads(parameters_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.warning("provenance.unreadable parameters=%s error_type=%s error=%s", parameters_path, type(e).__name__, e)
            return None
        files = _get(description, 'data', 'files')
        declared = next(
            (_text(f.get('sha256')) for f in files if isinstance(f, dict) and f.get('name') == Path(csv_path).name),
            None,
        ) if isinstance(files, list) else None
        return AcquisitionProvenanceDTO(
            activity_id=_text(_get(description, 'provenance', 'activity', 'id')), declared_csv_sha256=declared
        )
