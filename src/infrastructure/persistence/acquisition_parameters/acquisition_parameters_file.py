"""
Acquisition Parameters File — the file side of acquisition-parameters.json,
shared by every export port that writes it: describe a produced file
(size + SHA-256) and write the document atomically.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

from application.shared.acquisition_parameters.acquisition_conditions_dtos import ExportedFileDTO

# File extension -> format name written in data.files.
FORMATS = {".csv": "CSV", ".h5": "HDF5", ".jsonl": "JSON Lines", ".log": "text", ".json": "JSON"}


def describe_file(path: Path, file_format: str) -> ExportedFileDTO:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            digest.update(block)
    return ExportedFileDTO(name=path.name, format=file_format, byte_size=path.stat().st_size, sha256=digest.hexdigest())


def write_document(path: Path, document: Dict[str, Any]) -> None:
    """Never a half-written document: write aside, then replace."""
    temporary = path.with_suffix(".json.tmp")
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
    os.replace(temporary, path)
