"""
Hdf5StepReader - Reads the processing steps stored in an HDF5 file (see hdf5_step_reader_intention.md).
"""

import logging
import os
from typing import List

import h5py
import numpy as np

from ...application.field_map_service.dtos.stored_step_dto import StoredStepDTO
from ...application.field_map_service.ports.i_step_reader import IStepReader
from ..hdf5_step_format.hdf5_step_format import DATA_DATASET, RAW_SCAN_GROUP, processing_store_path, step_group_name

logger = logging.getLogger(__name__)


class Hdf5StepReader(IStepReader):
    def list_steps(self, acquisition_file: str) -> List[str]:
        path = processing_store_path(acquisition_file)
        if not os.path.exists(path):
            logger.warning("scan.file_missing path=%s", path)
            return []
        try:
            with h5py.File(path, 'r') as h5:
                return [key for key in h5.keys() if isinstance(h5[key], h5py.Group) and key != RAW_SCAN_GROUP]
        except Exception as e:
            logger.warning("scan.steps_unreadable path=%s error_type=%s error=%s", path, type(e).__name__, e, exc_info=True)
            return []

    def read_step(self, acquisition_file: str, step_name: str) -> StoredStepDTO:
        path = processing_store_path(acquisition_file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"HDF5 file not found: {path}")
        with h5py.File(path, 'r') as h5:
            group_name = step_group_name(step_name)
            if group_name not in h5:
                raise KeyError(f"Processing step '{step_name}' not found in HDF5 file.")
            group = h5[group_name]
            return StoredStepDTO(data=np.array(group[DATA_DATASET]), metadata=dict(group.attrs))
