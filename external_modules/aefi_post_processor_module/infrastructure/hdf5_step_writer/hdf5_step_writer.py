"""
Hdf5StepWriter - Stores the computed steps in an HDF5 file, one group per step (see hdf5_step_writer_intention.md).
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np

from ...application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ...application.post_processing_service.dtos.source_record_dto import SourceRecordDTO
from ...application.post_processing_service.ports.i_step_writer import IStepWriter
from ..hdf5_step_format.hdf5_step_format import (
    DATA_DATASET,
    DATA_DTYPE_ATTR,
    DATA_SHAPE_ATTR,
    LOAD_TIMESTAMP_ATTR,
    PROCESSING_HISTORY_ATTR,
    RAW_CHANNEL_NAMES_ATTR,
    RAW_POSITIONS_DATASET,
    RAW_SCAN_GROUP,
    RAW_VALUES_DATASET,
    SOURCE_ACTIVITY_ID_ATTR,
    SOURCE_CSV_ATTR,
    SOURCE_DECLARED_SHA256_ATTR,
    SOURCE_SHA256_ATTR,
    SOURCE_SHA256_MATCHES_ATTR,
    STEP_NAME_ATTR,
    TIMESTAMP_ATTR,
    processing_store_path,
    step_group_name,
)

logger = logging.getLogger(__name__)


class Hdf5StepWriter(IStepWriter):
    def __init__(self, acquisition_file: str):
        self._file_path = processing_store_path(acquisition_file)
        self._history: List[str] = []
        self._file: Optional[h5py.File] = h5py.File(self._file_path, 'a')
        if PROCESSING_HISTORY_ATTR in self._file.attrs:
            self._history = list(self._file.attrs[PROCESSING_HISTORY_ATTR])

    def record_source(self, source: SourceRecordDTO) -> None:
        if self._file is not None:
            attrs = self._file.attrs
            attrs[SOURCE_CSV_ATTR] = str(source.csv_path)
            attrs[LOAD_TIMESTAMP_ATTR] = datetime.now().isoformat()
            for attr, value in (
                (SOURCE_SHA256_ATTR, source.sha256),
                (SOURCE_ACTIVITY_ID_ATTR, source.activity_id),
                (SOURCE_DECLARED_SHA256_ATTR, source.declared_sha256),
                (SOURCE_SHA256_MATCHES_ATTR, source.matches_declared),
            ):
                if value is not None:
                    attrs[attr] = value
                elif attr in attrs:
                    del attrs[attr]  # a source recorded again does not keep what the previous one said

    def save_raw_scan(self, samples: ScanSamplesDTO) -> None:
        if self._file is None:
            raise RuntimeError("HDF5 file not open. Cannot save the raw scan.")
        if RAW_SCAN_GROUP in self._file:
            del self._file[RAW_SCAN_GROUP]
        group = self._file.create_group(RAW_SCAN_GROUP)
        group.create_dataset(RAW_POSITIONS_DATASET, data=np.column_stack([samples.x, samples.y]),
                             compression='gzip', compression_opts=4)
        group.create_dataset(RAW_VALUES_DATASET, data=np.asarray(samples.values, dtype=float),
                             compression='gzip', compression_opts=4)
        group.attrs[RAW_CHANNEL_NAMES_ATTR] = json.dumps(list(samples.channel_names))
        self._file.flush()

    def save_step(self, step_name: str, data: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._file is None:
            raise RuntimeError("HDF5 file not open. Cannot save step.")
        group_name = step_group_name(step_name)
        if group_name in self._file:
            del self._file[group_name]
        group = self._file.create_group(group_name)
        group.create_dataset(DATA_DATASET, data=data, compression='gzip', compression_opts=4)
        group.attrs[TIMESTAMP_ATTR] = datetime.now().isoformat()
        group.attrs[STEP_NAME_ATTR] = step_name
        group.attrs[DATA_SHAPE_ATTR] = data.shape
        group.attrs[DATA_DTYPE_ATTR] = str(data.dtype)

        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (dict, list, tuple)):
                    try:
                        if isinstance(value, (list, tuple)) and len(value) > 0 and isinstance(value[0], str):
                            group.attrs[key] = json.dumps(value)
                        elif isinstance(value, np.ndarray) and value.dtype.kind in ('U', 'S'):
                            group.attrs[key] = json.dumps(value.tolist())
                        elif isinstance(value, (np.ndarray, list, tuple)):
                            group.attrs[key] = np.array(value)
                        else:
                            group.attrs[key] = json.dumps(value)
                    except Exception as e:
                        logger.debug(
                            "hdf5.attribute_stored_as_text file=%s step=%s key=%s error_type=%s",
                            self._file_path, step_name, key, type(e).__name__,
                        )
                        group.attrs[key] = str(value)
                elif isinstance(value, (str, int, float, bool)):
                    group.attrs[key] = value
                else:
                    group.attrs[key] = str(value)

        self._history.append(f"{step_name} @ {datetime.now().isoformat()}")
        self._file.attrs[PROCESSING_HISTORY_ATTR] = self._history
        self._file.flush()

    def load_step(self, step_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        if self._file is None:
            raise RuntimeError("HDF5 file not open. Cannot load step.")
        group_name = step_group_name(step_name)
        if group_name not in self._file:
            raise KeyError(f"Processing step '{step_name}' not found in HDF5 file.")
        group = self._file[group_name]
        return np.array(group[DATA_DATASET]), dict(group.attrs)

    def processing_history(self) -> List[str]:
        return list(self._history)

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def __del__(self):
        self.close()
