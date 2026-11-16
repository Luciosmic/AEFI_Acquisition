"""
FakeHdf5StepReader - Steps held in memory (see fake_hdf5_step_reader_intention.md).
"""

from typing import Any, Dict, List, Tuple

import numpy as np

from ....application.field_map_service.dtos.stored_step_dto import StoredStepDTO
from ....application.field_map_service.ports.i_step_reader import IStepReader


class FakeHdf5StepReader(IStepReader):
    def __init__(self) -> None:
        self._files: Dict[str, Dict[str, Tuple[np.ndarray, Dict[str, Any]]]] = {}

    def add_step(self, acquisition_file: str, step_name: str, data: np.ndarray, metadata: Dict[str, Any]) -> None:
        self._files.setdefault(acquisition_file, {})[step_name] = (np.array(data), dict(metadata))

    def list_steps(self, acquisition_file: str) -> List[str]:
        return list(self._files.get(acquisition_file, {}))

    def read_step(self, acquisition_file: str, step_name: str) -> StoredStepDTO:
        if acquisition_file not in self._files:
            raise FileNotFoundError(f"HDF5 file not found: {acquisition_file}")
        if step_name not in self._files[acquisition_file]:
            raise KeyError(f"Processing step '{step_name}' not found in HDF5 file.")
        data, metadata = self._files[acquisition_file][step_name]
        return StoredStepDTO(data=np.array(data), metadata=dict(metadata))
